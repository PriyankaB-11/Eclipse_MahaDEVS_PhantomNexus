from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"
SYNTHETIC_DATASET_PATH = DATASET_DIR / "iot_sample.csv"
NBAIOT_DATASET_PATH = DATASET_DIR / "iot_sample_n_baiot.csv"
DATASET_PATH = SYNTHETIC_DATASET_PATH
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
    if telemetry.empty:
        raise ValueError("Telemetry dataset is empty")

    telemetry["timestamp"] = pd.to_datetime(telemetry["timestamp"], utc=True)
    for column in NUMERIC_COLUMNS:
        telemetry[column] = pd.to_numeric(telemetry[column], errors="coerce").fillna(0)

    telemetry = telemetry.dropna(subset=["device_id", "src_ip", "dest_ip", "protocol"])
    telemetry["dest_port"] = telemetry["dest_port"].astype(int)
    telemetry["bytes"] = telemetry["bytes"].astype(float)
    telemetry["packets"] = telemetry["packets"].astype(float)

    return telemetry.sort_values(["device_id", "timestamp"]).reset_index(drop=True)


def build_device_ip_index(telemetry: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    latest_device_ips = (
        telemetry.sort_values("timestamp")
        .groupby("device_id")["src_ip"]
        .last()
        .to_dict()
    )
    ip_to_device = {ip: device_id for device_id, ip in latest_device_ips.items()}
    return latest_device_ips, ip_to_device
