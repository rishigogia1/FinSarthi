"""
services/workflows/workflow_registry.py — Configuration-driven Workflow Registry.

Defines pure data workflow configurations for FinSarthi V2 Guided AI Workflows.
Adding new workflows is 100% data configuration — no core code changes needed.
"""
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class WorkflowConfig:
    id: str
    title: str
    icon: str
    primary_agent: str  # "coach", "planner", "guardian", "navigator", "learn"
    supporting_agents: list[str] = field(default_factory=list)
    starter_prompt: str = ""
    default_chips: list[str] = field(default_factory=list)


class WorkflowRegistry:
    _WORKFLOWS: dict[str, WorkflowConfig] = {
        "save_money": WorkflowConfig(
            id="save_money",
            title="Saving More Every Month",
            icon="💰",
            primary_agent="coach",
            supporting_agents=["planner"],
            starter_prompt="Analyse my spending and identify where I can realistically save money this month.",
            default_chips=["Reduce shopping", "Reduce food expenses", "Set a savings goal", "Create a monthly budget"]
        ),
        "government_schemes": WorkflowConfig(
            id="government_schemes",
            title="Government Schemes & Benefits",
            icon="🏛️",
            primary_agent="navigator",
            supporting_agents=["learn"],
            starter_prompt="Recommend relevant government financial schemes and benefits based on my profile.",
            default_chips=["Tax saving schemes", "Student / Youth schemes", "Senior Citizen benefits", "Update profile details"]
        ),
        "fraud_protection": WorkflowConfig(
            id="fraud_protection",
            title="Fraud & Security Check",
            icon="🛡️",
            primary_agent="guardian",
            supporting_agents=[],
            starter_prompt="Help protect me from financial scams, phishing links, suspicious QR codes, or fake UPI requests.",
            default_chips=["Verify QR Code", "Check UPI Request", "Verify Payment Link", "Check SMS Scam"]
        ),
        "financial_goals": WorkflowConfig(
            id="financial_goals",
            title="Financial Goal Planning",
            icon="🎯",
            primary_agent="planner",
            supporting_agents=["navigator"],
            starter_prompt="Let's plan a financial goal. What step-by-step roadmap should I follow?",
            default_chips=["Emergency Fund", "Buy a Bike", "Buy a Car", "Home Purchase", "Retirement Planning"]
        ),
        "investment_advice": WorkflowConfig(
            id="investment_advice",
            title="Investment Planning",
            icon="📈",
            primary_agent="navigator",
            supporting_agents=["planner", "coach", "learn"],
            starter_prompt="Guide me on building a personalized investment strategy suited to my income and risk profile.",
            default_chips=["Low Risk Options", "Moderate SIP Strategy", "High Growth Portfolio", "Explain Mutual Funds"]
        ),
        "learn_finance": WorkflowConfig(
            id="learn_finance",
            title="Financial Learning",
            icon="💡",
            primary_agent="learn",
            supporting_agents=[],
            starter_prompt="Teach me essential personal finance concepts, smart money habits, and investment basics.",
            default_chips=["Explain SIP", "Mutual Funds 101", "Emergency Fund Rule", "Tax Regimes Explained", "Credit Score Tips"]
        ),
    }

    @classmethod
    def get(cls, workflow_id: str) -> WorkflowConfig | None:
        """Retrieve workflow configuration by ID."""
        return cls._WORKFLOWS.get(workflow_id)

    @classmethod
    def list_all(cls) -> list[WorkflowConfig]:
        """List all available workflow configurations."""
        return list(cls._WORKFLOWS.values())
