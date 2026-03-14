from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"
SYNTHETIC_DATASET_PATH = DATASET_DIR / "iot_sample.csv"
NBAIOT_DATASET_PATH = DATASET_DIR / "iot_sample_n_baiot.csv"
DATASET_PATH = SYNTHETIC_DATASET_PATH
UPLOADS_DIR = DATASET_DIR / "uploads"
REQUIRED_COLUMNS = [
    "device_id",
    "timestamp",
    "src_ip",
    "dest_ip",
    "dest_port",
    "protocol",
    "bytes",
    "packets",
]
NUMERIC_COLUMNS = ["dest_port", "bytes", "packets"]


def resolve_dataset_path(csv_path: str | Path | None = None, source: str | None = None) -> Path:
    if csv_path:
        return Path(csv_path)

    selected_source = (source or os.getenv("PHANTOM_DATA_SOURCE", "synthetic")).strip().lower()
    if selected_source in {"synthetic", "demo", "default"}:
        return SYNTHETIC_DATASET_PATH
    if selected_source in {"n_baiot", "n-baiot", "nbaiot"}:
        return NBAIOT_DATASET_PATH

    allowed = "synthetic | n_baiot"
    raise ValueError(f"Unsupported data source '{selected_source}'. Allowed values: {allowed}")


def validate_telemetry_dataframe(telemetry: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in telemetry.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Telemetry dataset is missing required columns: {missing}")

    if telemetry.empty:
        raise ValueError("Telemetry dataset is empty")

    prepared = telemetry.copy()
    prepared["timestamp"] = pd.to_datetime(prepared["timestamp"], utc=True, errors="coerce")
    for column in NUMERIC_COLUMNS:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

    prepared = prepared.dropna(subset=REQUIRED_COLUMNS)
    if prepared.empty:
        raise ValueError("Telemetry dataset has no valid rows after validation")

    prepared["dest_port"] = prepared["dest_port"].astype(int)
    prepared["bytes"] = prepared["bytes"].astype(float)
    prepared["packets"] = prepared["packets"].astype(float)

    return prepared.sort_values(["device_id", "timestamp"]).reset_index(drop=True)


def load_telemetry(csv_path: str | Path | None = None, source: str | None = None) -> pd.DataFrame:
    path = resolve_dataset_path(csv_path=csv_path, source=source)
    if not path.exists():
        if path == NBAIOT_DATASET_PATH:
            raise FileNotFoundError(
                "N-BaIoT preprocessed dataset not found. "
                "Run backend/scripts/preprocess_n_baiot.py first."
            )
        raise FileNotFoundError(f"Telemetry dataset not found at {path}")

    telemetry = pd.read_csv(path)
    return validate_telemetry_dataframe(telemetry)


def build_device_ip_index(telemetry: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    latest_device_ips = (
        telemetry.sort_values("timestamp")
        .groupby("device_id")["src_ip"]
        .last()
        .to_dict()
    )
    ip_to_device = {ip: device_id for device_id, ip in latest_device_ips.items()}
    return latest_device_ips, ip_to_device
