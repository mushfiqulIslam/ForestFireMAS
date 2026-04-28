import jade.core.Agent;
import jade.core.behaviours.CyclicBehaviour;
import jade.lang.acl.ACLMessage;
import jade.lang.acl.MessageTemplate;

public class ResponseAgent extends Agent {

    @Override
    protected void setup() {
        System.out.println("[ResponseAgent] Started. Waiting for response plans...");
        addBehaviour(new ExecuteResponseBehaviour());
    }

    private class ExecuteResponseBehaviour extends CyclicBehaviour {

        @Override
        public void action() {
            MessageTemplate mt = MessageTemplate.and(
                MessageTemplate.MatchPerformative(ACLMessage.PROPOSE),
                MessageTemplate.MatchConversationId(Protocol.CID_SEND_RESPONSE_PLAN)
            );

            ACLMessage msg = receive(mt);

            if (msg != null) {
                String plan = msg.getContent();
                System.out.println("[ResponseAgent] Received response plan: " + plan);

                String action = decideAction(plan);
                System.out.println("[ResponseAgent][AUTONOMOUS_DECISION] " + action);

                System.out.println("================================================");
                System.out.println("  FOREST FIRE ALERT - DISPATCH CENTRE NOTIFIED");
                System.out.println("  Action : " + action);
                System.out.println("  Plan   : " + plan);
                System.out.println("================================================");
            } else {
                block();
            }
        }

        private String decideAction(String plan) {
            if (plan.contains(Protocol.K_PLAN + ":EMERGENCY") && plan.contains("EVACUATE:YES")) {
                return "IMMEDIATE EVACUATION ORDERED + FULL EMERGENCY DISPATCH ACTIVATED";
            } else if (plan.contains(Protocol.K_PLAN + ":STANDARD")) {
                return "STANDARD FIREFIGHTING DISPATCH ACTIVATED - MONITOR EVACUATION ROUTES";
            } else {
                return "MONITORING MODE ACTIVATED - PATROL TEAMS DEPLOYED";
            }
        }
    }

    @Override
    protected void takeDown() {
        System.out.println("[ResponseAgent] Shutting down.");
    }
}
