from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

FEATURE_COLUMNS = [
    "MI_dir_L5_weight",
    "H_L5_mean",
    "HH_L5_mean",
    "HH_L5_std",
    "HH_jit_L5_mean",
    "HpHp_L5_mean",
]
EXTERNAL_IP_POOL = [
    "34.117.59.81",
    "44.199.21.10",
    "52.25.73.90",
    "54.214.14.121",
    "18.211.90.52",
]
MALICIOUS_IP_POOL = ["185.244.25.72", "103.245.125.11", "91.240.118.7"]


def _device_ip(index: int) -> str:
    return f"10.88.0.{11 + index}"


def _map_port(row: pd.Series) -> int:
    score = float(row["H_L5_mean"]) + float(row["HH_L5_std"]) + float(row["HpHp_L5_mean"])
    if score > 450:
        return 8443
    if score > 260:
        return 1883
    if score > 180:
        return 8080
    if score > 120:
        return 443
    if score > 80:
        return 554
    return 53


def _map_protocol(port: int) -> str:
    return "UDP" if port in {53, 123, 1900} else "TCP"


def _map_dest_ip(jitter_value: float, row_index: int, source_ip: str) -> str:
    internal_hub = "10.88.0.1"
    hash_value = int(abs(jitter_value) + row_index)
    if hash_value % 6 < 2:
        return internal_hub

    pool_index = hash_value % len(EXTERNAL_IP_POOL)
    destination = EXTERNAL_IP_POOL[pool_index]
    if destination == source_ip:
        destination = EXTERNAL_IP_POOL[(pool_index + 1) % len(EXTERNAL_IP_POOL)]
    return destination


def _convert_benign_rows(
    frame: pd.DataFrame,
    device_id: str,
    source_ip: str,
    start_time: datetime,
) -> list[dict]:
    rows: list[dict] = []
    for index, row in frame.reset_index(drop=True).iterrows():
        dest_port = _map_port(row)
        timestamp = start_time + timedelta(seconds=index * 3)
        bytes_value = max(
            60,
            int(round(float(row["H_L5_mean"]) + 0.35 * float(row["HH_L5_mean"]) + 0.2 * float(row["HpHp_L5_mean"]))),
        )
        packets = max(1, int(round(float(row["MI_dir_L5_weight"]))))
        dest_ip = _map_dest_ip(float(row["HH_jit_L5_mean"]), index, source_ip)
        rows.append(
            {
                "device_id": device_id,
                "timestamp": timestamp.isoformat(),
                "src_ip": source_ip,
                "dest_ip": dest_ip,
                "dest_port": dest_port,
                "protocol": _map_protocol(dest_port),
                "bytes": bytes_value,
                "packets": packets,
            }
        )
    return rows


def _inject_attack_like_rows(
    rows: list[dict],
    device_id: str,
    source_ip: str,
    base_time: datetime,
    attack_rows: int,
) -> None:
    for step in range(attack_rows):
        timestamp = base_time + timedelta(seconds=step * 9)
        malicious_ip = MALICIOUS_IP_POOL[step % len(MALICIOUS_IP_POOL)]
        attack_port = [23, 48101, 5555][step % 3]
        rows.append(
            {
                "device_id": device_id,
                "timestamp": timestamp.isoformat(),
                "src_ip": source_ip,
                "dest_ip": malicious_ip,
                "dest_port": attack_port,
                "protocol": "TCP",
                "bytes": 180 + (step % 7) * 22,
                "packets": 3 + (step % 4),
            }
        )


def preprocess_n_baiot(
    input_root: Path,
    output_csv: Path,
    max_devices: int,
    rows_per_device: int,
    inject_attacks: bool,
) -> pd.DataFrame:
    benign_files = sorted(input_root.glob("*/benign_traffic.csv"))
    if not benign_files:
        raise FileNotFoundError(f"No benign_traffic.csv files found under {input_root}")

    selected_files = benign_files[:max_devices]
    all_rows: list[dict] = []
    base_start = datetime(2026, 3, 1, 0, 0, tzinfo=UTC)

    for device_index, benign_path in enumerate(selected_files):
        device_id = benign_path.parent.name.lower().replace(" ", "_")
        source_ip = _device_ip(device_index)
        start_time = base_start + timedelta(minutes=device_index * 11)

        frame = pd.read_csv(benign_path, usecols=FEATURE_COLUMNS, nrows=rows_per_device)
        all_rows.extend(_convert_benign_rows(frame, device_id, source_ip, start_time))

        if inject_attacks and device_index < min(2, len(selected_files)):
            attack_base = start_time + timedelta(seconds=max(1, rows_per_device - 180) * 3)
            _inject_attack_like_rows(
                rows=all_rows,
                device_id=device_id,
                source_ip=source_ip,
                base_time=attack_base,
                attack_rows=max(40, rows_per_device // 8),
            )

    output = pd.DataFrame(all_rows).sort_values(["device_id", "timestamp"]).reset_index(drop=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_csv, index=False)
    return output


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Convert N-BaIoT feature CSVs into Phantom Nexus telemetry format.")
    parser.add_argument(
        "--input-root",
        type=Path,
        default=project_root / "datasets" / "n-baiot",
        help="Folder containing extracted N-BaIoT directories.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=project_root / "backend" / "dataset" / "iot_sample_n_baiot.csv",
        help="Output telemetry CSV compatible with backend pipeline.",
    )
    parser.add_argument("--max-devices", type=int, default=8, help="Number of device folders to include.")
    parser.add_argument("--rows-per-device", type=int, default=1800, help="Benign rows sampled per device.")
    parser.add_argument(
        "--no-attack-injection",
        action="store_true",
        help="Disable attack-like injection at the end of selected device timelines.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = preprocess_n_baiot(
        input_root=args.input_root,
        output_csv=args.output_csv,
        max_devices=max(1, args.max_devices),
        rows_per_device=max(200, args.rows_per_device),
        inject_attacks=not args.no_attack_injection,
    )
    print(f"Wrote {len(dataset)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
