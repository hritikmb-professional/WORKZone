"""
Train all 3 ML models in sequence.
Run: python -m ml_models.training.train_all
Output: ml_models/artifacts/*.pkl + metrics printed to console
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml_models.training.generate_dataset import generate_dataset
from ml_models import productivity_model, burnout_model, clustering


def main():
    print("=" * 60)
    print("AI Workplace Intelligence — ML Training Pipeline")
    print("=" * 60)

    # Step 1 — Generate dataset
    print("\n[1/4] Generating synthetic dataset (500 employees x 12 weeks)...")
    df = generate_dataset()
    print(f"      Rows: {len(df)} | Features: {len(df.columns)}")

    # Step 2 — Random Forest
    print("\n[2/4] Training Random Forest (Productivity Scoring)...")
    rf_metrics = productivity_model.train(df)
    print(f"      RMSE={rf_metrics['rmse']} | R²={rf_metrics['r2']} | MAE={rf_metrics['mae']}")
    print(f"      Top feature: {rf_metrics['top_feature']} ({rf_metrics['top_feature_importance']})")

    # Step 3 — Isolation Forest
    print("\n[3/4] Training Isolation Forest (Burnout Detection)...")
    if_metrics = burnout_model.train(df)
    print(f"      Flagged: {if_metrics['flagged_count']} ({if_metrics['flag_rate']:.1%})")
    if if_metrics["precision_at_k"]:
        print(f"      Precision@k: {if_metrics['precision_at_k']}")

    # Step 4 — KMeans
    print("\n[4/4] Training KMeans (Employee Clustering)...")
    km_metrics = clustering.train(df)
    print(f"      Silhouette: {km_metrics['silhouette_score']} | k={km_metrics['final_k']}")
    for label, stats in km_metrics["cluster_distribution"].items():
        print(f"      {label}: {stats['pct']}% ({stats['count']} employees)")

    # Save metrics summary
    metrics_path = Path(__file__).parent / "training_metrics.json"
    all_metrics = {
        "random_forest": rf_metrics,
        "isolation_forest": if_metrics,
        "kmeans": km_metrics,
    }
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\nAll models saved to ml_models/artifacts/")
    print(f"Metrics saved to {metrics_path}")
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
