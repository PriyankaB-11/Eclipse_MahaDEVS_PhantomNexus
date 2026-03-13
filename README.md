# Phantom Nexus

Phantom Nexus is a hackathon-ready prototype for detecting early-stage IoT botnet recruitment from network telemetry. It builds per-device behavioral baselines, detects drift, scores botnet-recruitment indicators, propagates risk across an internal communication graph, and presents the results in a SOC-style dashboard.

## Stack

- Frontend: React, Vite, Tailwind CSS, Bootstrap utilities, Recharts, React Flow
- Backend: FastAPI, Pandas, NumPy, scikit-learn, Ruptures, NetworkX

## Project Layout

```text
backend/
  app/
  dataset/
  requirements.txt
  scripts/generate_demo_dataset.py
frontend/
  src/
```

## Backend

```powershell
Set-Location .\backend
pip install -r requirements.txt
python scripts/generate_demo_dataset.py
uvicorn app.main:app --reload
```

Available endpoints:

- `GET /devices`
- `GET /trust_scores`
- `GET /drift`
- `GET /risk_graph`
- `GET /digital_twins`
- `GET /device/{device_id}`

## Frontend

```powershell
Set-Location .\frontend
npm install
npm run dev
```

If needed, set `VITE_API_BASE_URL` to point at a different backend host. By default the UI targets `http://127.0.0.1:8000`.

## Demo Flow

1. Generate telemetry with `backend/scripts/generate_demo_dataset.py`.
2. Start the FastAPI server.
3. Start the Vite frontend.
4. Open the dashboard and inspect the critical devices `camera_01` and `speaker_01`, then review trust propagation in the network map.
