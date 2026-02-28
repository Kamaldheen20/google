"""
Task Orchestrator
Executes tasks and manages workflow
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from core.task_decomposer import Task, TaskStatus, TaskPriority
from services import get_service


class Orchestrator:
    """Orchestrates task execution"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        self.results = {}
    
    def run_tasks(self, tasks: List[Dict]) -> Dict[str, Any]:
        """
        Execute a list of tasks
        Returns execution results
        """
        # Convert dicts back to Task objects
        task_objects = []
        for task_dict in tasks:
            task = Task(
                task_id=task_dict['task_id'],
                service=task_dict['service'],
                action=task_dict['action'],
                parameters=task_dict.get('parameters', {}),
                status=TaskStatus(task_dict.get('status', 'pending')),
                priority=TaskPriority(task_dict.get('priority', 2)),
                depends_on=task_dict.get('depends_on', [])
            )
            task_objects.append(task)
        
        # Sort by priority
        task_objects.sort(key=lambda t: t.priority.value, reverse=True)
        
        # Track completed task results for dependency resolution
        completed_results = {}
        execution_order = []
        
        # Execute tasks respecting dependencies
        for task in task_objects:
            # Check dependencies
            if task.depends_on:
                deps_completed = all(
                    dep_id in completed_results 
                    for dep_id in task.depends_on
                )
                if not deps_completed:
                    continue
            
            # Execute task
            result = self._execute_task(task, completed_results)
            completed_results[task.task_id] = result
            execution_order.append({
                "task_id": task.task_id,
                "service": task.service,
                "action": task.action,
                "status": result.get('status', 'completed'),
                "result": result
            })
        
        return {
            "success": True,
            "executed": len(completed_results),
            "total": len(task_objects),
            "results": execution_order
        }
    
    def _execute_task(self, task: Task, 
                     previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task"""
        self.logger.info(f"Executing task: {task.task_id} - {task.service}.{task.action}")
        
        try:
            # Get the service
            service = get_service(task.service, self.user_id)
            
            if not service:
                return {
                    "status": "failed",
                    "error": f"Service {task.service} not available",
                    "task_id": task.task_id
                }
            
            # Resolve parameter placeholders
            resolved_params = self._resolve_parameters(task.parameters, previous_results)
            
            # Execute the action
            action_method = getattr(service, task.action, None)
            
            if not action_method:
                return {
                    "status": "failed",
                    "error": f"Action {task.action} not found in service {task.service}",
                    "task_id": task.task_id
                }
            
            # Call the method
            result = action_method(**resolved_params)
            
            # Store result
            task.result = result
            task.status = TaskStatus.COMPLETED if result.get('success') else TaskStatus.FAILED
            
            return {
                "status": "completed" if result.get('success') else "failed",
                "task_id": task.task_id, # Ensure task_id is always present
                "service": task.service,
                "action": task.action,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Task {task.task_id} failed: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            
            return {
                "status": "failed",
                "task_id": task.task_id,
                "service": task.service,
                "action": task.action,
                "error": str(e)
            }
    
    def _resolve_parameters(self, parameters: Dict[str, Any],
                           previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter placeholders from previous task results"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                # This is a placeholder
                task_id = value[2:-2]
                if task_id in previous_results:
                    # Get the result from that task
                    prev_result = previous_results[task_id]
                    if isinstance(prev_result, dict) and 'result' in prev_result:
                        resolved[key] = prev_result['result']
                    else:
                        resolved[key] = prev_result
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def run_single_task(self, service: str, action: str,
                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task without decomposition"""
        task = Task(
            task_id=f"single_{datetime.utcnow().timestamp()}",
            service=service,
            action=action,
            parameters=parameters
        )
        
        return self._execute_task(task, {})


# Singleton factory
def create_orchestrator(user_id: str) -> Orchestrator:
    """Create an orchestrator instance"""
    return Orchestrator(user_id)


def run_tasks(tasks: List[Dict], user_id: str = "default") -> Dict[str, Any]:
    """Execute tasks using orchestrator"""
    orchestrator = Orchestrator(user_id)
    return orchestrator.run_tasks(tasks)
