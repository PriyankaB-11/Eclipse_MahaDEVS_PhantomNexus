from __future__ import annotations

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"


def _extract_json(text: str) -> dict:
    """Parse JSON even if the LLM wraps it in markdown code fences."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text.strip())
    return json.loads(text.strip())


def _fallback_summary(device_id: str, trust_score: float, anomalies: list[str], peer_results: dict) -> dict:
    attack_stage = "command-and-control" if peer_results.get("coordinated_anomaly") else "reconnaissance"
    evidence = anomalies or ["No strong anomaly markers were triggered"]
    correlated_peers = [peer["device_id"] for peer in peer_results.get("correlated_peers", [])]
    mitigation = [
        "Quarantine the device from east-west traffic until behavior stabilizes.",
        "Reset credentials and block suspicious outbound ports at the gateway.",
        "Validate firmware integrity before allowing it back into the adaptive baseline.",
    ]
    if correlated_peers:
        mitigation.append(f"Inspect correlated peers for the same playbook: {', '.join(correlated_peers)}.")

    return {
        "threat_explanation": f"{device_id} is operating below normal trust expectations and is showing behavior consistent with suspicious IoT recruitment activity.",
        "possible_attack_stage": attack_stage,
        "evidence": evidence,
        "recommended_mitigation": mitigation,
        "provider": "heuristic_fallback",
        "model": "local-summary",
        "confidence": round(min(0.95, max(0.35, (100.0 - trust_score) / 100.0 + peer_results.get("correlation_score", 0.0) * 0.3)), 2),
    }


def _build_prompt(device_id: str, trust_score: float, anomalies: list[str], peer_results: dict) -> str:
    return (
        "You are a SOC analyst assistant. Respond with strict JSON only using the keys "
        "threat_explanation, possible_attack_stage, evidence, recommended_mitigation, confidence. "
        "The evidence and recommended_mitigation values must be arrays of strings. "
        f"Device: {device_id}. Trust score: {trust_score}. "
        f"Detected anomalies: {json.dumps(anomalies)}. "
        f"Peer correlation: {json.dumps(peer_results)}. "
        "Summarize the likely threat, attack stage, key evidence, and mitigation steps for a hackathon SOC report."
    )


def generate_security_summary(
    device_id: str,
    trust_score: float,
    anomalies: list[str],
    peer_results: dict,
    model_name: str = GROQ_MODEL,
) -> dict:
    if not GROQ_API_KEY:
        return _fallback_summary(device_id, trust_score, anomalies, peer_results)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        prompt = _build_prompt(device_id, trust_score, anomalies, peer_results)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=512,
        )
        raw = response.choices[0].message.content or "{}"
        parsed = _extract_json(raw)
        return {
            "threat_explanation": parsed.get("threat_explanation", "Threat explanation unavailable"),
            "possible_attack_stage": parsed.get("possible_attack_stage", "unknown"),
            "evidence": parsed.get("evidence", anomalies),
            "recommended_mitigation": parsed.get("recommended_mitigation", []),
            "provider": "groq",
            "model": model_name,
            "confidence": parsed.get("confidence", 0.7),
        }
    except Exception as exc:
        logger.warning("Groq LLM call failed (%s: %s), using heuristic fallback", type(exc).__name__, exc)
        return _fallback_summary(device_id, trust_score, anomalies, peer_results)