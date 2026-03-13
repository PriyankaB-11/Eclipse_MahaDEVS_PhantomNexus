from __future__ import annotations

from pathlib import Path

import pandas as pd

DATASET_PATH = Path(__file__).resolve().parents[1] / "dataset" / "iot_sample.csv"
NUMERIC_COLUMNS = ["dest_port", "bytes", "packets"]


def load_telemetry(csv_path: str | Path | None = None) -> pd.DataFrame:
    path = Path(csv_path) if csv_path else DATASET_PATH
    if not path.exists():
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
