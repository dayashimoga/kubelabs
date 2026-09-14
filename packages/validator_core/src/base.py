"""
Base Validator Interface and Execution Context.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from packages.lab_schema import ValidatorRule, ValidationResultItem


class ExecutionContext(BaseModel):
    """Execution context provided to validators for inspecting sandbox or environment."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    sandbox_id: Optional[str] = None
    container_id: Optional[str] = None
    workdir: Optional[str] = None
    host_base_url: Optional[str] = "http://localhost"
    podman_executor: Optional[Any] = None
    simulation_state: Optional[Dict[str, Any]] = None
    simulator: Optional[Any] = None


class BaseValidator(ABC):
    """Abstract base class for all state validators."""

    @abstractmethod
    def validate(self, rule: ValidatorRule, context: ExecutionContext) -> ValidationResultItem:
        """Evaluate system state against the rule and return detailed result."""
        pass
