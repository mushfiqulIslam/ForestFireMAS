import jade.core.Agent;
import jade.core.AID;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;
import jade.lang.acl.MessageTemplate;

public class ResourceCoordinationAgent extends Agent {

    @Override
    protected void setup() {
        System.out.println("[ResourceCoordinationAgent] Started. Waiting for severity reports...");
        addBehaviour(new CoordinateResourcesBehaviour());
    }

    private class CoordinateResourcesBehaviour extends CyclicBehaviour {

        @Override
        public void action() {
            MessageTemplate mt = MessageTemplate.and(
                MessageTemplate.MatchPerformative(ACLMessage.INFORM),
                MessageTemplate.MatchConversationId(Protocol.CID_INFORM_SEVERITY)
            );

            ACLMessage msg = receive(mt);

            if (msg != null) {
                String severityData = msg.getContent();
                System.out.println("[ResourceCoordinationAgent] Received severity report: " + severityData);

                String plan = buildResponsePlan(severityData);
                System.out.println("[ResourceCoordinationAgent][AUTONOMOUS_DECISION] Plan selected: " + plan);

                ACLMessage reply = new ACLMessage(ACLMessage.PROPOSE);
                reply.addReceiver(new AID("ResponseAgent", AID.ISLOCALNAME));
                reply.setOntology(Protocol.ONTOLOGY);
                reply.setConversationId(Protocol.CID_SEND_RESPONSE_PLAN);
                reply.setContent(plan);
                send(reply);

                System.out.println("[ResourceCoordinationAgent] SendResponsePlan sent to ResponseAgent.");
            } else {
                block();
            }
        }

        private String buildResponsePlan(String severityData) {
            if (severityData.contains(Protocol.K_SEVERITY + ":CRITICAL")) {
                return Protocol.K_PLAN + ":EMERGENCY" +
                       "|HELICOPTERS:4|GROUND_TEAMS:8|WATER_TANKERS:6" +
                       "|PRIORITY_ZONES:SectorA,SectorB|EVACUATE:YES";
            } else if (severityData.contains(Protocol.K_SEVERITY + ":MODERATE")) {
                return Protocol.K_PLAN + ":STANDARD" +
                       "|HELICOPTERS:2|GROUND_TEAMS:4|WATER_TANKERS:3" +
                       "|PRIORITY_ZONES:SectorC|EVACUATE:NO";
            } else {
                return Protocol.K_PLAN + ":MONITOR" +
                       "|HELICOPTERS:1|GROUND_TEAMS:2|WATER_TANKERS:1" +
                       "|PRIORITY_ZONES:SectorD|EVACUATE:NO";
            }
        }
    }

    @Override
    protected void takeDown() {
        System.out.println("[ResourceCoordinationAgent] Shutting down.");
    }
}
