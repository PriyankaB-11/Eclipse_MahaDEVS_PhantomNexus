from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .botnet_detector import detect_botnet_patterns
from .data_loader import REQUIRED_COLUMNS, UPLOADS_DIR, load_telemetry, resolve_dataset_path, validate_telemetry_dataframe
from .drift_detection import detect_drift
from .explainability import build_explainability_report
from .feature_engineering import engineer_device_windows
from .gated_learning import evaluate_gated_learning
from .llm_explainer import generate_security_summary
from .ml_model import run_behavior_model
from .phantom_twin import build_behavioral_baselines, build_digital_twins
from .pdf_report_generator import build_pdf_report
from .peer_correlation import detect_peer_correlations
from .risk_graph import build_risk_graph
from .trust_engine import build_trust_scores


@dataclass
class Snapshot:
    devices: list[dict[str, Any]]
    trust_scores: list[dict[str, Any]]
    drift: list[dict[str, Any]]
    risk_graph: dict[str, Any]
    digital_twins: list[dict[str, Any]]
    peer_correlations: list[dict[str, Any]]
    device_details: dict[str, dict[str, Any]]
    investigations: dict[str, dict[str, Any]]
    dataset_info: dict[str, Any]


class PhantomNexusService:
    def __init__(self, dataset_path: Path) -> None:
        self.dataset_path = dataset_path
        self.upload_dir = UPLOADS_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._snapshot: Snapshot | None = None
        self._dataset_mtime: float | None = None
        self._adaptive_baselines: dict[str, dict[str, Any]] = {}
        self._shadow_baselines: dict[str, dict[str, Any]] = {}

    def _combine_detections(
        self,
        heuristic_detections: dict[str, dict[str, Any]],
        ml_predictions: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        # Merge protocol-level heuristics with the per-device ML classifier into one device verdict.
        combined: dict[str, dict[str, Any]] = {}
        for device_id, heuristic in heuristic_detections.items():
            ml_prediction = ml_predictions[device_id]
            anomalies = list(dict.fromkeys(heuristic["anomalies"] + ml_prediction["detected_anomalies"]))
            evidence = dict(heuristic.get("evidence", {}))
            evidence["ml_features"] = ml_prediction["feature_summary"]
            if ml_prediction["suspicious_ports"]:
                evidence["ml_suspicious_ports"] = ml_prediction["suspicious_ports"]

            combined[device_id] = {
                "device_id": device_id,
                "botnet_probability": round(max(heuristic["botnet_probability"], ml_prediction["botnet_probability"]), 4),
                "anomaly_score": ml_prediction["anomaly_score"],
                "anomalies": anomalies,
                "evidence": evidence,
                "new_external_ip_count": max(heuristic.get("new_external_ip_count", 0), ml_prediction["new_external_ip_count"]),
                "port_anomaly_count": max(heuristic.get("port_anomaly_count", 0), ml_prediction["port_anomaly_count"]),
                "feature_summary": ml_prediction["feature_summary"],
            }

        return combined

    def set_dataset_path(self, dataset_path: Path) -> None:
        self.dataset_path = dataset_path
        self._snapshot = None
        self._dataset_mtime = None

    def upload_dataset(self, file_name: str, file_bytes: bytes) -> tuple[Path, Snapshot]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        sanitized_name = Path(file_name).stem.replace(" ", "_")
        target_path = self.upload_dir / f"{sanitized_name}_{timestamp}.csv"
        frame = pd.read_csv(BytesIO(file_bytes))
        # Validate before persisting so bad uploads never become the active dataset.
        validate_telemetry_dataframe(frame)
        target_path.write_bytes(file_bytes)
        self.set_dataset_path(target_path)
        return target_path, self.get_snapshot()

    def _rebuild_snapshot(self) -> None:
        telemetry = load_telemetry(self.dataset_path)
        window_features = engineer_device_windows(telemetry)
        baselines = build_behavioral_baselines(window_features)
        drift_results = detect_drift(window_features)
        heuristic_detections = detect_botnet_patterns(telemetry, window_features, baselines)
        ml_bundle = run_behavior_model(telemetry)
        detections = self._combine_detections(heuristic_detections, ml_bundle.predictions)
        trust_scores, histories = build_trust_scores(window_features, baselines, drift_results, detections)
        digital_twins = build_digital_twins(window_features, baselines, trust_scores, drift_results, detections)
        peer_correlations = detect_peer_correlations(telemetry, ml_bundle.features, detections)
        gated_learning, self._adaptive_baselines, self._shadow_baselines = evaluate_gated_learning(
            baselines,
            trust_scores,
            detections,
            peer_correlations,
            self._adaptive_baselines,
            self._shadow_baselines,
        )
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
        investigations: dict[str, dict[str, Any]] = {}
        for device_id, trust_payload in trust_scores.items():
            latest_window = latest_windows.loc[device_id]
            latest_flow = latest_flows.loc[device_id]
            explanation = build_explainability_report(
                device_id,
                trust_payload,
                drift_results[device_id],
                detections[device_id],
            )
            llm_summary = generate_security_summary(
                device_id,
                trust_payload["trust_score"],
                detections[device_id]["anomalies"],
                peer_correlations[device_id],
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
                    "anomaly_score": detections[device_id]["anomaly_score"],
                    "correlation_score": peer_correlations[device_id]["correlation_score"],
                    "latest_destinations": latest_window["destinations"],
                    "latest_ports": latest_window["ports"],
                    "anomalies": detections[device_id]["anomalies"],
                }
            )
            investigations[device_id] = {
                "device_id": device_id,
                "trust_score": trust_payload["trust_score"],
                "anomaly_scores": {
                    "drift_score": drift_results[device_id]["drift_score"],
                    "anomaly_score": detections[device_id]["anomaly_score"],
                    "botnet_probability": detections[device_id]["botnet_probability"],
                },
                "detected_anomalies": detections[device_id]["anomalies"],
                "peer_correlations": peer_correlations[device_id],
                "botnet_probability": detections[device_id]["botnet_probability"],
                "llm_summary": llm_summary,
                "gated_learning": gated_learning[device_id],
                "report_download_url": f"/device_report/{device_id}",
            }
            device_details[device_id] = {
                "device_id": device_id,
                "summary": devices[-1],
                "history": histories[device_id],
                "drift": drift_results[device_id],
                "detection": detections[device_id],
                "explanation": explanation,
                "phantom_twin": baselines[device_id],
                "digital_twin": digital_twins[device_id],
                "ml_prediction": ml_bundle.predictions[device_id],
                "peer_correlations": peer_correlations[device_id],
                "gated_learning": gated_learning[device_id],
                "llm_summary": llm_summary,
                "investigation": investigations[device_id],
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
            peer_correlations=[peer_correlations[device_id] for device_id in sorted(peer_correlations)],
            device_details=device_details,
            investigations=investigations,
            dataset_info={
                "dataset_path": str(self.dataset_path),
                "dataset_name": self.dataset_path.name,
                "required_columns": REQUIRED_COLUMNS,
                "record_count": int(len(telemetry)),
                "device_count": int(telemetry["device_id"].nunique()),
            },
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


@app.get("/peer_correlations")
def get_peer_correlations() -> list[dict[str, Any]]:
    return service.get_snapshot().peer_correlations


@app.get("/dataset_info")
def get_dataset_info() -> dict[str, Any]:
    return service.get_snapshot().dataset_info


@app.get("/device/{device_id}")
def get_device(device_id: str) -> dict[str, Any]:
    snapshot = service.get_snapshot()
    if device_id not in snapshot.device_details:
        raise HTTPException(status_code=404, detail="Device not found")
    return snapshot.device_details[device_id]


@app.post("/upload_dataset")
async def upload_dataset(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV datasets are supported")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        saved_path, snapshot = service.upload_dataset(file.filename, file_bytes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "message": "Dataset uploaded and ML pipeline refreshed",
        "dataset": {
            "filename": saved_path.name,
            "required_columns": REQUIRED_COLUMNS,
            "record_count": snapshot.dataset_info["record_count"],
            "device_count": snapshot.dataset_info["device_count"],
        },
        "devices_analyzed": len(snapshot.devices),
    }


@app.get("/device_investigation/{device_id}")
def get_device_investigation(device_id: str) -> dict[str, Any]:
    snapshot = service.get_snapshot()
    if device_id not in snapshot.investigations:
        raise HTTPException(status_code=404, detail="Device not found")
    return snapshot.investigations[device_id]


@app.get("/device_report/{device_id}")
def get_device_report(device_id: str) -> StreamingResponse:
    snapshot = service.get_snapshot()
    if device_id not in snapshot.investigations:
        raise HTTPException(status_code=404, detail="Device not found")

    report_bytes = build_pdf_report(snapshot.investigations[device_id])
    return StreamingResponse(
        BytesIO(report_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{device_id}_investigation_report.pdf"'},
    )
