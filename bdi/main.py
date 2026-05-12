"""
main.py — ForestFireMAS BDI Entry Point

Runs both scenarios in sequence and prints a final summary.

Usage:
    python main.py            # run both scenarios
    python main.py --s1       # run Scenario 1 only
    python main.py --s2       # run Scenario 2 only

Architecture reminder
─────────────────────
  Framework  : CrewAI  (multi-agent orchestration)
  LLMs       : Ollama  (local, no API key required)
  BDI layer  : beliefs.py + agents.py (explicit B/D/I mapping)
  Models     :
    DetectionAgent            → mistral
    AssessmentAgent           → llama3.1
    ResourceCoordinationAgent → llama3.1
    ResponseAgent             → gemma2:9b
"""

import sys
import time

DIVIDER_HEAVY = "█" * 60
DIVIDER_LIGHT = "─" * 60


def banner() -> None:
    print()
    print(DIVIDER_HEAVY)
    print("  ForestFireMAS — BDI Extension")
    print(DIVIDER_HEAVY)
    print()


def run_all() -> None:
    banner()

    args = sys.argv[1:]
    run_s1 = "--s2" not in args or "--s1" in args
    run_s2 = "--s1" not in args or "--s2" in args

    results = {}

    # ── Scenario 1 ────────────────────────────────────────────────────────────
    if run_s1:
        print(f"\n{DIVIDER_HEAVY}")
        print("  RUNNING SCENARIO 1 — Standard Single-Zone Response")
        print(DIVIDER_HEAVY)
        from scenario1 import run_scenario1
        t0 = time.time()
        results["scenario1"] = run_scenario1()
        elapsed1 = time.time() - t0
        print(f"\n  [Scenario 1 completed in {elapsed1:.1f}s]")

    # ── Scenario 2 ────────────────────────────────────────────────────────────
    if run_s2:
        print(f"\n{DIVIDER_HEAVY}")
        print("  RUNNING SCENARIO 2 — Dual-Zone Resource Conflict")
        print(DIVIDER_HEAVY)
        from scenario2 import run_scenario2
        t0 = time.time()
        results["scenario2"] = run_scenario2()
        elapsed2 = time.time() - t0
        print(f"\n  [Scenario 2 completed in {elapsed2:.1f}s]")

    # ── Final summary ─────────────────────────────────────────────────────────
    print()
    print(DIVIDER_HEAVY)
    print("  FINAL SUMMARY")
    print(DIVIDER_HEAVY)

    if "scenario1" in results:
        print(f"\n{'SCENARIO 1 OUTPUT':─<58}")
        print(results["scenario1"])

    if "scenario2" in results:
        print(f"\n{'SCENARIO 2 OUTPUT':─<58}")
        print(results["scenario2"])

    print()
    print(DIVIDER_HEAVY)
    print("  All scenarios completed.")
    print("  BDI mapping demonstrated:")
    print("    Beliefs  → BeliefBase updates printed above")
    print("    Desires  → Agent.goal fields in agents.py")
    print("    Intentions → Task objects in scenario1.py / scenario2.py")
    print(DIVIDER_HEAVY)
    print()


if __name__ == "__main__":
    run_all()
