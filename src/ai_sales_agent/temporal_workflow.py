"""Temporal workflow module for orchestrating sales agent tasks."""

from datetime import timedelta
from typing import Dict, List
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.common import RetryPolicy
from temporalio.exceptions import TemporalError
from .config import get_config
from .agency_agents import SalesAgency
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@activity.defn
async def execute_sales_workflow_activity(industry: str, company_size: str, job_titles: List[str]) -> Dict:
    """Activity to execute the sales workflow using CrewAI agents.

    Args:
        industry (str): Target industry
        company_size (str): Company size range
        job_titles (List[str]): Target job titles

    Returns:
        Dict: Workflow execution results
    """
    logger.info(f"Starting sales workflow for {industry} industry")
    try:
        agency = SalesAgency()
        result = agency.execute_sales_workflow(industry, company_size, job_titles)
        logger.info(f"Completed sales workflow for {industry} industry")
        return result
    except Exception as e:
        logger.error(f"Error in sales workflow: {str(e)}")
        raise

@workflow.defn
class SalesAgentWorkflow:
    """Temporal workflow for managing sales agent tasks."""

    @workflow.run
    async def run(self, industry: str, company_size: str, job_titles: List[str]) -> Dict:
        """Run the sales agent workflow.

        Args:
            industry (str): Target industry
            company_size (str): Company size range
            job_titles (List[str]): Target job titles

        Returns:
            Dict: Workflow execution results
        """
        logger.info(f"Initializing workflow for {industry} industry")
        
        # Execute the sales workflow with retry policy and monitoring
        try:
            result = await workflow.execute_activity(
                execute_sales_workflow_activity,
                industry,
                company_size,
                job_titles,
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(minutes=5),
                    maximum_attempts=3
                )
            )
            logger.info(f"Workflow completed successfully for {industry}")
            return result
        except TemporalError as e:
            logger.error(f"Temporal workflow error: {str(e)}")
            raise

async def run_worker():
    """Start the Temporal worker to process sales agent workflows."""
    config = get_config()
    logger.info("Initializing Temporal worker")
    
    try:
        client = await Client.connect(config['temporal']['server_url'])
        logger.info("Connected to Temporal server")
        
        worker = Worker(
            client,
            task_queue=config['temporal']['task_queue'],
            workflows=[SalesAgentWorkflow],
            activities=[execute_sales_workflow_activity]
        )
        
        logger.info(f"Starting worker on task queue: {config['temporal']['task_queue']}")
        await worker.run()
    except Exception as e:
        logger.error(f"Error starting Temporal worker: {str(e)}")
        raise