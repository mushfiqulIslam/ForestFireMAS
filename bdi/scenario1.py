"""
scenario1.py — Standard Single-Zone Forest Fire Response

Scenario
────────
A single fire is detected in Sector C.
Sensors report MODERATE intensity with stable wind conditions.
All four agents work cooperatively in sequence: detect → assess → allocate → dispatch.
No resource conflict. Demonstrates the core BDI pipeline.

BDI cycle visible in this scenario
───────────────────────────────────
  Beliefs update at each stage (printed by BeliefBase.update)
  Desire    = each agent's persistent goal (defined in agents.py)
  Intention = each Task object — the agent's current committed plan

"""

import textwrap
from crewai import Task, Crew, Process

from agents import (
    detection_agent,
    assessment_agent,
    resource_agent,
    response_agent,
)
from beliefs import (
    detection_beliefs,
    assessment_beliefs,
    resource_beliefs,
    response_beliefs,
)

DIVIDER = "═" * 60


def print_section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


SCENARIO_INPUT = textwrap.dedent("""\
    FIRE INCIDENT REPORT — SCENARIO 1
    ──────────────────────────────────
    Zone ID       : SectorC
    GPS           : 62.2426° N, 25.7473° E
    Temperature   : 68 °C (sensor array average)
    Smoke density : 340 µg/m³
    Wind speed    : 12 km/h (north-east)
    Humidity      : 28 %
    Nearest town  : Jyväskylä (11 km south-west)
    Fuel moisture : 9 % (dry understory)
    Time of day   : 14:32 local
""")


def run_scenario1() -> str:
    """
    Execute Scenario 1: single-zone cooperative BDI pipeline.
    Returns the final ResponseAgent output string.
    """

    print_section("SCENARIO 1 — Standard Single-Zone Response  [START]")
    print(SCENARIO_INPUT)

    print_section("Belief Updates — Pre-Crew")
    detection_beliefs.update("active_zones",    1)
    detection_beliefs.update("zone_id",         "SectorC")
    detection_beliefs.update("zone_intensity",  "MODERATE")
    detection_beliefs.update("wind_speed_kmh",  12)
    detection_beliefs.update("humidity_pct",    28)

    assessment_beliefs.update("pending_zones",    1)
    assessment_beliefs.update("zone_id",          "SectorC")
    assessment_beliefs.update("proximity_km",     11)

    resource_beliefs.update("zones_needing_resources", 1)
    resource_beliefs.update("resource_conflict",        False)

    response_beliefs.update("evacuation_required", False)

    task_detection = Task(
        description=textwrap.dedent(f"""\
            You have received the following raw sensor data. Analyse it and produce
            a structured detection report.

            {SCENARIO_INPUT}

            Your report MUST include:
            1. Confirmed zone ID and GPS coordinates
            2. Intensity classification: LOW / MODERATE / HIGH / CRITICAL
            3. Spread risk assessment: STABLE / GROWING / EXTREME
            4. Confidence level (0–100 %) based on sensor agreement
            5. One-sentence summary for downstream agents
        """),
        expected_output=(
            "A structured detection report with zone ID, GPS, intensity level, "
            "spread risk, confidence %, and a one-sentence summary."
        ),
        agent=detection_agent,
    )

    task_assessment = Task(
        description=textwrap.dedent("""\
            Review the detection report from DetectionAgent for SectorC.
            Apply wildfire severity classification rules and produce an assessment.

            Severity rules (apply all that match, take the highest):
            - CRITICAL : intensity HIGH/CRITICAL AND nearest town < 5 km
            - HIGH     : intensity HIGH OR spread risk EXTREME
            - MODERATE : intensity MODERATE AND spread risk STABLE/GROWING
            - LOW      : intensity LOW AND humidity > 40 %
            - UNCERTAIN: conflicting sensors OR missing key fields

            Your output MUST include:
            1. Final severity label
            2. Key factors driving the decision (bullet list)
            3. Recommended resource tier: LIGHT / MEDIUM / HEAVY
            4. Any UNCERTAIN flags and what data is missing
        """),
        expected_output=(
            "Severity label (LOW/MODERATE/HIGH/CRITICAL/UNCERTAIN), "
            "driving factors, resource tier recommendation, and uncertainty flags."
        ),
        agent=assessment_agent,
        context=[task_detection],
    )

    task_resource = Task(
        description=textwrap.dedent("""\
            Allocate firefighting resources for SectorC based on the assessment.

            Available assets (current inventory):
            - Helicopters    : 3  (each can carry 2 000 L water)
            - Ground crews   : 5  (each 8-person team with hand tools + pump)
            - Water tankers  : 4  (each 10 000 L capacity)

            There is only ONE active zone (SectorC). No resource conflict exists.
            Allocate what is proportionate to the assessed severity tier.

            Your output MUST include:
            1. Assets assigned to SectorC (unit type + quantity)
            2. Assets held in reserve (with reason)
            3. Estimated suppression time
            4. Any constraints or risks to the plan
        """),
        expected_output=(
            "Allocation table: assets deployed to SectorC, assets in reserve, "
            "estimated suppression time, and plan constraints."
        ),
        agent=resource_agent,
        context=[task_assessment],
    )

    task_response = Task(
        description=textwrap.dedent("""\
            Convert the resource allocation plan for SectorC into formal field
            dispatch orders and, if required, evacuation notices.

            Format each dispatch order exactly as:
            ┌─────────────────────────────────────────┐
            │ DISPATCH ORDER #<n>                     │
            │ Unit       : <type and ID>              │
            │ Zone       : SectorC                    │
            │ GPS        : 62.2426° N, 25.7473° E    │
            │ Task       : <primary task>             │
            │ ETA        : <estimated minutes>        │
            └─────────────────────────────────────────┘

            After all dispatch orders, include:
            - EVACUATION NOTICE (if HIGH or CRITICAL and town < 15 km): YES / NO
            - Incident status: CONTAINED / ACTIVE / ESCALATING
            - Next review in: <minutes>
        """),
        expected_output=(
            "One dispatch order block per unit deployed, followed by evacuation "
            "notice status, incident status, and next review time."
        ),
        agent=response_agent,
        context=[task_resource],
    )
    print_section("CrewAI Pipeline — Executing")

    crew = Crew(
        agents=[detection_agent, assessment_agent, resource_agent, response_agent],
        tasks=[task_detection, task_assessment, task_resource, task_response],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    # ── Post-run belief updates ───────────────────────────────────────────────
    print_section("Belief Updates — Post-Crew")
    detection_beliefs.update("last_report",         "SectorC-MODERATE")
    assessment_beliefs.update("last_severity",      "MODERATE")
    assessment_beliefs.update("uncertainty_flag",   False)
    resource_beliefs.update("resource_conflict",    False)
    response_beliefs.update("dispatch_orders_issued", 1)
    response_beliefs.update("last_dispatch_zone",   "SectorC")

    # ── Dump final belief bases ───────────────────────────────────────────────
    print_section("Final Belief Bases — Scenario 1")
    detection_beliefs.dump()
    assessment_beliefs.dump()
    resource_beliefs.dump()
    response_beliefs.dump()

    print_section("SCENARIO 1 — COMPLETE")
    return str(result)


# ── Standalone execution ──────────────────────────────────────────────────────
if __name__ == "__main__":
    output = run_scenario1()
    print("\n── Final ResponseAgent Output ──────────────────────────")
    print(output)
