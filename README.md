# Forest Fire MAS (JADE) - Single Agent Demo

This version is a one-agent runnable JADE prototype for easy cloning and testing.

## Agents

- `DetectionAgent`: simulates fire detection and makes an autonomous decision based on scenario input.
- `AssessmentAgent`: receives fire zone report and autonomously assesses severity level (CRITICAL / MODERATE / LOW).
- `ResourceCoordinationAgent`: receives severity report and autonomously allocates firefighting resources and selects response plan.
- `ResponseAgent`: receives response plan and autonomously decides and dispatches the appropriate emergency action.

## Run (WSL)

```bash
cd "/mnt/e/Semester 2/TIES454 - Agent Technologies for Developers 2026/Project/ForestFireMAS"
mvn -q clean package
mvn -q exec:java
```

Scenario runs:

```bash
mvn -q exec:java -Dexec.args="critical"
mvn -q exec:java -Dexec.args="moderate"
mvn -q exec:java -Dexec.args="low"
```

## What to expect

- JADE main container starts.
- `DetectionAgent` starts.
- It prints an `[AUTONOMOUS_DECISION]` line and detected zone payload.
- Single-agent simulation completes.

## GitHub quick start for others

```bash
git clone <your-repo-url>
cd ForestFireMAS
mvn -q clean package
mvn -q exec:java
```
