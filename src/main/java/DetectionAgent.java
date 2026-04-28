import jade.core.AID;
import jade.core.Agent;
import jade.core.behaviours.CyclicBehaviour;
import jade.core.behaviours.OneShotBehaviour;
import jade.lang.acl.ACLMessage;
import jade.lang.acl.MessageTemplate;

public class DetectionAgent extends Agent {

    private static final String CID_TRIGGER_RUN = "TriggerRun";

    @Override
    protected void setup() {
        String scenario = (getArguments() != null && getArguments().length > 0)
            ? String.valueOf(getArguments()[0])
            : "critical";

        System.out.println("[DetectionAgent] Started. Scenario=" + scenario + ". Scanning for fire zones...");

        addBehaviour(new DetectFireBehaviour(scenario));
        addBehaviour(new TriggerRunBehaviour());
    }

    private class DetectFireBehaviour extends OneShotBehaviour {
        private final String scenario;

        DetectFireBehaviour(String scenario) {
            this.scenario = normalizeScenario(scenario);
        }

        @Override
        public void action() {
            sendFireReportForScenario(scenario);
        }
    }

    private class TriggerRunBehaviour extends CyclicBehaviour {
        @Override
        public void action() {
            MessageTemplate mt = MessageTemplate.MatchPerformative(ACLMessage.REQUEST);
            ACLMessage req = receive(mt);

            if (req == null) {
                block();
                return;
            }

            String convId = req.getConversationId();
            String sender = req.getSender() == null ? "unknown" : req.getSender().getLocalName();
            String content = req.getContent() == null ? "" : req.getContent().trim();

            // Preferred trigger protocol is REQUEST + conversationId=TriggerRun.
            // Fallback: allow missing conversationId if content starts with RUN:.
            boolean convMatch = CID_TRIGGER_RUN.equals(convId);
            boolean contentLooksRunnable = content.toUpperCase().startsWith("RUN:");
            if (!convMatch && !(convId == null && contentLooksRunnable)) {
                ACLMessage fail = req.createReply();
                fail.setPerformative(ACLMessage.FAILURE);
                fail.setConversationId(CID_TRIGGER_RUN);
                fail.setContent("Trigger rejected: use REQUEST + conversationId=TriggerRun + content RUN:<critical|moderate|low>");
                send(fail);
                System.out.println("[DetectionAgent][TRIGGER_REJECTED] sender=" + sender + " convId=" + convId + " content=" + content);
                return;
            }

            if (!contentLooksRunnable) {
                ACLMessage fail = req.createReply();
                fail.setPerformative(ACLMessage.FAILURE);
                fail.setConversationId(CID_TRIGGER_RUN);
                fail.setContent("Unsupported trigger content. Use RUN:<critical|moderate|low>");
                send(fail);
                System.out.println("[DetectionAgent][TRIGGER_REJECTED] sender=" + sender + " convId=" + convId + " content=" + content);
                return;
            }

            String requestedScenario = normalizeScenario(content.substring(4));
            System.out.println("[DetectionAgent][TRIGGER_RECEIVED] sender=" + sender + " convId=" + convId + " content=" + content);
            sendFireReportForScenario(requestedScenario);

            ACLMessage ok = req.createReply();
            ok.setPerformative(ACLMessage.INFORM);
            ok.setConversationId(CID_TRIGGER_RUN);
            ok.setContent("RUN executed|scenario=" + requestedScenario + "|timestamp=" + System.currentTimeMillis());
            send(ok);
            System.out.println("[DetectionAgent][TRIGGER_ACK] scenario=" + requestedScenario + " sentTo=" + sender);
        }
    }

    private void sendFireReportForScenario(String scenario) {
        String fireZoneData = buildFireZoneData(scenario);
        System.out.println("[DetectionAgent][AUTONOMOUS_DECISION] Trigger fire report for scenario=" + scenario);
        System.out.println("[DetectionAgent] Fire detected! Data: " + fireZoneData);

        ACLMessage msg = new ACLMessage(ACLMessage.INFORM);
        msg.addReceiver(new AID("AssessmentAgent", AID.ISLOCALNAME));
        msg.setOntology(Protocol.ONTOLOGY);
        msg.setConversationId(Protocol.CID_REPORT_FIRE_ZONE);
        String traceId = "trace-detect-" + System.currentTimeMillis();
        msg.setReplyWith(traceId);
        msg.setContent(fireZoneData);
        send(msg);

        System.out.println("[DetectionAgent] ReportFireZone sent to AssessmentAgent. replyWith=" + traceId);
    }

    private String normalizeScenario(String scenario) {
        if (scenario == null) {
            return "critical";
        }
        String s = scenario.trim().toLowerCase();
        return switch (s) {
            case "moderate", "low", "critical" -> s;
            default -> "critical";
        };
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

    @Override
    protected void takeDown() {
        System.out.println("[DetectionAgent] Shutting down.");
    }
}
