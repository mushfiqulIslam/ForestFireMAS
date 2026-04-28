import jade.core.Profile;
import jade.core.ProfileImpl;
import jade.core.Runtime;
import jade.wrapper.AgentContainer;
import jade.wrapper.AgentController;

public class ForestFireLauncher {

    public static void main(String[] args) throws Exception {
        String scenario = (args != null && args.length > 0) ? args[0].toLowerCase() : "critical";

        System.out.println("=== Forest Fire Multi-Agent System Starting ===");
        System.out.println("=== Scenario: " + scenario + " ===");

        Runtime rt = Runtime.instance();

        Profile profile = new ProfileImpl();
        profile.setParameter(Profile.MAIN_HOST, "localhost");
        profile.setParameter(Profile.GUI, "true");

        AgentContainer mainContainer = rt.createMainContainer(profile);

        AgentController responseAgent = mainContainer.createNewAgent(
            "ResponseAgent",
            "ResponseAgent",
            new Object[]{}
        );
        responseAgent.start();
        System.out.println("ResponseAgent started.");

        Thread.sleep(500);

        AgentController resourceAgent = mainContainer.createNewAgent(
            "ResourceCoordinationAgent",
            "ResourceCoordinationAgent",
            new Object[]{}
        );
        resourceAgent.start();
        System.out.println("ResourceCoordinationAgent started.");

        Thread.sleep(500);

        AgentController assessmentAgent = mainContainer.createNewAgent(
            "AssessmentAgent",
            "AssessmentAgent",
            new Object[]{}
        );
        assessmentAgent.start();
        System.out.println("AssessmentAgent started.");

        Thread.sleep(500);

        AgentController detectionAgent = mainContainer.createNewAgent(
            "DetectionAgent",
            "DetectionAgent",
            new Object[]{ scenario }
        );
        detectionAgent.start();
        System.out.println("DetectionAgent started.");

        System.out.println("=== All agents launched. System running. ===");
    }
}
