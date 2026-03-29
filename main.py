#!/usr/bin/env python3
"""
PawPal+ CLI Demo Script

This script demonstrates the core functionality of the PawPal+ system.
Run this to verify your backend logic before connecting to Streamlit.

Usage:
    python main.py
"""

from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler, Priority


def create_sample_data() -> Owner:
    """Create sample owner, pets, and tasks for demonstration."""

    # Create the owner
    # 2 hours available today
    owner = Owner(name="Jordan", available_minutes=120)

    # Create pets
    mochi = Pet(name="Mochi", species="dog", age=3)
    whiskers = Pet(name="Whiskers", species="cat", age=5)

    # Add pets to owner
    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    # Create tasks for Mochi (dog)
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)

    mochi.add_task(Task(
        title="Morning walk",
        duration_minutes=30,
        priority=Priority.HIGH,
        scheduled_time=today,
        is_recurring=True
    ))

    mochi.add_task(Task(
        title="Breakfast feeding",
        duration_minutes=10,
        priority=Priority.HIGH,
        scheduled_time=today + timedelta(minutes=35)
    ))

    mochi.add_task(Task(
        title="Play fetch",
        duration_minutes=20,
        priority=Priority.MEDIUM,
        scheduled_time=today + timedelta(hours=2)
    ))

    mochi.add_task(Task(
        title="Grooming session",
        duration_minutes=45,
        priority=Priority.LOW,
        is_recurring=False
    ))

    # Create tasks for Whiskers (cat)
    whiskers.add_task(Task(
        title="Morning feeding",
        duration_minutes=5,
        priority=Priority.HIGH,
        scheduled_time=today + timedelta(minutes=10)
    ))

    whiskers.add_task(Task(
        title="Medication (daily pill)",
        duration_minutes=5,
        priority=Priority.HIGH,
        scheduled_time=today + timedelta(minutes=15),
        is_recurring=True
    ))

    whiskers.add_task(Task(
        title="Litter box cleaning",
        duration_minutes=10,
        priority=Priority.MEDIUM,
        scheduled_time=today + timedelta(hours=1)
    ))

    whiskers.add_task(Task(
        title="Interactive play",
        duration_minutes=15,
        priority=Priority.LOW
    ))

    return owner


def print_header(text: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)


def demo_basic_info(owner: Owner) -> None:
    """Display basic owner and pet information."""
    print_header("OWNER & PETS INFO")
    print(f"\n{owner}\n")

    for pet in owner.pets:
        print(f"  {pet}")
        for task in pet.tasks:
            print(f"      -> {task}")
        print()


def demo_scheduling(owner: Owner) -> None:
    """Demonstrate the scheduler functionality."""
    print_header("SCHEDULE GENERATION")

    scheduler = Scheduler(
        owner=owner, daily_limit_minutes=owner.available_minutes)

    # Generate optimized schedule
    schedule = scheduler.generate_schedule()

    # Display formatted schedule
    print(scheduler.format_schedule(schedule))

    # Show what didn't fit
    all_tasks = owner.get_pending_tasks()
    excluded = [t for t in all_tasks if t not in schedule]

    if excluded:
        print("\n[!] Tasks that didn't fit in today's schedule:")
        for task in excluded:
            print(
                f"    - {task.title} ({task.duration_minutes}min) - {task.priority}")


def demo_conflict_detection(owner: Owner) -> None:
    """Demonstrate conflict detection."""
    print_header("CONFLICT DETECTION")

    scheduler = Scheduler(owner=owner)
    all_tasks = owner.get_all_tasks()
    conflicts = scheduler.detect_conflicts(all_tasks)

    if conflicts:
        print("\n[!] Overlapping tasks detected:")
        for task in conflicts:
            print(f"    - {task}")
    else:
        print("\n[OK] No scheduling conflicts found!")


def demo_task_completion(owner: Owner) -> None:
    """Demonstrate marking tasks complete."""
    print_header("TASK COMPLETION DEMO")

    # Find a task to complete
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        task = all_tasks[0]
        print(f"\nBefore: {task}")

        task.mark_complete()
        print(f"After:  {task}")

        # Reset for demo purposes
        task.mark_incomplete()
        print(f"Reset:  {task}")


def demo_priority_sorting(owner: Owner) -> None:
    """Demonstrate priority-based sorting."""
    print_header("PRIORITY SORTING")

    scheduler = Scheduler(owner=owner)
    all_tasks = owner.get_all_tasks()
    sorted_tasks = scheduler.sort_by_priority(all_tasks)

    print("\nTasks sorted by priority (HIGH -> LOW):\n")
    current_priority = None
    for task in sorted_tasks:
        if task.priority != current_priority:
            current_priority = task.priority
            print(f"  [{current_priority}]")
        print(f"      - {task.title} ({task.duration_minutes}min)")


def main():
    """Main entry point for the demo."""
    print("\n" + "=" * 40)
    print("     PAWPAL+ SYSTEM DEMO")
    print("=" * 40)

    # Create sample data
    owner = create_sample_data()

    # Run all demos
    demo_basic_info(owner)
    demo_priority_sorting(owner)
    demo_scheduling(owner)
    demo_conflict_detection(owner)
    demo_task_completion(owner)

    # Summary
    print_header("SUMMARY STATISTICS")
    print(f"""
    Owner: {owner.name}
    Total Pets: {len(owner.pets)}
    Total Tasks: {len(owner.get_all_tasks())}
    Pending Tasks: {len(owner.get_pending_tasks())}
    Daily Budget: {owner.available_minutes} minutes
    """)

    print("\n[OK] Demo complete! Your backend logic is working.\n")
    print("Next step: Connect this to the Streamlit UI in app.py\n")


if __name__ == "__main__":
    main()
