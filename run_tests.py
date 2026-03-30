#!/usr/bin/env python3
"""
PawPal+ Test Runner (No pytest required)

Run with: python tests/run_tests.py
"""

# =============================================================================
# FIX: Add parent directory to path so imports work from tests/ folder
# =============================================================================
from pawpal_system import (
    Task, Pet, Owner, Scheduler,
    Priority, Frequency, ConflictWarning
)
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


passed = 0
failed = 0
errors = []


def test(name):
    """Decorator to register and run a test."""
    def decorator(func):
        global passed, failed, errors
        try:
            func()
            print(f"  ✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {name}")
            print(f"      AssertionError: {e}")
            failed += 1
            errors.append((name, str(e)))
        except Exception as e:
            print(f"  ✗ {name}")
            print(f"      {type(e).__name__}: {e}")
            failed += 1
            errors.append((name, str(e)))
        return func
    return decorator


def section(name):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print('='*60)


# =============================================================================
# TASK TESTS
# =============================================================================
section("TASK TESTS")


@test("Task creation with defaults")
def test_task_creation_with_defaults():
    task = Task(title="Walk the dog", duration_minutes=30)
    assert task.title == "Walk the dog"
    assert task.duration_minutes == 30
    assert task.priority == Priority.MEDIUM
    assert task.frequency == Frequency.ONCE
    assert task.is_complete is False
    assert task.is_recurring is False


@test("Task mark_complete changes status")
def test_mark_complete():
    task = Task(title="Feed", duration_minutes=10)
    assert task.is_complete is False
    task.mark_complete()
    assert task.is_complete is True


@test("Task mark_incomplete resets status")
def test_mark_incomplete():
    task = Task(title="Groom", duration_minutes=45)
    task.mark_complete()
    assert task.is_complete is True
    task.mark_incomplete()
    assert task.is_complete is False


@test("Task reschedule updates time")
def test_reschedule():
    task = Task(title="Vet", duration_minutes=60)
    new_time = datetime(2026, 3, 28, 14, 0)
    assert task.scheduled_time is None
    task.reschedule(new_time)
    assert task.scheduled_time == new_time


@test("Task is_recurring property")
def test_is_recurring():
    once = Task(title="T1", duration_minutes=10, frequency=Frequency.ONCE)
    daily = Task(title="T2", duration_minutes=10, frequency=Frequency.DAILY)
    assert once.is_recurring is False
    assert daily.is_recurring is True


# =============================================================================
# RECURRING TASK TESTS
# =============================================================================
section("RECURRING TASK TESTS")


@test("Daily task creates next day occurrence")
def test_daily_recurrence():
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
    assert next_task.is_complete is False


@test("Weekly task creates next week occurrence")
def test_weekly_recurrence():
    base_time = datetime(2026, 3, 29, 10, 0)
    task = Task(
        title="Grooming",
        duration_minutes=45,
        frequency=Frequency.WEEKLY,
        scheduled_time=base_time
    )
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.scheduled_time == base_time + timedelta(days=7)


@test("Biweekly task creates two weeks later")
def test_biweekly_recurrence():
    base_time = datetime(2026, 3, 29, 14, 0)
    task = Task(
        title="Deep clean",
        duration_minutes=60,
        frequency=Frequency.BIWEEKLY,
        scheduled_time=base_time
    )
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.scheduled_time == base_time + timedelta(days=14)


@test("Non-recurring task returns None on completion")
def test_non_recurring_returns_none():
    task = Task(title="Vet visit", duration_minutes=60,
                frequency=Frequency.ONCE)
    result = task.mark_complete()
    assert result is None


@test("Recurring task preserves pet_name")
def test_recurring_preserves_pet():
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


# =============================================================================
# PET TESTS
# =============================================================================
section("PET TESTS")


@test("Pet creation")
def test_pet_creation():
    pet = Pet(name="Mochi", species="dog", age=3)
    assert pet.name == "Mochi"
    assert pet.species == "dog"
    assert pet.age == 3
    assert pet.tasks == []


@test("Pet add_task increases count and sets pet_name")
def test_pet_add_task():
    pet = Pet(name="Buddy", species="dog")
    task = Task(title="Walk", duration_minutes=30)
    assert task.pet_name is None
    pet.add_task(task)
    assert len(pet.tasks) == 1
    assert task.pet_name == "Buddy"


@test("Pet remove_task by title")
def test_pet_remove_task():
    pet = Pet(name="Max", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=30))
    pet.add_task(Task(title="Feed", duration_minutes=10))
    assert len(pet.tasks) == 2
    removed = pet.remove_task("Walk")
    assert removed is True
    assert len(pet.tasks) == 1


@test("Pet remove nonexistent task returns False")
def test_pet_remove_nonexistent():
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task(title="Feed", duration_minutes=5))
    removed = pet.remove_task("Unknown")
    assert removed is False


@test("Pet get_pending_tasks excludes completed")
def test_pet_pending_tasks():
    pet = Pet(name="Rex", species="dog")
    task1 = Task(title="Walk", duration_minutes=30)
    task2 = Task(title="Feed", duration_minutes=10)
    task2.mark_complete()
    pet.add_task(task1)
    pet.add_task(task2)
    pending = pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].title == "Walk"


@test("Pet with no tasks returns empty lists")
def test_pet_no_tasks():
    pet = Pet(name="Lonely", species="cat")
    assert pet.tasks == []
    assert pet.get_pending_tasks() == []
    assert pet.get_completed_tasks() == []


# =============================================================================
# OWNER TESTS
# =============================================================================
section("OWNER TESTS")


@test("Owner creation with defaults")
def test_owner_creation():
    owner = Owner(name="Jordan")
    assert owner.name == "Jordan"
    assert owner.available_minutes == 480
    assert owner.pets == []


@test("Owner add and remove pet")
def test_owner_add_remove_pet():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_pet(Pet(name="Whiskers", species="cat"))
    assert len(owner.pets) == 2
    removed = owner.remove_pet("Mochi")
    assert removed is True
    assert len(owner.pets) == 1


@test("Owner get_pet by name")
def test_owner_get_pet():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_pet(Pet(name="Whiskers", species="cat"))
    pet = owner.get_pet("Whiskers")
    assert pet is not None
    assert pet.species == "cat"


@test("Owner get_pet returns None for unknown")
def test_owner_get_unknown_pet():
    owner = Owner(name="Jordan")
    pet = owner.get_pet("Unknown")
    assert pet is None


@test("Owner get_all_tasks across pets")
def test_owner_all_tasks():
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


@test("Owner with no pets returns empty")
def test_owner_no_pets():
    owner = Owner(name="Empty")
    assert owner.pets == []
    assert owner.get_all_tasks() == []


# =============================================================================
# SCHEDULER SORTING TESTS
# =============================================================================
section("SCHEDULER SORTING TESTS")


@test("Sort by time (chronological)")
def test_sort_by_time():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    base = datetime(2026, 3, 29, 8, 0)
    pet.add_task(Task(title="Later", duration_minutes=10,
                 scheduled_time=base + timedelta(hours=2)))
    pet.add_task(Task(title="First", duration_minutes=10, scheduled_time=base))
    pet.add_task(Task(title="Unscheduled", duration_minutes=10))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    sorted_tasks = scheduler.sort_by_time(pet.tasks)
    assert sorted_tasks[0].title == "First"
    assert sorted_tasks[1].title == "Later"
    assert sorted_tasks[2].title == "Unscheduled"


@test("Sort by priority (HIGH first)")
def test_sort_by_priority():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(Task(title="Low", duration_minutes=10, priority=Priority.LOW))
    pet.add_task(
        Task(title="High", duration_minutes=10, priority=Priority.HIGH))
    pet.add_task(Task(title="Medium", duration_minutes=10,
                 priority=Priority.MEDIUM))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    sorted_tasks = scheduler.sort_by_priority(pet.tasks)
    assert sorted_tasks[0].priority == Priority.HIGH
    assert sorted_tasks[1].priority == Priority.MEDIUM
    assert sorted_tasks[2].priority == Priority.LOW


@test("Sort by duration (shortest first)")
def test_sort_by_duration():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(Task(title="Long", duration_minutes=60))
    pet.add_task(Task(title="Short", duration_minutes=5))
    pet.add_task(Task(title="Medium", duration_minutes=30))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    sorted_tasks = scheduler.sort_by_duration(pet.tasks, ascending=True)
    assert sorted_tasks[0].duration_minutes == 5
    assert sorted_tasks[1].duration_minutes == 30
    assert sorted_tasks[2].duration_minutes == 60


@test("Sort empty list returns empty")
def test_sort_empty():
    owner = Owner(name="Test")
    scheduler = Scheduler(owner=owner)
    assert scheduler.sort_by_time([]) == []
    assert scheduler.sort_by_priority([]) == []


# =============================================================================
# SCHEDULER FILTERING TESTS
# =============================================================================
section("SCHEDULER FILTERING TESTS")


@test("Filter by pet")
def test_filter_by_pet():
    owner = Owner(name="Test")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Whiskers", species="cat")
    dog.add_task(Task(title="Walk", duration_minutes=30))
    cat.add_task(Task(title="Feed", duration_minutes=10))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner=owner)
    mochi_tasks = scheduler.filter_by_pet(owner.get_all_tasks(), "Mochi")
    assert len(mochi_tasks) == 1
    assert mochi_tasks[0].title == "Walk"


@test("Filter by status")
def test_filter_by_status():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    task1 = Task(title="Pending", duration_minutes=10)
    task2 = Task(title="Done", duration_minutes=10)
    task2.mark_complete()
    pet.add_task(task1)
    pet.add_task(task2)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    pending = scheduler.filter_by_status(pet.tasks, completed=False)
    completed = scheduler.filter_by_status(pet.tasks, completed=True)
    assert len(pending) == 1
    assert len(completed) == 1


@test("Filter by priority")
def test_filter_by_priority():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(
        Task(title="High1", duration_minutes=10, priority=Priority.HIGH))
    pet.add_task(
        Task(title="High2", duration_minutes=10, priority=Priority.HIGH))
    pet.add_task(Task(title="Low", duration_minutes=10, priority=Priority.LOW))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    high = scheduler.filter_by_priority(pet.tasks, Priority.HIGH)
    assert len(high) == 2


@test("Filter recurring tasks")
def test_filter_recurring():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(Task(title="Daily", duration_minutes=10, frequency=Frequency.DAILY,
                      scheduled_time=datetime(2026, 3, 29, 8, 0)))
    pet.add_task(Task(title="Once", duration_minutes=10,
                 frequency=Frequency.ONCE))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    recurring = scheduler.filter_recurring(pet.tasks)
    assert len(recurring) == 1
    assert recurring[0].title == "Daily"


@test("Filter chain multiple filters")
def test_filter_chain():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(
        Task(title="H-Pending", duration_minutes=10, priority=Priority.HIGH))
    task2 = Task(title="H-Done", duration_minutes=10, priority=Priority.HIGH)
    task2.mark_complete()
    pet.add_task(task2)
    pet.add_task(
        Task(title="L-Pending", duration_minutes=10, priority=Priority.LOW))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    result = scheduler.filter_chain(
        pet.tasks,
        lambda t: scheduler.filter_by_status(t, completed=False),
        lambda t: scheduler.filter_by_priority(t, Priority.HIGH)
    )
    assert len(result) == 1
    assert result[0].title == "H-Pending"


# =============================================================================
# CONFLICT DETECTION TESTS
# =============================================================================
section("CONFLICT DETECTION TESTS")


@test("Detect overlapping conflicts")
def test_detect_overlapping():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    base = datetime(2026, 3, 28, 10, 0)
    pet.add_task(Task(title="T1", duration_minutes=30, scheduled_time=base))
    pet.add_task(Task(title="T2", duration_minutes=30,
                 scheduled_time=base + timedelta(minutes=15)))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts(pet.tasks)
    assert len(warnings) == 1
    assert warnings[0].overlap_minutes == 15


@test("Exact same time conflict")
def test_exact_same_time():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    same_time = datetime(2026, 3, 28, 10, 0)
    pet.add_task(Task(title="T1", duration_minutes=30,
                 scheduled_time=same_time))
    pet.add_task(Task(title="T2", duration_minutes=20,
                 scheduled_time=same_time))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts(pet.tasks)
    assert len(warnings) == 1
    assert warnings[0].overlap_minutes == 20


@test("No overlap when tasks are sequential")
def test_no_overlap_sequential():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    base = datetime(2026, 3, 28, 10, 0)
    pet.add_task(Task(title="T1", duration_minutes=30, scheduled_time=base))
    pet.add_task(Task(title="T2", duration_minutes=30,
                 scheduled_time=base + timedelta(minutes=30)))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts(pet.tasks)
    assert len(warnings) == 0


@test("Conflicts across different pets")
def test_conflicts_different_pets():
    owner = Owner(name="Test")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Whiskers", species="cat")
    same_time = datetime(2026, 3, 28, 10, 0)
    dog.add_task(Task(title="Walk", duration_minutes=30,
                 scheduled_time=same_time))
    cat.add_task(Task(title="Feed", duration_minutes=10,
                 scheduled_time=same_time))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts(owner.get_all_tasks())
    assert len(warnings) == 1
    assert "Different pets" in warnings[0].message


@test("Unscheduled tasks don't cause conflicts")
def test_unscheduled_no_conflict():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(Task(title="Scheduled", duration_minutes=30,
                      scheduled_time=datetime(2026, 3, 28, 10, 0)))
    pet.add_task(Task(title="Unscheduled", duration_minutes=30))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts(pet.tasks)
    assert len(warnings) == 0


@test("Get conflict-free tasks")
def test_conflict_free_tasks():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    base = datetime(2026, 3, 28, 10, 0)
    pet.add_task(
        Task(title="Conflict1", duration_minutes=30, scheduled_time=base))
    pet.add_task(Task(title="Conflict2", duration_minutes=30,
                      scheduled_time=base + timedelta(minutes=10)))
    pet.add_task(Task(title="Safe", duration_minutes=30,
                      scheduled_time=base + timedelta(hours=2)))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    safe, warnings = scheduler.get_conflict_free_tasks(pet.tasks)
    assert len(safe) == 1
    assert safe[0].title == "Safe"
    assert len(warnings) == 1


# =============================================================================
# SCHEDULE GENERATION TESTS
# =============================================================================
section("SCHEDULE GENERATION TESTS")


@test("Generate schedule respects time limit")
def test_schedule_time_limit():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(Task(title="T1", duration_minutes=30, priority=Priority.HIGH))
    pet.add_task(Task(title="T2", duration_minutes=30, priority=Priority.HIGH))
    pet.add_task(Task(title="T3", duration_minutes=30, priority=Priority.LOW))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner, daily_limit_minutes=60)
    schedule = scheduler.generate_schedule()
    total = sum(t.duration_minutes for t in schedule)
    assert total <= 60


@test("Generate schedule prioritizes HIGH")
def test_schedule_prioritizes_high():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(Task(title="Low", duration_minutes=20, priority=Priority.LOW))
    pet.add_task(
        Task(title="High", duration_minutes=30, priority=Priority.HIGH))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner, daily_limit_minutes=30)
    schedule = scheduler.generate_schedule()
    assert len(schedule) == 1
    assert schedule[0].title == "High"


@test("Generate schedule excludes completed by default")
def test_schedule_excludes_completed():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    task = Task(title="Done", duration_minutes=10)
    task.mark_complete()
    pet.add_task(task)
    pet.add_task(Task(title="Pending", duration_minutes=10))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule(include_completed=False)
    assert len(schedule) == 1
    assert schedule[0].title == "Pending"


@test("Empty schedule when all complete")
def test_empty_schedule_all_complete():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    task = Task(title="Done", duration_minutes=10)
    task.mark_complete()
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule(include_completed=False)
    assert schedule == []


@test("Assign times sequential")
def test_assign_times():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(Task(title="T1", duration_minutes=30))
    pet.add_task(Task(title="T2", duration_minutes=20))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    start = datetime(2026, 3, 29, 8, 0)
    scheduler.assign_times(pet.tasks, start)
    assert pet.tasks[0].scheduled_time == start
    assert pet.tasks[1].scheduled_time == start + timedelta(minutes=30)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================
section("INTEGRATION TESTS")


@test("Full workflow")
def test_full_workflow():
    owner = Owner(name="Jordan", available_minutes=90)
    dog = Pet(name="Mochi", species="dog", age=3)
    cat = Pet(name="Whiskers", species="cat", age=5)
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(
        Task(title="Walk", duration_minutes=30, priority=Priority.HIGH))
    dog.add_task(
        Task(title="Feed", duration_minutes=10, priority=Priority.HIGH))
    cat.add_task(
        Task(title="Medication", duration_minutes=5, priority=Priority.HIGH))
    scheduler = Scheduler(owner=owner, daily_limit_minutes=90)
    schedule = scheduler.generate_schedule()
    assert len(schedule) >= 3
    total = scheduler.get_total_scheduled_minutes(schedule)
    assert total <= 90


@test("Recurring task workflow")
def test_recurring_workflow():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    base = datetime(2026, 3, 29, 8, 0)
    task = Task(title="Daily", duration_minutes=30, frequency=Frequency.DAILY,
                scheduled_time=base)
    pet.add_task(task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    # Complete 3 times
    current = task
    for i in range(1, 4):
        next_task = scheduler.complete_task_with_recurrence(pet, current)
        assert next_task is not None
        assert next_task.scheduled_time == base + timedelta(days=i)
        current = next_task
    assert len(pet.tasks) == 4


# =============================================================================
# EDGE CASE TESTS
# =============================================================================
section("EDGE CASE TESTS")


@test("Zero duration task")
def test_zero_duration():
    task = Task(title="Instant", duration_minutes=0)
    assert task.duration_minutes == 0


@test("Exact time budget match")
def test_exact_budget():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(Task(title="T1", duration_minutes=30, priority=Priority.HIGH))
    pet.add_task(Task(title="T2", duration_minutes=30, priority=Priority.HIGH))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner, daily_limit_minutes=60)
    schedule = scheduler.generate_schedule()
    total = scheduler.get_total_scheduled_minutes(schedule)
    assert total == 60


@test("Single task exceeds budget")
def test_exceeds_budget():
    owner = Owner(name="Test")
    pet = Pet(name="Pet", species="dog")
    pet.add_task(Task(title="Long", duration_minutes=120))
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner, daily_limit_minutes=60)
    schedule = scheduler.generate_schedule()
    assert schedule == []


# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 60)
print(f"  TEST RESULTS: {passed} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    print("\nFailed tests:")
    for name, err in errors:
        print(f"  ✗ {name}: {err}")
    exit(1)
else:
    print("\n✅ All tests passed!")
    exit(0)
