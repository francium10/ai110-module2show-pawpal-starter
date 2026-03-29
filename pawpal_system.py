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
    pet_name: Optional[str] = None  # Tracks which pet this task belongs to

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.is_complete = True

    def mark_incomplete(self) -> None:
        """Reset the task back to incomplete."""
        self.is_complete = False

    def reschedule(self, new_time: datetime) -> None:
        """Reschedule the task to a new time."""
        self.scheduled_time = new_time

    def __str__(self) -> str:
        priority_label = self.priority.name.capitalize()
        time_str = self.scheduled_time.strftime("%H:%M") if self.scheduled_time else "Unscheduled"
        return f"{self.title} ({self.duration_minutes}min) [{priority_label}] @ {time_str}"


@dataclass
class Pet:
    """Represents a pet."""
    name: str
    species: str
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        task.pet_name = self.name  # Link task back to this pet
        self.tasks.append(task)

    def remove_task(self, task_title: str) -> bool:
        """Remove a task by title. Returns True if removed."""
        original_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.title != task_title]
        return len(self.tasks) < original_len

    def get_pending_tasks(self) -> List[Task]:
        """Get tasks that are not yet complete."""
        return [t for t in self.tasks if not t.is_complete]


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
        original_len = len(self.pets)
        self.pets = [p for p in self.pets if p.name != pet_name]
        return len(self.pets) < original_len

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_pending_tasks(self) -> List[Task]:
        """Get all incomplete tasks across all pets."""
        return [task for task in self.get_all_tasks() if not task.is_complete]

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Find and return a pet by name, or None if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None


@dataclass
class Scheduler:
    """Handles scheduling logic for pet care tasks."""
    owner: Owner
    daily_limit_minutes: int = 480

    def generate_schedule(self, include_completed: bool = False) -> List[Task]:
        """
        Generate an optimized daily schedule.
        Returns tasks sorted by priority and time, capped at daily_limit_minutes.
        """
        all_tasks = self.owner.get_all_tasks()
        if not include_completed:
            all_tasks = [t for t in all_tasks if not t.is_complete]
        sorted_tasks = self.sort_by_priority(all_tasks)

        scheduled: List[Task] = []
        total_minutes = 0
        for task in sorted_tasks:
            if total_minutes + task.duration_minutes <= self.daily_limit_minutes:
                scheduled.append(task)
                total_minutes += task.duration_minutes

        return scheduled

    def detect_conflicts(self, tasks: List[Task]) -> List[Task]:
        """Detect scheduling conflicts (overlapping tasks). Returns conflicting tasks."""
        conflicts: List[Task] = []
        timed_tasks = [t for t in tasks if t.scheduled_time is not None]

        for i, task_a in enumerate(timed_tasks):
            end_a = task_a.scheduled_time.timestamp() + task_a.duration_minutes * 60  # type: ignore[union-attr]
            for task_b in timed_tasks[i + 1:]:
                start_b = task_b.scheduled_time.timestamp()  # type: ignore[union-attr]
                end_b = start_b + task_b.duration_minutes * 60
                start_a = task_a.scheduled_time.timestamp()  # type: ignore[union-attr]

                # Overlap if one starts before the other ends
                if start_a < end_b and start_b < end_a:
                    if task_a not in conflicts:
                        conflicts.append(task_a)
                    if task_b not in conflicts:
                        conflicts.append(task_b)

        return conflicts

    def format_schedule(self, tasks: List[Task]) -> str:
        """Return a formatted string representation of the schedule."""
        if not tasks:
            return "  No tasks fit within today's time budget."

        lines = ["\nOptimized Schedule:\n"]
        total = 0
        for i, task in enumerate(tasks, start=1):
            time_str = task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "Unscheduled"
            lines.append(
                f"  {i}. [{task.priority.name:<6}] {task.title} "
                f"({task.duration_minutes}min) | {time_str}"
                f"  [pet: {task.pet_name or '?'}]"
            )
            total += task.duration_minutes
        lines.append(f"\n  Total time: {total} minutes")
        return "\n".join(lines)

    def get_total_scheduled_minutes(self, tasks: List[Task]) -> int:
        """Return the sum of duration_minutes for all given tasks."""
        return sum(t.duration_minutes for t in tasks)

    def assign_times(self, tasks: List[Task], start: datetime) -> None:
        """Assign sequential scheduled_time to each task starting from start."""
        from datetime import timedelta
        current = start
        for task in tasks:
            task.scheduled_time = current
            current = current + timedelta(minutes=task.duration_minutes)

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority (HIGH first), then by scheduled_time as tiebreaker."""
        return sorted(
            tasks,
            key=lambda task: (
                -task.priority.value,
                task.scheduled_time or datetime.max
            )
        )


# CLI Demo (for testing)
if __name__ == "__main__":
    print("PawPal+ System Initialized")
    # TODO: Add demo code in Phase 2
