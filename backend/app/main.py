from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .botnet_detector import detect_botnet_patterns
from .data_loader import load_telemetry, resolve_dataset_path
from .drift_detection import detect_drift
from .explainability import build_explainability_report
from .feature_engineering import engineer_device_windows
from .phantom_twin import build_behavioral_baselines, build_digital_twins
from .risk_graph import build_risk_graph
from .trust_engine import build_trust_scores


@dataclass
class Snapshot:
    devices: list[dict[str, Any]]
    trust_scores: list[dict[str, Any]]
    drift: list[dict[str, Any]]
    risk_graph: dict[str, Any]
    digital_twins: list[dict[str, Any]]
    device_details: dict[str, dict[str, Any]]


class PhantomNexusService:
    def __init__(self, dataset_path: Path) -> None:
        self.dataset_path = dataset_path
        self._snapshot: Snapshot | None = None
        self._dataset_mtime: float | None = None

    def _rebuild_snapshot(self) -> None:
        telemetry = load_telemetry(self.dataset_path)
        window_features = engineer_device_windows(telemetry)
        baselines = build_behavioral_baselines(window_features)
        drift_results = detect_drift(window_features)
        detections = detect_botnet_patterns(telemetry, window_features, baselines)
        trust_scores, histories = build_trust_scores(window_features, baselines, drift_results, detections)
        digital_twins = build_digital_twins(window_features, baselines, trust_scores, drift_results, detections)
        risk_graph = build_risk_graph(telemetry, trust_scores)

        latest_windows = (
            window_features.sort_values("window_start")
            .groupby("device_id")
            .tail(1)
            .set_index("device_id")
        )
        latest_flows = (
            telemetry.sort_values("timestamp")
            .groupby("device_id")
            .tail(1)
            .set_index("device_id")
        )

        devices = []
        device_details: dict[str, dict[str, Any]] = {}
        for device_id, trust_payload in trust_scores.items():
            latest_window = latest_windows.loc[device_id]
            latest_flow = latest_flows.loc[device_id]
            explanation = build_explainability_report(
                device_id,
                trust_payload,
                drift_results[device_id],
                detections[device_id],
            )
            devices.append(
                {
                    "device_id": device_id,
                    "src_ip": latest_flow["src_ip"],
                    "trust_score": trust_payload["trust_score"],
                    "status": trust_payload["status"],
                    "risk_level": trust_payload["risk_level"],
                    "drift_score": drift_results[device_id]["drift_score"],
                    "botnet_probability": detections[device_id]["botnet_probability"],
                    "latest_destinations": latest_window["destinations"],
                    "latest_ports": latest_window["ports"],
                    "anomalies": detections[device_id]["anomalies"],
                }
            )
            device_details[device_id] = {
                "device_id": device_id,
                "summary": devices[-1],
                "history": histories[device_id],
                "drift": drift_results[device_id],
                "detection": detections[device_id],
                "explanation": explanation,
                "phantom_twin": baselines[device_id],
                "digital_twin": digital_twins[device_id],
            }

        self._snapshot = Snapshot(
            devices=sorted(devices, key=lambda item: item["trust_score"]),
            trust_scores=[
                {
                    "device_id": device_id,
                    "trust_score": trust_scores[device_id]["trust_score"],
                    "history": histories[device_id],
                }
                for device_id in sorted(trust_scores)
            ],
            drift=[drift_results[device_id] for device_id in sorted(drift_results)],
            risk_graph=risk_graph,
            digital_twins=[digital_twins[device_id] for device_id in sorted(digital_twins)],
            device_details=device_details,
        )
        self._dataset_mtime = self.dataset_path.stat().st_mtime

    def get_snapshot(self) -> Snapshot:
        dataset_mtime = self.dataset_path.stat().st_mtime
        if self._snapshot is None or self._dataset_mtime != dataset_mtime:
            self._rebuild_snapshot()
        return self._snapshot


service = PhantomNexusService(resolve_dataset_path())
app = FastAPI(title="Phantom Nexus API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Phantom Nexus backend is running"}


@app.get("/devices")
def get_devices() -> list[dict[str, Any]]:
    return service.get_snapshot().devices


@app.get("/trust_scores")
def get_trust_scores() -> list[dict[str, Any]]:
    return service.get_snapshot().trust_scores


@app.get("/drift")
def get_drift() -> list[dict[str, Any]]:
    return service.get_snapshot().drift


@app.get("/risk_graph")
def get_risk_graph() -> dict[str, Any]:
    return service.get_snapshot().risk_graph


@app.get("/digital_twins")
def get_digital_twins() -> list[dict[str, Any]]:
    return service.get_snapshot().digital_twins


@app.get("/device/{device_id}")
def get_device(device_id: str) -> dict[str, Any]:
    snapshot = service.get_snapshot()
    if device_id not in snapshot.device_details:
        raise HTTPException(status_code=404, detail="Device not found")
    return snapshot.device_details[device_id]
