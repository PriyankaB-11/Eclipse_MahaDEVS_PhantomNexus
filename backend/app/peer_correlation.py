from __future__ import annotations

from itertools import combinations

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .ml_model import FEATURE_COLUMNS


def _build_suspicious_windows(telemetry: pd.DataFrame) -> dict[str, set[str]]:
    # Time-window overlap is used to separate shared long-term traits from synchronized suspicious activity.
    suspicious = telemetry[
        telemetry["dest_port"].isin([23, 2323, 4444, 48101, 5555, 6667])
        | (~telemetry["dest_ip"].str.startswith("10.", na=False) & (telemetry["bytes"] >= telemetry["bytes"].median()))
    ].copy()
    suspicious["window"] = suspicious["timestamp"].dt.floor("1h").astype(str)
    return {
        device_id: set(frame["window"].tolist())
        for device_id, frame in suspicious.groupby("device_id")
    }


def build_device_communication_graph(telemetry: pd.DataFrame) -> nx.Graph:
    device_graph = nx.Graph()
    device_ips = (
        telemetry.sort_values("timestamp")
        .groupby("device_id")["src_ip"]
        .last()
        .to_dict()
    )
    ip_to_device = {ip: device_id for device_id, ip in device_ips.items()}

    for device_id in device_ips:
        device_graph.add_node(device_id)

    # Direct device-to-device edges capture east-west chatter, while overlap edges capture shared destinations.
    for _, row in telemetry.iterrows():
        source_device = row["device_id"]
        target_device = ip_to_device.get(row["dest_ip"])
        if target_device and target_device != source_device:
            weight = device_graph.get_edge_data(source_device, target_device, {}).get("weight", 0) + 1
            device_graph.add_edge(source_device, target_device, weight=weight, relationship="direct")

    destination_sets = telemetry.groupby("device_id")["dest_ip"].agg(lambda series: set(series.tolist())).to_dict()
    for left_device, right_device in combinations(destination_sets.keys(), 2):
        overlap = destination_sets[left_device] & destination_sets[right_device]
        if not overlap:
            continue
        existing = device_graph.get_edge_data(left_device, right_device, {})
        weight = existing.get("weight", 0) + len(overlap)
        relationship = existing.get("relationship", "shared_targets")
        device_graph.add_edge(left_device, right_device, weight=weight, relationship=relationship)

    return device_graph


def detect_peer_correlations(
    telemetry: pd.DataFrame,
    device_features: pd.DataFrame,
    detections: dict[str, dict],
    similarity_threshold: float = 0.82,
) -> dict[str, dict]:
    graph = build_device_communication_graph(telemetry)
    suspicious_windows = _build_suspicious_windows(telemetry)

    ordered_features = device_features.sort_values("device_id").reset_index(drop=True)
    feature_vectors = ordered_features[FEATURE_COLUMNS].to_numpy(dtype=float)
    similarity_matrix = cosine_similarity(feature_vectors) if len(ordered_features) else np.empty((0, 0))

    correlations: dict[str, dict] = {}
    device_ids = ordered_features["device_id"].tolist()
    for row_index, device_id in enumerate(device_ids):
        correlated_peers = []
        correlation_score = 0.0
        device_windows = suspicious_windows.get(device_id, set())

        for col_index, peer_id in enumerate(device_ids):
            if device_id == peer_id:
                continue
            similarity = float(similarity_matrix[row_index][col_index])
            peer_windows = suspicious_windows.get(peer_id, set())
            overlap_count = len(device_windows & peer_windows)
            window_overlap = overlap_count / max(len(device_windows | peer_windows), 1)
            shared_graph_weight = graph.get_edge_data(device_id, peer_id, {}).get("weight", 0)
            combined_score = round((similarity * 0.7) + (window_overlap * 0.2) + (min(shared_graph_weight, 10) / 10 * 0.1), 4)

            if similarity >= similarity_threshold and overlap_count > 0:
                correlated_peers.append(
                    {
                        "device_id": peer_id,
                        "correlation_score": combined_score,
                        "shared_suspicious_windows": overlap_count,
                    }
                )
                correlation_score = max(correlation_score, combined_score)

        correlations[device_id] = {
            "device_id": device_id,
            "correlated_peers": sorted(correlated_peers, key=lambda item: item["correlation_score"], reverse=True),
            "correlation_score": round(correlation_score, 4),
            "graph_neighbors": sorted(graph.neighbors(device_id)) if device_id in graph else [],
            "coordinated_anomaly": correlation_score >= 0.75 and bool(correlated_peers),
        }

        if detections.get(device_id, {}).get("botnet_probability", 0.0) >= 0.7 and correlations[device_id]["correlated_peers"]:
            correlations[device_id]["coordinated_anomaly"] = True

    return correlations