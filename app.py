"""
PawPal+ Streamlit Application (Phase 6 - Polished)

A smart pet care management system featuring:
- Priority-based scheduling algorithms
- Multiple sorting methods (time, priority, duration)
- Filtering by pet, status, priority, recurring
- Conflict detection with visual warnings
- Recurring task automation with timedelta
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List

# =============================================================================
# Import backend classes from pawpal_system.py
# =============================================================================
from pawpal_system import (
    Owner, Pet, Task, Scheduler, 
    Priority, Frequency, ConflictWarning
)


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name="", available_minutes=120)
    if "last_schedule" not in st.session_state:
        st.session_state.last_schedule = None

initialize_session_state()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def priority_from_string(priority_str: str) -> Priority:
    """Convert string priority to Priority enum."""
    return {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}.get(
        priority_str.lower(), Priority.MEDIUM
    )

def frequency_from_string(freq_str: str) -> Frequency:
    """Convert string frequency to Frequency enum."""
    return {
        "once": Frequency.ONCE,
        "daily": Frequency.DAILY,
        "weekly": Frequency.WEEKLY,
        "biweekly": Frequency.BIWEEKLY
    }.get(freq_str.lower(), Frequency.ONCE)

def get_priority_emoji(priority: Priority) -> str:
    """Return emoji for priority level."""
    return {Priority.HIGH: "🔴", Priority.MEDIUM: "🟡", Priority.LOW: "🟢"}.get(priority, "⚪")

def get_species_emoji(species: str) -> str:
    """Return emoji for species."""
    return {"dog": "🐕", "cat": "🐱", "bird": "🐦", "rabbit": "🐰"}.get(species, "🐾")

def format_time(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%I:%M %p") if dt else "Unscheduled"

def display_conflict_warnings(warnings: List[ConflictWarning]):
    """Display conflict warnings with visual styling - helpful for pet owners."""
    if warnings:
        st.error(f"⚠️ **{len(warnings)} Scheduling Conflict(s) Detected!**")
        st.markdown("*You're trying to do two things at once! Consider rescheduling:*")
        
        for i, warning in enumerate(warnings, 1):
            with st.container():
                col1, col2 = st.columns([1, 6])
                with col1:
                    st.markdown(f"### 🚨")
                with col2:
                    st.warning(
                        f"**Conflict {i}:** '{warning.task_a.title}' and '{warning.task_b.title}' "
                        f"overlap by **{warning.overlap_minutes} minutes**.\n\n"
                        f"💡 *Tip: Reschedule one task or adjust the start times.*"
                    )
    else:
        st.success("✅ No scheduling conflicts! Your day is well-organized.")


# =============================================================================
# MAIN APPLICATION
# =============================================================================
st.title("🐾 PawPal+")
st.caption("Smart Pet Care Management System with Intelligent Scheduling Algorithms")

owner = st.session_state.owner


# =============================================================================
# SIDEBAR: Owner & Pet Setup
# =============================================================================
with st.sidebar:
    st.header("👤 Owner Setup")
    
    new_owner_name = st.text_input("Your Name", value=owner.name, placeholder="Enter your name")
    if new_owner_name != owner.name:
        owner.name = new_owner_name
    
    owner.available_minutes = st.slider(
        "Daily Time Budget (minutes)",
        min_value=30, max_value=480,
        value=owner.available_minutes, step=15,
        help="How many minutes can you dedicate to pet care today?"
    )
    
    st.divider()
    
    # Add Pet Form
    st.header("🐕 Add a Pet")
    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet Name", placeholder="e.g., Mochi")
        pet_species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
        
        if st.form_submit_button("➕ Add Pet", use_container_width=True):
            if pet_name:
                if owner.get_pet(pet_name):
                    st.error(f"A pet named '{pet_name}' already exists!")
                else:
                    owner.add_pet(Pet(name=pet_name, species=pet_species, age=pet_age))
                    st.success(f"Added {pet_name}! 🎉")
                    st.rerun()
    
    # Display current pets
    if owner.pets:
        st.divider()
        st.subheader("Your Pets")
        for pet in owner.pets:
            col1, col2 = st.columns([3, 1])
            with col1:
                emoji = get_species_emoji(pet.species)
                pending = len(pet.get_pending_tasks())
                st.write(f"{emoji} **{pet.name}** ({pet.age}yr)")
                st.caption(f"{pending} pending / {len(pet.tasks)} total")
            with col2:
                if st.button("🗑️", key=f"del_pet_{pet.name}"):
                    owner.remove_pet(pet.name)
                    st.rerun()


# =============================================================================
# MAIN CONTENT
# =============================================================================
if not owner.pets:
    st.info("👈 Start by adding your pets in the sidebar!")
    st.stop()

# Owner summary bar
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("👤 Owner", owner.name or "Not set")
with col2:
    st.metric("🐾 Pets", len(owner.pets))
with col3:
    st.metric("📋 Total Tasks", len(owner.get_all_tasks()))
with col4:
    st.metric("⏱️ Budget", f"{owner.available_minutes} min")

st.divider()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Manage Tasks", 
    "📅 Smart Schedule", 
    "🔍 Filter & Sort",
    "📊 Analytics"
])


# =============================================================================
# TAB 1: Manage Tasks
# =============================================================================
with tab1:
    st.subheader("Add & Manage Care Tasks")
    
    col_form, col_list = st.columns([1, 1])
    
    with col_form:
        st.markdown("### ➕ Add New Task")
        
        pet_names = [pet.name for pet in owner.pets]
        selected_pet_name = st.selectbox("Select Pet", options=pet_names, key="task_pet")
        selected_pet = owner.get_pet(selected_pet_name)
        
        if selected_pet:
            with st.form("add_task_form", clear_on_submit=True):
                task_title = st.text_input("Task Name", placeholder="e.g., Morning walk")
                
                col1, col2 = st.columns(2)
                with col1:
                    task_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=15)
                    task_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
                with col2:
                    task_frequency = st.selectbox("Frequency", ["Once", "Daily", "Weekly", "Biweekly"])
                    set_time = st.checkbox("Set specific time")
                
                task_time = None
                if set_time:
                    task_time_input = st.time_input("Scheduled Time")
                    if task_time_input:
                        task_time = datetime.combine(datetime.now().date(), task_time_input)
                
                if st.form_submit_button("➕ Add Task", use_container_width=True):
                    if task_title:
                        new_task = Task(
                            title=task_title,
                            duration_minutes=task_duration,
                            priority=priority_from_string(task_priority),
                            frequency=frequency_from_string(task_frequency),
                            scheduled_time=task_time
                        )
                        selected_pet.add_task(new_task)
                        st.success(f"Added '{task_title}' for {selected_pet.name}!")
                        st.rerun()
    
    with col_list:
        st.markdown(f"### 📋 Tasks for {selected_pet_name}")
        
        if selected_pet and selected_pet.tasks:
            for i, task in enumerate(selected_pet.tasks):
                with st.container():
                    col1, col2, col3 = st.columns([4, 1, 1])
                    
                    with col1:
                        status = "✅" if task.is_complete else "⏳"
                        priority_emoji = get_priority_emoji(task.priority)
                        freq = f" 🔄{task.frequency.name}" if task.is_recurring else ""
                        time_str = format_time(task.scheduled_time)
                        
                        st.write(f"{status} {priority_emoji} **{task.title}**{freq}")
                        st.caption(f"{task.duration_minutes}min | {time_str}")
                    
                    with col2:
                        if task.is_complete:
                            if st.button("↩️", key=f"undo_{i}_{task.title}", help="Mark incomplete"):
                                task.mark_incomplete()
                                st.rerun()
                        else:
                            if st.button("✓", key=f"done_{i}_{task.title}", help="Mark complete"):
                                # Handle recurring task automation
                                scheduler = Scheduler(owner=owner)
                                next_task = scheduler.complete_task_with_recurrence(selected_pet, task)
                                if next_task:
                                    st.toast(f"🔄 Next occurrence created for {next_task.scheduled_time.strftime('%m/%d')}")
                                st.rerun()
                    
                    with col3:
                        if st.button("🗑️", key=f"del_{i}_{task.title}"):
                            selected_pet.remove_task(task.title)
                            st.rerun()
                    
                    st.divider()
        else:
            st.info(f"No tasks for {selected_pet_name} yet. Add one!")


# =============================================================================
# TAB 2: Smart Schedule (with Conflict Detection)
# =============================================================================
with tab2:
    st.subheader("📅 Generate Optimized Daily Schedule")
    
    scheduler = Scheduler(owner=owner, daily_limit_minutes=owner.available_minutes)
    all_tasks = owner.get_all_tasks()
    pending_tasks = owner.get_pending_tasks()
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tasks", len(all_tasks))
    with col2:
        st.metric("Pending", len(pending_tasks))
    with col3:
        total_time = sum(t.duration_minutes for t in pending_tasks)
        st.metric("Time Needed", f"{total_time} min")
    with col4:
        fits = "✅ Yes" if total_time <= owner.available_minutes else "⚠️ Over"
        st.metric("Fits Budget?", fits)
    
    st.divider()
    
    # Schedule options
    col1, col2, col3 = st.columns(3)
    with col1:
        start_hour = st.selectbox(
            "Start Time",
            options=list(range(5, 22)),
            index=3,
            format_func=lambda x: f"{x}:00 {'AM' if x < 12 else 'PM'}"
        )
    with col2:
        include_completed = st.checkbox("Include completed", value=False)
    with col3:
        check_conflicts = st.checkbox("Check for conflicts", value=True)
    
    if st.button("🗓️ Generate Optimized Schedule", type="primary", use_container_width=True):
        if not pending_tasks and not include_completed:
            st.warning("No pending tasks! Add some tasks first.")
        else:
            schedule = scheduler.generate_schedule(include_completed=include_completed)
            start_time = datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)
            scheduler.assign_times(schedule, start_time)
            st.session_state.last_schedule = schedule
            st.success("✅ Schedule generated using priority-based algorithm!")
    
    # Display schedule
    if st.session_state.last_schedule:
        schedule = st.session_state.last_schedule
        
        st.divider()
        
        # Algorithm explanation
        with st.expander("💡 **How the Scheduling Algorithm Works**", expanded=False):
            st.markdown("""
            ### Priority-Based Greedy Scheduling
            
            **Step 1: Sort by Priority**
            - Tasks sorted: HIGH → MEDIUM → LOW
            - Same-priority tasks use scheduled time as tiebreaker
            
            **Step 2: Greedy Selection**
            - Add tasks until time budget is reached
            - Higher priority tasks always get scheduled first
            
            **Step 3: Sequential Time Assignment**
            - Times assigned back-to-back starting from your chosen start time
            
            **Why this approach?**
            - 🔴 Critical care (medications, urgent needs) always happens first
            - 🟡 Routine tasks (walks, feeding) come next
            - 🟢 Optional enrichment scheduled if time permits
            """)
        
        # CONFLICT DETECTION - Key Phase 6 Feature
        if check_conflicts:
            warnings = scheduler.detect_conflicts(schedule)
            display_conflict_warnings(warnings)
        
        st.markdown("### 📋 Today's Schedule")
        
        if schedule:
            total_mins = 0
            
            # Table header
            header_cols = st.columns([1.5, 3, 1.5, 1])
            with header_cols[0]:
                st.markdown("**Time**")
            with header_cols[1]:
                st.markdown("**Task**")
            with header_cols[2]:
                st.markdown("**Priority**")
            with header_cols[3]:
                st.markdown("**Action**")
            
            st.divider()
            
            for i, task in enumerate(schedule, 1):
                col1, col2, col3, col4 = st.columns([1.5, 3, 1.5, 1])
                
                with col1:
                    time_display = format_time(task.scheduled_time)
                    end_time = task.scheduled_time + timedelta(minutes=task.duration_minutes) if task.scheduled_time else None
                    st.markdown(f"**{time_display}**")
                    if end_time:
                        st.caption(f"→ {format_time(end_time)}")
                
                with col2:
                    emoji = get_priority_emoji(task.priority)
                    recurring = " 🔄" if task.is_recurring else ""
                    status_icon = "✅ " if task.is_complete else ""
                    st.write(f"{status_icon}{emoji} {task.title}{recurring}")
                    st.caption(f"📍 {task.pet_name} • {task.duration_minutes} min")
                
                with col3:
                    st.write(f"{task.priority.name.capitalize()}")
                
                with col4:
                    if task.is_complete:
                        st.write("Done ✅")
                    else:
                        if st.button("Complete", key=f"sched_{i}"):
                            pet = owner.get_pet(task.pet_name)
                            if pet:
                                scheduler.complete_task_with_recurrence(pet, task)
                            st.rerun()
                
                total_mins += task.duration_minutes
            
            # Summary
            st.divider()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Scheduled", f"{len(schedule)} tasks")
            with col2:
                h, m = divmod(total_mins, 60)
                st.metric("Duration", f"{h}h {m}m")
            with col3:
                remaining = owner.available_minutes - total_mins
                delta_color = "normal" if remaining >= 0 else "inverse"
                st.metric("Remaining", f"{remaining} min")
            
            # Excluded tasks warning
            excluded = [t for t in pending_tasks if t not in schedule]
            if excluded:
                st.warning(f"⚠️ **{len(excluded)} task(s) didn't fit in today's schedule:**")
                for task in excluded:
                    emoji = get_priority_emoji(task.priority)
                    st.write(f"  • {emoji} {task.title} ({task.duration_minutes}min)")
                st.info("💡 *Tip: Increase your time budget or reduce task durations.*")
        else:
            st.info("No tasks in schedule.")


# =============================================================================
# TAB 3: Filter & Sort (Showcasing Algorithms)
# =============================================================================
with tab3:
    st.subheader("🔍 Filter & Sort Tasks")
    st.caption("Explore the Scheduler's sorting and filtering algorithms")
    
    scheduler = Scheduler(owner=owner)
    all_tasks = owner.get_all_tasks()
    
    if not all_tasks:
        st.info("Add some tasks to use filtering and sorting!")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔧 Filters")
            
            # Filter by pet
            pet_filter = st.selectbox(
                "Filter by Pet",
                options=["All Pets"] + [p.name for p in owner.pets],
                help="Uses scheduler.filter_by_pet()"
            )
            
            # Filter by status
            status_filter = st.selectbox(
                "Filter by Status",
                options=["All", "Pending Only", "Completed Only"],
                help="Uses scheduler.filter_by_status()"
            )
            
            # Filter by priority
            priority_filter = st.selectbox(
                "Filter by Priority",
                options=["All", "High", "Medium", "Low"],
                help="Uses scheduler.filter_by_priority()"
            )
            
            # Filter recurring
            recurring_filter = st.checkbox(
                "Show only recurring tasks",
                help="Uses scheduler.filter_recurring()"
            )
        
        with col2:
            st.markdown("### 📊 Sort Options")
            
            sort_by = st.radio(
                "Sort by",
                options=[
                    "Priority (High → Low)", 
                    "Time (Earliest → Latest)", 
                    "Duration (Shortest → Longest)"
                ],
                help="Uses scheduler.sort_by_priority(), sort_by_time(), or sort_by_duration()"
            )
            
            st.markdown("---")
            st.markdown("**Algorithm Used:**")
            if sort_by == "Priority (High → Low)":
                st.code("scheduler.sort_by_priority(tasks)", language="python")
            elif sort_by == "Time (Earliest → Latest)":
                st.code("scheduler.sort_by_time(tasks)", language="python")
            else:
                st.code("scheduler.sort_by_duration(tasks, ascending=True)", language="python")
        
        # Apply filters using Scheduler methods
        filtered = all_tasks
        
        if pet_filter != "All Pets":
            filtered = scheduler.filter_by_pet(filtered, pet_filter)
        
        if status_filter == "Pending Only":
            filtered = scheduler.filter_by_status(filtered, completed=False)
        elif status_filter == "Completed Only":
            filtered = scheduler.filter_by_status(filtered, completed=True)
        
        if priority_filter != "All":
            p = priority_from_string(priority_filter)
            filtered = scheduler.filter_by_priority(filtered, p)
        
        if recurring_filter:
            filtered = scheduler.filter_recurring(filtered)
        
        # Apply sorting using Scheduler methods
        if sort_by == "Priority (High → Low)":
            filtered = scheduler.sort_by_priority(filtered)
        elif sort_by == "Time (Earliest → Latest)":
            filtered = scheduler.sort_by_time(filtered)
        else:
            filtered = scheduler.sort_by_duration(filtered, ascending=True)
        
        # Display results
        st.divider()
        st.markdown(f"### 📋 Results ({len(filtered)} tasks)")
        
        if filtered:
            # Professional table display using st.table
            table_data = []
            for task in filtered:
                table_data.append({
                    "Status": "✅" if task.is_complete else "⏳",
                    "Task": task.title,
                    "Pet": task.pet_name or "—",
                    "Duration": f"{task.duration_minutes} min",
                    "Priority": f"{get_priority_emoji(task.priority)} {task.priority.name}",
                    "Time": format_time(task.scheduled_time),
                    "Recurring": "🔄" if task.is_recurring else "—"
                })
            
            st.dataframe(table_data, use_container_width=True, hide_index=True)
        else:
            st.info("No tasks match your filters.")


# =============================================================================
# TAB 4: Analytics
# =============================================================================
with tab4:
    st.subheader("📊 Pet Care Analytics")
    
    scheduler = Scheduler(owner=owner)
    all_tasks = owner.get_all_tasks()
    
    if not all_tasks:
        st.info("Add some tasks to see analytics!")
    else:
        # Overall stats
        col1, col2, col3, col4 = st.columns(4)
        
        completed = len([t for t in all_tasks if t.is_complete])
        pending = len([t for t in all_tasks if not t.is_complete])
        recurring = len(scheduler.filter_recurring(all_tasks))
        total_mins = sum(t.duration_minutes for t in all_tasks)
        
        with col1:
            st.metric("Completed", completed)
        with col2:
            st.metric("Pending", pending)
        with col3:
            st.metric("Recurring", recurring)
        with col4:
            h, m = divmod(total_mins, 60)
            st.metric("Total Time", f"{h}h {m}m")
        
        # Progress bar
        if all_tasks:
            progress = completed / len(all_tasks)
            st.progress(progress, text=f"Overall Progress: {int(progress * 100)}%")
        
        st.divider()
        
        # Per-pet breakdown
        st.markdown("### 🐾 Per-Pet Breakdown")
        
        for pet in owner.pets:
            emoji = get_species_emoji(pet.species)
            
            with st.expander(f"{emoji} **{pet.name}** ({pet.species}, {pet.age}yr)", expanded=True):
                pet_tasks = pet.tasks
                pet_completed = len(pet.get_completed_tasks())
                pet_pending = len(pet.get_pending_tasks())
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", len(pet_tasks))
                with col2:
                    st.metric("Completed", pet_completed)
                with col3:
                    st.metric("Pending", pet_pending)
                
                if pet_tasks:
                    prog = pet_completed / len(pet_tasks)
                    st.progress(prog, text=f"{int(prog * 100)}% complete")
                    
                    # Priority breakdown
                    high = len([t for t in pet_tasks if t.priority == Priority.HIGH and not t.is_complete])
                    med = len([t for t in pet_tasks if t.priority == Priority.MEDIUM and not t.is_complete])
                    low = len([t for t in pet_tasks if t.priority == Priority.LOW and not t.is_complete])
                    
                    st.caption(f"Pending by priority: 🔴 {high} high | 🟡 {med} medium | 🟢 {low} low")
        
        st.divider()
        
        # Conflict Analysis Section
        st.markdown("### ⚠️ Conflict Analysis")
        st.caption("Checking all tasks for scheduling overlaps...")
        
        warnings = scheduler.detect_conflicts(all_tasks)
        display_conflict_warnings(warnings)
        
        st.divider()
        
        # Recurring Tasks Summary
        st.markdown("### 🔄 Recurring Tasks")
        st.caption("Tasks that automatically create the next occurrence when completed")
        
        recurring_tasks = scheduler.filter_recurring(all_tasks)
        if recurring_tasks:
            for task in recurring_tasks:
                freq_text = task.frequency.name.lower()
                emoji = get_priority_emoji(task.priority)
                st.write(f"• {emoji} **{task.title}** ({task.pet_name}) — repeats {freq_text}")
                if task.scheduled_time:
                    next_date = task.scheduled_time + timedelta(days=task.frequency.value)
                    st.caption(f"  Next occurrence: {next_date.strftime('%A, %B %d')}")
        else:
            st.info("No recurring tasks set up. Add tasks with Daily/Weekly/Biweekly frequency!")


# =============================================================================
# FOOTER
# =============================================================================
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🐾 **PawPal+** v1.0")
with col2:
    st.caption("Smart Pet Care Management")
with col3:
    st.caption("Built with ❤️ using Streamlit")
