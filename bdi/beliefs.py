"""
beliefs.py — Explicit BDI Belief Base for ForestFireMAS agents.

Each agent has its own BeliefBase instance. Beliefs are stored as
key-value pairs and every update is printed to the terminal so the
belief change is visible in screenshots for the project report.

BDI mapping:
    BeliefBase  → Beliefs (B)
    Agent.goal  → Desires  (D)   [defined in agents.py]
    Task        → Plans    (P)   [defined in scenario files]
"""


class BeliefBase:
    """
    A per-agent belief store that logs every update to stdout.

    Usage:
        beliefs = BeliefBase("DetectionAgent")
        beliefs.update("zone_intensity", "HIGH")
        val = beliefs.get("zone_intensity")
        beliefs.dump()
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._store: dict = {}

    def update(self, key: str, value) -> None:
        """Add or update a belief. Prints the change to stdout."""
        old = self._store.get(key, "<undefined>")
        self._store[key] = value
        print(f"  [BELIEF] {self.agent_name:<30} {key}: {old}  →  {value}")

    def get(self, key: str, default=None):
        """Retrieve a belief value."""
        return self._store.get(key, default)

    def all(self) -> dict:
        """Return a snapshot of all current beliefs."""
        return dict(self._store)

    def dump(self) -> None:
        """Print the full belief base to stdout."""
        print(f"\n  ┌─ [{self.agent_name}] Belief Base ────────────────────")
        if not self._store:
            print("  │  (empty)")
        for k, v in self._store.items():
            print(f"  │  {k}: {v}")
        print("  └────────────────────────────────────────────────\n")


# ── One belief base per agent ─────────────────────────────────────
# Instantiated at module level so beliefs persist across tasks
# within a single scenario run.

detection_beliefs  = BeliefBase("DetectionAgent")
assessment_beliefs = BeliefBase("AssessmentAgent")
resource_beliefs   = BeliefBase("ResourceCoordinationAgent")
response_beliefs   = BeliefBase("ResponseAgent")
