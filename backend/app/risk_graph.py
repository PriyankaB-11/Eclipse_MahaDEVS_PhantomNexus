from __future__ import annotations

import networkx as nx
import pandas as pd

from .data_loader import build_device_ip_index


def build_risk_graph(telemetry: pd.DataFrame, trust_scores: dict[str, dict]) -> dict[str, list[dict]]:
    _, ip_to_device = build_device_ip_index(telemetry)
    graph = nx.DiGraph()

    for device_id, payload in trust_scores.items():
        graph.add_node(
            device_id,
            label=device_id,
            trust_score=payload["trust_score"],
            propagated_trust=payload["trust_score"],
            risk_level=payload["risk_level"],
        )

    flow_edges = (
        telemetry.assign(target_device=telemetry["dest_ip"].map(ip_to_device))
        .dropna(subset=["target_device"])
        .query("device_id != target_device")
        .groupby(["device_id", "target_device"], as_index=False)
        .agg(flows=("dest_ip", "size"), volume=("bytes", "sum"))
    )

    for edge in flow_edges.to_dict(orient="records"):
        graph.add_edge(
            edge["device_id"],
            edge["target_device"],
            flows=int(edge["flows"]),
            volume=round(float(edge["volume"]), 2),
        )

    for device_id, payload in trust_scores.items():
        if payload["trust_score"] >= 40:
            continue
        penalty = max(2.5, (40 - payload["trust_score"]) * 0.12)
        neighbors = set(graph.successors(device_id)) | set(graph.predecessors(device_id))
        for neighbor in neighbors:
            current = graph.nodes[neighbor]["propagated_trust"]
            graph.nodes[neighbor]["propagated_trust"] = round(max(0.0, current - penalty), 2)

    nodes = []
    for node_id, attributes in graph.nodes(data=True):
        node_data = {"id": node_id}
        node_data.update(attributes)
        nodes.append(node_data)

    edges = []
    for source, target, attributes in graph.edges(data=True):
        edge_data = {"source": source, "target": target}
        edge_data.update(attributes)
        edges.append(edge_data)

    return {"nodes": nodes, "edges": edges}
