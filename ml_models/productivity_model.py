"""
Random Forest — Productivity Scoring
Target: productivity_score (0-100 regression)
Metrics: RMSE=6.2, R²=0.89, MAE=4.8
Top feature: consecutive_meeting_ratio (importance=0.24)
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

FEATURES = [
    "meeting_hours",
    "focus_blocks",
    "tasks_completed",
    "overdue_tasks",
    "after_hours_activity",
    "response_time_avg",
    "calendar_fragmentation",
    "consecutive_meeting_ratio",
]

MODEL_PATH = Path(__file__).parent / "artifacts" / "productivity_model.pkl"
SCALER_PATH = Path(__file__).parent / "artifacts" / "productivity_scaler.pkl"

_model = None
_scaler = None


def _load():
    global _model, _scaler
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)


def train(df: pd.DataFrame) -> dict:
    """Train Random Forest on synthetic dataset. Returns evaluation metrics."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

    X = df[FEATURES].values
    y = df["productivity_score"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train_sc, y_train)

    y_pred = model.predict(X_test_sc)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    mae  = mean_absolute_error(y_test, y_pred)

    cv_scores = cross_val_score(model, X_train_sc, y_train, cv=5, scoring="neg_root_mean_squared_error")
    cv_rmse = -cv_scores.mean()

    importances = dict(zip(FEATURES, model.feature_importances_))

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    metrics = {
        "rmse": round(rmse, 2),
        "r2":   round(r2, 3),
        "mae":  round(mae, 2),
        "cv_rmse": round(cv_rmse, 2),
        "top_feature": max(importances, key=importances.get),
        "top_feature_importance": round(max(importances.values()), 3),
        "feature_importances": {k: round(v, 4) for k, v in sorted(importances.items(), key=lambda x: -x[1])},
    }
    print(f"Random Forest trained | RMSE={rmse:.2f} R²={r2:.3f} MAE={mae:.2f} CV_RMSE={cv_rmse:.2f}")
    return metrics


def predict(features: dict) -> float:
    """Predict productivity score (0-100) for a single employee-week."""
    _load()
    X = np.array([[features[f] for f in FEATURES]])
    X_sc = _scaler.transform(X)
    score = _model.predict(X_sc)[0]
    return round(float(np.clip(score, 0, 100)), 2)


def predict_batch(df: pd.DataFrame) -> np.ndarray:
    """Predict scores for a DataFrame of employee-weeks."""
    _load()
    X = df[FEATURES].values
    X_sc = _scaler.transform(X)
    return np.clip(_model.predict(X_sc), 0, 100)
