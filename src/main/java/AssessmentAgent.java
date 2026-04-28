import jade.core.Agent;
import jade.core.AID;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;
import jade.lang.acl.MessageTemplate;

public class AssessmentAgent extends Agent {

    @Override
    protected void setup() {
        System.out.println("[AssessmentAgent] Started. Waiting for fire zone reports...");
        addBehaviour(new AssessFireBehaviour());
    }

    private class AssessFireBehaviour extends CyclicBehaviour {
        @Override
        public void action() {
            MessageTemplate mt = MessageTemplate.and(
                MessageTemplate.MatchPerformative(ACLMessage.INFORM),
                MessageTemplate.MatchConversationId(Protocol.CID_REPORT_FIRE_ZONE)
            );

            ACLMessage msg = receive(mt);

            if (msg != null) {
                String fireZoneData = msg.getContent();
                System.out.println("[AssessmentAgent] Received fire zone report: " + fireZoneData);

                String severityScore = assessSeverity(fireZoneData);
                System.out.println("[AssessmentAgent][AUTONOMOUS_DECISION] Severity assessed: " + severityScore);

                ACLMessage reply = new ACLMessage(ACLMessage.INFORM);
                reply.addReceiver(new AID("ResourceCoordinationAgent", AID.ISLOCALNAME));
                reply.setOntology(Protocol.ONTOLOGY);
                reply.setConversationId(Protocol.CID_INFORM_SEVERITY);
                String traceId = "trace-assess-" + System.currentTimeMillis();
                reply.setReplyWith(traceId);
                reply.setInReplyTo(msg.getReplyWith());
                reply.setContent(severityScore);
                send(reply);

                System.out.println("[AssessmentAgent] InformSeverity sent. inReplyTo=" + msg.getReplyWith() + ", replyWith=" + traceId);
            } else {
                block();
            }
        }

        private String assessSeverity(String zoneData) {
            if (zoneData.contains(Protocol.K_INTENSITY + ":HIGH")
                    && zoneData.contains(Protocol.K_SPREAD_RISK + ":EXTREME")) {
                return Protocol.K_SEVERITY + ":CRITICAL|SCORE:9|AFFECTED_AREA:500ha|SPREAD_RATE:FAST|ZONES:SectorA,SectorB";
            } else if (zoneData.contains(Protocol.K_INTENSITY + ":MEDIUM")) {
                return Protocol.K_SEVERITY + ":MODERATE|SCORE:5|AFFECTED_AREA:200ha|SPREAD_RATE:SLOW|ZONES:SectorC";
            } else {
                return Protocol.K_SEVERITY + ":LOW|SCORE:2|AFFECTED_AREA:50ha|SPREAD_RATE:CONTAINED|ZONES:SectorD";
            }
        }
    }

    @Override
    protected void takeDown() {
        System.out.println("[AssessmentAgent] Shutting down.");
    }
}
