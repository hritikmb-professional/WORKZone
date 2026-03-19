"""
Synthetic dataset generator.
500 employees x 12 weeks = 6,000 rows with realistic feature distributions.
Matches the feature engineering spec from the proposal exactly.
"""
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

N_EMPLOYEES = 500
N_WEEKS = 12
OUTPUT_PATH = Path(__file__).parent / "synthetic_dataset.csv"


def generate_dataset() -> pd.DataFrame:
    records = []

    for emp_id in range(N_EMPLOYEES):
        # Assign employee archetype — drives realistic feature distributions
        archetype = np.random.choice(
            ["meeting_heavy", "deep_focus", "balanced", "at_risk"],
            p=[0.27, 0.31, 0.29, 0.13],
        )

        for week in range(N_WEEKS):
            rec = _generate_week(emp_id, week, archetype)
            rec["employee_id"] = emp_id
            rec["week"] = week
            rec["archetype"] = archetype
            records.append(rec)

    df = pd.DataFrame(records)
    df["productivity_score"] = df.apply(_compute_score, axis=1)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Dataset saved: {len(df)} rows → {OUTPUT_PATH}")
    return df


def _generate_week(emp_id: int, week: int, archetype: str) -> dict:
    noise = lambda scale: np.random.normal(0, scale)

    if archetype == "meeting_heavy":
        meeting_hours         = np.clip(np.random.normal(25, 4) + noise(2), 15, 38)
        focus_blocks          = max(0, int(np.random.normal(2, 1)))
        tasks_completed       = max(0, int(np.random.normal(4, 2)))
        overdue_ratio         = np.clip(np.random.normal(0.35, 0.1), 0, 1)
        after_hours           = max(0, int(np.random.normal(3, 2)))
        response_time_avg     = np.clip(np.random.normal(6, 2), 0.5, 24)
        cal_fragmentation     = np.clip(np.random.normal(0.75, 0.1), 0, 1)
        consec_meeting_ratio  = np.clip(np.random.normal(0.60, 0.1), 0, 1)

    elif archetype == "deep_focus":
        meeting_hours         = np.clip(np.random.normal(8, 3) + noise(1), 1, 18)
        focus_blocks          = max(0, int(np.random.normal(9, 2)))
        tasks_completed       = max(0, int(np.random.normal(14, 3)))
        overdue_ratio         = np.clip(np.random.normal(0.05, 0.04), 0, 1)
        after_hours           = max(0, int(np.random.normal(1, 1)))
        response_time_avg     = np.clip(np.random.normal(4, 1.5), 0.5, 12)
        cal_fragmentation     = np.clip(np.random.normal(0.20, 0.08), 0, 1)
        consec_meeting_ratio  = np.clip(np.random.normal(0.10, 0.05), 0, 1)

    elif archetype == "balanced":
        meeting_hours         = np.clip(np.random.normal(15, 3) + noise(2), 5, 25)
        focus_blocks          = max(0, int(np.random.normal(6, 2)))
        tasks_completed       = max(0, int(np.random.normal(10, 2)))
        overdue_ratio         = np.clip(np.random.normal(0.12, 0.06), 0, 1)
        after_hours           = max(0, int(np.random.normal(1.5, 1)))
        response_time_avg     = np.clip(np.random.normal(3, 1), 0.5, 10)
        cal_fragmentation     = np.clip(np.random.normal(0.40, 0.1), 0, 1)
        consec_meeting_ratio  = np.clip(np.random.normal(0.25, 0.08), 0, 1)

    else:  # at_risk
        meeting_hours         = np.clip(np.random.normal(30, 5) + noise(3), 20, 45)
        focus_blocks          = max(0, int(np.random.normal(1, 1)))
        tasks_completed       = max(0, int(np.random.normal(3, 2)))
        overdue_ratio         = np.clip(np.random.normal(0.55, 0.15), 0, 1)
        after_hours           = max(0, int(np.random.normal(7, 3)))
        response_time_avg     = np.clip(np.random.normal(10, 3), 1, 24)
        cal_fragmentation     = np.clip(np.random.normal(0.85, 0.08), 0, 1)
        consec_meeting_ratio  = np.clip(np.random.normal(0.75, 0.1), 0, 1)

    return {
        "meeting_hours":            round(meeting_hours, 2),
        "focus_blocks":             focus_blocks,
        "tasks_completed":          tasks_completed,
        "overdue_tasks":            round(overdue_ratio, 3),
        "after_hours_activity":     after_hours,
        "response_time_avg":        round(response_time_avg, 2),
        "calendar_fragmentation":   round(cal_fragmentation, 3),
        "consecutive_meeting_ratio": round(consec_meeting_ratio, 3),
    }


def _compute_score(row) -> float:
    """
    Ground truth productivity score (0-100).
    consecutive_meeting_ratio has highest weight (matches feature importance=0.24).
    """
    score = 100.0
    score -= row["consecutive_meeting_ratio"] * 30   # highest weight
    score -= row["overdue_tasks"] * 25
    score -= min(row["meeting_hours"] / 40, 1) * 15
    score -= row["calendar_fragmentation"] * 10
    score -= min(row["after_hours_activity"] / 10, 1) * 8
    score += min(row["focus_blocks"] / 10, 1) * 15
    score += min(row["tasks_completed"] / 15, 1) * 10
    score -= (row["response_time_avg"] / 24) * 7
    score += np.random.normal(0, 3)  # realistic noise
    return round(np.clip(score, 0, 100), 2)


if __name__ == "__main__":
    generate_dataset()
