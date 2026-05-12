"""
scenario2.py — Dual-Zone Resource Conflict with Uncertainty

Scenario
────────
Two simultaneous fires are detected.
  SectorA : CRITICAL intensity — only 4 km from the town of Äänekoski
  SectorB : UNCERTAIN — sensors partially offline, conflicting readings

Available resources are insufficient to fully suppress BOTH zones.
The ResourceCoordinationAgent must reason about the trade-off explicitly
and commit to a prioritised plan.

This scenario demonstrates:
  • BDI conflict resolution    — competing zone goals, limited resources
  • Uncertainty handling       — UNCERTAIN flag from AssessmentAgent
  • Multi-step deliberation    — ResourceCoordinationAgent reasons transparently
  • Belief revision            — beliefs update as new information arrives
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


SECTOR_A_INPUT = textwrap.dedent("""\
    FIRE INCIDENT — SECTOR A (PRIMARY)
    ───────────────────────────────────
    Zone ID       : SectorA
    GPS           : 62.6018° N, 25.7261° E
    Temperature   : 94 °C (sensor array average)
    Smoke density : 780 µg/m³
    Wind speed    : 31 km/h (south-west, gusting)
    Humidity      : 14 %
    Nearest town  : Äänekoski (4 km north-east)
    Fuel moisture : 5 % (extremely dry, pine canopy)
    Time of day   : 11:47 local
""")

SECTOR_B_INPUT = textwrap.dedent("""\
    FIRE INCIDENT — SECTOR B (SECONDARY, UNCERTAIN)
    ────────────────────────────────────────────────
    Zone ID       : SectorB
    GPS           : 62.7341° N, 25.5882° E
    Temperature   : 41 °C (only 2 of 6 sensors responding)
    Smoke density : SENSOR OFFLINE
    Wind speed    : 18 km/h (variable direction)
    Humidity      : 35 %
    Nearest town  : Saarijärvi (22 km east)
    Fuel moisture : UNKNOWN (sensor fault)
    Time of day   : 11:47 local
    ALERT         : Sensor network 67 % offline in this sector
""")


def run_scenario2() -> str:
    """
    Execute Scenario 2: dual-zone resource conflict with uncertainty.
    Returns the final ResponseAgent output string.
    """

    print_section("SCENARIO 2 — Dual-Zone Resource Conflict  [START]")
    print(SECTOR_A_INPUT)
    print(SECTOR_B_INPUT)

    # ── Update beliefs to reflect scenario context ────────────────────────────
    print_section("Belief Updates — Pre-Crew")
    detection_beliefs.update("active_zones",          2)
    detection_beliefs.update("zone_A_id",             "SectorA")
    detection_beliefs.update("zone_A_intensity",      "CRITICAL")
    detection_beliefs.update("zone_B_id",             "SectorB")
    detection_beliefs.update("zone_B_intensity",      "UNCERTAIN")
    detection_beliefs.update("sensor_fault_B",        True)

    assessment_beliefs.update("pending_zones",        2)
    assessment_beliefs.update("zone_A_proximity_km",  4)
    assessment_beliefs.update("zone_B_proximity_km",  22)
    assessment_beliefs.update("uncertainty_flag",     True)

    resource_beliefs.update("zones_needing_resources", 2)
    resource_beliefs.update("resource_conflict",        True)   # KEY belief
    resource_beliefs.update("helicopters_available",    3)
    resource_beliefs.update("ground_crews_available",   5)
    resource_beliefs.update("water_tankers_available",  4)

    response_beliefs.update("evacuation_required",    True)    # SectorA near town

    task_detection = Task(
        description=textwrap.dedent(f"""\
            You have received simultaneous reports from two sectors.
            Analyse both and produce a combined detection report.

            {SECTOR_A_INPUT}
            {SECTOR_B_INPUT}

            For EACH zone your report MUST include:
            1. Zone ID and GPS coordinates
            2. Intensity classification: LOW / MODERATE / HIGH / CRITICAL / UNABLE_TO_CONFIRM
            3. Spread risk: STABLE / GROWING / EXTREME / UNKNOWN
            4. Confidence level (0–100 %) — note sensor faults where relevant
            5. Data gaps or sensor faults that affect confidence

            End with a one-paragraph summary comparing both zones.
        """),
        expected_output=(
            "Dual detection report: one block per zone with ID, GPS, intensity, "
            "spread risk, confidence %, sensor fault notes, and comparative summary."
        ),
        agent=detection_agent,
    )

    # ── Task 2: Assessment (both zones, one UNCERTAIN) ────────────────────────
    task_assessment = Task(
        description=textwrap.dedent("""\
            Assess severity for BOTH zones from the detection report.

            Severity rules:
            - CRITICAL : intensity HIGH/CRITICAL AND nearest town < 5 km
            - HIGH     : intensity HIGH OR spread risk EXTREME
            - MODERATE : intensity MODERATE AND spread risk STABLE/GROWING
            - LOW      : intensity LOW AND humidity > 40 %
            - UNCERTAIN: conflicting sensors OR confidence < 50 % OR missing
                         critical fields (smoke density, fuel moisture)

            IMPORTANT: SectorB has 67 % sensor failure.
            If you cannot determine severity with ≥ 50 % confidence, classify
            it UNCERTAIN and state exactly what data is missing.

            Your output for EACH zone MUST include:
            1. Final severity label (apply UNCERTAIN rigorously)
            2. Key factors (bullet list)
            3. Recommended resource tier: LIGHT / MEDIUM / HEAVY / HOLD
            4. UNCERTAIN flag with missing data listed (if applicable)
        """),
        expected_output=(
            "Two severity assessments (one per zone). SectorA should be CRITICAL. "
            "SectorB should be flagged UNCERTAIN with missing data listed."
        ),
        agent=assessment_agent,
        context=[task_detection],
    )

    # ── Task 3: Resource Coordination (conflict resolution) ───────────────────
    task_resource = Task(
        description=textwrap.dedent("""\
            Allocate firefighting resources across BOTH zones.
            Resources are INSUFFICIENT to fully suppress both simultaneously.

            Available assets (total fleet):
            - Helicopters    : 3  (each 2 000 L, ~20 min flight time to either zone)
            - Ground crews   : 5  (each 8-person; SectorA ETA 25 min, SectorB 40 min)
            - Water tankers  : 4  (road access: SectorA YES, SectorB UNCERTAIN)

            Constraints:
            - SectorA is 4 km from Äänekoski — life-risk is HIGH
            - SectorB severity is UNCERTAIN — committing full resources is risky
            - Wind 31 km/h at SectorA means fire can reach town in ~35 minutes
            - You CANNOT split a ground crew between zones

            You MUST:
            1. Prioritise explicitly — state which zone gets priority and WHY
            2. Show the trade-off: what SectorB loses because of SectorA priority
            3. Recommend a minimum holding action for the lower-priority zone
            4. Flag any zone left unattended and estimate consequence
            5. State what additional information about SectorB would change the plan
        """),
        expected_output=(
            "Prioritised allocation: SectorA gets dominant resources (justify). "
            "SectorB gets a holding action or is flagged as unattended. "
            "Trade-off explanation, consequence estimate, and info gaps stated."
        ),
        agent=resource_agent,
        context=[task_assessment],
    )

    # ── Task 4: Response / Dispatch (with evacuation) ─────────────────────────
    task_response = Task(
        description=textwrap.dedent("""\
            Issue dispatch orders and evacuation notices for both zones.

            Format EACH dispatch order exactly as:
            ┌─────────────────────────────────────────┐
            │ DISPATCH ORDER #<n>                     │
            │ Unit       : <type and ID>              │
            │ Zone       : <SectorA or SectorB>       │
            │ GPS        : <coordinates>              │
            │ Task       : <primary task>             │
            │ ETA        : <estimated minutes>        │
            └─────────────────────────────────────────┘

            After dispatch orders, issue:

            EVACUATION NOTICE — SECTOR A
            ┌─────────────────────────────────────────┐
            │ EVACUATION ORDER                        │
            │ Area       : Äänekoski (4 km radius)   │
            │ Reason     : CRITICAL fire, 4 km away  │
            │ Direction  : Away from north-east       │
            │ Issued at  : 11:47 local               │
            └─────────────────────────────────────────┘

            End with:
            - SECTOR A status: <CONTAINED / ACTIVE / ESCALATING>
            - SECTOR B status: <MONITORING / UNATTENDED / ACTIVE>
            - Resource conflict resolved: YES / PARTIAL / NO
            - Next review in: <minutes>
        """),
        expected_output=(
            "Dispatch orders for all deployed units, a formal evacuation notice "
            "for Äänekoski, and a dual-zone status summary."
        ),
        agent=response_agent,
        context=[task_resource],
    )

    # ── Assemble and run the Crew ─────────────────────────────────────────────
    print_section("CrewAI Pipeline — Executing (Scenario 2)")

    crew = Crew(
        agents=[detection_agent, assessment_agent, resource_agent, response_agent],
        tasks=[task_detection, task_assessment, task_resource, task_response],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    # ── Post-run belief updates ───────────────────────────────────────────────
    print_section("Belief Updates — Post-Crew")
    detection_beliefs.update("last_report",          "SectorA-CRITICAL + SectorB-UNCERTAIN")
    assessment_beliefs.update("last_severity",       "CRITICAL (SectorA), UNCERTAIN (SectorB)")
    assessment_beliefs.update("uncertainty_flag",    True)
    resource_beliefs.update("resource_conflict",     False)   # resolved (partially)
    response_beliefs.update("dispatch_orders_issued", 2)
    response_beliefs.update("evacuations_ordered",   1)
    response_beliefs.update("last_dispatch_zone",    "SectorA+SectorB")

    # ── Dump final belief bases ───────────────────────────────────────────────
    print_section("Final Belief Bases — Scenario 2")
    detection_beliefs.dump()
    assessment_beliefs.dump()
    resource_beliefs.dump()
    response_beliefs.dump()

    print_section("SCENARIO 2 — COMPLETE")
    return str(result)


# ── Standalone execution ──────────────────────────────────────────────────────
if __name__ == "__main__":
    output = run_scenario2()
    print("\n── Final ResponseAgent Output ──────────────────────────")
    print(output)
