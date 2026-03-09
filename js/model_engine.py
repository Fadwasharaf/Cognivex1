"""
model_engine.py — Cognivex
Handles Isolation Forest training, prediction, versioning, and in-memory caching.
"""

import io
import logging
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# RISK LEVEL THRESHOLDS (configurable)
# ─────────────────────────────────────────────
THRESHOLD_LOW = -0.1      # score > -0.1  → LOW
THRESHOLD_MEDIUM = -0.3   # score > -0.3  → MEDIUM
# score <= -0.3            → HIGH

RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"

# ─────────────────────────────────────────────
# FEATURE COLUMNS (must match behavior_features columns)
# ─────────────────────────────────────────────
FEATURE_COLUMNS = [
    "typing_speed",
    "backspace_ratio",
    "avg_keystroke_interval",
    "keystroke_variance",
    "avg_mouse_speed",
    "mouse_move_variance",
    "scroll_frequency",
    "idle_ratio",
]

# ─────────────────────────────────────────────
# IN-MEMORY MODEL CACHE
# Structure: { user_id: {"version": int, "model": IsolationForest} }
# ─────────────────────────────────────────────
_model_cache: dict = {}


# ─────────────────────────────────────────────
# SERIALIZE / DESERIALIZE
# ─────────────────────────────────────────────

def serialize_model(model: IsolationForest) -> bytes:
    """Serialize model to bytes using joblib for Supabase storage."""
    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    buffer.seek(0)
    return buffer.read()


def deserialize_model(model_bytes: bytes) -> IsolationForest:
    """Deserialize model from bytes retrieved from Supabase."""
    buffer = io.BytesIO(model_bytes)
    return joblib.load(buffer)


# ─────────────────────────────────────────────
# FEATURE PREP
# ─────────────────────────────────────────────

def features_to_array(feature_rows: list[dict]) -> np.ndarray:
    """
    Convert a list of feature dicts (from behavior_features rows)
    into a 2D numpy array with consistent column order.

    Args:
        feature_rows: list of dicts, each containing the 8 feature keys.

    Returns:
        np.ndarray of shape (n_samples, 8)
    """
    data = []
    for row in feature_rows:
        data.append([float(row.get(col, 0.0) or 0.0) for col in FEATURE_COLUMNS])
    return np.array(data)


def single_feature_array(feature_dict: dict) -> np.ndarray:
    """
    Convert a single feature dict to a 2D numpy array (1 row).
    Used for in-session scoring.
    """
    return np.array([[float(feature_dict.get(col, 0.0) or 0.0) for col in FEATURE_COLUMNS]])


# ─────────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────────

def train_model(feature_rows: list[dict]) -> IsolationForest:
    """
    Train an Isolation Forest on the provided feature rows.

    Args:
        feature_rows: list of dicts from behavior_features (at least 15 rows recommended).

    Returns:
        Trained IsolationForest instance.
    """
    if len(feature_rows) < 1:
        raise ValueError("Cannot train model: no feature rows provided.")

    X = features_to_array(feature_rows)

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,  # assume ~10% anomalous sessions
        random_state=42,
        max_samples="auto",
    )
    model.fit(X)
    logger.info(f"Model trained on {len(feature_rows)} rows.")
    return model


# ─────────────────────────────────────────────
# PREDICTION & RISK SCORING
# ─────────────────────────────────────────────

def predict_risk(model: IsolationForest, feature_dict: dict) -> dict:
    """
    Score a single feature snapshot against the trained model.

    Args:
        model: Trained IsolationForest.
        feature_dict: dict with the 8 feature keys.

    Returns:
        dict with keys: score (float), risk_level (str)
    """
    X = single_feature_array(feature_dict)
    score = float(model.decision_function(X)[0])
    risk_level = score_to_risk(score)

    logger.debug(f"Score: {score:.4f} → Risk: {risk_level}")
    return {
        "score": round(score, 4),
        "risk_level": risk_level,
    }


def score_to_risk(score: float) -> str:
    """Map Isolation Forest decision_function score to a risk level."""
    if score > THRESHOLD_LOW:
        return RISK_LOW
    elif score > THRESHOLD_MEDIUM:
        return RISK_MEDIUM
    else:
        return RISK_HIGH


# ─────────────────────────────────────────────
# IN-MEMORY CACHE MANAGEMENT
# ─────────────────────────────────────────────

def cache_model(user_id: str, model: IsolationForest, version: int):
    """Store a trained model in the in-memory cache."""
    _model_cache[user_id] = {
        "version": version,
        "model": model,
    }
    logger.info(f"Model cached for user {user_id} (version {version}).")


def get_cached_model(user_id: str) -> dict | None:
    """
    Retrieve cached model for a user.

    Returns:
        dict with 'version' and 'model', or None if not cached.
    """
    return _model_cache.get(user_id)


def invalidate_cache(user_id: str):
    """Remove a user's model from the in-memory cache (called before retraining)."""
    if user_id in _model_cache:
        del _model_cache[user_id]
        logger.info(f"Cache invalidated for user {user_id}.")


def is_cache_stale(user_id: str, db_model_version: int) -> bool:
    """
    Check if the cached model version is out of sync with the DB version.

    Args:
        user_id: The user's UUID.
        db_model_version: The model_version stored in model_metadata.

    Returns:
        True if stale (needs reload), False if up to date.
    """
    cached = _model_cache.get(user_id)
    if cached is None:
        return True
    return cached["version"] != db_model_version


# ─────────────────────────────────────────────
# HIGH-LEVEL: LOAD MODEL (cache-aware)
# ─────────────────────────────────────────────

def load_model_for_user(user_id: str, model_metadata_row: dict) -> IsolationForest | None:
    """
    Load model for a user, using cache if up to date, otherwise deserializing from DB bytes.

    Args:
        user_id: The user's UUID.
        model_metadata_row: Row from model_metadata table, must include
                            'model_version' (int) and 'model_bytes' (bytes or base64).

    Returns:
        IsolationForest instance, or None if no model exists.
    """
    if model_metadata_row is None:
        return None

    db_version = model_metadata_row["model_version"]

    # Return cached model if version matches
    if not is_cache_stale(user_id, db_version):
        logger.debug(f"Cache hit for user {user_id} (version {db_version}).")
        return _model_cache[user_id]["model"]

    # Deserialize from DB and update cache
    logger.info(f"Cache miss for user {user_id}. Loading from DB (version {db_version}).")
    raw_bytes = model_metadata_row["model_bytes"]

    # Handle base64 string if stored as text in Supabase
    if isinstance(raw_bytes, str):
        import base64
        raw_bytes = base64.b64decode(raw_bytes)

    model = deserialize_model(raw_bytes)
    cache_model(user_id, model, db_version)
    return model


# ─────────────────────────────────────────────
# HIGH-LEVEL: TRAIN AND PREPARE FOR STORAGE
# ─────────────────────────────────────────────

def build_model_payload(
    user_id: str,
    feature_rows: list[dict],
    current_version: int,
    total_sessions: int,
) -> dict:
    """
    Train a model and prepare the full payload for upserting into model_metadata.

    Args:
        user_id: The user's UUID.
        feature_rows: Rows from behavior_features to train on.
        current_version: Existing version number (pass 0 for first train).
        total_sessions: Current total session count for this user.

    Returns:
        dict ready to upsert into model_metadata table.
    """
    import base64

    model = train_model(feature_rows)
    new_version = current_version + 1
    model_bytes = serialize_model(model)

    # Cache immediately after training
    cache_model(user_id, model, new_version)

    return {
        "user_id": user_id,
        "model_bytes": base64.b64encode(model_bytes).decode("utf-8"),
        "model_version": new_version,
        "last_trained_count": total_sessions,
        "total_sessions": total_sessions,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }