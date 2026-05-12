"""
agents.py — CrewAI Agent definitions for ForestFireMAS BDI system.

BDI mapping
───────────
  Beliefs  → BeliefBase instances from beliefs.py (runtime state)
  Desires  → Agent.goal field (what the agent persistently wants)
  Intentions → Task objects constructed in scenario files (what it commits to doing now)

Four agents mirror the JADE implementation but run locally via Ollama:
  DetectionAgent            — mistral      (fast sensor reader)
  AssessmentAgent           — llama3.1     (rule-based severity classifier)
  ResourceCoordinationAgent — llama3.1     (conflict-aware allocator)
  ResponseAgent             — gemma2:9b    (structured dispatch writer)
"""

from crewai import Agent
from config import LLM_DETECTION, LLM_ASSESSMENT, LLM_RESOURCE, LLM_RESPONSE
from beliefs import (
    detection_beliefs,
    assessment_beliefs,
    resource_beliefs,
    response_beliefs,
)


# ── 1. DetectionAgent ─────────────────────────────────────────────────────────
# Desire: continuously monitor sensor feeds and report confirmed fire zones.
# Runs on mistral — task is structured (read inputs, emit a report), no deep
# reasoning needed; speed matters more than deliberation here.

detection_agent = Agent(
    role="DetectionAgent",
    goal=(
        "Monitor all incoming sensor feeds, identify active fire zones, "
        "and produce a concise detection report: zone ID, GPS coordinates, "
        "intensity level (LOW / MODERATE / HIGH / CRITICAL), and spread risk."
    ),
    backstory=(
        "You are a real-time sensor fusion agent in the ForestFireMAS system. "
        "You receive temperature, smoke-density, wind, and satellite imagery feeds "
        "from deployed IoT sensors across a forested region. "
        "Your reports are the ground truth that all downstream agents rely on — "
        "accuracy and speed are both critical. "
        "You never speculate beyond the sensor data."
    ),
    llm=LLM_DETECTION,
    verbose=True,
)

# Seed initial beliefs for DetectionAgent
detection_beliefs.update("sensor_status",   "ONLINE")
detection_beliefs.update("active_zones",    0)
detection_beliefs.update("last_report",     "NONE")


# ── 2. AssessmentAgent ────────────────────────────────────────────────────────
# Desire: classify each detected fire zone with a severity level and flag
# uncertainty when sensor data is incomplete or contradictory.

assessment_agent = Agent(
    role="AssessmentAgent",
    goal=(
        "Receive fire detection reports and classify each zone as "
        "LOW / MODERATE / HIGH / CRITICAL, or flag it as UNCERTAIN when "
        "sensor data is insufficient. Output a severity assessment with "
        "justification and a recommended resource tier."
    ),
    backstory=(
        "You are a fire-behaviour expert agent in ForestFireMAS. "
        "You apply established wildfire severity rules: wind speed, humidity, "
        "fuel moisture, proximity to populated areas, and rate of spread. "
        "When data is conflicting or missing you explicitly flag the zone UNCERTAIN "
        "rather than guessing — downstream agents treat UNCERTAIN zones differently "
        "from confirmed ones. You never escalate unnecessarily."
    ),
    llm=LLM_ASSESSMENT,
    verbose=True,
)

# Seed initial beliefs for AssessmentAgent
assessment_beliefs.update("pending_zones",       0)
assessment_beliefs.update("last_severity",       "NONE")
assessment_beliefs.update("uncertainty_flag",    False)


# ── 3. ResourceCoordinationAgent ──────────────────────────────────────────────
# Desire: allocate finite firefighting resources optimally across all active
# zones, resolving conflicts when multiple zones compete for the same units.

resource_agent = Agent(
    role="ResourceCoordinationAgent",
    goal=(
        "Allocate available firefighting resources — helicopters, ground crews, "
        "water tankers, and retardant aircraft — across active fire zones. "
        "When resources are insufficient for all zones, prioritise by severity "
        "and life-risk, explain the trade-off explicitly, and flag any zone "
        "that must be left unattended due to resource exhaustion."
    ),
    backstory=(
        "You are the logistics brain of ForestFireMAS. "
        "You maintain a live inventory of all firefighting assets and their "
        "current deployment status. You must balance competing demands: a CRITICAL "
        "zone near a town versus a HIGH zone deeper in the forest when you only have "
        "resources for one. You reason transparently about every allocation decision "
        "so the ResponseAgent can include the rationale in dispatch orders."
    ),
    llm=LLM_RESOURCE,
    verbose=True,
)

# Seed initial beliefs for ResourceCoordinationAgent
resource_beliefs.update("helicopters_available",   3)
resource_beliefs.update("ground_crews_available",  5)
resource_beliefs.update("water_tankers_available", 4)
resource_beliefs.update("resource_conflict",       False)


# ── 4. ResponseAgent ──────────────────────────────────────────────────────────
# Desire: translate resource allocation decisions into clear, unambiguous
# field dispatch orders and coordinate evacuation notices.

response_agent = Agent(
    role="ResponseAgent",
    goal=(
        "Convert resource allocation plans into structured field dispatch orders. "
        "Each order must include: unit ID, assigned zone, GPS waypoint, "
        "primary task, and estimated arrival time. "
        "Also issue evacuation notices for any HIGH or CRITICAL zones "
        "near populated areas."
    ),
    backstory=(
        "You are the command-and-control output agent in ForestFireMAS. "
        "Field commanders and evacuation coordinators read your output directly — "
        "it must be precise, unambiguous, and formatted consistently. "
        "You do not make resource decisions yourself; you translate the "
        "ResourceCoordinationAgent's plan into actionable orders and ensure "
        "nothing is lost in translation."
    ),
    llm=LLM_RESPONSE,
    verbose=True,
)

# Seed initial beliefs for ResponseAgent
response_beliefs.update("dispatch_orders_issued", 0)
response_beliefs.update("evacuations_ordered",    0)
response_beliefs.update("last_dispatch_zone",     "NONE")


# ── Export list for scenario files ────────────────────────────────────────────
ALL_AGENTS = [detection_agent, assessment_agent, resource_agent, response_agent]
