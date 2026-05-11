"""
config.py — LLM configuration for ForestFireMAS BDI agents.

Each agent gets its own model matched to task complexity.
All models run locally via Ollama — no API key or internet needed.

To swap a model, change the value here. Nothing else needs to change.
"""

from langchain_ollama import OllamaLLM

OLLAMA_BASE_URL = "http://localhost:11434"

# ── DetectionAgent — simplest task (sensor reading + reporting) ──
# mistral is fast and light — no complex reasoning needed here
LLM_DETECTION = OllamaLLM(
    model="mistral",
    base_url=OLLAMA_BASE_URL,
    temperature=0.1,
)

# ── AssessmentAgent — rule-based severity classification ─────────
# llama3.1 handles edge cases like UNCERTAIN flagging cleanly
LLM_ASSESSMENT = OllamaLLM(
    model="llama3.1",
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
)

# ── ResourceCoordinationAgent — conflicting goals, deliberation ──
# Heaviest task → best available model
# If RAM < 32GB change to "llama3.1"
LLM_RESOURCE = OllamaLLM(
    model="llama3.1",
    base_url=OLLAMA_BASE_URL,
    temperature=0.3,
)

# ── ResponseAgent — structured dispatch output ───────────────────
# gemma2:9b is reliable and decisive for command-style output
LLM_RESPONSE = OllamaLLM(
    model="gemma2:9b",
    base_url=OLLAMA_BASE_URL,
    temperature=0.1,
)
