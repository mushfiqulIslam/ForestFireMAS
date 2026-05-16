"""
main.py — ForestFireMAS BDI Entry Point

Runs all scenarios in sequence and prints a final summary.

Usage:
    python main.py            # run all scenarios
    python main.py --s1       # run Scenario 1 only
    python main.py --s2       # run Scenario 2 only
    python main.py --s3       # run Scenario 3 only

Architecture reminder
─────────────────────
  Framework  : CrewAI  (multi-agent orchestration)
  LLMs       : Ollama  (local, no API key required)
  BDI layer  : beliefs.py + agents.py (explicit B/D/I mapping)
  Models     :
    DetectionAgent            → mistral
    AssessmentAgent           → llama3.1
    ResourceCoordinationAgent → llama3.1
    ResponseAgent             → mistral
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
    scenario_flags = {"--s1", "--s2", "--s3"}
    requested = scenario_flags.intersection(args)
    run_s1 = not requested or "--s1" in requested
    run_s2 = not requested or "--s2" in requested
    run_s3 = not requested or "--s3" in requested

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

    # ── Scenario 3 ────────────────────────────────────────────────────────────
    if run_s3:
        print(f"\n{DIVIDER_HEAVY}")
        print("  RUNNING SCENARIO 3 — Cascading Emergency with Belief Revision")
        print(DIVIDER_HEAVY)
        from scenario3 import run_scenario3
        t0 = time.time()
        results["scenario3"] = run_scenario3()
        elapsed3 = time.time() - t0
        print(f"\n  [Scenario 3 completed in {elapsed3:.1f}s]")

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

    if "scenario3" in results:
        print(f"\n{'SCENARIO 3 OUTPUT':─<58}")
        print(results["scenario3"])

    print()
    print(DIVIDER_HEAVY)
    print("  All scenarios completed.")
    print("  BDI mapping demonstrated:")
    print("    Beliefs  → BeliefBase updates printed above")
    print("    Desires  → Agent.goal fields in agents.py")
    print("    Intentions → Task objects in scenario1.py / scenario2.py / scenario3.py")
    print(DIVIDER_HEAVY)
    print()


if __name__ == "__main__":
    run_all()
