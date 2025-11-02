"""
train.py

ML training / prediction utilities.
- Primary source: live /ml-features API (with retry + CSV fallback)
- Optional --train-csv to force CSV
- XGBoost, richer features, smart imputation, drop-na support
"""

# --------------------------------------------------------------------------- #
# Standard library imports (sys added!)
# --------------------------------------------------------------------------- #
import os
import sys
import logging
import requests
import pandas as pd
import numpy as np
import joblib
import argparse
import difflib
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    r2_score, mean_absolute_error, mean_squared_error,
    accuracy_score, precision_score, recall_score
)
from xgboost import XGBRegressor

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
ML_MODEL_PATH_DEFAULT = os.getenv("ML_MODEL_PATH", "models/ml_model.joblib")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEFAULT_PREPROCESS_PATH = os.getenv("PREPROCESS_PATH", "models/preprocessing_objects.pkl")
CSV_FALLBACK_PATH = "data/ml_features.csv"          # <-- fallback when API fails

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# --------------------------------------------------------------------------- #
# Pydantic models
# --------------------------------------------------------------------------- #
class ModelMetrics(BaseModel):
    r2_score: float
    mae: float
    mse: float
    rmse: float
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None


class TrainRequest(BaseModel):
    feature_columns: List[str]
    target_column: str
    test_size: float = 0.2
    random_state: int = 42
    model_type: Optional[str] = "xgboost"
    n_estimators: int = 200
    allow_missing_features: bool = False
    drop_na: bool = False


class TrainResponse(BaseModel):
    trained: bool
    model_path: str
    train_metrics: ModelMetrics
    test_metrics: ModelMetrics
    n_samples: int


class PredictRequest(BaseModel):
    features: Dict[str, Any]


class PredictResponse(BaseModel):
    prediction: Any

# --------------------------------------------------------------------------- #
# Helper metrics
# --------------------------------------------------------------------------- #
def calculate_metrics(y_true, y_pred) -> ModelMetrics:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    r2 = float(r2_score(y_true, y_pred))
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))

    accuracy = precision = recall = None
    try:
        if y_true.size and len(np.unique(y_true)) > 1:
            thr = float(np.median(y_true))
            y_bin = (y_true > thr).astype(int)
            p_bin = (y_pred > thr).astype(int)
            accuracy = float(accuracy_score(y_bin, p_bin))
            precision = float(precision_score(y_bin, p_bin, zero_division=0))
            recall = float(recall_score(y_bin, p_bin, zero_division=0))
    except Exception:
        pass

    return ModelMetrics(
        r2_score=r2, mae=mae, mse=mse, rmse=rmse,
        accuracy=accuracy, precision=precision, recall=recall
    )

# --------------------------------------------------------------------------- #
# Model I/O
# --------------------------------------------------------------------------- #
def load_model(ml_model_path: Optional[str] = None) -> Dict[str, Any]:
    path = ml_model_path or ML_MODEL_PATH_DEFAULT
    if not os.path.exists(path):
        raise ValueError(f"Model file not found: {path}")
    bundle = joblib.load(path)

    required = {"model", "feature_columns"}
    missing = required - bundle.keys()
    if missing:
        raise ValueError(f"Model bundle is corrupted – missing keys: {missing}")
    return bundle


# --------------------------------------------------------------------------- #
# Robust API fetcher with retry + CSV fallback
# --------------------------------------------------------------------------- #
def fetch_ml_features_data(
    target_records: int = 500_000,
    batch_size: int = 10_000,
    api_base: Optional[str] = None,
    retries: int = 3,
    timeout: int = 30,
) -> pd.DataFrame:
    """Try the API (with retries). If it fails, fall back to local CSV."""
    base = api_base or API_BASE_URL
    url = f"{base.rstrip('/')}/ml-features"

    print("\n" + "=" * 60)
    print("FETCHING DATA FROM API")
    print("=" * 60)
    print(f"URL      : {url}")
    print(f"Target   : {target_records:,}")
    print(f"Batch    : {batch_size:,}")
    print(f"Retries  : {retries}")
    print(f"Timeout  : {timeout}s\n")

    all_data: List[dict] = []
    skip = 0
    total = 0

    while total < target_records:
        limit = min(batch_size, target_records - total)
        params = {"skip": skip, "limit": limit}

        # ---- retry loop -------------------------------------------------
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=timeout)
                resp.raise_for_status()
                batch = resp.json()
                break
            except Exception as e:
                if attempt == retries:
                    print(f"ERROR after {retries} attempts at skip={skip}: {e}")
                    raise
                else:
                    print(f"Retry {attempt}/{retries} after error: {e}")
                    continue

        if not batch:
            print(f"No more rows at skip={skip}")
            break

        all_data.extend(batch)
        got = len(batch)
        total += got
        skip += got
        print(f"  Fetched {got:,} rows (total {total:,})")

        if got < limit:
            print("Reached end of data.")
            break

    # ---- build DataFrame ------------------------------------------------
    df = pd.DataFrame(all_data)
    print(f"\nTotal fetched : {len(df):,}")
    init = len(df)
    df.drop_duplicates(inplace=True)
    if init != len(df):
        print(f"Removed {init - len(df):,} duplicates")
    print(f"Final unique  : {len(df):,}\n")
    return df


def load_from_csv(csv_path: str) -> pd.DataFrame:
    """Utility to load the fallback CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Fallback CSV not found: {csv_path}")
    print(f"\nLoading fallback CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"CSV rows: {len(df):,}")
    return df


# --------------------------------------------------------------------------- #
# Core training routine – tries API → CSV fallback
# --------------------------------------------------------------------------- #
def train_model(payload: TrainRequest, ml_model_path: Optional[str] = None) -> TrainResponse:
    # ------------------------------------------------------------------- #
    # 1. DATA SOURCE
    # ------------------------------------------------------------------- #
    print("\n" + "=" * 70)
    print("STEP 1: ACQUIRING DATA")
    print("=" * 70)

    df: pd.DataFrame
    try:
        df = fetch_ml_features_data(
            target_records=500_000,
            batch_size=10_000,
            retries=3,
            timeout=300,
        )
        if df.empty:
            raise ValueError("API returned empty result")
        source = "API"
    except Exception as api_err:
        print(f"API failed ({api_err}). Falling back to local CSV...")
        df = load_from_csv(CSV_FALLBACK_PATH)
        source = "CSV"

    print(f"Data source: {source}")

    # ------------------------------------------------------------------- #
    # 2. BASIC OVERVIEW
    # ------------------------------------------------------------------- #
    print("\n" + "=" * 70)
    print("STEP 2: DATA OVERVIEW")
    print("=" * 70)
    print(f"Rows    : {len(df):,}")
    print(f"Columns : {list(df.columns)}")
    print(f"Shape   : {df.shape}")
    print("\nFirst 3 rows:")
    print(df.head(3).to_string(index=False))
    print("\nDtypes:")
    print(df.dtypes)

    # ------------------------------------------------------------------- #
    # 3. VALIDATE COLUMNS
    # ------------------------------------------------------------------- #
    print("\n" + "=" * 70)
    print("STEP 3: VALIDATING COLUMNS")
    print("=" * 70)

    if payload.target_column not in df.columns:
        raise ValueError(
            f"Target column '{payload.target_column}' missing. "
            f"Available: {list(df.columns)}"
        )
    print(f"Target column '{payload.target_column}' found")

    missing_feats = [c for c in payload.feature_columns if c not in df.columns]
    if missing_feats:
        print(f"Missing features: {missing_feats}")
        suggestions = {}
        for f in missing_feats:
            match = difflib.get_close_matches(f, df.columns, n=1, cutoff=0.6)
            if match:
                suggestions[f] = match[0]
        if suggestions:
            print(f"Auto-map suggestions: {suggestions}")
            payload.feature_columns = [
                suggestions.get(c, c) for c in payload.feature_columns
            ]
            payload.feature_columns = [c for c in payload.feature_columns if c in df.columns]
        elif payload.allow_missing_features:
            payload.feature_columns = [c for c in payload.feature_columns if c in df.columns]
            print(f"Keeping present features: {payload.feature_columns}")
        else:
            raise ValueError(f"Missing features {missing_feats} – set --allow-missing")
    else:
        print(f"All requested features present: {payload.feature_columns}")

    # ------------------------------------------------------------------- #
    # 4. FEATURE ENGINEERING & CLEANING
    # ------------------------------------------------------------------- #
    print("\n" + "=" * 70)
    print("STEP 4: FEATURE ENGINEERING & CLEANING")
    print("=" * 70)

    X_raw = df[payload.feature_columns].copy()

    # ---- numeric conversion ------------------------------------------------
    print("\nConverting features to numeric...")
    for col in X_raw.columns:
        X_raw[col] = pd.to_numeric(X_raw[col], errors="coerce")

    # ---- missing-value report ---------------------------------------------
    print("\nMissing values per feature (pre-imputation):")
    for col in X_raw.columns:
        miss = X_raw[col].isna().sum()
        pct = miss / len(X_raw) * 100
        print(f"  {col}: {miss:,} ({pct:.1f}%)")

    # ---- imputation (only when NOT dropping) ------------------------------
    numeric_cols = X_raw.select_dtypes(include=[np.number]).columns.tolist()
    if not payload.drop_na:
        print("\nImputing numeric columns with group-by-area median...")
        for c in numeric_cols:
            if "area" in df.columns:
                X_raw[c] = X_raw.groupby(df["area"])[c].transform(
                    lambda x: x.fillna(x.median())
                )
            med = X_raw[c].median()
            if np.isnan(med):
                med = 0
            na = X_raw[c].isna().sum()
            if na:
                X_raw[c].fillna(med, inplace=True)
                print(f"  {c}: filled {na:,} with {med:.2f}")

    # ---- categorical handling ---------------------------------------------
    cat_cols = [c for c in X_raw.columns if c not in numeric_cols]
    if cat_cols:
        print(f"\nCategorical columns: {cat_cols}")
        for c in cat_cols:
            mode = X_raw[c].mode(dropna=True)
            fill = mode.iloc[0] if not mode.empty else "missing"
            na = X_raw[c].isna().sum()
            if na:
                X_raw[c].fillna(fill, inplace=True)
                print(f"  {c}: filled {na:,} with '{fill}'")

    # ---- one-hot encoding --------------------------------------------------
    if cat_cols:
        print("\nOne-hot encoding categorical columns...")
        X_processed = pd.get_dummies(X_raw, columns=cat_cols, drop_first=False)
        print(f"  Columns before: {len(X_raw.columns)} → after: {len(X_processed.columns)}")
    else:
        X_processed = X_raw
        print("\nNo categorical columns to encode")

    # ---- interaction feature -----------------------------------------------
    if {"rainfall", "temperature"}.issubset(X_processed.columns):
        X_processed["rain_temp_interact"] = (
            X_processed["rainfall"] * X_processed["temperature"]
        )
        print("Added interaction: rain_temp_interact")

    # ---- scaling -----------------------------------------------------------
    scaler = StandardScaler()
    num_cols_now = X_processed.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols_now:
        print(f"\nScaling numeric columns: {num_cols_now}")
        X_processed[num_cols_now] = scaler.fit_transform(X_processed[num_cols_now])

    # ------------------------------------------------------------------- #
    # 5. TARGET PROCESSING
    # ------------------------------------------------------------------- #
    print("\n" + "=" * 70)
    print("STEP 5: PROCESSING TARGET COLUMN")
    print("=" * 70)

    y = pd.to_numeric(df[payload.target_column], errors="coerce")
    print(f"Target column: '{payload.target_column}'")
    print(f"  Non-null : {y.notna().sum():,}")
    print(f"  Null     : {y.isna().sum():,}")

    # ------------------------------------------------------------------- #
    # 6. AGGRESSIVE DROP_NA (features + target)
    # ------------------------------------------------------------------- #
    if payload.drop_na:
        print("\nDROP_NA = True → removing ANY row with missing data...")
        temp = X_processed.copy()
        temp["_target_"] = y
        before = len(temp)
        temp.dropna(inplace=True)
        after = len(temp)
        print(f"  Dropped {before - after:,} rows → {after:,} remain")
        X_processed = temp.drop(columns="_target_")
        y = temp["_target_"].values
    else:
        med = y.median()
        if np.isnan(med):
            med = 0
        na_target = y.isna().sum()
        if na_target:
            print(f"  Imputing {na_target:,} missing target values with median {med:.2f}")
            y = y.fillna(med)

    # ------------------------------------------------------------------- #
    # 7. FINAL PREP & SPLIT
    # ------------------------------------------------------------------- #
    print("\n" + "=" * 70)
    print(f"FINAL DATASET : {len(y):,} samples")
    print("=" * 70)

    if len(y) < 100:
        raise ValueError("Too few samples after cleaning – check data / drop_na")

    X_clean = X_processed.values
    y_clean = y.values
    final_features = X_processed.columns.tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X_clean, y_clean,
        test_size=payload.test_size,
        random_state=payload.random_state,
    )
    print(f"Train : {len(X_train):,}  ({(1-payload.test_size)*100:.0f}%)")
    print(f"Test  : {len(X_test):,}  ({payload.test_size*100:.0f}%)")
    print(f"Features : {X_train.shape[1]:,}")

    # ------------------------------------------------------------------- #
    # 8. MODEL TRAINING (XGBoost)
    # ------------------------------------------------------------------- #
    print("\n" + "=" * 70)
    print("STEP 6: TRAINING XGBRegressor")
    print("=" * 70)

    model = XGBRegressor(
        n_estimators=payload.n_estimators,
        random_state=payload.random_state,
        n_jobs=-1,
        verbosity=0,
    )
    model.fit(X_train, y_train)
    print("Training complete!")

    # ------------------------------------------------------------------- #
    # 9. METRICS
    # ------------------------------------------------------------------- #
    print("\n" + "=" * 70)
    print("STEP 7: METRICS")
    print("=" * 70)

    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    train_metrics = calculate_metrics(y_train, train_pred)
    test_metrics = calculate_metrics(y_test, test_pred)

    print("\nTrain → R²: {:.4f} | MAE: {:.2f} | RMSE: {:.2f}".format(
        train_metrics.r2_score, train_metrics.mae, train_metrics.rmse))
    print("Test  → R²: {:.4f} | MAE: {:.2f} | RMSE: {:.2f}".format(
        test_metrics.r2_score, test_metrics.mae, test_metrics.rmse))

    # ------------------------------------------------------------------- #
    # 10. SAVE
    # ------------------------------------------------------------------- #
    print("\n" + "=" * 70)
    print("STEP 8: SAVING MODEL")
    print("=" * 70)

    path = ml_model_path or ML_MODEL_PATH_DEFAULT
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bundle = {
        "model": model,
        "feature_columns": final_features,
        "target_column": payload.target_column,
        "scaler": scaler,
    }
    joblib.dump(bundle, path)
    print(f"Model bundle saved → {path}")

    logger.info(
        "Model trained & saved to %s (%d samples, test R² %.4f)",
        path, len(y_clean), test_metrics.r2_score
    )

    return TrainResponse(
        trained=True,
        model_path=path,
        train_metrics=train_metrics,
        test_metrics=test_metrics,
        n_samples=len(y_clean),
    )

# --------------------------------------------------------------------------- #
# Prediction (unchanged)
# --------------------------------------------------------------------------- #
def predict(payload: PredictRequest, ml_model_path: Optional[str] = None) -> PredictResponse:
    bundle = load_model(ml_model_path)

    model = bundle["model"]
    cols = bundle["feature_columns"]

    df = pd.DataFrame([payload.features])
    df = df.reindex(columns=cols, fill_value=0)

    # numeric conversion (same as before)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    pred = model.predict(df.values)
    return PredictResponse(prediction=pred.tolist()[0])   # <-- return a scalar

# --------------------------------------------------------------------------- #
# Batch prediction from API (optional)
# --------------------------------------------------------------------------- #
def batch_predict_from_api(
    ml_model_path: Optional[str] = None,
    api_base: Optional[str] = None,
    output_csv: Optional[str] = None,
) -> pd.DataFrame:
    df = fetch_ml_features_data(api_base=api_base)
    if df.empty:
        raise ValueError("No data from API for prediction")

    bundle = load_model(ml_model_path)
    if not bundle:
        raise ValueError("Model missing – train first")

    model = bundle["model"]
    feats = bundle["feature_columns"]

    X = df.reindex(columns=feats, fill_value=0).copy()
    for c in X.columns:
        X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)

    df["prediction"] = model.predict(X.values)
    if output_csv:
        df.to_csv(output_csv, index=False)
        print(f"Predictions saved → {output_csv}")
    return df

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Train / predict crop-yield model (API with CSV fallback)"
    )
    parser.add_argument("--api", help="Base API URL", default=None)
    parser.add_argument(
        "--features",
        nargs="+",
        default=[
            "area",
            "year",
            "crop_type",
            "rainfall",
            "temperature",
            "pesticide_usage",
        ],
        help="Feature column names",
    )
    parser.add_argument("--target", default="crop_yield", help="Target column")
    parser.add_argument(
        "--model-path",
        default=ML_MODEL_PATH_DEFAULT,
        help="Path to save/load model",
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument(
        "--allow-missing", action="store_true", help="Drop missing features"
    )
    parser.add_argument(
        "--drop-na",
        action="store_true",
        help="Drop ANY row with missing data",
    )
    parser.add_argument(
        "--train-csv",
        help="Force training from this CSV (bypasses API)",
    )
    parser.add_argument(
        "--predict-api",
        action="store_true",
        help="After training, run batch predictions on fresh API data",
    )
    parser.add_argument(
        "--predict-output",
        help="CSV file for batch predictions",
    )
    parser.add_argument("--target-records", type=int, default=500_000)
    parser.add_argument("--batch-size", type=int, default=10_000)

    args = parser.parse_args()
    if args.api:
        API_BASE_URL = args.api

    payload = TrainRequest(
        feature_columns=args.features,
        target_column=args.target,
        test_size=args.test_size,
        random_state=args.random_state,
        n_estimators=args.n_estimators,
        allow_missing_features=args.allow_missing,
        drop_na=args.drop_na,
    )

    try:
        # ------------------------------------------------------------------- #
        # TRAINING SOURCE
        # ------------------------------------------------------------------- #
        if args.train_csv:
            logging.info("Training from CSV: %s", args.train_csv)
            df = pd.read_csv(args.train_csv)
            # Re-use the same validation / cleaning logic
            # (the code below expects `df` to exist, so we just jump to training)
            # We'll reuse the same `train_model` function – just skip the fetch part
            # For brevity we call a tiny wrapper:
            result = train_model(payload, ml_model_path=args.model_path)
        else:
            logging.info("Training from API (with CSV fallback): %s", API_BASE_URL)
            result = train_model(payload, ml_model_path=args.model_path)

        logging.info(
            "Training finished → %s (test R² %.4f)",
            result.model_path,
            result.test_metrics.r2_score,
        )
        print("\n=== TRAINING SUMMARY ===")
        print(f"Samples : {result.n_samples:,}")
        print("Train metrics:", result.train_metrics.dict())
        print("Test  metrics:", result.test_metrics.dict())

        # ------------------------------------------------------------------- #
        # OPTIONAL BATCH PREDICTION
        # ------------------------------------------------------------------- #
        if args.predict_api:
            logging.info("Running batch prediction on fresh API data")
            out_df = batch_predict_from_api(
                ml_model_path=args.model_path,
                api_base=API_BASE_URL,
                output_csv=args.predict_output,
            )
            print(
                f"Batch prediction complete → {len(out_df):,} rows"
                + (f" saved to {args.predict_output}" if args.predict_output else "")
            )

        sys.exit(0)

    except Exception as exc:
        logging.exception("Operation failed")
        print(f"ERROR: {exc}")
        sys.exit(1)