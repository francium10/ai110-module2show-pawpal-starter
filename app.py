"""
PawPal+ Streamlit Application

A smart pet care management system that helps owners keep their furry friends
happy and healthy by tracking daily routines and generating optimized schedules.
"""

import streamlit as st
from datetime import datetime, timedelta

# =============================================================================
# STEP 1: Import backend classes from pawpal_system.py
# =============================================================================
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Frequency


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="centered",
    initial_sidebar_state="expanded"
)


# =============================================================================
# STEP 2: Session State Initialization (Application "Memory")
# =============================================================================
# Streamlit reruns the entire script on every interaction.
# st.session_state acts as a persistent "vault" to keep data alive between reruns.

def initialize_session_state():
    """Initialize session state variables if they don't exist."""

    # Check if Owner already exists in session state
    if "owner" not in st.session_state:
        # Create a new Owner instance and store it in the vault
        st.session_state.owner = Owner(name="", available_minutes=120)

    # Track if owner setup is complete
    if "owner_setup_complete" not in st.session_state:
        st.session_state.owner_setup_complete = False

    # Track selected pet for task management
    if "selected_pet" not in st.session_state:
        st.session_state.selected_pet = None

    # Store the last generated schedule
    if "last_schedule" not in st.session_state:
        st.session_state.last_schedule = None


# Initialize on every run
initialize_session_state()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def priority_from_string(priority_str: str) -> Priority:
    """Convert string priority to Priority enum."""
    mapping = {
        "low": Priority.LOW,
        "medium": Priority.MEDIUM,
        "high": Priority.HIGH
    }
    return mapping.get(priority_str.lower(), Priority.MEDIUM)


def priority_to_string(priority: Priority) -> str:
    """Convert Priority enum to display string."""
    return priority.name.capitalize()


def get_priority_color(priority: Priority) -> str:
    """Return color for priority level."""
    colors = {
        Priority.HIGH: "🔴",
        Priority.MEDIUM: "🟡",
        Priority.LOW: "🟢"
    }
    return colors.get(priority, "⚪")


def format_task_for_display(task: Task) -> dict:
    """Format a Task object for table display."""
    time_str = task.scheduled_time.strftime(
        "%I:%M %p") if task.scheduled_time else "Unscheduled"
    return {
        "Status": "✅" if task.is_complete else "⏳",
        "Task": task.title,
        "Pet": task.pet_name or "—",
        "Duration": f"{task.duration_minutes} min",
        "Priority": f"{get_priority_color(task.priority)} {priority_to_string(task.priority)}",
        "Time": time_str,
        "Recurring": "🔄" if task.is_recurring else "—"
    }


# =============================================================================
# MAIN APPLICATION
# =============================================================================

# Header
st.title("🐾 PawPal+")
st.caption("Smart Pet Care Management System")

# Get reference to owner from session state
owner = st.session_state.owner


# =============================================================================
# SIDEBAR: Owner & Pet Setup
# =============================================================================

with st.sidebar:
    st.header("👤 Owner Setup")

    # Owner name input
    new_owner_name = st.text_input(
        "Your Name",
        value=owner.name,
        placeholder="Enter your name"
    )

    # Update owner name if changed
    if new_owner_name != owner.name:
        owner.name = new_owner_name

    # Available time budget
    owner.available_minutes = st.slider(
        "Daily Time Budget (minutes)",
        min_value=30,
        max_value=480,
        value=owner.available_minutes,
        step=15,
        help="How many minutes can you dedicate to pet care today?"
    )

    st.divider()

    # ==========================================================================
    # STEP 3: Wiring UI Actions - Add Pet Form
    # ==========================================================================
    st.header("🐕 Add a Pet")

    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet Name", placeholder="e.g., Mochi")
        pet_species = st.selectbox(
            "Species", ["dog", "cat", "bird", "rabbit", "other"])
        pet_age = st.number_input(
            "Age (years)", min_value=0, max_value=30, value=1)

        submitted = st.form_submit_button(
            "➕ Add Pet", use_container_width=True)

        if submitted and pet_name:
            # Check if pet with same name exists
            existing_pet = owner.get_pet(pet_name)
            if existing_pet:
                st.error(f"A pet named '{pet_name}' already exists!")
            else:
                # Create new Pet object and add to Owner
                new_pet = Pet(name=pet_name, species=pet_species, age=pet_age)
                owner.add_pet(new_pet)
                st.success(f"Added {pet_name} the {pet_species}! 🎉")
                st.rerun()

    # Display current pets
    if owner.pets:
        st.divider()
        st.subheader("Your Pets")

        for pet in owner.pets:
            col1, col2 = st.columns([3, 1])
            with col1:
                species_emoji = {"dog": "🐕", "cat": "🐱",
                                 "bird": "🐦", "rabbit": "🐰"}.get(pet.species, "🐾")
                st.write(
                    f"{species_emoji} **{pet.name}** ({pet.species}, {pet.age}yr)")
                st.caption(f"{len(pet.tasks)} tasks assigned")
            with col2:
                if st.button("🗑️", key=f"remove_{pet.name}", help=f"Remove {pet.name}"):
                    owner.remove_pet(pet.name)
                    st.rerun()


# =============================================================================
# MAIN CONTENT AREA
# =============================================================================

# Check if owner has pets
if not owner.pets:
    st.info("👈 Start by adding your pets in the sidebar!")
    st.stop()

# Show owner summary
st.success(
    f"👤 **{owner.name or 'Pet Owner'}** | 🐾 {len(owner.pets)} pet(s) | ⏱️ {owner.available_minutes} min available")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(
    ["📝 Add Tasks", "📅 Generate Schedule", "📊 Overview"])


# =============================================================================
# TAB 1: Add Tasks
# =============================================================================
with tab1:
    st.subheader("Add Care Tasks")

    # Pet selector
    pet_names = [pet.name for pet in owner.pets]
    selected_pet_name = st.selectbox(
        "Select Pet",
        options=pet_names,
        help="Which pet is this task for?"
    )

    selected_pet = owner.get_pet(selected_pet_name)

    if selected_pet:
        # Task input form
        with st.form("add_task_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                task_title = st.text_input(
                    "Task Name",
                    placeholder="e.g., Morning walk"
                )
                task_duration = st.number_input(
                    "Duration (minutes)",
                    min_value=1,
                    max_value=240,
                    value=15
                )

            with col2:
                task_priority = st.selectbox(
                    "Priority",
                    options=["High", "Medium", "Low"],
                    index=1
                )
                task_recurring = st.checkbox("Recurring (daily)", value=False)

            # Optional: Set specific time
            set_time = st.checkbox("Set specific time")
            task_time = None
            if set_time:
                task_time_input = st.time_input("Scheduled Time", value=None)
                if task_time_input:
                    today = datetime.now().date()
                    task_time = datetime.combine(today, task_time_input)

            submitted = st.form_submit_button(
                "➕ Add Task", use_container_width=True)

            if submitted and task_title:
                # Create new Task object and add to Pet
                new_task = Task(
                    title=task_title,
                    duration_minutes=task_duration,
                    priority=priority_from_string(task_priority),
                    frequency=Frequency.DAILY if task_recurring else Frequency.ONCE,
                    scheduled_time=task_time
                )
                selected_pet.add_task(new_task)
                st.success(f"Added '{task_title}' for {selected_pet.name}! ✅")
                st.rerun()

        # Show tasks for selected pet
        st.divider()
        st.subheader(f"Tasks for {selected_pet.name}")

        if selected_pet.tasks:
            for i, task in enumerate(selected_pet.tasks):
                col1, col2, col3 = st.columns([4, 1, 1])

                with col1:
                    status = "✅" if task.is_complete else "⏳"
                    priority_color = get_priority_color(task.priority)
                    time_str = task.scheduled_time.strftime(
                        "%I:%M %p") if task.scheduled_time else ""
                    recurring = " 🔄" if task.is_recurring else ""

                    st.write(
                        f"{status} {priority_color} **{task.title}** "
                        f"({task.duration_minutes}min){recurring} {time_str}"
                    )

                with col2:
                    # Toggle completion
                    if task.is_complete:
                        if st.button("↩️", key=f"undo_{i}_{task.title}", help="Mark incomplete"):
                            task.mark_incomplete()
                            st.rerun()
                    else:
                        if st.button("✓", key=f"done_{i}_{task.title}", help="Mark complete"):
                            task.mark_complete()
                            st.rerun()

                with col3:
                    if st.button("🗑️", key=f"del_{i}_{task.title}", help="Delete task"):
                        selected_pet.remove_task(task.title)
                        st.rerun()
        else:
            st.info(f"No tasks for {selected_pet.name} yet. Add one above!")


# =============================================================================
# TAB 2: Generate Schedule
# =============================================================================
with tab2:
    st.subheader("📅 Generate Today's Schedule")

    all_tasks = owner.get_all_tasks()
    pending_tasks = owner.get_pending_tasks()

    # Show task summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tasks", len(all_tasks))
    with col2:
        st.metric("Pending", len(pending_tasks))
    with col3:
        total_time = sum(t.duration_minutes for t in pending_tasks)
        st.metric("Total Time Needed", f"{total_time} min")

    st.divider()

    # Schedule options
    col1, col2 = st.columns(2)
    with col1:
        start_hour = st.selectbox(
            "Start Time",
            options=list(range(5, 22)),
            index=3,  # Default 8 AM
            format_func=lambda x: f"{x}:00 {'AM' if x < 12 else 'PM'}"
        )
    with col2:
        include_completed = st.checkbox("Include completed tasks", value=False)

    # Generate schedule button
    if st.button("🗓️ Generate Optimized Schedule", type="primary", use_container_width=True):
        if not pending_tasks and not include_completed:
            st.warning("No pending tasks to schedule! Add some tasks first.")
        else:
            # Create scheduler and generate schedule
            scheduler = Scheduler(
                owner=owner,
                daily_limit_minutes=owner.available_minutes
            )

            schedule = scheduler.generate_schedule(
                include_completed=include_completed)

            # Assign sequential times starting from selected hour
            start_time = datetime.now().replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            )
            scheduler.assign_times(schedule, start_time)

            # Store in session state
            st.session_state.last_schedule = schedule

            st.success("✅ Schedule generated!")

    # Display schedule if it exists
    if st.session_state.last_schedule:
        schedule = st.session_state.last_schedule
        scheduler = Scheduler(
            owner=owner, daily_limit_minutes=owner.available_minutes)

        st.divider()
        st.subheader("📋 Today's Optimized Schedule")

        # Schedule explanation
        with st.expander("💡 How the schedule was built", expanded=False):
            st.markdown("""
            **Scheduling Algorithm:**
            1. **Priority First**: HIGH priority tasks are scheduled before MEDIUM and LOW
            2. **Time Constraint**: Tasks are added until the daily time budget is reached
            3. **Sequential Timing**: Tasks are assigned back-to-back starting from your chosen time
            
            **Why this order?**
            - Critical care tasks (medications, urgent needs) happen first
            - Routine tasks (walks, feeding) come next
            - Optional enrichment activities are scheduled if time permits
            """)

        # Display scheduled tasks
        if schedule:
            total_scheduled = 0

            for i, task in enumerate(schedule, 1):
                time_str = task.scheduled_time.strftime(
                    "%I:%M %p") if task.scheduled_time else "—"
                priority_color = get_priority_color(task.priority)
                recurring = "🔄" if task.is_recurring else ""

                col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

                with col1:
                    st.write(f"**{time_str}**")
                with col2:
                    st.write(f"{priority_color} {task.title} {recurring}")
                    st.caption(
                        f"📍 {task.pet_name} • {task.duration_minutes} min")
                with col3:
                    st.write(f"{priority_to_string(task.priority)}")
                with col4:
                    if task.is_complete:
                        st.write("✅")
                    else:
                        if st.button("Done", key=f"sched_done_{i}"):
                            task.mark_complete()
                            st.rerun()

                total_scheduled += task.duration_minutes

            # Summary
            st.divider()
            remaining = owner.available_minutes - total_scheduled

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tasks Scheduled", len(schedule))
            with col2:
                hours, mins = divmod(total_scheduled, 60)
                st.metric("Time Used", f"{hours}h {mins}m")
            with col3:
                st.metric("Time Remaining", f"{remaining} min")

            # Show excluded tasks
            all_pending = owner.get_pending_tasks()
            excluded = [t for t in all_pending if t not in schedule]

            if excluded:
                st.warning(
                    f"⚠️ {len(excluded)} task(s) didn't fit in today's schedule:")
                for task in excluded:
                    st.write(
                        f"  • {task.title} ({task.duration_minutes}min, {priority_to_string(task.priority)})")
        else:
            st.info("No tasks to display.")

        # Conflict detection
        conflicts = scheduler.detect_conflicts(schedule)
        if conflicts:
            st.error("⚠️ **Scheduling Conflicts Detected!**")
            for warning in conflicts:
                st.write(f"  • {warning.message}")


# =============================================================================
# TAB 3: Overview
# =============================================================================
with tab3:
    st.subheader("📊 Pet Care Overview")

    if not owner.get_all_tasks():
        st.info("Add some tasks to see your overview!")
    else:
        # Stats by pet
        for pet in owner.pets:
            species_emoji = {"dog": "🐕", "cat": "🐱",
                             "bird": "🐦", "rabbit": "🐰"}.get(pet.species, "🐾")

            with st.expander(f"{species_emoji} {pet.name}", expanded=True):
                total = len(pet.tasks)
                completed = len([t for t in pet.tasks if t.is_complete])
                pending = total - completed

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Tasks", total)
                with col2:
                    st.metric("Completed", completed)
                with col3:
                    st.metric("Pending", pending)

                if total > 0:
                    progress = completed / total
                    st.progress(
                        progress, text=f"{int(progress * 100)}% complete")

                # Task breakdown by priority
                if pet.tasks:
                    high = len([t for t in pet.tasks if t.priority ==
                               Priority.HIGH and not t.is_complete])
                    med = len([t for t in pet.tasks if t.priority ==
                              Priority.MEDIUM and not t.is_complete])
                    low = len([t for t in pet.tasks if t.priority ==
                              Priority.LOW and not t.is_complete])

                    st.caption(
                        f"Pending: 🔴 {high} high | 🟡 {med} medium | 🟢 {low} low")

        st.divider()

        # All tasks table
        st.subheader("📋 All Tasks")

        all_tasks = owner.get_all_tasks()
        if all_tasks:
            task_data = [format_task_for_display(task) for task in all_tasks]
            st.dataframe(task_data, use_container_width=True, hide_index=True)


# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("🐾 PawPal+ | Smart Pet Care Management System | Built with Streamlit")
