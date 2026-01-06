from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr


class TaskBase(BaseModel):
    """Shared fields for tasks."""

    title: constr(min_length=1, max_length=255) = Field(..., description="Short task title.")


class TaskCreate(TaskBase):
    """Payload to create a new task."""


class TaskUpdate(BaseModel):
    """Payload to update task fields (partial update)."""

    title: Optional[constr(min_length=1, max_length=255)] = Field(
        default=None, description="New title for the task."
    )
    is_completed: Optional[bool] = Field(
        default=None, description="Set completion state explicitly."
    )


class TaskRead(BaseModel):
    """Task representation returned by the API."""

    id: int = Field(..., description="Task ID.")
    title: str = Field(..., description="Task title.")
    is_completed: bool = Field(..., description="Whether task is completed.")
    created_at: datetime = Field(..., description="Creation timestamp (server time).")
    updated_at: datetime = Field(..., description="Last update timestamp (server time).")

    model_config = {"from_attributes": True}
