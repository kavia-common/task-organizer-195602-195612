from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.api.models import Task
from src.api.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "",
    summary="List tasks",
    description="Returns all tasks ordered by newest first.",
    response_model=List[TaskRead],
    operation_id="list_tasks",
)
def list_tasks(db: Session = Depends(get_db)):
    """List all tasks."""
    stmt = select(Task).order_by(Task.created_at.desc(), Task.id.desc())
    return list(db.execute(stmt).scalars().all())


@router.post(
    "",
    summary="Create task",
    description="Creates a new task with the given title.",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_task",
)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    task = Task(title=payload.title, is_completed=False)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put(
    "/{task_id}",
    summary="Update task",
    description="Updates a task title and/or completion state.",
    response_model=TaskRead,
    operation_id="update_task",
)
def update_task(
    payload: TaskUpdate,
    task_id: int = Path(..., description="Task ID."),
    db: Session = Depends(get_db),
):
    """Update an existing task."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if payload.title is not None:
        task.title = payload.title
    if payload.is_completed is not None:
        task.is_completed = payload.is_completed

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.post(
    "/{task_id}/toggle",
    summary="Toggle completion",
    description="Toggles a task between completed and not completed.",
    response_model=TaskRead,
    operation_id="toggle_task",
)
def toggle_task(
    task_id: int = Path(..., description="Task ID."),
    db: Session = Depends(get_db),
):
    """Toggle a task's completion state."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task.is_completed = not bool(task.is_completed)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    summary="Delete task",
    description="Deletes a task by ID.",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_task",
)
def delete_task(
    task_id: int = Path(..., description="Task ID."),
    db: Session = Depends(get_db),
):
    """Delete a task."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db.delete(task)
    db.commit()
    return None
