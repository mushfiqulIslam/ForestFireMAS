"""
config.py — LLM configuration for ForestFireMAS BDI agents.

Each agent gets its own model matched to task complexity.
All models run locally via Ollama — no API key or internet needed.

Uses CrewAI's native LLM class (backed by LiteLLM) with the
"ollama/<model>" prefix so LiteLLM routes calls to the local
Ollama server automatically.

To swap a model, change the value here. Nothing else needs to change.
"""

from crewai import LLM

OLLAMA_BASE_URL = "http://localhost:11434"

# ── DetectionAgent — simplest task (sensor reading + reporting) ──
# mistral is fast and light — no complex reasoning needed here
LLM_DETECTION = LLM(
    model="ollama/mistral",
    base_url=OLLAMA_BASE_URL,
    temperature=0.1,
)

# ── AssessmentAgent — rule-based severity classification ─────────
# llama3.1 handles edge cases like UNCERTAIN flagging cleanly
LLM_ASSESSMENT = LLM(
    model="ollama/llama3.1",
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
)

# ── ResourceCoordinationAgent — conflicting goals, deliberation ──
# Heaviest task → best available model
# If RAM < 32GB change to "ollama/llama3.1"
LLM_RESOURCE = LLM(
    model="ollama/llama3.1",
    base_url=OLLAMA_BASE_URL,
    temperature=0.3,
)

# ── ResponseAgent — structured dispatch output ───────────────────
# mistral is fast and precise for structured command-style output
# (gemma2:9b needs 6.4 GB RAM which exceeds available memory)
LLM_RESPONSE = LLM(
    model="ollama/mistral",
    base_url=OLLAMA_BASE_URL,
    temperature=0.1,
)
