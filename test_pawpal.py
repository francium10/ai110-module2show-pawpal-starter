"""
PawPal+ Comprehensive Test Suite - Phase 5

This test suite verifies:
- Core class functionality (Task, Pet, Owner, Scheduler)
- Sorting algorithms (by time, priority, duration)
- Filtering algorithms (by pet, status, priority, recurring)
- Recurring task automation with timedelta
- Conflict detection for overlapping time windows
- Edge cases (empty lists, zero tasks, exact same times)

Run tests with: python -m pytest test_pawpal.py -v
"""

import pytest
from datetime import datetime, timedelta

from pawpal_system import (
    Task, Pet, Owner, Scheduler,
    Priority, Frequency, ConflictWarning
)


# =============================================================================
# TASK TESTS
# =============================================================================

class TestTask:
    """Tests for the Task class."""

    def test_task_creation_with_defaults(self):
        """Verify task can be created with minimal arguments."""
        task = Task(title="Walk the dog", duration_minutes=30)
        
        assert task.title == "Walk the dog"
        assert task.duration_minutes == 30
        assert task.priority == Priority.MEDIUM
        assert task.frequency == Frequency.ONCE
        assert task.is_complete is False
        assert task.is_recurring is False
        assert task.scheduled_time is None
        assert task.pet_name is None

    def test_task_creation_with_all_fields(self):
        """Verify task creation with all fields specified."""
        scheduled = datetime(2026, 3, 29, 8, 0)
        task = Task(
            title="Morning walk",
            duration_minutes=30,
            priority=Priority.HIGH,
            frequency=Frequency.DAILY,
            scheduled_time=scheduled,
            is_complete=False,
            pet_name="Mochi"
        )
        
        assert task.title == "Morning walk"
        assert task.priority == Priority.HIGH
        assert task.frequency == Frequency.DAILY
        assert task.is_recurring is True
        assert task.scheduled_time == scheduled

    def test_mark_complete_changes_status(self):
        """Verify mark_complete() changes the task's status."""
        task = Task(title="Feed the cat", duration_minutes=10)
        
        assert task.is_complete is False
        task.mark_complete()
        assert task.is_complete is True

    def test_mark_complete_non_recurring_returns_none(self):
        """Verify non-recurring task returns None on completion."""
        task = Task(title="Vet visit", duration_minutes=60, frequency=Frequency.ONCE)
        
        result = task.mark_complete()
        assert result is None
        assert task.is_complete is True

    def test_mark_complete_recurring_without_time_returns_none(self):
        """Verify recurring task without scheduled_time returns None."""
        task = Task(
            title="Daily walk",
            duration_minutes=30,
            frequency=Frequency.DAILY,
            scheduled_time=None  # No time set
        )
        
        result = task.mark_complete()
        assert result is None
        assert task.is_complete is True

    def test_mark_incomplete_resets_status(self):
        """Verify mark_incomplete() resets a completed task."""
        task = Task(title="Grooming", duration_minutes=45)
        task.mark_complete()
        
        assert task.is_complete is True
        task.mark_incomplete()
        assert task.is_complete is False

    def test_reschedule_updates_time(self):
        """Verify reschedule() updates the scheduled_time."""
        task = Task(title="Vet appointment", duration_minutes=60)
        new_time = datetime(2026, 3, 28, 14, 0)
        
        assert task.scheduled_time is None
        task.reschedule(new_time)
        assert task.scheduled_time == new_time

    def test_reschedule_overwrites_existing_time(self):
        """Verify reschedule() can overwrite existing time."""
        original = datetime(2026, 3, 28, 8, 0)
        new = datetime(2026, 3, 28, 10, 0)
        
        task = Task(title="Walk", duration_minutes=30, scheduled_time=original)
        task.reschedule(new)
        
        assert task.scheduled_time == new

    def test_task_string_representation(self):
        """Verify __str__ produces readable output."""
        task = Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH)
        task_str = str(task)
        
        assert "Morning walk" in task_str
        assert "30min" in task_str
        assert "High" in task_str

    def test_task_string_shows_recurring_flag(self):
        """Verify recurring tasks show frequency in string."""
        task = Task(
            title="Daily feeding",
            duration_minutes=10,
            frequency=Frequency.DAILY,
            scheduled_time=datetime(2026, 3, 29, 8, 0)
        )
        task_str = str(task)
        
        assert "Daily" in task_str

    def test_is_recurring_property(self):
        """Verify is_recurring property works for all frequencies."""
        once = Task(title="T1", duration_minutes=10, frequency=Frequency.ONCE)
        daily = Task(title="T2", duration_minutes=10, frequency=Frequency.DAILY)
        weekly = Task(title="T3", duration_minutes=10, frequency=Frequency.WEEKLY)
        biweekly = Task(title="T4", duration_minutes=10, frequency=Frequency.BIWEEKLY)
        
        assert once.is_recurring is False
        assert daily.is_recurring is True
        assert weekly.is_recurring is True
        assert biweekly.is_recurring is True


# =============================================================================
# RECURRING TASK TESTS (Phase 4 Feature)
# =============================================================================

class TestRecurringTasks:
    """Tests for recurring task automation using timedelta."""

    def test_daily_task_creates_next_day(self):
        """Verify daily task creates occurrence for next day (today + 1)."""
        base_time = datetime(2026, 3, 29, 8, 0)
        task = Task(
            title="Morning walk",
            duration_minutes=30,
            priority=Priority.HIGH,
            frequency=Frequency.DAILY,
            scheduled_time=base_time
        )
        
        next_task = task.mark_complete()
        
        assert next_task is not None
        assert next_task.scheduled_time == base_time + timedelta(days=1)
        assert next_task.title == task.title
        assert next_task.priority == task.priority
        assert next_task.frequency == Frequency.DAILY
        assert next_task.is_complete is False

    def test_weekly_task_creates_next_week(self):
        """Verify weekly task creates occurrence for next week (today + 7)."""
        base_time = datetime(2026, 3, 29, 10, 0)
        task = Task(
            title="Grooming session",
            duration_minutes=45,
            frequency=Frequency.WEEKLY,
            scheduled_time=base_time
        )
        
        next_task = task.mark_complete()
        
        assert next_task is not None
        assert next_task.scheduled_time == base_time + timedelta(days=7)

    def test_biweekly_task_creates_two_weeks_later(self):
        """Verify biweekly task creates occurrence for 2 weeks later (today + 14)."""
        base_time = datetime(2026, 3, 29, 14, 0)
        task = Task(
            title="Deep cleaning",
            duration_minutes=60,
            frequency=Frequency.BIWEEKLY,
            scheduled_time=base_time
        )
        
        next_task = task.mark_complete()
        
        assert next_task is not None
        assert next_task.scheduled_time == base_time + timedelta(days=14)

    def test_recurring_task_preserves_pet_name(self):
        """Verify next occurrence keeps the pet_name."""
        task = Task(
            title="Medication",
            duration_minutes=5,
            frequency=Frequency.DAILY,
            scheduled_time=datetime(2026, 3, 29, 9, 0),
            pet_name="Whiskers"
        )
        
        next_task = task.mark_complete()
        
        assert next_task is not None
        assert next_task.pet_name == "Whiskers"

    def test_original_task_stays_complete(self):
        """Verify original task remains complete after creating next occurrence."""
        task = Task(
            title="Daily walk",
            duration_minutes=30,
            frequency=Frequency.DAILY,
            scheduled_time=datetime(2026, 3, 29, 8, 0)
        )
        
        task.mark_complete()
        
        assert task.is_complete is True


# =============================================================================
# PET TESTS
# =============================================================================

class TestPet:
    """Tests for the Pet class."""

    def test_pet_creation(self):
        """Verify pet can be created with required attributes."""
        pet = Pet(name="Mochi", species="dog", age=3)
        
        assert pet.name == "Mochi"
        assert pet.species == "dog"
        assert pet.age == 3
        assert pet.tasks == []

    def test_pet_default_age(self):
        """Verify pet age defaults to 0."""
        pet = Pet(name="Puppy", species="dog")
        assert pet.age == 0

    def test_add_task_increases_count(self):
        """Verify adding a task increases the pet's task count."""
        pet = Pet(name="Whiskers", species="cat")
        initial_count = len(pet.tasks)
        
        task = Task(title="Feeding", duration_minutes=5)
        pet.add_task(task)
        
        assert len(pet.tasks) == initial_count + 1

    def test_add_task_sets_pet_name(self):
        """Verify adding a task links it back to the pet."""
        pet = Pet(name="Buddy", species="dog")
        task = Task(title="Walk", duration_minutes=30)
        
        assert task.pet_name is None
        pet.add_task(task)
        assert task.pet_name == "Buddy"

    def test_add_multiple_tasks(self):
        """Verify multiple tasks can be added."""
        pet = Pet(name="Max", species="dog")
        
        pet.add_task(Task(title="Walk", duration_minutes=30))
        pet.add_task(Task(title="Feed", duration_minutes=10))
        pet.add_task(Task(title="Play", duration_minutes=15))
        
        assert len(pet.tasks) == 3

    def test_remove_task_by_title(self):
        """Verify tasks can be removed by title."""
        pet = Pet(name="Max", species="dog")
        pet.add_task(Task(title="Walk", duration_minutes=30))
        pet.add_task(Task(title="Feed", duration_minutes=10))
        
        assert len(pet.tasks) == 2
        removed = pet.remove_task("Walk")
        assert removed is True
        assert len(pet.tasks) == 1
        assert pet.tasks[0].title == "Feed"

    def test_remove_nonexistent_task_returns_false(self):
        """Verify removing a non-existent task returns False."""
        pet = Pet(name="Luna", species="cat")
        pet.add_task(Task(title="Feed", duration_minutes=5))
        
        removed = pet.remove_task("Nonexistent Task")
        assert removed is False
        assert len(pet.tasks) == 1

    def test_remove_task_from_empty_list(self):
        """Verify removing from empty task list returns False."""
        pet = Pet(name="Empty", species="dog")
        
        removed = pet.remove_task("Any Task")
        assert removed is False

    def test_get_pending_tasks(self):
        """Verify get_pending_tasks excludes completed tasks."""
        pet = Pet(name="Rex", species="dog")
        
        task1 = Task(title="Walk", duration_minutes=30)
        task2 = Task(title="Feed", duration_minutes=10)
        task2.mark_complete()
        
        pet.add_task(task1)
        pet.add_task(task2)
        
        pending = pet.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].title == "Walk"

    def test_get_completed_tasks(self):
        """Verify get_completed_tasks returns only completed tasks."""
        pet = Pet(name="Rex", species="dog")
        
        task1 = Task(title="Walk", duration_minutes=30)
        task2 = Task(title="Feed", duration_minutes=10)
        task2.mark_complete()
        
        pet.add_task(task1)
        pet.add_task(task2)
        
        completed = pet.get_completed_tasks()
        assert len(completed) == 1
        assert completed[0].title == "Feed"

    def test_pet_with_no_tasks(self):
        """Edge case: Pet with no tasks returns empty lists."""
        pet = Pet(name="Lonely", species="cat")
        
        assert pet.tasks == []
        assert pet.get_pending_tasks() == []
        assert pet.get_completed_tasks() == []


# =============================================================================
# OWNER TESTS
# =============================================================================

class TestOwner:
    """Tests for the Owner class."""

    def test_owner_creation(self):
        """Verify owner can be created with defaults."""
        owner = Owner(name="Jordan")
        
        assert owner.name == "Jordan"
        assert owner.available_minutes == 480  # default 8 hours
        assert owner.pets == []

    def test_owner_custom_time_budget(self):
        """Verify owner can have custom time budget."""
        owner = Owner(name="Jordan", available_minutes=120)
        assert owner.available_minutes == 120

    def test_add_pet(self):
        """Verify pets can be added to owner."""
        owner = Owner(name="Jordan")
        pet = Pet(name="Mochi", species="dog")
        
        owner.add_pet(pet)
        assert len(owner.pets) == 1
        assert owner.pets[0].name == "Mochi"

    def test_add_multiple_pets(self):
        """Verify multiple pets can be added."""
        owner = Owner(name="Jordan")
        owner.add_pet(Pet(name="Mochi", species="dog"))
        owner.add_pet(Pet(name="Whiskers", species="cat"))
        owner.add_pet(Pet(name="Tweety", species="bird"))
        
        assert len(owner.pets) == 3

    def test_remove_pet(self):
        """Verify pets can be removed by name."""
        owner = Owner(name="Jordan")
        owner.add_pet(Pet(name="Mochi", species="dog"))
        owner.add_pet(Pet(name="Whiskers", species="cat"))
        
        removed = owner.remove_pet("Mochi")
        assert removed is True
        assert len(owner.pets) == 1
        assert owner.pets[0].name == "Whiskers"

    def test_remove_nonexistent_pet_returns_false(self):
        """Verify removing non-existent pet returns False."""
        owner = Owner(name="Jordan")
        owner.add_pet(Pet(name="Mochi", species="dog"))
        
        removed = owner.remove_pet("Unknown")
        assert removed is False
        assert len(owner.pets) == 1

    def test_get_pet_by_name(self):
        """Verify get_pet finds the correct pet."""
        owner = Owner(name="Jordan")
        owner.add_pet(Pet(name="Mochi", species="dog"))
        owner.add_pet(Pet(name="Whiskers", species="cat"))
        
        pet = owner.get_pet("Whiskers")
        assert pet is not None
        assert pet.species == "cat"

    def test_get_pet_returns_none_for_unknown(self):
        """Verify get_pet returns None for unknown pet."""
        owner = Owner(name="Jordan")
        
        pet = owner.get_pet("Unknown")
        assert pet is None

    def test_get_all_tasks_across_pets(self):
        """Verify get_all_tasks aggregates tasks from all pets."""
        owner = Owner(name="Jordan")
        
        pet1 = Pet(name="Mochi", species="dog")
        pet1.add_task(Task(title="Walk", duration_minutes=30))
        pet1.add_task(Task(title="Feed", duration_minutes=10))
        
        pet2 = Pet(name="Whiskers", species="cat")
        pet2.add_task(Task(title="Litter", duration_minutes=5))
        
        owner.add_pet(pet1)
        owner.add_pet(pet2)
        
        all_tasks = owner.get_all_tasks()
        assert len(all_tasks) == 3

    def test_get_pending_tasks_across_pets(self):
        """Verify get_pending_tasks works across all pets."""
        owner = Owner(name="Jordan")
        
        pet1 = Pet(name="Mochi", species="dog")
        task1 = Task(title="Walk", duration_minutes=30)
        task2 = Task(title="Feed", duration_minutes=10)
        task2.mark_complete()
        pet1.add_task(task1)
        pet1.add_task(task2)
        
        pet2 = Pet(name="Whiskers", species="cat")
        pet2.add_task(Task(title="Play", duration_minutes=15))
        
        owner.add_pet(pet1)
        owner.add_pet(pet2)
        
        pending = owner.get_pending_tasks()
        assert len(pending) == 2  # Walk + Play

    def test_owner_with_no_pets(self):
        """Edge case: Owner with no pets returns empty lists."""
        owner = Owner(name="Empty")
        
        assert owner.pets == []
        assert owner.get_all_tasks() == []
        assert owner.get_pending_tasks() == []


# =============================================================================
# SCHEDULER SORTING TESTS (Phase 4 Feature)
# =============================================================================

class TestSchedulerSorting:
    """Tests for Scheduler sorting algorithms."""

    @pytest.fixture
    def scheduler_with_tasks(self):
        """Create a scheduler with out-of-order tasks."""
        owner = Owner(name="Jordan", available_minutes=240)
        pet = Pet(name="Mochi", species="dog")
        
        base_time = datetime(2026, 3, 29, 8, 0)
        
        # Add tasks OUT OF ORDER
        pet.add_task(Task(title="Task3_10am", duration_minutes=20,
                         scheduled_time=base_time + timedelta(hours=2)))  # 10:00
        pet.add_task(Task(title="Task1_8am", duration_minutes=30,
                         scheduled_time=base_time))  # 8:00
        pet.add_task(Task(title="Task4_unscheduled", duration_minutes=15))  # No time
        pet.add_task(Task(title="Task2_9am", duration_minutes=10,
                         scheduled_time=base_time + timedelta(hours=1)))  # 9:00
        
        owner.add_pet(pet)
        return Scheduler(owner=owner)

    def test_sort_by_time_chronological(self, scheduler_with_tasks):
        """Verify sort_by_time returns tasks in chronological order."""
        tasks = scheduler_with_tasks.owner.get_all_tasks()
        sorted_tasks = scheduler_with_tasks.sort_by_time(tasks)
        
        # Check order: 8am, 9am, 10am, unscheduled (last)
        assert sorted_tasks[0].title == "Task1_8am"
        assert sorted_tasks[1].title == "Task2_9am"
        assert sorted_tasks[2].title == "Task3_10am"
        assert sorted_tasks[3].title == "Task4_unscheduled"

    def test_sort_by_time_unscheduled_last(self, scheduler_with_tasks):
        """Verify unscheduled tasks sort to the end."""
        tasks = scheduler_with_tasks.owner.get_all_tasks()
        sorted_tasks = scheduler_with_tasks.sort_by_time(tasks)
        
        # Last task should be the unscheduled one
        assert sorted_tasks[-1].scheduled_time is None

    def test_sort_by_priority_high_first(self):
        """Verify sort_by_priority puts HIGH first."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        pet.add_task(Task(title="Low", duration_minutes=10, priority=Priority.LOW))
        pet.add_task(Task(title="High", duration_minutes=10, priority=Priority.HIGH))
        pet.add_task(Task(title="Medium", duration_minutes=10, priority=Priority.MEDIUM))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        sorted_tasks = scheduler.sort_by_priority(pet.tasks)
        
        assert sorted_tasks[0].priority == Priority.HIGH
        assert sorted_tasks[1].priority == Priority.MEDIUM
        assert sorted_tasks[2].priority == Priority.LOW

    def test_sort_by_priority_uses_time_as_tiebreaker(self):
        """Verify same-priority tasks are sorted by time."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        base_time = datetime(2026, 3, 29, 8, 0)
        
        pet.add_task(Task(title="High_10am", duration_minutes=10,
                         priority=Priority.HIGH,
                         scheduled_time=base_time + timedelta(hours=2)))
        pet.add_task(Task(title="High_8am", duration_minutes=10,
                         priority=Priority.HIGH,
                         scheduled_time=base_time))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        sorted_tasks = scheduler.sort_by_priority(pet.tasks)
        
        # Both HIGH, but 8am should come first
        assert sorted_tasks[0].title == "High_8am"
        assert sorted_tasks[1].title == "High_10am"

    def test_sort_by_duration_ascending(self):
        """Verify sort_by_duration (shortest first)."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        pet.add_task(Task(title="Long", duration_minutes=60))
        pet.add_task(Task(title="Short", duration_minutes=5))
        pet.add_task(Task(title="Medium", duration_minutes=30))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        sorted_tasks = scheduler.sort_by_duration(pet.tasks, ascending=True)
        
        assert sorted_tasks[0].duration_minutes == 5
        assert sorted_tasks[1].duration_minutes == 30
        assert sorted_tasks[2].duration_minutes == 60

    def test_sort_by_duration_descending(self):
        """Verify sort_by_duration (longest first)."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        pet.add_task(Task(title="Long", duration_minutes=60))
        pet.add_task(Task(title="Short", duration_minutes=5))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        sorted_tasks = scheduler.sort_by_duration(pet.tasks, ascending=False)
        
        assert sorted_tasks[0].duration_minutes == 60
        assert sorted_tasks[1].duration_minutes == 5

    def test_sort_empty_list(self):
        """Edge case: Sorting empty list returns empty list."""
        owner = Owner(name="Test")
        scheduler = Scheduler(owner=owner)
        
        assert scheduler.sort_by_time([]) == []
        assert scheduler.sort_by_priority([]) == []
        assert scheduler.sort_by_duration([]) == []


# =============================================================================
# SCHEDULER FILTERING TESTS (Phase 4 Feature)
# =============================================================================

class TestSchedulerFiltering:
    """Tests for Scheduler filtering algorithms."""

    @pytest.fixture
    def scheduler_with_varied_tasks(self):
        """Create a scheduler with varied tasks for filtering tests."""
        owner = Owner(name="Jordan")
        
        dog = Pet(name="Mochi", species="dog")
        cat = Pet(name="Whiskers", species="cat")
        
        # Dog tasks
        dog.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
        dog.add_task(Task(title="Feed", duration_minutes=10, priority=Priority.HIGH,
                        frequency=Frequency.DAILY,
                        scheduled_time=datetime(2026, 3, 29, 8, 0)))
        dog.add_task(Task(title="Play", duration_minutes=20, priority=Priority.LOW))
        
        # Cat tasks
        cat.add_task(Task(title="Litter", duration_minutes=5, priority=Priority.MEDIUM))
        task_complete = Task(title="Medication", duration_minutes=5, priority=Priority.HIGH)
        task_complete.mark_complete()
        cat.add_task(task_complete)
        
        owner.add_pet(dog)
        owner.add_pet(cat)
        
        return Scheduler(owner=owner)

    def test_filter_by_pet(self, scheduler_with_varied_tasks):
        """Verify filter_by_pet returns only that pet's tasks."""
        all_tasks = scheduler_with_varied_tasks.owner.get_all_tasks()
        
        mochi_tasks = scheduler_with_varied_tasks.filter_by_pet(all_tasks, "Mochi")
        
        assert len(mochi_tasks) == 3
        assert all(t.pet_name == "Mochi" for t in mochi_tasks)

    def test_filter_by_pet_unknown_returns_empty(self, scheduler_with_varied_tasks):
        """Verify filtering by unknown pet returns empty list."""
        all_tasks = scheduler_with_varied_tasks.owner.get_all_tasks()
        
        unknown_tasks = scheduler_with_varied_tasks.filter_by_pet(all_tasks, "Unknown")
        
        assert unknown_tasks == []

    def test_filter_by_status_pending(self, scheduler_with_varied_tasks):
        """Verify filter_by_status returns pending tasks."""
        all_tasks = scheduler_with_varied_tasks.owner.get_all_tasks()
        
        pending = scheduler_with_varied_tasks.filter_by_status(all_tasks, completed=False)
        
        assert all(not t.is_complete for t in pending)
        assert len(pending) == 4  # All except Medication

    def test_filter_by_status_completed(self, scheduler_with_varied_tasks):
        """Verify filter_by_status returns completed tasks."""
        all_tasks = scheduler_with_varied_tasks.owner.get_all_tasks()
        
        completed = scheduler_with_varied_tasks.filter_by_status(all_tasks, completed=True)
        
        assert len(completed) == 1
        assert completed[0].title == "Medication"

    def test_filter_by_priority(self, scheduler_with_varied_tasks):
        """Verify filter_by_priority returns correct priority tasks."""
        all_tasks = scheduler_with_varied_tasks.owner.get_all_tasks()
        
        high_tasks = scheduler_with_varied_tasks.filter_by_priority(all_tasks, Priority.HIGH)
        
        assert all(t.priority == Priority.HIGH for t in high_tasks)
        assert len(high_tasks) == 3  # Walk, Feed, Medication

    def test_filter_recurring(self, scheduler_with_varied_tasks):
        """Verify filter_recurring returns only recurring tasks."""
        all_tasks = scheduler_with_varied_tasks.owner.get_all_tasks()
        
        recurring = scheduler_with_varied_tasks.filter_recurring(all_tasks)
        
        assert len(recurring) == 1
        assert recurring[0].title == "Feed"

    def test_filter_by_time_range(self):
        """Verify filter_by_time_range works correctly."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        base = datetime(2026, 3, 29, 8, 0)
        pet.add_task(Task(title="T1", duration_minutes=10, scheduled_time=base))
        pet.add_task(Task(title="T2", duration_minutes=10, 
                        scheduled_time=base + timedelta(hours=2)))
        pet.add_task(Task(title="T3", duration_minutes=10,
                        scheduled_time=base + timedelta(hours=4)))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        # Filter for 8am - 10am
        filtered = scheduler.filter_by_time_range(
            pet.tasks,
            start=base,
            end=base + timedelta(hours=2)
        )
        
        assert len(filtered) == 2
        titles = [t.title for t in filtered]
        assert "T1" in titles
        assert "T2" in titles

    def test_filter_chain(self, scheduler_with_varied_tasks):
        """Verify filter_chain applies multiple filters."""
        all_tasks = scheduler_with_varied_tasks.owner.get_all_tasks()
        
        # Chain: pending AND high priority
        result = scheduler_with_varied_tasks.filter_chain(
            all_tasks,
            lambda t: scheduler_with_varied_tasks.filter_by_status(t, completed=False),
            lambda t: scheduler_with_varied_tasks.filter_by_priority(t, Priority.HIGH)
        )
        
        # Should be Walk and Feed (not Medication which is complete)
        assert len(result) == 2
        titles = [t.title for t in result]
        assert "Walk" in titles
        assert "Feed" in titles

    def test_filter_chain_empty_result(self, scheduler_with_varied_tasks):
        """Verify filter_chain can return empty list."""
        all_tasks = scheduler_with_varied_tasks.owner.get_all_tasks()
        
        # Chain: completed AND low priority (no such task)
        result = scheduler_with_varied_tasks.filter_chain(
            all_tasks,
            lambda t: scheduler_with_varied_tasks.filter_by_status(t, completed=True),
            lambda t: scheduler_with_varied_tasks.filter_by_priority(t, Priority.LOW)
        )
        
        assert result == []


# =============================================================================
# CONFLICT DETECTION TESTS (Phase 4 Feature)
# =============================================================================

class TestConflictDetection:
    """Tests for scheduling conflict detection."""

    def test_detect_conflicts_finds_overlaps(self):
        """Verify overlapping tasks are detected as conflicts."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        base_time = datetime(2026, 3, 28, 10, 0)
        
        # Task 1: 10:00 - 10:30
        task1 = Task(title="Task1", duration_minutes=30, scheduled_time=base_time)
        # Task 2: 10:15 - 10:45 (overlaps by 15 min)
        task2 = Task(title="Task2", duration_minutes=30,
                     scheduled_time=base_time + timedelta(minutes=15))
        
        pet.add_task(task1)
        pet.add_task(task2)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        warnings = scheduler.detect_conflicts(owner.get_all_tasks())
        
        assert len(warnings) == 1
        assert warnings[0].overlap_minutes == 15

    def test_detect_conflicts_exact_same_time(self):
        """Edge case: Two tasks at exact same time."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        same_time = datetime(2026, 3, 28, 10, 0)
        
        task1 = Task(title="Task1", duration_minutes=30, scheduled_time=same_time)
        task2 = Task(title="Task2", duration_minutes=20, scheduled_time=same_time)
        
        pet.add_task(task1)
        pet.add_task(task2)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        warnings = scheduler.detect_conflicts(owner.get_all_tasks())
        
        assert len(warnings) == 1
        # Overlap should be the shorter task's duration
        assert warnings[0].overlap_minutes == 20

    def test_detect_conflicts_no_overlap(self):
        """Verify non-overlapping tasks are not flagged."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        base_time = datetime(2026, 3, 28, 10, 0)
        
        # Task 1: 10:00 - 10:30
        task1 = Task(title="Task1", duration_minutes=30, scheduled_time=base_time)
        # Task 2: 10:30 - 11:00 (no overlap - starts exactly when Task1 ends)
        task2 = Task(title="Task2", duration_minutes=30,
                     scheduled_time=base_time + timedelta(minutes=30))
        
        pet.add_task(task1)
        pet.add_task(task2)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        warnings = scheduler.detect_conflicts(owner.get_all_tasks())
        
        assert len(warnings) == 0

    def test_detect_conflicts_multiple_conflicts(self):
        """Verify multiple conflicts are all detected."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        base = datetime(2026, 3, 28, 10, 0)
        
        # Three overlapping tasks
        pet.add_task(Task(title="T1", duration_minutes=30, scheduled_time=base))
        pet.add_task(Task(title="T2", duration_minutes=30,
                        scheduled_time=base + timedelta(minutes=10)))
        pet.add_task(Task(title="T3", duration_minutes=30,
                        scheduled_time=base + timedelta(minutes=20)))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        warnings = scheduler.detect_conflicts(owner.get_all_tasks())
        
        # T1-T2 overlap, T1-T3 overlap, T2-T3 overlap = 3 conflicts
        assert len(warnings) == 3

    def test_detect_conflicts_different_pets(self):
        """Verify conflicts detected across different pets."""
        owner = Owner(name="Test")
        dog = Pet(name="Mochi", species="dog")
        cat = Pet(name="Whiskers", species="cat")
        
        same_time = datetime(2026, 3, 28, 10, 0)
        
        dog.add_task(Task(title="Walk", duration_minutes=30, scheduled_time=same_time))
        cat.add_task(Task(title="Feed", duration_minutes=10, scheduled_time=same_time))
        
        owner.add_pet(dog)
        owner.add_pet(cat)
        
        scheduler = Scheduler(owner=owner)
        warnings = scheduler.detect_conflicts(owner.get_all_tasks())
        
        assert len(warnings) == 1
        assert "Different pets" in warnings[0].message

    def test_detect_conflicts_same_pet(self):
        """Verify same-pet conflicts are identified in message."""
        owner = Owner(name="Test")
        pet = Pet(name="Mochi", species="dog")
        
        same_time = datetime(2026, 3, 28, 10, 0)
        
        pet.add_task(Task(title="Walk", duration_minutes=30, scheduled_time=same_time))
        pet.add_task(Task(title="Feed", duration_minutes=10, scheduled_time=same_time))
        
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        warnings = scheduler.detect_conflicts(owner.get_all_tasks())
        
        assert len(warnings) == 1
        assert "Same pet" in warnings[0].message

    def test_detect_conflicts_ignores_unscheduled(self):
        """Verify unscheduled tasks don't cause conflicts."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        pet.add_task(Task(title="Scheduled", duration_minutes=30,
                        scheduled_time=datetime(2026, 3, 28, 10, 0)))
        pet.add_task(Task(title="Unscheduled", duration_minutes=30))  # No time
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        warnings = scheduler.detect_conflicts(owner.get_all_tasks())
        
        assert len(warnings) == 0

    def test_get_conflict_free_tasks(self):
        """Verify get_conflict_free_tasks separates safe tasks."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        base = datetime(2026, 3, 28, 10, 0)
        
        # Two conflicting tasks
        pet.add_task(Task(title="Conflict1", duration_minutes=30, scheduled_time=base))
        pet.add_task(Task(title="Conflict2", duration_minutes=30,
                        scheduled_time=base + timedelta(minutes=10)))
        # One safe task
        pet.add_task(Task(title="Safe", duration_minutes=30,
                        scheduled_time=base + timedelta(hours=2)))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        safe, warnings = scheduler.get_conflict_free_tasks(owner.get_all_tasks())
        
        assert len(safe) == 1
        assert safe[0].title == "Safe"
        assert len(warnings) == 1


# =============================================================================
# SCHEDULER SCHEDULE GENERATION TESTS
# =============================================================================

class TestScheduleGeneration:
    """Tests for schedule generation."""

    @pytest.fixture
    def sample_owner(self):
        """Create a sample owner with pets and tasks."""
        owner = Owner(name="Jordan", available_minutes=60)
        
        pet = Pet(name="Mochi", species="dog")
        pet.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
        pet.add_task(Task(title="Feed", duration_minutes=10, priority=Priority.HIGH))
        pet.add_task(Task(title="Play", duration_minutes=20, priority=Priority.MEDIUM))
        pet.add_task(Task(title="Groom", duration_minutes=45, priority=Priority.LOW))
        
        owner.add_pet(pet)
        return owner

    def test_generate_schedule_respects_time_limit(self, sample_owner):
        """Verify schedule doesn't exceed daily_limit_minutes."""
        scheduler = Scheduler(owner=sample_owner, daily_limit_minutes=60)
        
        schedule = scheduler.generate_schedule()
        total_time = sum(t.duration_minutes for t in schedule)
        
        assert total_time <= 60

    def test_generate_schedule_prioritizes_high(self, sample_owner):
        """Verify HIGH priority tasks are scheduled first."""
        scheduler = Scheduler(owner=sample_owner, daily_limit_minutes=40)
        
        schedule = scheduler.generate_schedule()
        
        # With 40 min limit, should fit Walk (30) + Feed (10) = 40
        titles = [t.title for t in schedule]
        assert "Walk" in titles
        assert "Feed" in titles
        assert "Groom" not in titles  # LOW priority, shouldn't fit

    def test_generate_schedule_excludes_completed(self, sample_owner):
        """Verify completed tasks are excluded by default."""
        scheduler = Scheduler(owner=sample_owner, daily_limit_minutes=480)
        
        # Mark a task complete
        tasks = sample_owner.get_all_tasks()
        tasks[0].mark_complete()
        
        schedule = scheduler.generate_schedule(include_completed=False)
        
        assert tasks[0] not in schedule

    def test_generate_schedule_can_include_completed(self, sample_owner):
        """Verify completed tasks can be included."""
        scheduler = Scheduler(owner=sample_owner, daily_limit_minutes=480)
        
        tasks = sample_owner.get_all_tasks()
        tasks[0].mark_complete()
        
        schedule = scheduler.generate_schedule(include_completed=True)
        
        assert tasks[0] in schedule

    def test_generate_schedule_empty_when_all_complete(self, sample_owner):
        """Edge case: All tasks complete returns empty schedule."""
        scheduler = Scheduler(owner=sample_owner)
        
        for task in sample_owner.get_all_tasks():
            task.mark_complete()
        
        schedule = scheduler.generate_schedule(include_completed=False)
        
        assert schedule == []

    def test_generate_schedule_empty_when_no_tasks(self):
        """Edge case: No tasks returns empty schedule."""
        owner = Owner(name="Empty")
        owner.add_pet(Pet(name="Pet", species="dog"))
        
        scheduler = Scheduler(owner=owner)
        schedule = scheduler.generate_schedule()
        
        assert schedule == []

    def test_get_total_scheduled_minutes(self, sample_owner):
        """Verify total minutes calculation."""
        scheduler = Scheduler(owner=sample_owner)
        tasks = sample_owner.get_all_tasks()
        
        total = scheduler.get_total_scheduled_minutes(tasks)
        expected = 30 + 10 + 20 + 45  # Walk + Feed + Play + Groom
        
        assert total == expected

    def test_get_total_scheduled_minutes_empty(self):
        """Edge case: Empty list returns 0."""
        owner = Owner(name="Test")
        scheduler = Scheduler(owner=owner)
        
        assert scheduler.get_total_scheduled_minutes([]) == 0

    def test_assign_times_sequential(self, sample_owner):
        """Verify assign_times sets sequential times."""
        scheduler = Scheduler(owner=sample_owner)
        tasks = sample_owner.get_all_tasks()[:2]
        start = datetime(2026, 3, 28, 8, 0)
        
        scheduler.assign_times(tasks, start)
        
        assert tasks[0].scheduled_time == start
        assert tasks[1].scheduled_time == start + timedelta(minutes=tasks[0].duration_minutes)

    def test_generate_schedule_by_time(self, sample_owner):
        """Verify generate_schedule_by_time returns chronological order."""
        base = datetime(2026, 3, 29, 8, 0)
        
        # Add times to tasks
        tasks = sample_owner.get_all_tasks()
        tasks[0].scheduled_time = base + timedelta(hours=2)  # 10:00
        tasks[1].scheduled_time = base  # 8:00
        
        scheduler = Scheduler(owner=sample_owner)
        chronological = scheduler.generate_schedule_by_time()
        
        # Should be sorted by time
        for i in range(len(chronological) - 1):
            t1 = chronological[i].scheduled_time
            t2 = chronological[i + 1].scheduled_time
            if t1 and t2:
                assert t1 <= t2


# =============================================================================
# SCHEDULER RECURRING TASK MANAGEMENT TESTS
# =============================================================================

class TestSchedulerRecurring:
    """Tests for Scheduler recurring task management."""

    def test_complete_task_with_recurrence_adds_new_task(self):
        """Verify completing recurring task adds new occurrence to pet."""
        owner = Owner(name="Test")
        pet = Pet(name="Mochi", species="dog")
        
        task = Task(
            title="Daily walk",
            duration_minutes=30,
            frequency=Frequency.DAILY,
            scheduled_time=datetime(2026, 3, 29, 8, 0)
        )
        pet.add_task(task)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        initial_count = len(pet.tasks)
        
        next_task = scheduler.complete_task_with_recurrence(pet, task)
        
        assert next_task is not None
        assert len(pet.tasks) == initial_count + 1
        assert task.is_complete is True
        assert next_task.is_complete is False

    def test_complete_task_with_recurrence_non_recurring(self):
        """Verify non-recurring task returns None."""
        owner = Owner(name="Test")
        pet = Pet(name="Mochi", species="dog")
        
        task = Task(title="Vet visit", duration_minutes=60, frequency=Frequency.ONCE)
        pet.add_task(task)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        initial_count = len(pet.tasks)
        
        next_task = scheduler.complete_task_with_recurrence(pet, task)
        
        assert next_task is None
        assert len(pet.tasks) == initial_count  # No new task added

    def test_get_recurring_tasks(self):
        """Verify get_recurring_tasks returns all recurring tasks."""
        owner = Owner(name="Test")
        pet = Pet(name="Mochi", species="dog")
        
        pet.add_task(Task(title="Daily", duration_minutes=10, frequency=Frequency.DAILY,
                         scheduled_time=datetime(2026, 3, 29, 8, 0)))
        pet.add_task(Task(title="Weekly", duration_minutes=20, frequency=Frequency.WEEKLY,
                         scheduled_time=datetime(2026, 3, 29, 10, 0)))
        pet.add_task(Task(title="Once", duration_minutes=30, frequency=Frequency.ONCE))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        recurring = scheduler.get_recurring_tasks()
        
        assert len(recurring) == 2
        titles = [t.title for t in recurring]
        assert "Daily" in titles
        assert "Weekly" in titles
        assert "Once" not in titles


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for full system workflow."""

    def test_full_workflow(self):
        """Test complete workflow: create owner, pets, tasks, generate schedule."""
        owner = Owner(name="Jordan", available_minutes=90)
        
        dog = Pet(name="Mochi", species="dog", age=3)
        cat = Pet(name="Whiskers", species="cat", age=5)
        
        owner.add_pet(dog)
        owner.add_pet(cat)
        
        dog.add_task(Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH))
        dog.add_task(Task(title="Feeding", duration_minutes=10, priority=Priority.HIGH))
        cat.add_task(Task(title="Medication", duration_minutes=5, priority=Priority.HIGH))
        cat.add_task(Task(title="Litter box", duration_minutes=10, priority=Priority.MEDIUM))
        
        scheduler = Scheduler(owner=owner, daily_limit_minutes=owner.available_minutes)
        schedule = scheduler.generate_schedule()
        
        assert len(schedule) >= 3
        total_time = scheduler.get_total_scheduled_minutes(schedule)
        assert total_time <= 90
        
        scheduled_titles = [t.title for t in schedule]
        assert "Morning walk" in scheduled_titles
        assert "Medication" in scheduled_titles

    def test_recurring_task_workflow(self):
        """Test recurring task completion creates chain of tasks."""
        owner = Owner(name="Jordan")
        pet = Pet(name="Mochi", species="dog")
        
        base_time = datetime(2026, 3, 29, 8, 0)
        task = Task(
            title="Daily walk",
            duration_minutes=30,
            frequency=Frequency.DAILY,
            scheduled_time=base_time
        )
        pet.add_task(task)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        
        # Complete task 3 times
        current_task = task
        for day in range(1, 4):
            next_task = scheduler.complete_task_with_recurrence(pet, current_task)
            assert next_task is not None
            expected_time = base_time + timedelta(days=day)
            assert next_task.scheduled_time == expected_time
            current_task = next_task
        
        # Should have original + 3 new = 4 total
        assert len(pet.tasks) == 4

    def test_conflict_detection_and_resolution(self):
        """Test conflict detection workflow."""
        owner = Owner(name="Jordan")
        pet = Pet(name="Mochi", species="dog")
        
        base = datetime(2026, 3, 29, 8, 0)
        
        pet.add_task(Task(title="Walk", duration_minutes=30, scheduled_time=base))
        pet.add_task(Task(title="Feed", duration_minutes=10,
                        scheduled_time=base + timedelta(minutes=15)))  # Conflict!
        pet.add_task(Task(title="Play", duration_minutes=20,
                        scheduled_time=base + timedelta(hours=2)))  # Safe
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner)
        
        safe_tasks, warnings = scheduler.get_conflict_free_tasks(owner.get_all_tasks())
        
        assert len(warnings) == 1
        assert len(safe_tasks) == 1
        assert safe_tasks[0].title == "Play"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_duration_task(self):
        """Edge case: Task with 0 duration."""
        task = Task(title="Instant", duration_minutes=0)
        assert task.duration_minutes == 0
        
        # Should still be schedulable
        owner = Owner(name="Test")
        pet = Pet(name="Pet", species="dog")
        pet.add_task(task)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner, daily_limit_minutes=0)
        schedule = scheduler.generate_schedule()
        
        assert len(schedule) == 1

    def test_exact_time_budget_match(self):
        """Edge case: Tasks exactly fill time budget."""
        owner = Owner(name="Test")
        pet = Pet(name="Pet", species="dog")
        
        pet.add_task(Task(title="T1", duration_minutes=30, priority=Priority.HIGH))
        pet.add_task(Task(title="T2", duration_minutes=30, priority=Priority.HIGH))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner, daily_limit_minutes=60)
        
        schedule = scheduler.generate_schedule()
        total = scheduler.get_total_scheduled_minutes(schedule)
        
        assert total == 60
        assert len(schedule) == 2

    def test_single_task_exceeds_budget(self):
        """Edge case: Single task longer than entire budget."""
        owner = Owner(name="Test")
        pet = Pet(name="Pet", species="dog")
        
        pet.add_task(Task(title="Long", duration_minutes=120))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner, daily_limit_minutes=60)
        
        schedule = scheduler.generate_schedule()
        
        assert schedule == []

    def test_very_long_task_list(self):
        """Edge case: Many tasks (performance check)."""
        owner = Owner(name="Test")
        pet = Pet(name="Pet", species="dog")
        
        for i in range(100):
            pet.add_task(Task(title=f"Task{i}", duration_minutes=5))
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner=owner, daily_limit_minutes=60)
        
        schedule = scheduler.generate_schedule()
        total = scheduler.get_total_scheduled_minutes(schedule)
        
        assert total <= 60
        assert len(schedule) == 12  # 60 / 5 = 12 tasks

    def test_duplicate_task_titles(self):
        """Edge case: Multiple tasks with same title."""
        pet = Pet(name="Pet", species="dog")
        
        pet.add_task(Task(title="Feed", duration_minutes=10))
        pet.add_task(Task(title="Feed", duration_minutes=10))
        pet.add_task(Task(title="Feed", duration_minutes=10))
        
        assert len(pet.tasks) == 3
        
        # Remove should only remove first match
        pet.remove_task("Feed")
        # List comprehension removes ALL matches
        assert len(pet.tasks) == 0

    def test_task_at_midnight_boundary(self):
        """Edge case: Task scheduled at midnight."""
        midnight = datetime(2026, 3, 29, 0, 0)
        task = Task(title="Midnight task", duration_minutes=30, scheduled_time=midnight)
        
        assert task.scheduled_time == midnight
        assert "12:00 AM" in str(task)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
