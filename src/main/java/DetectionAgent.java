import jade.core.Agent;
import jade.core.behaviours.OneShotBehaviour;

public class DetectionAgent extends Agent {

    @Override
    protected void setup() {
        String scenario = (getArguments() != null && getArguments().length > 0)
            ? String.valueOf(getArguments()[0])
            : "critical";

        System.out.println("[DetectionAgent] Started. Scenario=" + scenario + ". Scanning for fire zones...");
        addBehaviour(new DetectFireBehaviour(scenario));
    }

    private class DetectFireBehaviour extends OneShotBehaviour {
        private final String scenario;

        DetectFireBehaviour(String scenario) {
            this.scenario = scenario == null ? "critical" : scenario.toLowerCase();
        }

        @Override
        public void action() {
            String fireZoneData = buildFireZoneData(scenario);
            System.out.println("[DetectionAgent][AUTONOMOUS_DECISION] Trigger fire report for scenario=" + scenario);
            System.out.println("[DetectionAgent] Fire detected! Data: " + fireZoneData);
            System.out.println("[DetectionAgent] Local simulation complete (single-agent mode).");
        }

        private String buildFireZoneData(String scenario) {
            switch (scenario) {
                case "moderate":
                    return Protocol.K_ZONE + ":SectorC|" +
                           Protocol.K_LOCATION + ":43.0N,110.1W|" +
                           Protocol.K_INTENSITY + ":MEDIUM|" +
                           Protocol.K_SPREAD_RISK + ":MEDIUM";
                case "low":
                    return Protocol.K_ZONE + ":SectorD|" +
                           Protocol.K_LOCATION + ":42.7N,109.9W|" +
                           Protocol.K_INTENSITY + ":LOW|" +
                           Protocol.K_SPREAD_RISK + ":LOW";
                default:
                    return Protocol.K_ZONE + ":SectorA|" +
                           Protocol.K_LOCATION + ":43.2N,110.5W|" +
                           Protocol.K_INTENSITY + ":HIGH|" +
                           Protocol.K_SPREAD_RISK + ":EXTREME";
            }
        }
    }

    @Override
    protected void takeDown() {
        System.out.println("[DetectionAgent] Shutting down.");
    }
}
