from __future__ import annotations

from io import BytesIO

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _list_text(values: list[str]) -> str:
    if not values:
        return "None"
    return "<br/>".join(f"• {value}" for value in values)


def _build_score_chart(trust_score: float, botnet_probability: float, correlation_score: float) -> Drawing:
    drawing = Drawing(360, 180)
    chart = VerticalBarChart()
    chart.x = 30
    chart.y = 30
    chart.height = 110
    chart.width = 290
    chart.data = [[trust_score, botnet_probability * 100.0, correlation_score * 100.0]]
    chart.categoryAxis.categoryNames = ["Trust", "Botnet", "Correlation"]
    chart.categoryAxis.labels.fillColor = colors.HexColor("#0f172a")
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 100
    chart.valueAxis.valueStep = 20
    chart.valueAxis.labels.fillColor = colors.HexColor("#475569")
    chart.bars[0].fillColor = colors.HexColor("#14b8a6")
    chart.strokeColor = colors.HexColor("#cbd5e1")
    drawing.add(chart)
    return drawing


def build_pdf_report(investigation: dict) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#0f766e"), spaceAfter=8))
    styles.add(ParagraphStyle(name="BodyMuted", parent=styles["BodyText"], fontSize=10, leading=14, alignment=TA_LEFT))

    anomaly_scores = investigation.get("anomaly_scores", {})
    peer_correlations = investigation.get("peer_correlations", {})
    llm_summary = investigation.get("llm_summary", {})
    correlated_devices = [peer["device_id"] for peer in peer_correlations.get("correlated_peers", [])]
    anomalies = investigation.get("detected_anomalies", [])

    story = [
        Paragraph("Phantom Nexus Security Investigation Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Device Information", styles["SectionTitle"]),
        Table(
            [
                ["Device ID", investigation["device_id"]],
                ["Trust Score", f"{investigation['trust_score']}"] ,
                ["Report URL", investigation["report_download_url"]],
            ],
            colWidths=[130, 360],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]),
        ),
        Spacer(1, 12),
        Paragraph("Trust Score", styles["SectionTitle"]),
        Paragraph(f"Current trust score: {investigation['trust_score']}", styles["BodyMuted"]),
        Spacer(1, 12),
        Paragraph("Detected Anomalies", styles["SectionTitle"]),
        Paragraph(_list_text(anomalies), styles["BodyMuted"]),
        Spacer(1, 12),
        Paragraph("Peer Correlation Findings", styles["SectionTitle"]),
        Paragraph(
            _list_text(correlated_devices) + f"<br/>Correlation score: {peer_correlations.get('correlation_score', 0.0)}",
            styles["BodyMuted"],
        ),
        Spacer(1, 12),
        Paragraph("LLM Explanation", styles["SectionTitle"]),
        Paragraph(llm_summary.get("threat_explanation", "No summary available"), styles["BodyMuted"]),
        Spacer(1, 6),
        Paragraph(f"Possible attack stage: {llm_summary.get('possible_attack_stage', 'unknown')}", styles["BodyMuted"]),
        Spacer(1, 6),
        Paragraph("Recommended Actions", styles["SectionTitle"]),
        Paragraph(_list_text(llm_summary.get("recommended_mitigation", [])), styles["BodyMuted"]),
        Spacer(1, 18),
        _build_score_chart(
            float(investigation["trust_score"]),
            float(investigation.get("botnet_probability", 0.0)),
            float(peer_correlations.get("correlation_score", 0.0)),
        ),
        Spacer(1, 12),
        Paragraph(
            f"Drift score: {anomaly_scores.get('drift_score', 0.0)} | Anomaly score: {anomaly_scores.get('anomaly_score', 0.0)}",
            styles["BodyMuted"],
        ),
    ]

    document.build(story)
    return buffer.getvalue()