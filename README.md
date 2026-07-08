# Energy Recovery Digital Twin -- Prototype

A working prototype of the AI-optimized digital twin + operator copilot described in
[`docs/Autonomous Energy Recovery Digital Twin Platform V1.0.pdf`](docs/Autonomous%20Energy%20Recovery%20Digital%20Twin%20Platform%20V1.0.pdf)
(Esyasoft Global Innovation Competition 2026 pitch). This is a **local, live-demoable
prototype**, not the full platform -- see [Scope](#scope-what-is-real-vs-mocked-vs-not-built)
below for exactly what's real.

## What it is

A simulated gas pressure letdown station (inlet -> preheater HX -> turboexpander ->
generator -> outlet, with a bypass PRV path) driven by real thermodynamics
(Joule-Thomson cooling across the bypass, isentropic expansion through the
turboexpander), streamed live to a dashboard with an interactive P&ID, KPI
tiles, charts, fault/alarm injection, and an AI operator copilot backed by a
local LLM (Ollama) that investigates alarms and writes shift handover reports
by querying the historian through real tool calls.

## Architecture

```
backend/   FastAPI + asyncio simulation engine + SQLite historian + Ollama tool-calling copilot
frontend/  Next.js dashboard (P&ID, KPIs, charts, alarms, copilot chat)
```

- **Simulation**: `backend/app/sim/` -- physics (`physics.py`), daily demand curve
  (`demand_curve.py`), fault scheduling (`faults.py`), station tick loop (`station.py`,
  `engine.py`). Simulated time runs at 240x (1 real second = 4 simulated minutes), so a
  full day/night demand cycle plays out in ~6 real minutes.
- **Historian**: SQLite (`backend/app/historian/`), stands in for a real OSIsoft/AVEVA
  historian.
- **API**: FastAPI REST + WebSocket (`backend/app/api/`).
- **Copilot**: `backend/app/copilot/` -- Ollama native tool-calling loop over 5 tools
  (`query_historian`, `list_alarms`, `compute_efficiency`, `get_current_state`,
  `get_shift_report_data`), bounded to 4 rounds, `think=False` for latency.
- **Frontend**: Next.js App Router + Tailwind + recharts (`frontend/`).

## Prerequisites

- Python 3.14+ (venv already created at `backend/.venv`)
- Node.js 20+ / npm
- [Ollama](https://ollama.com) installed and running, with the model pulled:
  ```bash
  ollama pull gemma4:e4b
  ```

## Running it (3 processes)

**1. Ollama** (if not already running as a service):
```bash
ollama serve
```

**2. Backend** (port **8001** -- not 8000, which may already be in use by something
else on your machine):
```bash
cd backend
.venv/bin/uvicorn app.main:app --port 8001
```

**3. Frontend** (port 3000):
```bash
cd frontend
npm run dev
```

Then open **http://localhost:3000**.

Environment overrides (optional): `OLLAMA_MODEL` (default `gemma4:e4b`, can be set to
`gemma4:e2b`), `OLLAMA_BASE_URL` (default `http://localhost:11434`),
`NEXT_PUBLIC_API_BASE` / `NEXT_PUBLIC_WS_BASE` (default `http://localhost:8001` /
`ws://localhost:8001`).

## Running the tests

```bash
cd backend
.venv/bin/python -m pytest tests/ -v
```

Covers physics calibration (power output lands in the deck's 200-600kW band, JT bypass
cooling is nonzero, temperatures stay physical), fault scheduling (each fault
opens/closes exactly once per simulated day and recurs on subsequent days), and copilot
tool validation.

## Demo script

The simulation starts at simulated `00:00` each time the backend restarts, and three
faults are scheduled every simulated day (~6 real minutes):

| Simulated time | Fault | Effect |
|---|---|---|
| 03:00 - 04:30 | Preheater HX fouling (`TI-002`) | Reduced preheat, lower efficiency |
| 03:15 - 03:45 | Bypass PRV valve stuck open (`PT-003`) | Turboexpander offline, 0 kW |
| 09:00 - 11:00 | Inlet pressure sensor drift (`PI-001`) | Biased reading, no power impact |

A walkthrough that shows all the working pieces:

1. **Open the dashboard.** Point out the live P&ID (values updating every ~1s), KPI
   tiles (power/efficiency instantaneous, CO2/revenue cumulative), and the two charts.
2. **Wait for or fast-forward to ~03:15 simulated** (about 45-90 real seconds after
   backend startup). Watch the P&ID's `TI-002` and `PT-003` badges turn red, the mode
   label flip to `bypass`, power drop to 0 kW, and the Alarms panel populate.
3. **Ask the copilot**: *"Why did power output drop around 03:00?"* (one of the
   suggested prompts). It calls `get_current_state` to learn the simulated date, then
   `get_shift_report_data` for a window around 03:00, and explains both contributing
   faults with correct timestamps -- not invented numbers, a real tool-call trace you
   can expand under the reply.
4. **Ask for a shift handover**: *"Generate a shift handover summary for the last few
   hours."* -- demonstrates the second copilot use case (report generation, not just
   Q&A).
5. **Switch chart time range** (6h / 24h / 3d buttons) to show the full day cycle and
   the fault dip in the power chart.

Recording a short screen-capture backup of this walkthrough before presenting live is a
good idea, since it depends on local Ollama inference (a few seconds per response) and
the timing of the fault windows.

## Scope: what is real vs. mocked vs. not built

**Real, working code** (not mocked): the thermodynamics (Joule-Thomson bypass cooling,
isentropic turboexpander expansion), the simulation/demand/fault engine, the SQLite
historian, the FastAPI REST + WebSocket API, the live dashboard, and the AI copilot's
tool-calling loop against a real local LLM.

**Mocked / synthetic** (stands in for something real): all sensor readings (physics
simulation, not real hardware), the historian (SQLite instead of OSIsoft/AVEVA), the
"SCADA layer" (an internal API, not real OPC-UA/Modbus).

**Explicitly out of scope** (described in the pitch deck, not built here): real
SCADA/OPC-UA/Modbus/ERP/SAP/AMI integration, the AI Recovery Control / RL optimizer
module, multi-tenant SaaS/auth/billing, compliance certifications (ISO 50001, IEC
61511, ATEX), BESS/hydrogen roadmap extensions, a mobile field app, and cloud
deployment (this runs local-only, by design, for a live walkthrough).
