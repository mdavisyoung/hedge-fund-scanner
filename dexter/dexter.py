"""
Dexter Multi-Agent Financial Research System
Python implementation using xAI Grok, Polygon.io, and Tavily
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, field, asdict
from openai import OpenAI
from datetime import datetime, timedelta


# Data Models
@dataclass
class ResearchTask:
    """Individual research task in the plan"""
    id: str
    description: str
    tool: str
    parameters: Dict[str, Any]
    status: Literal['pending', 'in_progress', 'completed', 'failed'] = 'pending'
    result: Optional[Any] = None


@dataclass
class ResearchPlan:
    """Complete research plan with tasks"""
    query: str
    tasks: List[ResearchTask]
    status: Literal['planning', 'executing', 'validating', 'completed', 'failed'] = 'planning'


# API Clients
class PolygonClient:
    """Polygon.io API client for financial data"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
    
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """Make API request with error handling"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Polygon API error: {e}")
            return None
    
    def get_stock_aggregates(self, symbol: str, from_date: str, to_date: str, 
                            timespan: str = 'day') -> Optional[Dict]:
        """Get stock price aggregates over time"""
        endpoint = f"/v2/aggs/ticker/{symbol}/range/1/{timespan}/{from_date}/{to_date}"
        endpoint += f"?adjusted=true&sort=asc&apiKey={self.api_key}"
        return self._make_request(endpoint)
    
    def get_ticker_details(self, symbol: str) -> Optional[Dict]:
        """Get company information and details"""
        endpoint = f"/v3/reference/tickers/{symbol}?apiKey={self.api_key}"
        return self._make_request(endpoint)
    
    def get_ticker_financials(self, symbol: str, period: str = 'annual') -> Optional[Dict]:
        """Get financial statements and data"""
        endpoint = f"/vX/reference/financials?ticker={symbol}&period={period}&apiKey={self.api_key}"
        return self._make_request(endpoint)
    
    def get_market_data(self, symbol: str, date: Optional[str] = None) -> Optional[Dict]:
        """Get current or historical market data"""
        if date:
            endpoint = f"/v1/open-close/{symbol}/{date}?adjusted=true&apiKey={self.api_key}"
        else:
            endpoint = f"/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={self.api_key}"
        return self._make_request(endpoint)


class TavilyClient:
    """Tavily API client for web search"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com"
    
    def search(self, query: str, max_results: int = 5) -> Optional[Dict]:
        """Search the web for financial news/context"""
        if not self.api_key:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Tavily search error: {e}")
            return None


# Agent Classes
class PlanningAgent:
    """Breaks down queries into structured research tasks"""
    
    def __init__(self, grok_api_key: str):
        self.grok = OpenAI(
            api_key=grok_api_key,
            base_url="https://api.x.ai/v1"
        )
    
    def create_plan(self, query: str) -> ResearchPlan:
        """Create a research plan from a query"""
        planning_prompt = f"""You are a financial research planning agent. Analyze the following query and break it down into specific, actionable research tasks.

Available tools:
- getStockAggregates: Get stock price data over time (parameters: symbol, from, to, timespan)
- getTickerDetails: Get company information and details (parameters: symbol)
- getTickerFinancials: Get financial statements and data (parameters: symbol, period)
- getMarketData: Get current or historical market data (parameters: symbol, date)
- webSearch: Search the web for financial news/context (parameters: query)

Query: "{query}"

Return a JSON object with a "tasks" array. Each task should have:
- id: unique identifier (e.g., "task-1")
- description: what this task accomplishes
- tool: which tool to use
- parameters: object with tool-specific parameters

Example:
{{
  "tasks": [
    {{
      "id": "task-1",
      "description": "Get Apple's stock price data for the last year",
      "tool": "getStockAggregates",
      "parameters": {{ "symbol": "AAPL", "from": "2023-12-01", "to": "2024-12-01", "timespan": "day" }}
    }}
  ]
}}"""

        try:
            completion = self.grok.chat.completions.create(
                model="grok-3",
                messages=[{"role": "user", "content": planning_prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            content = completion.choices[0].message.content
            parsed = json.loads(content)
            
            # Extract tasks array
            tasks_data = parsed.get('tasks', [])
            if not tasks_data:
                raise ValueError("No tasks found in planning response")
            
            # Convert to ResearchTask objects
            tasks = []
            for i, task_data in enumerate(tasks_data):
                task = ResearchTask(
                    id=task_data.get('id', f"task-{i+1}"),
                    description=task_data.get('description', f"Task {i+1}"),
                    tool=task_data['tool'],
                    parameters=task_data.get('parameters', {}),
                    status='pending'
                )
                tasks.append(task)
            
            return ResearchPlan(query=query, tasks=tasks, status='executing')
            
        except Exception as e:
            print(f"Planning agent error: {e}")
            raise ValueError(f"Failed to create research plan: {e}")


class ActionAgent:
    """Executes tasks using appropriate tools"""
    
    def __init__(self, polygon_api_key: str, tavily_api_key: Optional[str] = None):
        self.polygon = PolygonClient(polygon_api_key)
        self.tavily = TavilyClient(tavily_api_key)
    
    def execute_task(self, task: ResearchTask) -> ResearchTask:
        """Execute a single research task"""
        task.status = 'in_progress'
        
        try:
            result = None
            
            if task.tool == 'getStockAggregates':
                result = self.polygon.get_stock_aggregates(
                    symbol=task.parameters['symbol'],
                    from_date=task.parameters['from'],
                    to_date=task.parameters['to'],
                    timespan=task.parameters.get('timespan', 'day')
                )
            
            elif task.tool == 'getTickerDetails':
                result = self.polygon.get_ticker_details(task.parameters['symbol'])
            
            elif task.tool == 'getTickerFinancials':
                result = self.polygon.get_ticker_financials(
                    symbol=task.parameters['symbol'],
                    period=task.parameters.get('period', 'annual')
                )
            
            elif task.tool == 'getMarketData':
                result = self.polygon.get_market_data(
                    symbol=task.parameters['symbol'],
                    date=task.parameters.get('date')
                )
            
            elif task.tool == 'webSearch':
                result = self.tavily.search(task.parameters['query'])
            
            else:
                raise ValueError(f"Unknown tool: {task.tool}")
            
            task.result = result
            task.status = 'completed' if result else 'failed'
            
        except Exception as e:
            print(f"Task {task.id} failed: {e}")
            task.status = 'failed'
            task.result = {"error": str(e)}
        
        return task


class ValidationAgent:
    """Checks if tasks are complete and sufficient"""
    
    def __init__(self, grok_api_key: str):
        self.grok = OpenAI(
            api_key=grok_api_key,
            base_url="https://api.x.ai/v1"
        )
    
    def validate_plan(self, plan: ResearchPlan) -> bool:
        """Validate if research plan has sufficient data"""
        completed_tasks = [t for t in plan.tasks if t.status == 'completed']
        failed_tasks = [t for t in plan.tasks if t.status == 'failed']
        
        # If all tasks failed, plan is invalid
        if failed_tasks and not completed_tasks:
            return False
        
        # If we have at least one completed task, consider it sufficient
        # (Could add more sophisticated validation via Grok here)
        return len(completed_tasks) > 0


class AnswerAgent:
    """Synthesizes findings into comprehensive response"""
    
    def __init__(self, grok_api_key: str):
        self.grok = OpenAI(
            api_key=grok_api_key,
            base_url="https://api.x.ai/v1"
        )
    
    def synthesize_answer(self, plan: ResearchPlan) -> str:
        """Generate final answer from research data"""
        completed_tasks = [t for t in plan.tasks if t.status == 'completed']
        
        # Prepare research data summary
        research_summary = []
        for task in completed_tasks:
            research_summary.append(f"""
Task: {task.description}
Tool: {task.tool}
Result: {json.dumps(task.result, indent=2)[:1000]}  # Limit size
""")
        
        answer_prompt = f"""You are a financial research analyst. Based on the following research data, provide a comprehensive, data-backed answer to the query.

Query: "{plan.query}"

Research Data:
{''.join(research_summary)}

Provide a clear, well-structured answer that:
1. Directly addresses the query
2. Cites specific data points from the research
3. Includes relevant calculations or comparisons
4. Highlights key insights
5. Notes any limitations or missing data

Format your response as clear, professional prose suitable for a financial research platform."""

        try:
            completion = self.grok.chat.completions.create(
                model="grok-3",
                messages=[{"role": "user", "content": answer_prompt}],
                temperature=0.7
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Answer synthesis error: {e}")
            return "Unable to generate answer due to an error."


# Main Dexter Class
class Dexter:
    """Main orchestrator for multi-agent financial research"""
    
    def __init__(self, grok_api_key: str, polygon_api_key: str, tavily_api_key: Optional[str] = None):
        self.planning_agent = PlanningAgent(grok_api_key)
        self.action_agent = ActionAgent(polygon_api_key, tavily_api_key)
        self.validation_agent = ValidationAgent(grok_api_key)
        self.answer_agent = AnswerAgent(grok_api_key)
        self.max_iterations = 10
    
    def research(self, query: str) -> Dict[str, Any]:
        """
        Execute complete research workflow
        
        Args:
            query: Research question to answer
            
        Returns:
            Dict with 'answer', 'plan', and 'iterations'
        """
        # Step 1: Create research plan
        plan = self.planning_agent.create_plan(query)
        iterations = 0
        
        # Step 2: Execute tasks iteratively
        while plan.status == 'executing' and iterations < self.max_iterations:
            iterations += 1
            
            # Execute all pending tasks
            pending_tasks = [t for t in plan.tasks if t.status == 'pending']
            for task in pending_tasks:
                updated_task = self.action_agent.execute_task(task)
                # Update task in plan
                for i, t in enumerate(plan.tasks):
                    if t.id == task.id:
                        plan.tasks[i] = updated_task
                        break
            
            # Validate if we have sufficient data
            is_valid = self.validation_agent.validate_plan(plan)
            
            if is_valid:
                plan.status = 'validating'
                break
            
            # Check if we should continue
            failed_tasks = [t for t in plan.tasks if t.status == 'failed']
            if failed_tasks and iterations >= self.max_iterations:
                plan.status = 'validating'  # Proceed with what we have
                break
        
        # Step 3: Synthesize answer
        if plan.status == 'validating':
            answer = self.answer_agent.synthesize_answer(plan)
            plan.status = 'completed'
            
            return {
                'answer': answer,
                'plan': {
                    'query': plan.query,
                    'tasks': [asdict(t) for t in plan.tasks],
                    'status': plan.status
                },
                'iterations': iterations
            }
        else:
            plan.status = 'failed'
            raise Exception('Research failed to complete')


# Convenience function for easy use
def create_dexter(grok_api_key: Optional[str] = None,
                  polygon_api_key: Optional[str] = None,
                  tavily_api_key: Optional[str] = None) -> Dexter:
    """
    Create Dexter instance with API keys from environment or parameters
    
    Args:
        grok_api_key: xAI Grok API key (defaults to XAI_API_KEY env var)
        polygon_api_key: Polygon.io API key (defaults to POLYGON_API_KEY env var)
        tavily_api_key: Tavily API key (defaults to TAVILY_API_KEY env var)
    
    Returns:
        Configured Dexter instance
    """
    grok_key = grok_api_key or os.getenv('XAI_API_KEY')
    polygon_key = polygon_api_key or os.getenv('POLYGON_API_KEY')
    tavily_key = tavily_api_key or os.getenv('TAVILY_API_KEY')
    
    if not grok_key:
        raise ValueError("XAI_API_KEY not found in environment or parameters")
    if not polygon_key:
        raise ValueError("POLYGON_API_KEY not found in environment or parameters")
    
    return Dexter(grok_key, polygon_key, tavily_key)
