"""
CrewAI Orchestrator setup for multi-agent coordination.
"""

from typing import List, Dict, Any, Optional
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MockAgent:
    """Mock agent for local development when CrewAI is not available."""
    
    def __init__(self, name: str, role: str, goal: str):
        self.name = name
        self.role = role
        self.goal = goal
    
    def run_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simulate agent task execution."""
        logger.info(f"[{self.name}] Executing task: {task}")
        logger.info(f"[{self.name}] Context: {context}")
        
        return {
            "status": "success",
            "agent": self.name,
            "task": task,
            "result": f"Mock execution of {task} by {self.name}",
            "context": context or {}
        }


class MedicalSchedulerOrchestrator:
    """
    Orchestrator for managing CrewAI agents.
    Uses mock agents when USE_MOCK_AI is True, otherwise uses real CrewAI.
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.use_mock = settings.USE_MOCK_AI
        
        if self.use_mock:
            self._setup_mock_agents()
        else:
            self._setup_crewai_agents()
    
    def _setup_mock_agents(self):
        """Set up mock agents for local development."""
        logger.info("Setting up mock CrewAI agents (USE_MOCK_AI=True)")
        
        self.agents = {
            "booking": MockAgent(
                name="BookingAgent",
                role="Appointment Manager",
                goal="Book, reschedule, and cancel appointments."
            ),
            "reminder": MockAgent(
                name="ReminderAgent",
                role="Notification Handler",
                goal="Send and manage appointment reminders."
            ),
            "previsit": MockAgent(
                name="PreVisitAgent",
                role="Questionnaire Coordinator",
                goal="Collect and summarize pre-consultation patient data."
            )
        }
    
    def _setup_crewai_agents(self):
        """Set up real CrewAI agents."""
        try:
            from crewai import Agent, Task, Crew
            logger.info("Setting up real CrewAI agents")
            
            # Create agents
            booking_agent = Agent(
                name="BookingAgent",
                role="Appointment Manager",
                goal="Book, reschedule, and cancel appointments efficiently.",
                backstory="You are an expert appointment scheduler with years of experience managing medical appointments.",
                verbose=True,
                allow_delegation=False
            )
            
            reminder_agent = Agent(
                name="ReminderAgent",
                role="Notification Handler",
                goal="Send timely and appropriate appointment reminders.",
                backstory="You specialize in patient communication and ensure patients never miss their appointments.",
                verbose=True,
                allow_delegation=False
            )
            
            previsit_agent = Agent(
                name="PreVisitAgent",
                role="Questionnaire Coordinator",
                goal="Collect and summarize pre-consultation patient data effectively.",
                backstory="You help prepare patients for their visits by collecting and organizing their pre-visit information.",
                verbose=True,
                allow_delegation=False
            )
            
            self.agents = {
                "booking": booking_agent,
                "reminder": reminder_agent,
                "previsit": previsit_agent
            }
            
        except ImportError:
            logger.warning("CrewAI not installed, falling back to mock agents")
            self._setup_mock_agents()
            self.use_mock = True
    
    def get_agent(self, agent_type: str):
        """Get an agent by type."""
        return self.agents.get(agent_type)
    
    def execute_booking_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a booking-related task."""
        agent = self.get_agent("booking")
        if self.use_mock:
            return agent.run_task(task, context)
        else:
            # For real CrewAI, create a task and execute it
            from crewai import Task
            crew_task = Task(
                description=task,
                agent=agent,
                expected_output="Appointment booking operation result"
            )
            crew = Crew(agents=[agent], tasks=[crew_task])
            result = crew.kickoff()
            return {
                "status": "success",
                "agent": "BookingAgent",
                "task": task,
                "result": str(result),
                "context": context
            }
    
    def execute_reminder_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a reminder-related task."""
        agent = self.get_agent("reminder")
        if self.use_mock:
            return agent.run_task(task, context)
        else:
            from crewai import Task
            crew_task = Task(
                description=task,
                agent=agent,
                expected_output="Reminder scheduling operation result"
            )
            crew = Crew(agents=[agent], tasks=[crew_task])
            result = crew.kickoff()
            return {
                "status": "success",
                "agent": "ReminderAgent",
                "task": task,
                "result": str(result),
                "context": context
            }
    
    def execute_previsit_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a pre-visit questionnaire task."""
        agent = self.get_agent("previsit")
        if self.use_mock:
            return agent.run_task(task, context)
        else:
            from crewai import Task
            crew_task = Task(
                description=task,
                agent=agent,
                expected_output="Questionnaire processing result"
            )
            crew = Crew(agents=[agent], tasks=[crew_task])
            result = crew.kickoff()
            return {
                "status": "success",
                "agent": "PreVisitAgent",
                "task": task,
                "result": str(result),
                "context": context
            }


# Global orchestrator instance
orchestrator = MedicalSchedulerOrchestrator()

