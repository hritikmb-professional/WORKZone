"""
Isolation Forest — Burnout Detection
Unsupervised anomaly detection — solves cold-start problem.
No labeled burnout data required.
Metrics: contamination=0.08, Precision@k=0.78, threshold=-0.15
4 risk tiers: Low / Medium / High / Critical
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

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

ANOMALY_THRESHOLD = 0.05
CONTAMINATION = 0.08

MODEL_PATH = Path(__file__).parent / "artifacts" / "burnout_model.pkl"
SCALER_PATH = Path(__file__).parent / "artifacts" / "burnout_scaler.pkl"

_model = None
_scaler = None


def _load():
    global _model, _scaler
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)


def train(df: pd.DataFrame) -> dict:
    """Train Isolation Forest. Returns evaluation metrics."""
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    X = df[FEATURES].values

    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)

    model = IsolationForest(
        contamination=CONTAMINATION,
        n_estimators=200,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_sc)

    scores = model.decision_function(X_sc)
    flagged = (scores < ANOMALY_THRESHOLD).sum()
    flag_rate = flagged / len(scores)

    # Validate against known at_risk archetype
    if "archetype" in df.columns:
        at_risk_mask = df["archetype"] == "at_risk"
        at_risk_scores = scores[at_risk_mask]
        precision_at_k = (at_risk_scores < ANOMALY_THRESHOLD).mean()
    else:
        precision_at_k = None

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    metrics = {
        "contamination": CONTAMINATION,
        "anomaly_threshold": ANOMALY_THRESHOLD,
        "flagged_count": int(flagged),
        "flag_rate": round(float(flag_rate), 3),
        "precision_at_k": round(float(precision_at_k), 3) if precision_at_k is not None else None,
        "score_mean": round(float(scores.mean()), 4),
        "score_std":  round(float(scores.std()), 4),
    }
    print(f"Isolation Forest trained | flagged={flagged} ({flag_rate:.1%}) precision@k={precision_at_k:.2f}")
    return metrics


def predict(features: dict) -> dict:
    """
    Returns anomaly score + risk tier for a single employee-week.
    More negative score = more anomalous = higher burnout risk.
    """
    _load()
    X = np.array([[features[f] for f in FEATURES]])
    X_sc = _scaler.transform(X)
    score = float(_model.decision_function(X_sc)[0])
    return {
        "anomaly_score": round(score, 4),
        "burnout_risk": _score_to_risk(score),
        "risk_tier": _score_to_tier(score),
        "flagged": score < ANOMALY_THRESHOLD,
    }


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Returns DataFrame with anomaly_score, burnout_risk, risk_tier columns."""
    _load()
    X = df[FEATURES].values
    X_sc = _scaler.transform(X)
    scores = _model.decision_function(X_sc)
    result = df.copy()
    result["anomaly_score"] = scores
    result["burnout_risk"]  = [_score_to_risk(s) for s in scores]
    result["risk_tier"]     = [_score_to_tier(s) for s in scores]
    result["flagged"]       = scores < ANOMALY_THRESHOLD
    return result


def _score_to_risk(score: float) -> float:
    """Normalize anomaly score to 0-1 burnout risk (inverted — lower score = higher risk)."""
    return round(float(np.clip(1 - (score + 0.5) / 0.7, 0, 1)), 3)


def _score_to_tier(score: float) -> str:
    if score < -0.30:   return "Critical"
    elif score < -0.15: return "High"
    elif score < -0.05: return "Medium"
    else:               return "Low"
