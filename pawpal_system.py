"""
PawPal+ Core System
Backend logic for pet care management.

This module provides the core classes for managing pet care tasks with
intelligent scheduling algorithms including:
- Sorting by time and priority
- Filtering by pet, status, and priority
- Recurring task automation
- Conflict detection with warnings
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Callable
from enum import Enum
from copy import deepcopy


class Priority(Enum):
    """Task priority levels for scheduling."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    def __str__(self) -> str:
        """Return human-readable priority label."""
        return self.name.capitalize()


class Frequency(Enum):
    """Task recurrence frequency options."""
    ONCE = 0        # One-time task
    DAILY = 1       # Repeats every day
    WEEKLY = 7      # Repeats every week
    BIWEEKLY = 14   # Repeats every two weeks

    def __str__(self) -> str:
        """Return human-readable frequency label."""
        return self.name.capitalize()


@dataclass
class Task:
    """Represents a single pet care task.

    Attributes:
        title: Name/description of the task
        duration_minutes: How long the task takes
        priority: Urgency level (LOW, MEDIUM, HIGH)
        frequency: How often task repeats (ONCE, DAILY, WEEKLY, BIWEEKLY)
        scheduled_time: When the task is scheduled
        is_complete: Whether task has been completed
        pet_name: Which pet this task belongs to
    """
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    frequency: Frequency = Frequency.ONCE
    scheduled_time: Optional[datetime] = None
    is_complete: bool = False
    pet_name: Optional[str] = None

    # Legacy support for is_recurring boolean
    @property
    def is_recurring(self) -> bool:
        """Check if task recurs (for backwards compatibility)."""
        return self.frequency != Frequency.ONCE

    def mark_complete(self) -> Optional['Task']:
        """Mark the task as completed.

        Returns:
            If task is recurring, returns a new Task instance for the next occurrence.
            Otherwise, returns None.
        """
        self.is_complete = True

        # Handle recurring task automation
        if self.frequency != Frequency.ONCE and self.scheduled_time:
            return self._create_next_occurrence()
        return None

    def _create_next_occurrence(self) -> 'Task':
        """Create the next occurrence of a recurring task.

        Uses timedelta to calculate the next due date based on frequency:
        - DAILY: today + 1 day
        - WEEKLY: today + 7 days
        - BIWEEKLY: today + 14 days

        Returns:
            A new Task instance scheduled for the next occurrence.
        """
        days_delta = self.frequency.value  # DAILY=1, WEEKLY=7, BIWEEKLY=14
        next_time = self.scheduled_time + \
            timedelta(days=days_delta)  # type: ignore

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            scheduled_time=next_time,
            is_complete=False,
            pet_name=self.pet_name
        )

    def mark_incomplete(self) -> None:
        """Reset the task back to incomplete."""
        self.is_complete = False

    def reschedule(self, new_time: datetime) -> None:
        """Reschedule the task to a new time."""
        self.scheduled_time = new_time

    def __str__(self) -> str:
        """Return formatted string for display."""
        status = "✓" if self.is_complete else "○"
        time_str = self.scheduled_time.strftime(
            "%I:%M %p") if self.scheduled_time else "Unscheduled"
        freq = f" [{self.frequency}]" if self.is_recurring else ""
        pet = f" ({self.pet_name})" if self.pet_name else ""
        return f"{status} {time_str} | {self.title}{pet} - {self.duration_minutes}min [{self.priority}]{freq}"


@dataclass
class Pet:
    """Represents a pet with associated care tasks.

    Attributes:
        name: Pet's name
        species: Type of animal (dog, cat, etc.)
        age: Pet's age in years
        tasks: List of care tasks for this pet
    """
    name: str
    species: str
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_title: str) -> bool:
        """Remove a task by title. Returns True if removed."""
        original_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.title != task_title]
        return len(self.tasks) < original_len

    def get_pending_tasks(self) -> List[Task]:
        """Get all incomplete tasks for this pet."""
        return [t for t in self.tasks if not t.is_complete]

    def get_completed_tasks(self) -> List[Task]:
        """Get all completed tasks for this pet."""
        return [t for t in self.tasks if t.is_complete]

    def __str__(self) -> str:
        """Return formatted string for display."""
        pending = len(self.get_pending_tasks())
        total = len(self.tasks)
        return f"🐾 {self.name} ({self.species}, {self.age}yr) - {pending}/{total} tasks pending"


@dataclass
class Owner:
    """Represents a pet owner managing multiple pets.

    Attributes:
        name: Owner's name
        available_minutes: Daily time budget for pet care
        pets: List of pets owned
    """
    name: str
    available_minutes: int = 480
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's collection."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name. Returns True if removed."""
        original_len = len(self.pets)
        self.pets = [p for p in self.pets if p.name != pet_name]
        return len(self.pets) < original_len

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Find a pet by name. Returns None if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_pending_tasks(self) -> List[Task]:
        """Get all incomplete tasks across all pets."""
        return [t for t in self.get_all_tasks() if not t.is_complete]

    def __str__(self) -> str:
        """Return formatted string for display."""
        total_tasks = len(self.get_all_tasks())
        pending = len(self.get_pending_tasks())
        return f"👤 {self.name} - {len(self.pets)} pet(s), {pending}/{total_tasks} tasks pending"


@dataclass
class ConflictWarning:
    """Represents a scheduling conflict between two tasks.

    Attributes:
        task_a: First conflicting task
        task_b: Second conflicting task
        message: Human-readable warning message
        overlap_minutes: How many minutes the tasks overlap
    """
    task_a: Task
    task_b: Task
    message: str
    overlap_minutes: int = 0

    def __str__(self) -> str:
        return self.message


@dataclass
class Scheduler:
    """Handles scheduling logic for pet care tasks.

    The Scheduler is the "brain" of PawPal+. It provides algorithms for:
    - Sorting tasks by time or priority
    - Filtering tasks by pet, status, or priority
    - Detecting scheduling conflicts
    - Managing recurring task automation

    Attributes:
        owner: The pet owner to schedule for
        daily_limit_minutes: Maximum minutes to schedule per day
    """
    owner: Owner
    daily_limit_minutes: int = 480

    # =========================================================================
    # SORTING ALGORITHMS
    # =========================================================================

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by scheduled_time (earliest first).

        Uses Python's sorted() with a lambda key function to compare
        datetime objects. Unscheduled tasks are placed at the end.

        Args:
            tasks: List of tasks to sort

        Returns:
            New list of tasks sorted by time (earliest to latest)

        Example:
            >>> sorted_tasks = scheduler.sort_by_time(tasks)
        """
        return sorted(
            tasks,
            key=lambda task: task.scheduled_time or datetime.max
        )

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority (HIGH first), then by time.

        Uses a compound sort key: primary sort by priority value (descending),
        secondary sort by scheduled_time (ascending).

        Args:
            tasks: List of tasks to sort

        Returns:
            New list of tasks sorted by priority then time
        """
        return sorted(
            tasks,
            key=lambda task: (
                -task.priority.value,  # Negative for descending (HIGH=3 first)
                task.scheduled_time or datetime.max
            )
        )

    def sort_by_duration(self, tasks: List[Task], ascending: bool = True) -> List[Task]:
        """Sort tasks by duration (shortest or longest first).

        Args:
            tasks: List of tasks to sort
            ascending: If True, shortest first; if False, longest first

        Returns:
            New list of tasks sorted by duration
        """
        return sorted(
            tasks,
            key=lambda task: task.duration_minutes,
            reverse=not ascending
        )

    # =========================================================================
    # FILTERING ALGORITHMS
    # =========================================================================

    def filter_by_pet(self, tasks: List[Task], pet_name: str) -> List[Task]:
        """Filter tasks to only include those for a specific pet.

        Args:
            tasks: List of tasks to filter
            pet_name: Name of the pet to filter by

        Returns:
            List of tasks belonging to the specified pet
        """
        return [t for t in tasks if t.pet_name == pet_name]

    def filter_by_status(self, tasks: List[Task], completed: bool) -> List[Task]:
        """Filter tasks by completion status.

        Args:
            tasks: List of tasks to filter
            completed: If True, return completed tasks; if False, return pending

        Returns:
            List of tasks matching the specified status
        """
        return [t for t in tasks if t.is_complete == completed]

    def filter_by_priority(self, tasks: List[Task], priority: Priority) -> List[Task]:
        """Filter tasks by priority level.

        Args:
            tasks: List of tasks to filter
            priority: Priority level to filter by

        Returns:
            List of tasks with the specified priority
        """
        return [t for t in tasks if t.priority == priority]

    def filter_by_time_range(
        self,
        tasks: List[Task],
        start: datetime,
        end: datetime
    ) -> List[Task]:
        """Filter tasks scheduled within a time range.

        Args:
            tasks: List of tasks to filter
            start: Start of time range (inclusive)
            end: End of time range (inclusive)

        Returns:
            List of tasks scheduled within the range
        """
        return [
            t for t in tasks
            if t.scheduled_time and start <= t.scheduled_time <= end
        ]

    def filter_recurring(self, tasks: List[Task]) -> List[Task]:
        """Filter to only recurring tasks.

        Args:
            tasks: List of tasks to filter

        Returns:
            List of recurring tasks
        """
        return [t for t in tasks if t.is_recurring]

    def filter_chain(
        self,
        tasks: List[Task],
        *filters: Callable[[List[Task]], List[Task]]
    ) -> List[Task]:
        """Apply multiple filters in sequence.

        Args:
            tasks: List of tasks to filter
            *filters: Filter functions to apply in order

        Returns:
            List of tasks after all filters applied

        Example:
            >>> high_pending = scheduler.filter_chain(
            ...     tasks,
            ...     lambda t: scheduler.filter_by_status(t, completed=False),
            ...     lambda t: scheduler.filter_by_priority(t, Priority.HIGH)
            ... )
        """
        result = tasks
        for filter_func in filters:
            result = filter_func(result)
        return result

    # =========================================================================
    # CONFLICT DETECTION
    # =========================================================================

    def detect_conflicts(self, tasks: List[Task]) -> List[ConflictWarning]:
        """Detect scheduling conflicts (overlapping tasks).

        This algorithm compares each pair of timed tasks to check if their
        time windows overlap. Two tasks conflict if one starts before the
        other ends AND the other starts before the first one ends.

        Time Complexity: O(n²) where n = number of timed tasks

        Args:
            tasks: List of tasks to check for conflicts

        Returns:
            List of ConflictWarning objects describing each conflict
        """
        warnings: List[ConflictWarning] = []
        timed_tasks = self.sort_by_time([t for t in tasks if t.scheduled_time])

        for i, task_a in enumerate(timed_tasks):
            start_a = task_a.scheduled_time  # type: ignore
            end_a = start_a + timedelta(minutes=task_a.duration_minutes)

            for task_b in timed_tasks[i + 1:]:
                start_b = task_b.scheduled_time  # type: ignore
                end_b = start_b + timedelta(minutes=task_b.duration_minutes)

                # Check for overlap: A starts before B ends AND B starts before A ends
                if start_a < end_b and start_b < end_a:
                    # Calculate overlap duration
                    overlap_start = max(start_a, start_b)
                    overlap_end = min(end_a, end_b)
                    overlap_minutes = int(
                        (overlap_end - overlap_start).total_seconds() / 60)

                    # Determine if same pet or different pets
                    if task_a.pet_name == task_b.pet_name:
                        conflict_type = f"Same pet ({task_a.pet_name})"
                    else:
                        conflict_type = f"Different pets ({task_a.pet_name} & {task_b.pet_name})"

                    warning = ConflictWarning(
                        task_a=task_a,
                        task_b=task_b,
                        overlap_minutes=overlap_minutes,
                        message=(
                            f"⚠️ CONFLICT: '{task_a.title}' and '{task_b.title}' overlap by "
                            f"{overlap_minutes} minutes. {conflict_type}. "
                            f"({start_a.strftime('%I:%M %p')} - {end_a.strftime('%I:%M %p')} vs "
                            f"{start_b.strftime('%I:%M %p')} - {end_b.strftime('%I:%M %p')})"
                        )
                    )
                    warnings.append(warning)

        return warnings

    def get_conflict_free_tasks(self, tasks: List[Task]) -> Tuple[List[Task], List[ConflictWarning]]:
        """Get tasks without conflicts and list of warnings.

        Args:
            tasks: List of tasks to check

        Returns:
            Tuple of (conflict-free tasks, list of warnings)
        """
        warnings = self.detect_conflicts(tasks)
        conflicting_tasks = set()

        for warning in warnings:
            conflicting_tasks.add(id(warning.task_a))
            conflicting_tasks.add(id(warning.task_b))

        safe_tasks = [t for t in tasks if id(t) not in conflicting_tasks]
        return safe_tasks, warnings

    # =========================================================================
    # RECURRING TASK MANAGEMENT
    # =========================================================================

    def complete_task_with_recurrence(self, pet: Pet, task: Task) -> Optional[Task]:
        """Mark a task complete and handle recurring task creation.

        If the task is recurring, a new instance is automatically created
        for the next occurrence and added to the pet's task list.

        Args:
            pet: The pet the task belongs to
            task: The task to complete

        Returns:
            The new recurring task instance, or None if not recurring
        """
        next_task = task.mark_complete()

        if next_task:
            pet.add_task(next_task)
            return next_task

        return None

    def get_recurring_tasks(self) -> List[Task]:
        """Get all recurring tasks across all pets."""
        return self.filter_recurring(self.owner.get_all_tasks())

    # =========================================================================
    # SCHEDULE GENERATION
    # =========================================================================

    def generate_schedule(self, include_completed: bool = False) -> List[Task]:
        """Generate an optimized daily schedule.

        Algorithm:
        1. Filter to pending tasks (unless include_completed=True)
        2. Sort by priority (HIGH first) with time as tiebreaker
        3. Greedily add tasks until daily_limit_minutes is reached

        Args:
            include_completed: Whether to include already-completed tasks

        Returns:
            List of tasks for today's schedule, sorted by priority
        """
        if include_completed:
            all_tasks = self.owner.get_all_tasks()
        else:
            all_tasks = self.owner.get_pending_tasks()

        sorted_tasks = self.sort_by_priority(all_tasks)

        scheduled: List[Task] = []
        total_minutes = 0

        for task in sorted_tasks:
            if total_minutes + task.duration_minutes <= self.daily_limit_minutes:
                scheduled.append(task)
                total_minutes += task.duration_minutes

        return scheduled

    def generate_schedule_by_time(self) -> List[Task]:
        """Generate schedule sorted by time (for viewing chronologically).

        Returns:
            List of pending tasks sorted by scheduled time
        """
        pending = self.owner.get_pending_tasks()
        return self.sort_by_time(pending)

    def get_total_scheduled_minutes(self, tasks: List[Task]) -> int:
        """Calculate total duration of a task list."""
        return sum(task.duration_minutes for task in tasks)

    def assign_times(self, tasks: List[Task], start: datetime) -> List[Task]:
        """Assign sequential scheduled times to tasks.

        Args:
            tasks: Tasks to assign times to
            start: When to start the first task

        Returns:
            Same tasks with scheduled_time populated
        """
        current = start
        for task in tasks:
            task.scheduled_time = current
            current += timedelta(minutes=task.duration_minutes)
        return tasks

    # =========================================================================
    # FORMATTING & DISPLAY
    # =========================================================================

    def format_schedule(self, tasks: List[Task]) -> str:
        """Format a task list as a readable schedule string."""
        if not tasks:
            return "📭 No tasks scheduled!"

        lines = [
            "=" * 55,
            "📅 TODAY'S SCHEDULE",
            "=" * 55
        ]
        total_minutes = 0

        for i, task in enumerate(tasks, 1):
            lines.append(f"  {i}. {task}")
            total_minutes += task.duration_minutes

        lines.append("-" * 55)
        hours, mins = divmod(total_minutes, 60)
        remaining = self.daily_limit_minutes - total_minutes
        lines.append(
            f"⏱️  Total: {hours}h {mins}m | Budget remaining: {remaining}min")
        lines.append("=" * 55)

        return "\n".join(lines)

    def format_conflicts(self, warnings: List[ConflictWarning]) -> str:
        """Format conflict warnings as a readable string."""
        if not warnings:
            return "✅ No scheduling conflicts detected!"

        lines = [
            "=" * 55,
            f"⚠️ {len(warnings)} SCHEDULING CONFLICT(S) DETECTED",
            "=" * 55
        ]

        for i, warning in enumerate(warnings, 1):
            lines.append(f"  {i}. {warning.message}")

        lines.append("=" * 55)
        return "\n".join(lines)


# =============================================================================
# CLI Demo Entry Point
# =============================================================================

if __name__ == "__main__":
    print("🐾 PawPal+ System Initialized")
    print("Run 'python main.py' to see the full demo.")
