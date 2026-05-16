"""
scenario3.py — Multi-Zone Cascading Emergency with Belief Revision

Scenario
────────
Three simultaneous fires are detected at 09:15 local.
  SectorD : MODERATE — stable but active fire west of Petäjävesi
  SectorE : HIGH — near Äänekoski hospital, high life-risk
  SectorF : LOW at first, then escalates to CRITICAL after new sensor data

This scenario runs in two phases:
  Phase 1: full detect → assess → allocate → dispatch pipeline across all zones
  Phase 2: mid-run belief revision, then re-assess/reallocate/re-dispatch

BDI cycle visible in this scenario
───────────────────────────────────
  Beliefs    = live fire state and resource assumptions revised between phases
  Desires    = each agent's persistent goal (defined in agents.py)
  Intentions = Phase 1 and Phase 2 Task objects
"""

import textwrap
import re
from crewai import Task, Crew, Process

from utils import agent_log
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
    FIRE INCIDENT REPORT — SCENARIO 3
    ──────────────────────────────────
    Three simultaneous fires detected at 09:15 local.

    FIRE INCIDENT — SECTOR D
    ────────────────────────
    Zone ID       : SectorD
    GPS           : 62.4812° N, 25.6340° E
    Temperature   : 54 °C
    Smoke density : 210 µg/m³
    Wind speed    : 8 km/h (east)
    Humidity      : 33 %
    Fuel moisture : 12 %
    Nearest town  : Petäjävesi (18 km west)
    Time          : 09:15 local

    FIRE INCIDENT — SECTOR E
    ────────────────────────
    Zone ID       : SectorE
    GPS           : 62.5531° N, 25.8762° E
    Temperature   : 79 °C
    Smoke density : 520 µg/m³
    Wind speed    : 22 km/h (south, gusting)
    Humidity      : 19 %
    Fuel moisture : 7 %
    Nearest town  : Äänekoski hospital (8 km north)
    Time          : 09:15 local

    FIRE INCIDENT — SECTOR F (INITIALLY MINOR)
    ─────────────────────────────────────────
    Zone ID       : SectorF
    GPS           : 62.3947° N, 25.4218° E
    Temperature   : 38 °C
    Smoke density : 95 µg/m³
    Wind speed    : 11 km/h (variable)
    Humidity      : 41 %
    Fuel moisture : 18 %
    Nearest town  : Jyväskylä valley (24 km south-east)
    Time          : 09:15 local

    AVAILABLE RESOURCES
    ───────────────────
    Helicopters    : 3
    Ground crews   : 5
    Water tankers  : 4
""")


SECTOR_F_SENSOR_BURST = textwrap.dedent("""\
    NEW SENSOR BURST — SECTOR F
    ───────────────────────────
    Received at       : 09:52 local
    Zone ID           : SectorF
    GPS               : 62.3947° N, 25.4218° E
    Temperature       : 89 °C
    Wind speed        : 34 km/h
    Wind status       : SHIFT DETECTED
    Spread risk       : EXTREME
    Revised intensity : CRITICAL
    Life-risk note    : Fire front can reach Jyväskylä valley in ~40 minutes
""")


ZONE_COORDINATES = textwrap.dedent("""\
    Authoritative zone coordinates:
    - SectorD: 62.4812° N, 25.6340° E
    - SectorE: 62.5531° N, 25.8762° E
    - SectorF: 62.3947° N, 25.4218° E
""")


FLEET_INVENTORY = textwrap.dedent("""\
    Authoritative fleet inventory and only valid unit IDs:
    - Helicopters   : Helicopter-01, Helicopter-02, Helicopter-03
    - Ground crews  : Ground Crew-01, Ground Crew-02, Ground Crew-03,
                      Ground Crew-04, Ground Crew-05
    - Water tankers : Water Tanker-01, Water Tanker-02,
                      Water Tanker-03, Water Tanker-04
""")


PHASE1_CONTINUITY_SUMMARY = textwrap.dedent("""\
    Authoritative Phase 1 continuity summary:
    - SectorE remains HIGH life-risk because Äänekoski hospital is 8 km north.
    - SectorE has resources already en route and cannot be fully recalled.
    - SectorD received medium support in Phase 1 and may lose resources in Phase 2.
    - SectorF initially had only minimal/reserve coverage.
    - The Phase 1 hospital-area evacuation notice remains ACTIVE.
    - Ignore any Phase 1 output that conflicts with the authoritative coordinates
      or the fixed fleet inventory listed in this task.
""")


EXPECTED_ZONE_GPS = {
    "SectorD": "62.4812° N, 25.6340° E",
    "SectorE": "62.5531° N, 25.8762° E",
    "SectorF": "62.3947° N, 25.4218° E",
}

VALID_UNIT_IDS = {
    "Helicopter": {"Helicopter-01", "Helicopter-02", "Helicopter-03"},
    "Ground Crew": {
        "Ground Crew-01",
        "Ground Crew-02",
        "Ground Crew-03",
        "Ground Crew-04",
        "Ground Crew-05",
    },
    "Water Tanker": {
        "Water Tanker-01",
        "Water Tanker-02",
        "Water Tanker-03",
        "Water Tanker-04",
    },
}


def _validate_phase2_output(output: str) -> list[str]:
    issues: list[str] = []
    unit_counts = {unit_type: 0 for unit_type in VALID_UNIT_IDS}

    order_blocks = re.findall(
        r"REVISED DISPATCH ORDER #\d+.*?(?=┌|Evacuation Notices:|$)",
        output,
        flags=re.DOTALL,
    )

    for index, block in enumerate(order_blocks, start=1):
        unit_match = re.search(r"Unit\s+:\s+(.+?)\s*│", block)
        zone_match = re.search(r"Zone\s+:\s+(Sector[D-F])\s*│", block)
        gps_match = re.search(r"GPS\s+:\s+(.+?)\s*│", block)

        if not unit_match:
            issues.append(f"Order #{index} is missing a unit ID.")
            continue
        if not zone_match:
            issues.append(f"Order #{index} is missing a valid zone.")
            continue
        if not gps_match:
            issues.append(f"Order #{index} is missing GPS coordinates.")
            continue

        unit_id = unit_match.group(1).strip()
        zone_id = zone_match.group(1).strip()
        gps = gps_match.group(1).strip()

        unit_type = next(
            (candidate for candidate in VALID_UNIT_IDS if unit_id.startswith(candidate)),
            None,
        )
        if unit_type is None or unit_id not in VALID_UNIT_IDS[unit_type]:
            issues.append(f"Order #{index} uses out-of-fleet unit {unit_id}.")
        else:
            unit_counts[unit_type] += 1

        expected_gps = EXPECTED_ZONE_GPS[zone_id]
        if gps != expected_gps:
            issues.append(
                f"Order #{index} sends {zone_id} to GPS {gps}; expected {expected_gps}."
            )

    for unit_type, valid_ids in VALID_UNIT_IDS.items():
        if unit_counts[unit_type] > len(valid_ids):
            issues.append(
                f"Phase 2 uses {unit_counts[unit_type]} {unit_type} units; "
                f"fleet has only {len(valid_ids)}."
            )

    if "EVACUATION NOTICE" not in output.upper():
        issues.append("Phase 2 output does not include evacuation notices.")
    if "HOSPITAL" not in output.upper():
        issues.append("Phase 2 output does not confirm the hospital-area notice.")
    if "JYVÄSKYLÄ" not in output.upper() and "JYVASKYLA" not in output.upper():
        issues.append("Phase 2 output does not include the Jyväskylä valley notice.")

    return issues


def _update_phase1_beliefs() -> None:
    print_section("Belief Updates — Phase 1 Pre-Crew")
    detection_beliefs.update("active_zones",         3)
    detection_beliefs.update("zone_D_id",            "SectorD")
    detection_beliefs.update("zone_D_intensity",     "MODERATE")
    detection_beliefs.update("zone_E_id",            "SectorE")
    detection_beliefs.update("zone_E_intensity",     "HIGH")
    detection_beliefs.update("zone_F_id",            "SectorF")
    detection_beliefs.update("zone_F_intensity",     "LOW")
    detection_beliefs.update("zone_F_temperature",   38)
    detection_beliefs.update("zone_F_wind_speed",    11)

    assessment_beliefs.update("pending_zones",       3)
    assessment_beliefs.update("zone_D_proximity_km", 18)
    assessment_beliefs.update("zone_E_proximity_km", 8)
    assessment_beliefs.update("zone_F_proximity_km", 24)
    assessment_beliefs.update("hospital_risk_E",     "HIGH")
    assessment_beliefs.update("uncertainty_flag",    False)

    resource_beliefs.update("zones_needing_resources", 3)
    resource_beliefs.update("resource_conflict",        True)
    resource_beliefs.update("helicopters_available",    3)
    resource_beliefs.update("ground_crews_available",   5)
    resource_beliefs.update("water_tankers_available",  4)
    resource_beliefs.update("reserve_required_for_F",   "1 helicopter")

    response_beliefs.update("evacuation_required",      True)
    response_beliefs.update("hospital_notice_required", True)


def _apply_sector_f_revision() -> None:
    print("\n  ── NEW SENSOR DATA RECEIVED AT 09:52 ──────────────────")
    print(SECTOR_F_SENSOR_BURST)

    print_section("Belief Revision — SectorF Escalation")
    detection_beliefs.update("zone_F_intensity",    "CRITICAL")
    detection_beliefs.update("zone_F_temperature",  89)
    detection_beliefs.update("wind_shift_detected", True)
    detection_beliefs.update("zone_F_wind_speed",   34)
    detection_beliefs.update("zone_F_spread_risk",  "EXTREME")
    resource_beliefs.update("resource_conflict",    "CRITICAL_REPLAN")
    resource_beliefs.update("phase1_plan_status",   "REVOKED")
    response_beliefs.update("second_evacuation_required", True)


def run_scenario3() -> str:
    """
    Execute Scenario 3: multi-zone cascading emergency with mid-run belief
    revision. Returns the final Phase 2 ResponseAgent output string.
    """

    print_section("SCENARIO 3 — Cascading Emergency with Belief Revision  [START]")
    print(SCENARIO_INPUT)

    _update_phase1_beliefs()

    task_detection_phase1 = Task(
        description=textwrap.dedent(f"""\
            You have received simultaneous reports from three sectors.
            Analyse all three and produce a combined detection report.

            {SCENARIO_INPUT}

            Expected classification based on the sensor data:
            - SectorD: MODERATE
            - SectorE: HIGH
            - SectorF: LOW

            For EACH zone your report MUST include:
            1. Zone ID and GPS coordinates
            2. Intensity classification: LOW / MODERATE / HIGH / CRITICAL
            3. Spread risk: STABLE / GROWING / EXTREME
            4. Confidence level (0-100 %) based on sensor agreement
            5. One sentence describing immediate downstream concern

            End with a short comparison of D, E, and F.
        """),
        expected_output=(
            "Three-zone detection report with SectorD=MODERATE, SectorE=HIGH, "
            "SectorF=LOW, including GPS, spread risk, confidence, and comparison."
        ),
        agent=detection_agent,
    )

    task_assessment_phase1 = Task(
        description=textwrap.dedent("""\
            Assess severity for SectorD, SectorE, and SectorF from the detection
            report.

            Severity rules:
            - CRITICAL : intensity HIGH/CRITICAL AND populated area < 5 km
            - HIGH     : intensity HIGH OR spread risk EXTREME OR hospital risk
            - MODERATE : intensity MODERATE AND spread risk STABLE/GROWING
            - LOW      : intensity LOW and no immediate life-risk
            - UNCERTAIN: conflicting sensors OR missing critical fields

            Required assessment outcome:
            - SectorD: MODERATE
            - SectorE: HIGH because Äänekoski hospital is 8 km north
            - SectorF: LOW based on the initial 09:15 data

            Your output for EACH zone MUST include:
            1. Final severity label
            2. Key factors driving the decision
            3. Recommended resource tier: LIGHT / MEDIUM / HEAVY
            4. Life-risk note, especially for the hospital near SectorE
        """),
        expected_output=(
            "Severity assessment for D/E/F with SectorE marked HIGH due to "
            "hospital proximity and SectorF kept LOW during Phase 1."
        ),
        agent=assessment_agent,
        context=[task_detection_phase1],
    )

    task_resource_phase1 = Task(
        description=textwrap.dedent("""\
            Allocate firefighting resources across SectorD, SectorE, and SectorF.

            Available assets (total fleet):
            - Helicopters    : 3
            - Ground crews   : 5
            - Water tankers  : 4

            Hard constraints:
            - Hospital is 8 km from SectorE — life-risk HIGH.
            - SectorF looks minor, but you MUST hold 1 helicopter in reserve for it.
            - You CANNOT split ground crews between zones.
            - Prioritise SectorE first, assign medium support to SectorD, and
              only minimal monitoring or reserve support to SectorF.

            Your output MUST include:
            1. Allocation table for SectorD, SectorE, SectorF, and reserves
            2. Why SectorE receives priority
            3. What SectorD receives as medium support
            4. What SectorF receives or has held in reserve
            5. Any zone left unattended and the consequence
        """),
        expected_output=(
            "Phase 1 allocation plan prioritising SectorE, medium support to "
            "SectorD, minimal/reserve support for SectorF, and explicit constraints."
        ),
        agent=resource_agent,
        context=[task_assessment_phase1],
    )

    task_response_phase1 = Task(
        description=textwrap.dedent("""\
            Convert the Phase 1 allocation into field dispatch orders and
            evacuation notices.

            {zone_coordinates}

            {fleet_inventory}

            Phase 1 required response:
            - Dispatch priority resources to SectorE.
            - Dispatch medium support to SectorD.
            - Keep minimal/reserve coverage for SectorF.
            - Issue an evacuation or protective action notice for the Äänekoski
              hospital area near SectorE.

            Format EACH dispatch order exactly as:
            ┌─────────────────────────────────────────┐
            │ DISPATCH ORDER #<n>                     │
            │ Unit       : <type and ID>              │
            │ Zone       : <SectorD/SectorE/SectorF>  │
            │ GPS        : <coordinates>              │
            │ Task       : <primary task>             │
            │ ETA        : <estimated minutes>        │
            └─────────────────────────────────────────┘

            Validation rules:
            - Use ONLY the exact GPS coordinates from the authoritative list.
            - Use ONLY unit IDs from the authoritative fleet inventory.
            - Do NOT invent Helicopter-04, Ground Crew-06, Water Tanker-05, or
              any other out-of-fleet unit.
            - The total number of deployed plus reserved units may not exceed:
              3 helicopters, 5 ground crews, and 4 water tankers.

            After dispatch orders, include:
            - EVACUATION NOTICE — HOSPITAL AREA: ACTIVE
            - SectorD status
            - SectorE status
            - SectorF status
            - Next review in minutes
        """).format(
            zone_coordinates=ZONE_COORDINATES,
            fleet_inventory=FLEET_INVENTORY,
        ),
        expected_output=(
            "Phase 1 dispatch orders, active hospital-area evacuation notice, "
            "zone statuses, and next review time."
        ),
        agent=response_agent,
        context=[task_resource_phase1],
    )

    print_section("CrewAI Pipeline — Executing (Scenario 3 Phase 1)")
    crew_phase1 = Crew(
        agents=[detection_agent, assessment_agent, resource_agent, response_agent],
        tasks=[
            task_detection_phase1,
            task_assessment_phase1,
            task_resource_phase1,
            task_response_phase1,
        ],
        process=Process.sequential,
        verbose=True,
    )

    with agent_log("scenario3_phase1") as log_path:
        phase1_result = crew_phase1.kickoff()
    print(f"  Agent log saved → {log_path}")

    print_section("Belief Updates — Phase 1 Post-Crew")
    detection_beliefs.update("last_report",          "SectorD-MODERATE + SectorE-HIGH + SectorF-LOW")
    assessment_beliefs.update("last_severity",       "D=MODERATE, E=HIGH, F=LOW")
    resource_beliefs.update("phase1_plan_status",    "ACTIVE")
    response_beliefs.update("dispatch_orders_issued", "PHASE1_MULTI_ZONE")
    response_beliefs.update("evacuations_ordered",   1)
    response_beliefs.update("last_dispatch_zone",    "SectorD+SectorE+SectorF")

    _apply_sector_f_revision()

    task_assessment_phase2 = Task(
        description=textwrap.dedent(f"""\
            Re-assess SectorF only using the new 09:52 sensor burst.
            This is an emergency re-deliberation after Phase 1.

            {SECTOR_F_SENSOR_BURST}

            {PHASE1_CONTINUITY_SUMMARY}

            Required outcome:
            - SectorF must now be classified CRITICAL.
            - Explain why the wind shift and 34 km/h wind create EXTREME spread.
            - State that Jyväskylä valley is threatened within ~40 minutes.

            Your output MUST include:
            1. Revised severity label for SectorF
            2. Changed factors compared with Phase 1
            3. Recommended resource tier: HEAVY / EMERGENCY
            4. Immediate downstream instruction for resource replanning
        """),
        expected_output=(
            "SectorF emergency re-assessment: CRITICAL severity, EXTREME spread "
            "risk, Jyväskylä valley threat in ~40 minutes, and emergency tier."
        ),
        agent=assessment_agent,
    )

    task_resource_phase2 = Task(
        description=textwrap.dedent(f"""\
            Rebuild the allocation from scratch after the SectorF escalation.
            The Phase 1 plan is REVOKED due to a CRITICAL_REPLAN belief.

            New SectorF facts:
            {SECTOR_F_SENSOR_BURST}

            {ZONE_COORDINATES}

            {FLEET_INVENTORY}

            {PHASE1_CONTINUITY_SUMMARY}

            Available fleet remains:
            - Helicopters    : 3
            - Ground crews   : 5
            - Water tankers  : 4

            Hard constraints:
            - Phase 1 allocation is REVOKED due to SectorF escalation.
            - Some resources are already en route to SectorE and cannot be fully
              recalled because the hospital-area risk remains HIGH.
            - SectorF wind 34 km/h can reach Jyväskylä valley in ~40 minutes.
            - You CANNOT split ground crews between zones.

            You MUST show:
            1. What stays at SectorE and why the hospital notice remains active
            2. What moves or is newly assigned to SectorF
            3. What SectorD loses compared with Phase 1
            4. Whether any zone becomes completely unattended
            5. A revised allocation table for D, E, F, and reserve
            6. A validation line proving the allocation does not exceed
               3 helicopters, 5 ground crews, or 4 water tankers

            Do NOT invent additional units or request external assets. If the
            fixed fleet is insufficient, state the shortage instead of assigning
            out-of-fleet units.
        """),
        expected_output=(
            "Phase 2 reallocation table showing what stays at E, what moves to F, "
            "what D loses, and whether any zone is unattended."
        ),
        agent=resource_agent,
        context=[task_assessment_phase2],
    )

    task_response_phase2 = Task(
        description=textwrap.dedent(f"""\
            Issue revised dispatch orders and evacuation notices based on the
            Phase 2 reallocation.

            {ZONE_COORDINATES}

            {FLEET_INVENTORY}

            {PHASE1_CONTINUITY_SUMMARY}

            Required evacuation notices:
            1. Hospital area (SectorE): confirm the Phase 1 notice is STILL ACTIVE.
            2. Jyväskylä valley (SectorF): issue a NEW evacuation notice due to
               CRITICAL escalation and ~40 minute arrival risk.

            Format EACH revised dispatch order exactly as:
            ┌─────────────────────────────────────────┐
            │ REVISED DISPATCH ORDER #<n>             │
            │ Unit       : <type and ID>              │
            │ Zone       : <SectorD/SectorE/SectorF>  │
            │ Action     : <stay / move / newly assign>│
            │ GPS        : <coordinates>              │
            │ Task       : <primary task>             │
            │ ETA        : <estimated minutes>        │
            └─────────────────────────────────────────┘

            Validation rules:
            - Use ONLY the exact GPS coordinates from the authoritative list.
            - Use ONLY unit IDs from the authoritative fleet inventory.
            - Do NOT invent Helicopter-04, Ground Crew-06, Water Tanker-05, or
              any other out-of-fleet unit.
            - The revised dispatch orders must match the ResourceCoordinationAgent
              allocation and may not exceed 3 helicopters, 5 ground crews, or
              4 water tankers total.
            - If Phase 2 has a shortage, state it as a shortage; do not create
              additional units.

            After revised orders, issue both evacuation notices and end with:
            - SectorD status
            - SectorE status
            - SectorF status
            - Any unattended-zone warning
            - Resource validation: PASS / FAIL with one sentence
            - Next review in minutes
        """),
        expected_output=(
            "Revised Phase 2 dispatch orders plus two evacuation notices: "
            "hospital area still active and new Jyväskylä valley evacuation."
        ),
        agent=response_agent,
        context=[task_resource_phase2],
    )

    print_section("CrewAI Pipeline — Executing (Scenario 3 Phase 2)")
    crew_phase2 = Crew(
        agents=[assessment_agent, resource_agent, response_agent],
        tasks=[task_assessment_phase2, task_resource_phase2, task_response_phase2],
        process=Process.sequential,
        verbose=True,
    )

    with agent_log("scenario3_phase2") as log_path:
        phase2_result = crew_phase2.kickoff()
    print(f"  Agent log saved → {log_path}")

    print_section("QA Validation — Phase 2 Output")
    phase2_qa_issues = _validate_phase2_output(str(phase2_result))
    if phase2_qa_issues:
        print("  Phase 2 output validation: FAIL")
        for issue in phase2_qa_issues:
            print(f"  - {issue}")
    else:
        print("  Phase 2 output validation: PASS")

    print_section("Belief Updates — Phase 2 Post-Crew")
    detection_beliefs.update("last_report",          "SectorF-CRITICAL-REVISION")
    assessment_beliefs.update("last_severity",       "SectorF=CRITICAL")
    assessment_beliefs.update("zone_F_spread_risk",  "EXTREME")
    resource_beliefs.update("resource_conflict",     "REPLANNED")
    resource_beliefs.update("phase2_priority_zone",  "SectorF")
    resource_beliefs.update("phase1_plan_status",    "REVOKED_AND_REPLACED")
    response_beliefs.update("evacuations_ordered",   2)
    response_beliefs.update("hospital_notice_status", "STILL_ACTIVE")
    response_beliefs.update("jyvaskyla_valley_notice", "ISSUED")
    response_beliefs.update("last_dispatch_zone",    "SectorE+SectorF")
    response_beliefs.update("phase2_output_valid",    not phase2_qa_issues)

    print_section("Final Belief Bases — Scenario 3")
    detection_beliefs.dump()
    assessment_beliefs.dump()
    resource_beliefs.dump()
    response_beliefs.dump()

    print_section("SCENARIO 3 — COMPLETE")
    return str(phase2_result)


# ── Standalone execution ──────────────────────────────────────────────────────
if __name__ == "__main__":
    output = run_scenario3()
    print("\n── Final Phase 2 ResponseAgent Output ──────────────────")
    print(output)
