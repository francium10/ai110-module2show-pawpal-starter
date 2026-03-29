"""
PawPal+ Test Suite

Run tests with: python -m pytest tests/ -v
"""

import pytest
from datetime import datetime, timedelta

# Import the classes we're testing
from pawpal_system import Task, Pet, Owner, Scheduler, Priority


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
        assert task.priority == Priority.MEDIUM  # default
        assert task.is_complete is False  # default
        assert task.is_recurring is False  # default

    def test_mark_complete_changes_status(self):
        """Verify that mark_complete() changes the task's status."""
        task = Task(title="Feed the cat", duration_minutes=10)
        
        assert task.is_complete is False
        task.mark_complete()
        assert task.is_complete is True

    def test_mark_incomplete_resets_status(self):
        """Verify that mark_incomplete() resets a completed task."""
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

    def test_task_string_representation(self):
        """Verify __str__ produces readable output."""
        task = Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH)
        task_str = str(task)
        
        assert "Morning walk" in task_str
        assert "30min" in task_str
        assert "High" in task_str


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

    def test_add_pet(self):
        """Verify pets can be added to owner."""
        owner = Owner(name="Jordan")
        pet = Pet(name="Mochi", species="dog")
        
        owner.add_pet(pet)
        assert len(owner.pets) == 1
        assert owner.pets[0].name == "Mochi"

    def test_remove_pet(self):
        """Verify pets can be removed by name."""
        owner = Owner(name="Jordan")
        owner.add_pet(Pet(name="Mochi", species="dog"))
        owner.add_pet(Pet(name="Whiskers", species="cat"))
        
        removed = owner.remove_pet("Mochi")
        assert removed is True
        assert len(owner.pets) == 1
        assert owner.pets[0].name == "Whiskers"

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


# =============================================================================
# SCHEDULER TESTS
# =============================================================================

class TestScheduler:
    """Tests for the Scheduler class."""

    @pytest.fixture
    def sample_owner(self):
        """Create a sample owner with pets and tasks for testing."""
        owner = Owner(name="Jordan", available_minutes=60)
        
        pet = Pet(name="Mochi", species="dog")
        pet.add_task(Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
        pet.add_task(Task(title="Feed", duration_minutes=10, priority=Priority.HIGH))
        pet.add_task(Task(title="Play", duration_minutes=20, priority=Priority.MEDIUM))
        pet.add_task(Task(title="Groom", duration_minutes=45, priority=Priority.LOW))
        
        owner.add_pet(pet)
        return owner

    def test_sort_by_priority_high_first(self, sample_owner):
        """Verify tasks are sorted with HIGH priority first."""
        scheduler = Scheduler(owner=sample_owner)
        tasks = sample_owner.get_all_tasks()
        
        sorted_tasks = scheduler.sort_by_priority(tasks)
        
        # First tasks should be HIGH priority
        assert sorted_tasks[0].priority == Priority.HIGH
        assert sorted_tasks[1].priority == Priority.HIGH
        # Last should be LOW
        assert sorted_tasks[-1].priority == Priority.LOW

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
        
        # Completed task should not be in schedule
        assert tasks[0] not in schedule

    def test_detect_conflicts_finds_overlaps(self):
        """Verify overlapping tasks are detected as conflicts."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        base_time = datetime(2026, 3, 28, 10, 0)
        
        # Task 1: 10:00 - 10:30
        task1 = Task(title="Task1", duration_minutes=30, scheduled_time=base_time)
        # Task 2: 10:15 - 10:45 (overlaps with Task1)
        task2 = Task(title="Task2", duration_minutes=30, 
                     scheduled_time=base_time + timedelta(minutes=15))
        
        pet.add_task(task1)
        pet.add_task(task2)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        conflicts = scheduler.detect_conflicts(owner.get_all_tasks())
        
        assert len(conflicts) == 2
        assert task1 in conflicts
        assert task2 in conflicts

    def test_detect_conflicts_no_overlap(self):
        """Verify non-overlapping tasks are not flagged as conflicts."""
        owner = Owner(name="Test")
        pet = Pet(name="TestPet", species="dog")
        
        base_time = datetime(2026, 3, 28, 10, 0)
        
        # Task 1: 10:00 - 10:30
        task1 = Task(title="Task1", duration_minutes=30, scheduled_time=base_time)
        # Task 2: 10:30 - 11:00 (no overlap)
        task2 = Task(title="Task2", duration_minutes=30,
                     scheduled_time=base_time + timedelta(minutes=30))
        
        pet.add_task(task1)
        pet.add_task(task2)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        conflicts = scheduler.detect_conflicts(owner.get_all_tasks())
        
        assert len(conflicts) == 0

    def test_get_total_scheduled_minutes(self, sample_owner):
        """Verify total minutes calculation is correct."""
        scheduler = Scheduler(owner=sample_owner)
        tasks = sample_owner.get_all_tasks()
        
        total = scheduler.get_total_scheduled_minutes(tasks)
        expected = 30 + 10 + 20 + 45  # Walk + Feed + Play + Groom
        
        assert total == expected

    def test_assign_times_sequential(self, sample_owner):
        """Verify assign_times sets sequential scheduled_time."""
        scheduler = Scheduler(owner=sample_owner)
        tasks = sample_owner.get_all_tasks()[:2]  # Just first 2 tasks
        start = datetime(2026, 3, 28, 8, 0)
        
        scheduler.assign_times(tasks, start)
        
        assert tasks[0].scheduled_time == start
        assert tasks[1].scheduled_time == start + timedelta(minutes=tasks[0].duration_minutes)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full system workflow."""

    def test_full_workflow(self):
        """Test complete workflow: create owner, pets, tasks, generate schedule."""
        # Setup
        owner = Owner(name="Jordan", available_minutes=90)
        
        dog = Pet(name="Mochi", species="dog", age=3)
        cat = Pet(name="Whiskers", species="cat", age=5)
        
        owner.add_pet(dog)
        owner.add_pet(cat)
        
        # Add tasks
        dog.add_task(Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH))
        dog.add_task(Task(title="Feeding", duration_minutes=10, priority=Priority.HIGH))
        cat.add_task(Task(title="Medication", duration_minutes=5, priority=Priority.HIGH))
        cat.add_task(Task(title="Litter box", duration_minutes=10, priority=Priority.MEDIUM))
        
        # Generate schedule
        scheduler = Scheduler(owner=owner, daily_limit_minutes=owner.available_minutes)
        schedule = scheduler.generate_schedule()
        
        # Verify
        assert len(schedule) >= 3  # At least HIGH priority tasks
        total_time = scheduler.get_total_scheduled_minutes(schedule)
        assert total_time <= 90
        
        # Verify HIGH priority tasks are scheduled
        scheduled_titles = [t.title for t in schedule]
        assert "Morning walk" in scheduled_titles
        assert "Medication" in scheduled_titles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
