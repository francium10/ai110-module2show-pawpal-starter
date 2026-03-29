"""
PawPal+ Core System
Backend logic for pet care management
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional
from enum import Enum


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    """Represents a pet care task."""
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    is_recurring: bool = False
    scheduled_time: Optional[datetime] = None
    is_complete: bool = False

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.is_complete = True

    def reschedule(self, new_time: datetime) -> None:
        """Reschedule the task to a new time."""
        self.scheduled_time = new_time


@dataclass
class Pet:
    """Represents a pet."""
    name: str
    species: str
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        self.tasks.append(task)

    def remove_task(self, task_title: str) -> bool:
        """Remove a task by title. Returns True if removed."""
        for task in self.tasks:
            if task.title == task_title:
                self.tasks.remove(task)
                return True
        return False


@dataclass
class Owner:
    """Represents a pet owner."""
    name: str
    available_minutes: int = 480  # Default 8 hours
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's collection."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name. Returns True if removed."""
        for pet in self.pets:
            if pet.name == pet_name:
                self.pets.remove(pet)
                return True
        return False

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks across all pets."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    """Handles scheduling logic for pet care tasks."""
    owner: Owner
    daily_limit_minutes: int = 480

    def generate_schedule(self) -> List[Task]:
        """
        Generate an optimized daily schedule.
        Returns tasks sorted by priority and time.
        """
        all_tasks = self.owner.get_all_tasks()
        return self.sort_by_priority(all_tasks)

    def detect_conflicts(self, tasks: List[Task]) -> List[Task]:
        """Detect scheduling conflicts (overlapping tasks)."""
        return []  # TODO: Implement

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority (HIGH first)."""
        return sorted(tasks, key=lambda task: task.priority.value, reverse=True)


# CLI Demo (for testing)
if __name__ == "__main__":
    print("🐾 PawPal+ System Initialized")
    # TODO: Add demo code in Phase 2
