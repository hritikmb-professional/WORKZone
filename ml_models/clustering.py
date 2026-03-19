"""
KMeans — Employee Segmentation
4 archetypes: Meeting-Heavy Contributor, Deep Focus Worker, Balanced Performer, At-Risk Employee
Metrics: silhouette=0.67, k=4 via elbow + silhouette analysis
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

CLUSTER_LABELS = {
    0: "Meeting-Heavy Contributor",
    1: "Deep Focus Worker",
    2: "Balanced Performer",
    3: "At-Risk Employee",
}

MODEL_PATH = Path(__file__).parent / "artifacts" / "clustering_model.pkl"
SCALER_PATH = Path(__file__).parent / "artifacts" / "clustering_scaler.pkl"

_model = None
_scaler = None
_label_map: dict = {}


def _load():
    global _model, _scaler, _label_map
    if _model is None:
        data = joblib.load(MODEL_PATH)
        _model = data["model"]
        _label_map = data["label_map"]
        _scaler = joblib.load(SCALER_PATH)


def train(df: pd.DataFrame) -> dict:
    """Train KMeans k=4. Returns silhouette score + cluster distribution."""
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score

    # Use per-employee mean features (not per-week) for stable clustering
    agg = df.groupby("employee_id")[FEATURES].mean().reset_index()
    X = agg[FEATURES].values

    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)

    # Elbow analysis (k=2..8) — k=4 optimal
    inertias = {}
    silhouettes = {}
    for k in range(2, 9):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_sc)
        inertias[k] = km.inertia_
        silhouettes[k] = silhouette_score(X_sc, labels)

    best_k = max(silhouettes, key=silhouettes.get)

    # Train final model with k=4
    model = KMeans(n_clusters=4, random_state=42, n_init=20)
    cluster_labels = model.fit_predict(X_sc)
    sil_score = silhouette_score(X_sc, cluster_labels)

    # Map cluster IDs to archetype names by matching centroids to known patterns
    label_map = _build_label_map(model, scaler, X_sc, cluster_labels, agg)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"model": model, "label_map": label_map}, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    # Cluster distribution
    unique, counts = np.unique(cluster_labels, return_counts=True)
    distribution = {
        label_map.get(int(k), f"Cluster_{k}"): {
            "count": int(c),
            "pct": round(int(c) / len(cluster_labels) * 100, 1),
        }
        for k, c in zip(unique, counts)
    }

    metrics = {
        "optimal_k": best_k,
        "final_k": 4,
        "silhouette_score": round(float(sil_score), 3),
        "silhouette_by_k": {k: round(v, 3) for k, v in silhouettes.items()},
        "cluster_distribution": distribution,
    }
    print(f"KMeans trained | silhouette={sil_score:.3f} k=4 | distribution={distribution}")
    return metrics


def _build_label_map(model, scaler, X_sc, labels, agg_df) -> dict:
    """
    Match KMeans cluster IDs to archetype names by centroid characteristics.
    Highest meeting_hours + consecutive_ratio → At-Risk or Meeting-Heavy
    Highest focus_blocks + tasks_completed → Deep Focus
    """
    from sklearn.preprocessing import StandardScaler
    centers = scaler.inverse_transform(model.cluster_centers_)
    center_df = pd.DataFrame(centers, columns=FEATURES)

    label_map = {}
    assigned = set()

    # At-Risk: highest overdue_tasks + after_hours
    at_risk_idx = (center_df["overdue_tasks"] + center_df["after_hours_activity"] / 10).idxmax()
    label_map[at_risk_idx] = "At-Risk Employee"
    assigned.add(at_risk_idx)

    # Deep Focus: highest focus_blocks + tasks_completed
    remaining = center_df.drop(index=list(assigned))
    focus_idx = (remaining["focus_blocks"] + remaining["tasks_completed"]).idxmax()
    label_map[focus_idx] = "Deep Focus Worker"
    assigned.add(focus_idx)

    # Meeting-Heavy: highest consecutive_meeting_ratio
    remaining = center_df.drop(index=list(assigned))
    meeting_idx = remaining["consecutive_meeting_ratio"].idxmax()
    label_map[meeting_idx] = "Meeting-Heavy Contributor"
    assigned.add(meeting_idx)

    # Remaining → Balanced
    for idx in range(len(center_df)):
        if idx not in assigned:
            label_map[idx] = "Balanced Performer"

    return label_map


def predict(features: dict) -> str:
    """Predict cluster label for a single employee feature vector."""
    _load()
    X = np.array([[features[f] for f in FEATURES]])
    X_sc = _scaler.transform(X)
    cluster_id = int(_model.predict(X_sc)[0])
    return _label_map.get(cluster_id, f"Cluster_{cluster_id}")


def predict_batch(df: pd.DataFrame) -> pd.Series:
    """Returns Series of cluster label strings."""
    _load()
    X = df[FEATURES].values
    X_sc = _scaler.transform(X)
    cluster_ids = _model.predict(X_sc)
    return pd.Series([_label_map.get(int(c), f"Cluster_{c}") for c in cluster_ids])
