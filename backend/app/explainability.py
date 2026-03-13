from __future__ import annotations


def _recommendation(trust_score: float) -> str:
    if trust_score < 30:
        return "quarantine device"
    if trust_score < 50:
        return "segment device and inspect outbound destinations"
    if trust_score < 70:
        return "increase monitoring and validate recent connections"
    return "continue baseline monitoring"


def build_explainability_report(
    device_id: str,
    trust_payload: dict,
    drift_payload: dict,
    detection_payload: dict,
) -> dict:
    reasons = list(detection_payload["anomalies"])
    if drift_payload["drift_score"] > 0.3:
        reasons.append("behavioral drift above device baseline")

    if not reasons:
        reasons.append("no material anomalies detected")

    evidence = {
        "drift_score": drift_payload["drift_score"],
        "signal_breakdown": drift_payload["signal_breakdown"],
        "botnet_probability": detection_payload["botnet_probability"],
    }
    evidence.update(detection_payload["evidence"])

    return {
        "device_id": device_id,
        "trust_score": trust_payload["trust_score"],
        "reason": reasons,
        "evidence": evidence,
        "recommended_action": _recommendation(trust_payload["trust_score"]),
    }
