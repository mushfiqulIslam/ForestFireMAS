# ForestFireMAS — BDI Extension

Extends the original JADE-based ForestFireMAS with a Python BDI agent system built on **CrewAI** and **Ollama** (local LLMs — no API key or internet required).

---

## What is implemented

| File | Purpose |
|---|---|
| `config.py` | Per-agent LLM configuration (model + temperature) |
| `beliefs.py` | Explicit `BeliefBase` class — the **B** in BDI, logs every update to terminal |
| `agents.py` | 4 CrewAI agents with role / goal / backstory — the **D** (Desires) in BDI |
| `scenario1.py` | Scenario 1: single-zone cooperative pipeline |
| `scenario2.py` | Scenario 2: dual-zone resource conflict with uncertainty |
| `scenario3.py` | Scenario 3: cascading multi-zone emergency with belief revision |
| `main.py` | Entry point — runs one or more scenarios |

### BDI mapping

| BDI concept | Implementation |
|---|---|
| **Beliefs** | `BeliefBase` instances in `beliefs.py` — key/value store, every change printed to terminal |
| **Desires** | `Agent.goal` field in `agents.py` — what each agent persistently wants |
| **Intentions** | `Task` objects in `scenario*.py` — what each agent is currently committed to doing |

### Agents and models

| Agent | Model | Role |
|---|---|---|
| `DetectionAgent` | `mistral` | Reads sensor feeds, confirms fire zones |
| `AssessmentAgent` | `llama3.1` | Classifies severity, flags UNCERTAIN zones |
| `ResourceCoordinationAgent` | `llama3.1` | Allocates firefighting assets, resolves conflicts |
| `ResponseAgent` | `mistral` | Issues dispatch orders and evacuation notices |

### Scenarios

| Scenario | Description |
|---|---|
| **Scenario 1 — Standard Single-Zone Response** | One fire detected in SectorC (MODERATE intensity, 11 km from Jyväskylä). All four agents cooperate in sequence: detect → assess → allocate → dispatch. Demonstrates the core BDI pipeline with no resource conflict. |
| **Scenario 2 — Dual-Zone Resource Conflict with Uncertainty** | Two simultaneous fires: SectorA (CRITICAL, 4 km from Äänekoski) + SectorB (sensors 67 % offline → UNCERTAIN). Resources are insufficient to fully suppress both zones. Demonstrates conflict resolution, uncertainty handling, multi-step deliberation, and belief revision. |
| **Scenario 3 — Cascading Emergency with Belief Revision** | Three simultaneous fires: SectorD (MODERATE), SectorE (HIGH near Äänekoski hospital), and SectorF (initially LOW). After Phase 1, new 09:52 sensor data escalates SectorF to CRITICAL, revokes the Phase 1 plan, and triggers a second crew run for reassessment, resource replanning, and a new Jyväskylä valley evacuation notice. |

---

## Prerequisites

### 1. Install Ollama

Download and install from [https://ollama.com](https://ollama.com).

After installation, Ollama runs as a local server on `http://localhost:11434`.

### 2. Pull the required models

Open a terminal and run:

```bash
ollama pull mistral
ollama pull llama3.1
```

Verify both are available:

```bash
ollama list
```

You should see `mistral` and `llama3.1` in the list.

> **RAM requirement:** `mistral` needs ~4 GB, `llama3.1` needs ~5 GB.  
> Running one at a time is fine — Ollama swaps them automatically.

### 3. Python environment

You need **Python 3.10+** (tested on 3.12).

Create and activate a virtual environment, then install dependencies:

```bash
# Create venv (do this once)
python3 -m venv fireVenv
source fireVenv/bin/activate        # Linux / macOS / WSL
# fireVenv\Scripts\activate         # Windows CMD

# Install dependencies
pip install -r requirements.txt
```

---

## Running the project

Make sure you are inside the `bdi/` folder with the venv active:

```bash
cd bdi/
source ~/path/to/fireVenv/bin/activate   # adjust path to your venv
```

### Run all scenarios

```bash
python main.py
```

### Run Scenario 1 only

```bash
python main.py --s1
```

### Run Scenario 2 only

```bash
python main.py --s2
```

### Run Scenario 3 only

```bash
python main.py --s3
```

---

## What you will see in the terminal

1. **Belief updates** before the crew runs — shows beliefs changing as the scenario context loads
2. **CrewAI agent output** — each agent's reasoning printed step by step
3. **Belief updates** after the crew — shows how beliefs changed after the pipeline completes
4. **Final belief base dump** — snapshot of all four belief stores at the end

Example belief output:
```
  [BELIEF] DetectionAgent                 active_zones: 0  →  1
  [BELIEF] DetectionAgent                 zone_id: <undefined>  →  SectorC
  [BELIEF] AssessmentAgent                uncertainty_flag: <undefined>  →  False
  [BELIEF] ResourceCoordinationAgent      resource_conflict: False  →  True
```

---

## Project structure

```
bdi/
├── README.md          ← this file
├── requirements.txt   ← pinned dependencies
├── config.py          ← LLM config (swap models here)
├── beliefs.py         ← BeliefBase class + 4 agent instances
├── agents.py          ← CrewAI Agent definitions
├── scenario1.py       ← Single-zone scenario
├── scenario2.py       ← Dual-zone conflict scenario
├── scenario3.py       ← Cascading emergency scenario
└── main.py            ← Entry point
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `model requires more system memory` | Close other apps to free RAM, or edit `config.py` to use `mistral` for all agents |
| `connection refused` on port 11434 | Ollama is not running — start it with `ollama serve` |
| `No module named 'pkg_resources'` | Run `pip install setuptools==69.5.1` in your venv |
| `ModuleNotFoundError: crewai` | Make sure your venv is activated before running |
