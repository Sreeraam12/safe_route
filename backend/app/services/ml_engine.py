import json
from pathlib import Path

import lightgbm as lgb


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Model artifacts
MODEL_PATH = BASE_DIR / "artifacts" / "saferoute_lightgbm_real_weather.txt"
FEATURES_PATH = BASE_DIR / "artifacts" / "saferoute_ml_features_35.json"


print("Loading SafeRoute ML model...")

MODEL = lgb.Booster(
    model_file=str(MODEL_PATH)
)

with open(FEATURES_PATH, "r", encoding="utf-8") as file:
    ML_FEATURES = json.load(file)


print(
    f"SafeRoute ML model loaded successfully "
    f"with {len(ML_FEATURES)} features."
)


def predict_risk(features: dict) -> float:
    """
    Predict risk score for one road segment.
    """

    missing_features = [
        feature
        for feature in ML_FEATURES
        if feature not in features
    ]

    if missing_features:
        raise ValueError(
            f"Missing ML features: {missing_features}"
        )

    feature_values = [
        features[feature]
        for feature in ML_FEATURES
    ]

    prediction = MODEL.predict(
        [feature_values]
    )[0]

    return float(
        max(0.0, min(100.0, prediction))
    )

from datetime import datetime


def build_time_features(travel_datetime: datetime) -> dict:
    """
    Build the time-dependent ML features used by
    the SafeRoute LightGBM model.
    """

    hour = travel_datetime.hour
    day_of_week = travel_datetime.weekday()

    is_weekend = int(day_of_week >= 5)
    is_night = int(hour < 6 or hour >= 18)

    import math

    hour_sin = math.sin(
        2 * math.pi * hour / 24
    )

    hour_cos = math.cos(
        2 * math.pi * hour / 24
    )

    return {
        "hour": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_night": is_night,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
    }