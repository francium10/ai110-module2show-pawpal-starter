#!/usr/bin/env python3
"""
PawPal+ CLI Demo Script - Phase 4: Algorithmic Layer

This script demonstrates the intelligent scheduling features of PawPal+:
- Sorting algorithms (by time, priority, duration)
- Filtering algorithms (by pet, status, priority)
- Recurring task automation
- Conflict detection with warnings

Usage:
    python main.py
"""

from datetime import datetime, timedelta
from pawpal_system import (
    Owner, Pet, Task, Scheduler,
    Priority, Frequency, ConflictWarning
)


def print_header(text: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)


def print_subheader(text: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n  --- {text} ---")


def create_sample_data() -> Owner:
    """Create sample owner, pets, and tasks for demonstration.

    NOTE: Tasks are intentionally added OUT OF ORDER to demonstrate
    that sorting algorithms work correctly.
    """
    owner = Owner(name="Jordan", available_minutes=90)

    # Create pets
    mochi = Pet(name="Mochi", species="dog", age=3)
    whiskers = Pet(name="Whiskers", species="cat", age=5)

    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    # Base time for scheduling
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)

    # =========================================================================
    # Add tasks OUT OF ORDER to test sorting
    # =========================================================================

    # Task at 10:00 (added first, but should sort to later)
    mochi.add_task(Task(
        title="Play fetch",
        duration_minutes=20,
        priority=Priority.MEDIUM,
        scheduled_time=today + timedelta(hours=2),  # 10:00 AM
        frequency=Frequency.ONCE
    ))

    # Task at 8:00 (added second, but should sort to first)
    mochi.add_task(Task(
        title="Morning walk",
        duration_minutes=30,
        priority=Priority.HIGH,
        scheduled_time=today,  # 8:00 AM
        frequency=Frequency.DAILY  # Recurring!
    ))

    # Task at 9:30 (added third)
    mochi.add_task(Task(
        title="Grooming session",
        duration_minutes=45,
        priority=Priority.LOW,
        scheduled_time=today + timedelta(hours=1, minutes=30),  # 9:30 AM
        frequency=Frequency.WEEKLY  # Recurring weekly!
    ))

    # Task at 8:35
    mochi.add_task(Task(
        title="Breakfast feeding",
        duration_minutes=10,
        priority=Priority.HIGH,
        scheduled_time=today + timedelta(minutes=35),  # 8:35 AM
        frequency=Frequency.DAILY
    ))

    # =========================================================================
    # Whiskers tasks (some overlap with Mochi to test conflicts)
    # =========================================================================

    # Task at 8:10 - OVERLAPS with Mochi's morning walk!
    whiskers.add_task(Task(
        title="Morning feeding",
        duration_minutes=10,
        priority=Priority.HIGH,
        scheduled_time=today + timedelta(minutes=10),  # 8:10 AM
        frequency=Frequency.DAILY
    ))

    # Task at 8:15 - Also overlaps!
    whiskers.add_task(Task(
        title="Medication",
        duration_minutes=5,
        priority=Priority.HIGH,
        scheduled_time=today + timedelta(minutes=15),  # 8:15 AM
        frequency=Frequency.DAILY
    ))

    # Task at 9:00
    whiskers.add_task(Task(
        title="Litter box cleaning",
        duration_minutes=10,
        priority=Priority.MEDIUM,
        scheduled_time=today + timedelta(hours=1),  # 9:00 AM
        frequency=Frequency.ONCE
    ))

    # LOW priority task - no time set
    whiskers.add_task(Task(
        title="Interactive play",
        duration_minutes=15,
        priority=Priority.LOW,
        frequency=Frequency.ONCE
    ))

    return owner


def demo_sorting_algorithms(scheduler: Scheduler) -> None:
    """Demonstrate sorting algorithms."""
    print_header("📊 SORTING ALGORITHMS")

    all_tasks = scheduler.owner.get_all_tasks()

    # 1. Sort by Time
    print_subheader("Sort by Time (Earliest First)")
    sorted_by_time = scheduler.sort_by_time(all_tasks)
    for task in sorted_by_time:
        print(f"    {task}")

    # 2. Sort by Priority
    print_subheader("Sort by Priority (HIGH → LOW)")
    sorted_by_priority = scheduler.sort_by_priority(all_tasks)
    for task in sorted_by_priority:
        print(f"    {task}")

    # 3. Sort by Duration
    print_subheader("Sort by Duration (Shortest First)")
    sorted_by_duration = scheduler.sort_by_duration(all_tasks, ascending=True)
    for task in sorted_by_duration:
        print(f"    {task}")


def demo_filtering_algorithms(scheduler: Scheduler) -> None:
    """Demonstrate filtering algorithms."""
    print_header("🔍 FILTERING ALGORITHMS")

    all_tasks = scheduler.owner.get_all_tasks()

    # 1. Filter by Pet
    print_subheader("Filter by Pet: Mochi only")
    mochi_tasks = scheduler.filter_by_pet(all_tasks, "Mochi")
    for task in mochi_tasks:
        print(f"    {task}")

    # 2. Filter by Priority
    print_subheader("Filter by Priority: HIGH only")
    high_priority = scheduler.filter_by_priority(all_tasks, Priority.HIGH)
    for task in high_priority:
        print(f"    {task}")

    # 3. Filter by Status (pending)
    print_subheader("Filter by Status: Pending only")
    pending = scheduler.filter_by_status(all_tasks, completed=False)
    print(f"    {len(pending)} pending tasks")

    # 4. Filter recurring tasks
    print_subheader("Filter Recurring Tasks")
    recurring = scheduler.filter_recurring(all_tasks)
    for task in recurring:
        print(f"    {task}")

    # 5. Chained filtering (HIGH priority + pending)
    print_subheader("Chained Filter: HIGH + Pending")
    chained = scheduler.filter_chain(
        all_tasks,
        lambda t: scheduler.filter_by_status(t, completed=False),
        lambda t: scheduler.filter_by_priority(t, Priority.HIGH)
    )
    for task in chained:
        print(f"    {task}")


def demo_conflict_detection(scheduler: Scheduler) -> None:
    """Demonstrate conflict detection algorithm."""
    print_header("⚠️ CONFLICT DETECTION")

    all_tasks = scheduler.owner.get_all_tasks()

    # Detect conflicts
    warnings = scheduler.detect_conflicts(all_tasks)

    if warnings:
        print(f"\n  Found {len(warnings)} scheduling conflict(s):\n")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning.message}\n")
    else:
        print("\n  ✅ No conflicts detected!")

    # Show conflict-free tasks
    print_subheader("Conflict-Free Schedule")
    safe_tasks, _ = scheduler.get_conflict_free_tasks(all_tasks)
    print(f"  {len(safe_tasks)} tasks have no conflicts:")
    for task in scheduler.sort_by_time(safe_tasks):
        print(f"    {task}")


def demo_recurring_tasks(scheduler: Scheduler) -> None:
    """Demonstrate recurring task automation."""
    print_header("🔄 RECURRING TASK AUTOMATION")

    # Get a recurring task
    mochi = scheduler.owner.get_pet("Mochi")
    recurring_tasks = scheduler.filter_recurring(mochi.tasks)  # type: ignore

    if recurring_tasks:
        task = recurring_tasks[0]
        print(f"\n  Original Task: {task}")
        print(f"  Frequency: {task.frequency}")

        # Simulate completing the task
        print_subheader("Completing recurring task...")

        original_count = len(mochi.tasks)  # type: ignore
        next_task = scheduler.complete_task_with_recurrence(
            mochi, task)  # type: ignore

        if next_task:
            print(f"  ✅ Task marked complete!")
            print(f"  ✅ New occurrence created automatically:")
            print(f"     {next_task}")
            # type: ignore
            print(f"  Task count: {original_count} → {len(mochi.tasks)}")

            # Show timedelta calculation
            if task.scheduled_time and next_task.scheduled_time:
                delta = next_task.scheduled_time - task.scheduled_time
                print(
                    f"  Next occurrence is {delta.days} day(s) later (using timedelta)")


def demo_schedule_generation(scheduler: Scheduler) -> None:
    """Demonstrate optimized schedule generation."""
    print_header("📅 OPTIMIZED SCHEDULE GENERATION")

    print(f"\n  Daily time budget: {scheduler.daily_limit_minutes} minutes")
    print(f"  Total tasks available: {len(scheduler.owner.get_all_tasks())}")

    # Generate schedule
    schedule = scheduler.generate_schedule()

    # Display using formatter
    print("\n" + scheduler.format_schedule(schedule))

    # Show what was excluded
    all_pending = scheduler.owner.get_pending_tasks()
    excluded = [t for t in all_pending if t not in schedule]

    if excluded:
        print_subheader("Tasks Excluded (didn't fit time budget)")
        for task in excluded:
            print(f"    {task}")

    # Check for conflicts in schedule
    warnings = scheduler.detect_conflicts(schedule)
    print("\n" + scheduler.format_conflicts(warnings))


def demo_time_based_schedule(scheduler: Scheduler) -> None:
    """Demonstrate chronological schedule view."""
    print_header("🕐 CHRONOLOGICAL SCHEDULE VIEW")

    chronological = scheduler.generate_schedule_by_time()

    print("\n  Tasks ordered by scheduled time:\n")
    for task in chronological:
        print(f"    {task}")


def print_summary(owner: Owner) -> None:
    """Print summary statistics."""
    print_header("📈 SUMMARY STATISTICS")

    all_tasks = owner.get_all_tasks()
    pending = owner.get_pending_tasks()
    completed = [t for t in all_tasks if t.is_complete]
    recurring = [t for t in all_tasks if t.is_recurring]

    high = len([t for t in all_tasks if t.priority == Priority.HIGH])
    med = len([t for t in all_tasks if t.priority == Priority.MEDIUM])
    low = len([t for t in all_tasks if t.priority == Priority.LOW])

    total_duration = sum(t.duration_minutes for t in all_tasks)

    print(f"""
    Owner: {owner.name}
    Daily Budget: {owner.available_minutes} minutes
    
    PETS: {len(owner.pets)}
    {chr(10).join(f'    - {pet}' for pet in owner.pets)}
    
    TASKS:
    - Total: {len(all_tasks)}
    - Pending: {len(pending)}
    - Completed: {len(completed)}
    - Recurring: {len(recurring)}
    
    BY PRIORITY:
    - 🔴 High: {high}
    - 🟡 Medium: {med}
    - 🟢 Low: {low}
    
    Total Duration: {total_duration} minutes ({total_duration // 60}h {total_duration % 60}m)
    """)


def main():
    """Main entry point for the Phase 4 demo."""
    print("\n" + "🐾" * 25)
    print("     PAWPAL+ ALGORITHMIC DEMO (Phase 4)")
    print("🐾" * 25)

    # Create sample data (tasks added OUT OF ORDER)
    owner = create_sample_data()
    scheduler = Scheduler(
        owner=owner, daily_limit_minutes=owner.available_minutes)

    # Show initial state
    print_header("📋 INITIAL DATA (Tasks added out of order)")
    for pet in owner.pets:
        print(f"\n  {pet}")
        for task in pet.tasks:
            print(f"    → {task}")

    # Run all algorithm demos
    demo_sorting_algorithms(scheduler)
    demo_filtering_algorithms(scheduler)
    demo_conflict_detection(scheduler)
    demo_recurring_tasks(scheduler)
    demo_schedule_generation(scheduler)
    demo_time_based_schedule(scheduler)

    # Summary
    print_summary(owner)

    print("\n" + "=" * 60)
    print("  ✅ Phase 4 Demo Complete!")
    print("  Algorithms implemented:")
    print("    • sort_by_time() - Chronological ordering")
    print("    • sort_by_priority() - Priority-based ordering")
    print("    • sort_by_duration() - Duration-based ordering")
    print("    • filter_by_pet() - Pet-specific filtering")
    print("    • filter_by_status() - Completion status filtering")
    print("    • filter_by_priority() - Priority filtering")
    print("    • filter_recurring() - Recurring task filtering")
    print("    • filter_chain() - Combined filtering")
    print("    • detect_conflicts() - Overlap detection with warnings")
    print("    • complete_task_with_recurrence() - Auto-create next occurrence")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
