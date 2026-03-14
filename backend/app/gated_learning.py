from __future__ import annotations


def _baseline_vector(baseline: dict) -> list[float]:
    return [
        float(baseline.get("average_flow_frequency", 0.0)),
        float(baseline.get("average_external_ratio", 0.0)),
        float(baseline.get("average_dns_queries", 0.0)),
        float(len(baseline.get("normal_ports", []))),
        float(len(baseline.get("common_destinations", []))),
    ]


def _divergence_score(primary_baseline: dict, shadow_baseline: dict) -> float:
    primary_vector = _baseline_vector(primary_baseline)
    shadow_vector = _baseline_vector(shadow_baseline)
    deltas = [abs(left - right) / max(abs(right), 1.0) for left, right in zip(primary_vector, shadow_vector, strict=True)]
    return round(sum(deltas) / len(deltas), 4)


def evaluate_gated_learning(
    current_baselines: dict[str, dict],
    trust_scores: dict[str, dict],
    detections: dict[str, dict],
    peer_correlations: dict[str, dict],
    primary_models: dict[str, dict] | None = None,
    shadow_models: dict[str, dict] | None = None,
    divergence_threshold: float = 0.35,
) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    active_primary = dict(primary_models or {})
    active_shadow = dict(shadow_models or {})
    decisions: dict[str, dict] = {}

    for device_id, baseline in current_baselines.items():
        previous_primary = active_primary.get(device_id, baseline)
        shadow_model = active_shadow.get(device_id, previous_primary)
        trust_score = trust_scores[device_id]["trust_score"]
        active_anomalies = bool(detections[device_id].get("anomalies"))
        peer_anomaly = bool(peer_correlations[device_id].get("coordinated_anomaly"))
        freeze_reasons = []

        if trust_score < 80:
            freeze_reasons.append("trust score below 80")
        if active_anomalies:
            freeze_reasons.append("active anomaly flags present")
        if peer_anomaly:
            freeze_reasons.append("peer correlation anomaly detected")

        allow_update = not freeze_reasons
        proposed_primary = baseline if allow_update else previous_primary
        # Divergence against the static shadow model acts as a rollback guard for poisoning attempts.
        divergence_score = _divergence_score(proposed_primary, shadow_model)
        rolled_back = False

        if allow_update and divergence_score > divergence_threshold:
            rolled_back = True
            allow_update = False
            proposed_primary = previous_primary
            freeze_reasons.append("shadow model divergence exceeded threshold")

        active_primary[device_id] = proposed_primary
        active_shadow.setdefault(device_id, shadow_model)
        decisions[device_id] = {
            "device_id": device_id,
            "allow_model_update": allow_update,
            "learning_state": "adaptive" if allow_update else ("rolled_back" if rolled_back else "frozen"),
            "freeze_reasons": freeze_reasons,
            "divergence_score": divergence_score,
        }

    return decisions, active_primary, active_shadow