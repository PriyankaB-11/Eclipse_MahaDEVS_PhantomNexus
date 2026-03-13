from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import random

import pandas as pd

DATASET_PATH = Path(__file__).resolve().parents[1] / "dataset" / "iot_sample.csv"
RANDOM = random.Random(11)
DEVICES = {
    "camera_01": {"ip": "10.0.0.11", "cloud": ["34.117.59.81", "44.199.21.10"], "ports": [443, 554], "internal": "10.0.0.5"},
    "camera_02": {"ip": "10.0.0.12", "cloud": ["34.117.59.81", "44.199.21.10"], "ports": [443, 554], "internal": "10.0.0.5"},
    "thermostat_01": {"ip": "10.0.0.21", "cloud": ["52.25.73.90"], "ports": [443, 8883], "internal": "10.0.0.5"},
    "speaker_01": {"ip": "10.0.0.31", "cloud": ["54.214.14.121"], "ports": [443, 8009], "internal": "10.0.0.5"},
    "router_01": {"ip": "10.0.0.1", "cloud": ["8.8.8.8", "1.1.1.1"], "ports": [53, 443], "internal": "10.0.0.5"},
    "lock_01": {"ip": "10.0.0.41", "cloud": ["18.211.90.52"], "ports": [443], "internal": "10.0.0.5"},
    "sensor_01": {"ip": "10.0.0.51", "cloud": ["35.171.23.17"], "ports": [443, 1883], "internal": "10.0.0.5"},
    "hub_01": {"ip": "10.0.0.5", "cloud": ["52.204.44.12"], "ports": [443, 8883], "internal": "10.0.0.1"},
}
MALICIOUS_EXTERNALS = ["185.244.25.72", "103.245.125.11", "91.240.118.7"]


def _row(device_id: str, timestamp: datetime, dest_ip: str, dest_port: int, protocol: str, bytes_sent: int, packets: int) -> dict:
    return {
        "device_id": device_id,
        "timestamp": timestamp.isoformat(),
        "src_ip": DEVICES[device_id]["ip"],
        "dest_ip": dest_ip,
        "dest_port": dest_port,
        "protocol": protocol,
        "bytes": bytes_sent,
        "packets": packets,
    }


def build_clean_traffic(start: datetime, hours: int = 24) -> list[dict]:
    rows: list[dict] = []
    for hour in range(hours):
        base_time = start + timedelta(hours=hour)
        for device_id, config in DEVICES.items():
            for flow_index in range(3):
                timestamp = base_time + timedelta(minutes=flow_index * 18 + RANDOM.randint(0, 4))
                rows.append(
                    _row(
                        device_id,
                        timestamp,
                        RANDOM.choice(config["cloud"]),
                        RANDOM.choice(config["ports"]),
                        "TCP",
                        RANDOM.randint(180, 920),
                        RANDOM.randint(4, 18),
                    )
                )
            rows.append(
                _row(
                    device_id,
                    base_time + timedelta(minutes=52),
                    config["internal"],
                    8883 if device_id != "router_01" else 53,
                    "UDP" if device_id == "router_01" else "TCP",
                    RANDOM.randint(90, 250),
                    RANDOM.randint(2, 8),
                )
            )
    return rows


def inject_botnet_recruitment(rows: list[dict], start: datetime) -> None:
    infection_start = start + timedelta(hours=26)

    for step in range(18):
        timestamp = infection_start + timedelta(minutes=step * 10)
        rows.append(_row("camera_01", timestamp, MALICIOUS_EXTERNALS[0], 23, "TCP", 110, 3))
        rows.append(_row("camera_01", timestamp + timedelta(seconds=15), MALICIOUS_EXTERNALS[1], 53, "UDP", 96, 2))

    for step in range(12):
        timestamp = infection_start + timedelta(minutes=step * 15)
        rows.append(_row("speaker_01", timestamp, MALICIOUS_EXTERNALS[2], 48101, "TCP", 128, 3))

    for offset in range(6):
        timestamp = infection_start + timedelta(hours=offset, minutes=42)
        rows.append(_row("camera_01", timestamp, "10.0.0.31", 4444, "TCP", 140, 4))
        rows.append(_row("speaker_01", timestamp + timedelta(minutes=5), "10.0.0.51", 5555, "TCP", 150, 4))
        rows.append(_row("sensor_01", timestamp + timedelta(minutes=8), MALICIOUS_EXTERNALS[1], 1883, "TCP", 310, 7))


def main() -> None:
    start = datetime(2026, 3, 12, 0, 0, tzinfo=UTC)
    rows = build_clean_traffic(start, hours=30)
    inject_botnet_recruitment(rows, start)
    dataset = pd.DataFrame(rows).sort_values(["device_id", "timestamp"]).reset_index(drop=True)
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(DATASET_PATH, index=False)
    print(f"Wrote {len(dataset)} rows to {DATASET_PATH}")


if __name__ == "__main__":
    main()
