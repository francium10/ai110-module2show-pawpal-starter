"""
PawPal+ Core System (Extended Version)

Backend logic for pet care management with:
- Sorting by time and priority
- Filtering by pet, status, and priority
- Recurring task automation
- Conflict detection with warnings
- JSON persistence (save/load)
- Advanced slot-finding algorithm
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Callable, Dict, Any
from enum import Enum
from copy import deepcopy
import json
import os


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
    """Represents a single pet care task."""
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    frequency: Frequency = Frequency.ONCE
    scheduled_time: Optional[datetime] = None
    is_complete: bool = False
    pet_name: Optional[str] = None

    @property
    def is_recurring(self) -> bool:
        """Check if task recurs (for backwards compatibility)."""
        return self.frequency != Frequency.ONCE

    def mark_complete(self) -> Optional['Task']:
        """Mark the task as completed."""
        self.is_complete = True
        if self.frequency != Frequency.ONCE and self.scheduled_time:
            return self._create_next_occurrence()
        return None

    def _create_next_occurrence(self) -> 'Task':
        """Create the next occurrence of a recurring task using timedelta."""
        days_delta = self.frequency.value
        next_time = self.scheduled_time + timedelta(days=days_delta)  # type: ignore
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
        time_str = self.scheduled_time.strftime("%I:%M %p") if self.scheduled_time else "Unscheduled"
        freq = f" [{self.frequency}]" if self.is_recurring else ""
        pet = f" ({self.pet_name})" if self.pet_name else ""
        return f"{status} {time_str} | {self.title}{pet} - {self.duration_minutes}min [{self.priority}]{freq}"

    # =========================================================================
    # JSON SERIALIZATION (Challenge 2: Data Persistence)
    # =========================================================================
    def to_dict(self) -> Dict[str, Any]:
        """Convert Task to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.name,
            "frequency": self.frequency.name,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "is_complete": self.is_complete,
            "pet_name": self.pet_name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create Task from dictionary (JSON deserialization)."""
        return cls(
            title=data["title"],
            duration_minutes=data["duration_minutes"],
            priority=Priority[data["priority"]],
            frequency=Frequency[data["frequency"]],
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]) if data["scheduled_time"] else None,
            is_complete=data["is_complete"],
            pet_name=data.get("pet_name")
        )


@dataclass
class Pet:
    """Represents a pet with associated care tasks."""
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

    # =========================================================================
    # JSON SERIALIZATION
    # =========================================================================
    def to_dict(self) -> Dict[str, Any]:
        """Convert Pet to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "tasks": [task.to_dict() for task in self.tasks]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pet':
        """Create Pet from dictionary (JSON deserialization)."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            age=data["age"]
        )
        for task_data in data.get("tasks", []):
            task = Task.from_dict(task_data)
            pet.tasks.append(task)  # Don't use add_task to avoid resetting pet_name
        return pet


@dataclass
class Owner:
    """Represents a pet owner managing multiple pets."""
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

    # =========================================================================
    # JSON PERSISTENCE (Challenge 2: Data Persistence)
    # =========================================================================
    def to_dict(self) -> Dict[str, Any]:
        """Convert Owner to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "pets": [pet.to_dict() for pet in self.pets]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Owner':
        """Create Owner from dictionary (JSON deserialization)."""
        owner = cls(
            name=data["name"],
            available_minutes=data.get("available_minutes", 480)
        )
        for pet_data in data.get("pets", []):
            pet = Pet.from_dict(pet_data)
            owner.pets.append(pet)
        return owner

    def save_to_json(self, filepath: str = "data.json") -> bool:
        """
        Save owner data to a JSON file.
        
        This method was implemented using Agent Mode planning:
        1. Convert Owner → dict using to_dict()
        2. Write dict to JSON file with proper formatting
        3. Handle errors gracefully
        
        Args:
            filepath: Path to save the JSON file (default: data.json)
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except (IOError, OSError) as e:
            print(f"Error saving to {filepath}: {e}")
            return False

    @classmethod
    def load_from_json(cls, filepath: str = "data.json") -> Optional['Owner']:
        """
        Load owner data from a JSON file.
        
        This method was implemented using Agent Mode planning:
        1. Check if file exists
        2. Read and parse JSON
        3. Convert dict → Owner using from_dict()
        4. Handle missing/corrupt files gracefully
        
        Args:
            filepath: Path to the JSON file (default: data.json)
            
        Returns:
            Owner instance if loaded successfully, None otherwise
        """
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (IOError, json.JSONDecodeError, KeyError) as e:
            print(f"Error loading from {filepath}: {e}")
            return None


@dataclass
class ConflictWarning:
    """Represents a scheduling conflict between two tasks."""
    task_a: Task
    task_b: Task
    message: str
    overlap_minutes: int = 0

    def __str__(self) -> str:
        return self.message


@dataclass 
class TimeSlot:
    """
    Represents an available time slot (Challenge 1: Advanced Algorithm).
    
    Used by find_next_available_slot() to return slot information.
    """
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    
    def __str__(self) -> str:
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')} ({self.duration_minutes} min)"


@dataclass
class Scheduler:
    """
    The scheduling "brain" for PawPal+.
    
    Provides algorithms for:
    - Sorting (by time, priority, duration)
    - Filtering (by pet, status, priority, recurring)
    - Conflict detection
    - Schedule generation
    - Next available slot finding (Challenge 1)
    """
    owner: Owner
    daily_limit_minutes: int = 480

    # =========================================================================
    # SORTING ALGORITHMS
    # =========================================================================

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by scheduled time (earliest first, unscheduled last)."""
        return sorted(tasks, key=lambda t: t.scheduled_time or datetime.max)

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority (HIGH first) with time as tiebreaker."""
        return sorted(tasks, key=lambda t: (-t.priority.value, t.scheduled_time or datetime.max))

    def sort_by_duration(self, tasks: List[Task], ascending: bool = True) -> List[Task]:
        """Sort tasks by duration (shortest first by default)."""
        return sorted(tasks, key=lambda t: t.duration_minutes, reverse=not ascending)

    # =========================================================================
    # FILTERING ALGORITHMS
    # =========================================================================

    def filter_by_pet(self, tasks: List[Task], pet_name: str) -> List[Task]:
        """Filter tasks for a specific pet."""
        return [t for t in tasks if t.pet_name == pet_name]

    def filter_by_status(self, tasks: List[Task], completed: bool) -> List[Task]:
        """Filter tasks by completion status."""
        return [t for t in tasks if t.is_complete == completed]

    def filter_by_priority(self, tasks: List[Task], priority: Priority) -> List[Task]:
        """Filter tasks by priority level."""
        return [t for t in tasks if t.priority == priority]

    def filter_by_time_range(self, tasks: List[Task], start: datetime, end: datetime) -> List[Task]:
        """Filter tasks within a time range."""
        return [t for t in tasks if t.scheduled_time and start <= t.scheduled_time <= end]

    def filter_recurring(self, tasks: List[Task]) -> List[Task]:
        """Filter to only recurring tasks."""
        return [t for t in tasks if t.is_recurring]

    def filter_chain(self, tasks: List[Task], *filters: Callable) -> List[Task]:
        """Apply multiple filter functions in sequence."""
        result = tasks
        for filter_func in filters:
            result = filter_func(result)
        return result

    # =========================================================================
    # CONFLICT DETECTION
    # =========================================================================

    def detect_conflicts(self, tasks: List[Task]) -> List[ConflictWarning]:
        """Detect scheduling conflicts (overlapping tasks). O(n²) algorithm."""
        warnings: List[ConflictWarning] = []
        timed_tasks = self.sort_by_time([t for t in tasks if t.scheduled_time])

        for i, task_a in enumerate(timed_tasks):
            start_a = task_a.scheduled_time  # type: ignore
            end_a = start_a + timedelta(minutes=task_a.duration_minutes)

            for task_b in timed_tasks[i + 1:]:
                start_b = task_b.scheduled_time  # type: ignore
                end_b = start_b + timedelta(minutes=task_b.duration_minutes)

                # Check for overlap
                if start_a < end_b and start_b < end_a:
                    overlap_start = max(start_a, start_b)
                    overlap_end = min(end_a, end_b)
                    overlap_minutes = int((overlap_end - overlap_start).total_seconds() / 60)

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
                            f"{overlap_minutes} minutes. {conflict_type}."
                        )
                    )
                    warnings.append(warning)

        return warnings

    def get_conflict_free_tasks(self, tasks: List[Task]) -> Tuple[List[Task], List[ConflictWarning]]:
        """Get tasks without conflicts and list of warnings."""
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
        """Mark a task complete and handle recurring task creation."""
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
        """Generate an optimized daily schedule using priority-based greedy algorithm."""
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
        """Generate schedule sorted by time (for viewing chronologically)."""
        pending = self.owner.get_pending_tasks()
        return self.sort_by_time(pending)

    def get_total_scheduled_minutes(self, tasks: List[Task]) -> int:
        """Calculate total duration of a task list."""
        return sum(task.duration_minutes for task in tasks)

    def assign_times(self, tasks: List[Task], start: datetime) -> List[Task]:
        """Assign sequential scheduled times to tasks."""
        current = start
        for task in tasks:
            task.scheduled_time = current
            current += timedelta(minutes=task.duration_minutes)
        return tasks

    # =========================================================================
    # ADVANCED ALGORITHM: NEXT AVAILABLE SLOT (Challenge 1)
    # =========================================================================
    
    def find_next_available_slot(
        self, 
        duration_needed: int,
        search_start: Optional[datetime] = None,
        search_end: Optional[datetime] = None,
        day_start_hour: int = 6,
        day_end_hour: int = 22
    ) -> Optional[TimeSlot]:
        """
        Find the next available time slot that can fit a task of given duration.
        
        This advanced algorithm was implemented using Agent Mode:
        1. Get all scheduled tasks for the day
        2. Sort them by time
        3. Find gaps between tasks
        4. Return the first gap that fits the required duration
        
        Algorithm: Gap-finding with constraints
        - Respects day boundaries (default 6 AM - 10 PM)
        - Skips occupied time slots
        - Returns first available slot that fits
        
        Args:
            duration_needed: Minutes required for the new task
            search_start: When to start searching (default: now)
            search_end: When to stop searching (default: end of day)
            day_start_hour: Earliest hour to schedule (default: 6 AM)
            day_end_hour: Latest hour to end tasks (default: 10 PM)
            
        Returns:
            TimeSlot if found, None if no slot available
        """
        # Set defaults
        now = datetime.now()
        if search_start is None:
            search_start = now.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
            if search_start < now:
                # If day_start already passed, start from now (rounded up to next 15 min)
                minutes = (now.minute // 15 + 1) * 15
                if minutes >= 60:
                    search_start = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
                else:
                    search_start = now.replace(minute=minutes, second=0, microsecond=0)
        
        if search_end is None:
            search_end = now.replace(hour=day_end_hour, minute=0, second=0, microsecond=0)
        
        # Get all timed tasks for today, sorted by time
        all_tasks = self.owner.get_all_tasks()
        timed_tasks = [t for t in all_tasks if t.scheduled_time]
        
        # Filter to tasks within our search window
        day_tasks = [
            t for t in timed_tasks 
            if t.scheduled_time and search_start.date() == t.scheduled_time.date()
        ]
        day_tasks = self.sort_by_time(day_tasks)
        
        # Build list of occupied time slots
        occupied: List[Tuple[datetime, datetime]] = []
        for task in day_tasks:
            if task.scheduled_time:
                task_start = task.scheduled_time
                task_end = task_start + timedelta(minutes=task.duration_minutes)
                occupied.append((task_start, task_end))
        
        # Find gaps
        current_time = search_start
        
        for (occ_start, occ_end) in occupied:
            # Check gap before this occupied slot
            if current_time < occ_start:
                gap_duration = int((occ_start - current_time).total_seconds() / 60)
                if gap_duration >= duration_needed:
                    # Found a slot!
                    slot_end = current_time + timedelta(minutes=duration_needed)
                    return TimeSlot(
                        start_time=current_time,
                        end_time=slot_end,
                        duration_minutes=duration_needed
                    )
            
            # Move current time past this occupied slot
            if occ_end > current_time:
                current_time = occ_end
        
        # Check gap after all occupied slots
        if current_time < search_end:
            gap_duration = int((search_end - current_time).total_seconds() / 60)
            if gap_duration >= duration_needed:
                slot_end = current_time + timedelta(minutes=duration_needed)
                return TimeSlot(
                    start_time=current_time,
                    end_time=slot_end,
                    duration_minutes=duration_needed
                )
        
        # No slot found
        return None

    def find_all_available_slots(
        self,
        duration_needed: int,
        search_start: Optional[datetime] = None,
        search_end: Optional[datetime] = None,
        day_start_hour: int = 6,
        day_end_hour: int = 22
    ) -> List[TimeSlot]:
        """
        Find ALL available time slots that can fit a task.
        
        Similar to find_next_available_slot but returns all possibilities,
        allowing the user to choose their preferred time.
        
        Args:
            duration_needed: Minutes required for the new task
            search_start: When to start searching
            search_end: When to stop searching
            day_start_hour: Earliest scheduling hour
            day_end_hour: Latest hour to end tasks
            
        Returns:
            List of available TimeSlots
        """
        slots: List[TimeSlot] = []
        now = datetime.now()
        
        if search_start is None:
            search_start = now.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
            if search_start < now:
                minutes = (now.minute // 15 + 1) * 15
                if minutes >= 60:
                    search_start = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
                else:
                    search_start = now.replace(minute=minutes, second=0, microsecond=0)
        
        if search_end is None:
            search_end = now.replace(hour=day_end_hour, minute=0, second=0, microsecond=0)
        
        # Get occupied slots
        all_tasks = self.owner.get_all_tasks()
        timed_tasks = [t for t in all_tasks if t.scheduled_time]
        day_tasks = [
            t for t in timed_tasks 
            if t.scheduled_time and search_start.date() == t.scheduled_time.date()
        ]
        day_tasks = self.sort_by_time(day_tasks)
        
        occupied: List[Tuple[datetime, datetime]] = []
        for task in day_tasks:
            if task.scheduled_time:
                task_start = task.scheduled_time
                task_end = task_start + timedelta(minutes=task.duration_minutes)
                occupied.append((task_start, task_end))
        
        # Find all gaps
        current_time = search_start
        
        for (occ_start, occ_end) in occupied:
            if current_time < occ_start:
                gap_duration = int((occ_start - current_time).total_seconds() / 60)
                if gap_duration >= duration_needed:
                    slot_end = current_time + timedelta(minutes=duration_needed)
                    slots.append(TimeSlot(
                        start_time=current_time,
                        end_time=slot_end,
                        duration_minutes=duration_needed
                    ))
            if occ_end > current_time:
                current_time = occ_end
        
        # Check final gap
        if current_time < search_end:
            gap_duration = int((search_end - current_time).total_seconds() / 60)
            if gap_duration >= duration_needed:
                slot_end = current_time + timedelta(minutes=duration_needed)
                slots.append(TimeSlot(
                    start_time=current_time,
                    end_time=slot_end,
                    duration_minutes=duration_needed
                ))
        
        return slots

    def suggest_best_time(self, task: Task) -> Optional[TimeSlot]:
        """
        Suggest the best time for a task based on priority and availability.
        
        High priority tasks get earlier slots; low priority gets later slots.
        
        Args:
            task: The task to schedule
            
        Returns:
            Suggested TimeSlot or None if no slots available
        """
        slots = self.find_all_available_slots(task.duration_minutes)
        
        if not slots:
            return None
        
        if task.priority == Priority.HIGH:
            # Return earliest slot
            return slots[0]
        elif task.priority == Priority.LOW:
            # Return latest slot
            return slots[-1]
        else:
            # Medium priority: return middle slot
            return slots[len(slots) // 2]

    # =========================================================================
    # FORMATTING & DISPLAY
    # =========================================================================

    def format_schedule(self, tasks: List[Task]) -> str:
        """Format a task list as a readable schedule string."""
        if not tasks:
            return "📭 No tasks scheduled!"

        lines = ["=" * 55, "📅 TODAY'S SCHEDULE", "=" * 55]
        total_minutes = 0

        for i, task in enumerate(tasks, 1):
            lines.append(f"  {i}. {task}")
            total_minutes += task.duration_minutes

        lines.append("-" * 55)
        hours, mins = divmod(total_minutes, 60)
        remaining = self.daily_limit_minutes - total_minutes
        lines.append(f"⏱️  Total: {hours}h {mins}m | Budget remaining: {remaining}min")
        lines.append("=" * 55)

        return "\n".join(lines)

    def format_conflicts(self, warnings: List[ConflictWarning]) -> str:
        """Format conflict warnings as a readable string."""
        if not warnings:
            return "✅ No scheduling conflicts detected!"

        lines = ["=" * 55, f"⚠️ {len(warnings)} SCHEDULING CONFLICT(S) DETECTED", "=" * 55]
        for i, warning in enumerate(warnings, 1):
            lines.append(f"  {i}. {warning.message}")
        lines.append("=" * 55)
        
        return "\n".join(lines)


# =============================================================================
# CLI Demo Entry Point
# =============================================================================

if __name__ == "__main__":
    print("🐾 PawPal+ System Initialized (Extended Version)")
    print("Features: JSON Persistence + Next Available Slot Algorithm")
    print("\nRun 'python main.py' to see the full demo.")
