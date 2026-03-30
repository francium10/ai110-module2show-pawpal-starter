"""
PawPal+ Streamlit Application (Extended Version)

Features:
- Priority-based scheduling algorithms
- Multiple sorting methods (time, priority, duration)
- Filtering by pet, status, priority, recurring
- Conflict detection with visual warnings
- Recurring task automation with timedelta
- JSON persistence (saves between sessions)
- "Find Next Available Slot" algorithm
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List
import os

# =============================================================================
# Import backend classes (use extended version if available)
# =============================================================================
try:
    from pawpal_system_extended import (
        Owner, Pet, Task, Scheduler, 
        Priority, Frequency, ConflictWarning, TimeSlot
    )
    EXTENDED_VERSION = True
except ImportError:
    from pawpal_system import (
        Owner, Pet, Task, Scheduler, 
        Priority, Frequency, ConflictWarning
    )
    EXTENDED_VERSION = False
    TimeSlot = None  # type: ignore


# =============================================================================
# CONFIGURATION
# =============================================================================
DATA_FILE = "data.json"

st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# SESSION STATE & PERSISTENCE (Challenge 2)
# =============================================================================
def initialize_session_state():
    """Initialize session state, loading from JSON if available."""
    if "owner" not in st.session_state:
        # Try to load from JSON file
        if EXTENDED_VERSION and os.path.exists(DATA_FILE):
            loaded_owner = Owner.load_from_json(DATA_FILE)
            if loaded_owner:
                st.session_state.owner = loaded_owner
                st.session_state.loaded_from_file = True
            else:
                st.session_state.owner = Owner(name="", available_minutes=120)
                st.session_state.loaded_from_file = False
        else:
            st.session_state.owner = Owner(name="", available_minutes=120)
            st.session_state.loaded_from_file = False
    
    if "last_schedule" not in st.session_state:
        st.session_state.last_schedule = None


def save_data():
    """Save owner data to JSON file."""
    if EXTENDED_VERSION:
        st.session_state.owner.save_to_json(DATA_FILE)


initialize_session_state()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def priority_from_string(priority_str: str) -> Priority:
    return {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}.get(
        priority_str.lower(), Priority.MEDIUM
    )

def frequency_from_string(freq_str: str) -> Frequency:
    return {
        "once": Frequency.ONCE, "daily": Frequency.DAILY,
        "weekly": Frequency.WEEKLY, "biweekly": Frequency.BIWEEKLY
    }.get(freq_str.lower(), Frequency.ONCE)

def get_priority_emoji(priority: Priority) -> str:
    return {Priority.HIGH: "🔴", Priority.MEDIUM: "🟡", Priority.LOW: "🟢"}.get(priority, "⚪")

def get_species_emoji(species: str) -> str:
    return {"dog": "🐕", "cat": "🐱", "bird": "🐦", "rabbit": "🐰"}.get(species, "🐾")

def format_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p") if dt else "Unscheduled"

def display_conflict_warnings(warnings: List[ConflictWarning]):
    if warnings:
        st.error(f"⚠️ **{len(warnings)} Scheduling Conflict(s) Detected!**")
        for i, warning in enumerate(warnings, 1):
            st.warning(
                f"**Conflict {i}:** '{warning.task_a.title}' and '{warning.task_b.title}' "
                f"overlap by **{warning.overlap_minutes} minutes**."
            )
    else:
        st.success("✅ No scheduling conflicts!")


# =============================================================================
# MAIN APPLICATION
# =============================================================================
st.title("🐾 PawPal+")
st.caption("Smart Pet Care Management System")

# Show persistence status
if EXTENDED_VERSION:
    if st.session_state.get("loaded_from_file"):
        st.success("📂 Data loaded from saved file!")

owner = st.session_state.owner


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.header("👤 Owner Setup")
    
    new_name = st.text_input("Your Name", value=owner.name)
    if new_name != owner.name:
        owner.name = new_name
        save_data()
    
    new_minutes = st.slider("Daily Time Budget (minutes)", 30, 480, owner.available_minutes, 15)
    if new_minutes != owner.available_minutes:
        owner.available_minutes = new_minutes
        save_data()
    
    st.divider()
    
    # Add Pet
    st.header("🐕 Add a Pet")
    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet Name")
        pet_species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        pet_age = st.number_input("Age (years)", 0, 30, 1)
        
        if st.form_submit_button("➕ Add Pet", use_container_width=True):
            if pet_name:
                if owner.get_pet(pet_name):
                    st.error(f"'{pet_name}' already exists!")
                else:
                    owner.add_pet(Pet(name=pet_name, species=pet_species, age=pet_age))
                    save_data()
                    st.success(f"Added {pet_name}!")
                    st.rerun()
    
    # Pet list
    if owner.pets:
        st.divider()
        st.subheader("Your Pets")
        for pet in owner.pets:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{get_species_emoji(pet.species)} **{pet.name}**")
                st.caption(f"{len(pet.get_pending_tasks())} pending")
            with col2:
                if st.button("🗑️", key=f"del_{pet.name}"):
                    owner.remove_pet(pet.name)
                    save_data()
                    st.rerun()
    
    # Save/Load buttons
    if EXTENDED_VERSION:
        st.divider()
        st.subheader("💾 Data Management")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save", use_container_width=True):
                if owner.save_to_json(DATA_FILE):
                    st.success("Saved!")
                else:
                    st.error("Save failed")
        with col2:
            if st.button("📂 Reload", use_container_width=True):
                loaded = Owner.load_from_json(DATA_FILE)
                if loaded:
                    st.session_state.owner = loaded
                    st.success("Loaded!")
                    st.rerun()


# =============================================================================
# MAIN CONTENT
# =============================================================================
if not owner.pets:
    st.info("👈 Add your pets in the sidebar to get started!")
    st.stop()

# Summary bar
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("👤 Owner", owner.name or "Not set")
with col2:
    st.metric("🐾 Pets", len(owner.pets))
with col3:
    st.metric("📋 Tasks", len(owner.get_all_tasks()))
with col4:
    st.metric("⏱️ Budget", f"{owner.available_minutes}m")

st.divider()

# Tabs
if EXTENDED_VERSION:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Tasks", "📅 Schedule", "🔍 Filter", "⏰ Find Slot", "📊 Analytics"
    ])
else:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Tasks", "📅 Schedule", "🔍 Filter", "📊 Analytics"
    ])


# =============================================================================
# TAB 1: Manage Tasks
# =============================================================================
with tab1:
    st.subheader("Manage Tasks")
    
    col_form, col_list = st.columns([1, 1])
    
    with col_form:
        st.markdown("### ➕ Add Task")
        pet_names = [p.name for p in owner.pets]
        selected_name = st.selectbox("Pet", pet_names, key="task_pet")
        selected_pet = owner.get_pet(selected_name)
        
        if selected_pet:
            with st.form("add_task", clear_on_submit=True):
                title = st.text_input("Task Name")
                c1, c2 = st.columns(2)
                with c1:
                    duration = st.number_input("Duration (min)", 1, 240, 15)
                    priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
                with c2:
                    frequency = st.selectbox("Frequency", ["Once", "Daily", "Weekly", "Biweekly"])
                    set_time = st.checkbox("Set time")
                
                task_time = None
                if set_time:
                    time_input = st.time_input("Time")
                    task_time = datetime.combine(datetime.now().date(), time_input)
                
                if st.form_submit_button("➕ Add", use_container_width=True):
                    if title:
                        selected_pet.add_task(Task(
                            title=title,
                            duration_minutes=duration,
                            priority=priority_from_string(priority),
                            frequency=frequency_from_string(frequency),
                            scheduled_time=task_time
                        ))
                        save_data()
                        st.success(f"Added '{title}'!")
                        st.rerun()
    
    with col_list:
        st.markdown(f"### 📋 {selected_name}'s Tasks")
        if selected_pet and selected_pet.tasks:
            for i, task in enumerate(selected_pet.tasks):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    status = "✅" if task.is_complete else "⏳"
                    emoji = get_priority_emoji(task.priority)
                    freq = f" 🔄" if task.is_recurring else ""
                    st.write(f"{status} {emoji} **{task.title}**{freq}")
                    st.caption(f"{task.duration_minutes}m | {format_time(task.scheduled_time)}")
                with c2:
                    if not task.is_complete:
                        if st.button("✓", key=f"done_{i}"):
                            scheduler = Scheduler(owner=owner)
                            scheduler.complete_task_with_recurrence(selected_pet, task)
                            save_data()
                            st.rerun()
                    else:
                        if st.button("↩", key=f"undo_{i}"):
                            task.mark_incomplete()
                            save_data()
                            st.rerun()
                with c3:
                    if st.button("🗑", key=f"del_task_{i}"):
                        selected_pet.remove_task(task.title)
                        save_data()
                        st.rerun()
                st.divider()
        else:
            st.info("No tasks yet.")


# =============================================================================
# TAB 2: Schedule
# =============================================================================
with tab2:
    st.subheader("📅 Generate Schedule")
    
    scheduler = Scheduler(owner=owner, daily_limit_minutes=owner.available_minutes)
    pending = owner.get_pending_tasks()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Pending", len(pending))
    with c2:
        total = sum(t.duration_minutes for t in pending)
        st.metric("Time Needed", f"{total}m")
    with c3:
        fits = "✅" if total <= owner.available_minutes else "⚠️"
        st.metric("Fits?", fits)
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        start_hour = st.selectbox("Start", list(range(5, 22)), index=3,
                                  format_func=lambda x: f"{x}:00")
    with c2:
        include_done = st.checkbox("Include completed")
    
    if st.button("🗓️ Generate", type="primary", use_container_width=True):
        schedule = scheduler.generate_schedule(include_completed=include_done)
        start = datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0)
        scheduler.assign_times(schedule, start)
        st.session_state.last_schedule = schedule
        save_data()
        st.success("Schedule generated!")
    
    if st.session_state.last_schedule:
        schedule = st.session_state.last_schedule
        
        # Conflict check
        warnings = scheduler.detect_conflicts(schedule)
        display_conflict_warnings(warnings)
        
        st.markdown("### 📋 Today's Schedule")
        total_mins = 0
        for i, task in enumerate(schedule, 1):
            c1, c2, c3 = st.columns([2, 3, 1])
            with c1:
                st.write(f"**{format_time(task.scheduled_time)}**")
            with c2:
                emoji = get_priority_emoji(task.priority)
                st.write(f"{emoji} {task.title}")
                st.caption(f"{task.pet_name} • {task.duration_minutes}m")
            with c3:
                if not task.is_complete:
                    if st.button("Done", key=f"s_{i}"):
                        pet = owner.get_pet(task.pet_name)
                        if pet:
                            scheduler.complete_task_with_recurrence(pet, task)
                            save_data()
                        st.rerun()
            total_mins += task.duration_minutes
        
        st.divider()
        h, m = divmod(total_mins, 60)
        st.metric("Total", f"{h}h {m}m")


# =============================================================================
# TAB 3: Filter & Sort
# =============================================================================
with tab3:
    st.subheader("🔍 Filter & Sort")
    
    scheduler = Scheduler(owner=owner)
    all_tasks = owner.get_all_tasks()
    
    if not all_tasks:
        st.info("Add tasks first!")
    else:
        c1, c2 = st.columns(2)
        with c1:
            pet_filter = st.selectbox("Pet", ["All"] + [p.name for p in owner.pets])
            status_filter = st.selectbox("Status", ["All", "Pending", "Completed"])
            priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
        with c2:
            sort_by = st.radio("Sort", ["Priority", "Time", "Duration"])
        
        # Apply filters
        filtered = all_tasks
        if pet_filter != "All":
            filtered = scheduler.filter_by_pet(filtered, pet_filter)
        if status_filter == "Pending":
            filtered = scheduler.filter_by_status(filtered, completed=False)
        elif status_filter == "Completed":
            filtered = scheduler.filter_by_status(filtered, completed=True)
        if priority_filter != "All":
            filtered = scheduler.filter_by_priority(filtered, priority_from_string(priority_filter))
        
        # Apply sort
        if sort_by == "Priority":
            filtered = scheduler.sort_by_priority(filtered)
        elif sort_by == "Time":
            filtered = scheduler.sort_by_time(filtered)
        else:
            filtered = scheduler.sort_by_duration(filtered)
        
        st.markdown(f"### Results ({len(filtered)})")
        if filtered:
            data = [{
                "Status": "✅" if t.is_complete else "⏳",
                "Task": t.title,
                "Pet": t.pet_name,
                "Duration": f"{t.duration_minutes}m",
                "Priority": f"{get_priority_emoji(t.priority)} {t.priority.name}",
                "Time": format_time(t.scheduled_time)
            } for t in filtered]
            st.dataframe(data, use_container_width=True, hide_index=True)


# =============================================================================
# TAB 4: Find Available Slot (Challenge 1 - Advanced Algorithm)
# =============================================================================
if EXTENDED_VERSION:
    with tab4:
        st.subheader("⏰ Find Next Available Slot")
        st.caption("Advanced algorithm to find gaps in your schedule")
        
        scheduler = Scheduler(owner=owner)
        
        st.markdown("""
        **How it works:**
        1. Analyzes all scheduled tasks for today
        2. Finds gaps between occupied time slots
        3. Returns slots that fit your required duration
        """)
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            duration_needed = st.number_input("Duration needed (minutes)", 5, 240, 30)
            day_start = st.slider("Day starts at", 5, 12, 6)
        with c2:
            day_end = st.slider("Day ends at", 17, 23, 22)
        
        if st.button("🔍 Find Available Slots", type="primary", use_container_width=True):
            slots = scheduler.find_all_available_slots(
                duration_needed=duration_needed,
                day_start_hour=day_start,
                day_end_hour=day_end
            )
            
            if slots:
                st.success(f"✅ Found {len(slots)} available slot(s)!")
                
                st.markdown("### Available Time Slots")
                for i, slot in enumerate(slots, 1):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"**Slot {i}:** {slot.start_time.strftime('%I:%M %p')} → {slot.end_time.strftime('%I:%M %p')}")
                        st.caption(f"{slot.duration_minutes} minutes available")
                    with c2:
                        if st.button("Use", key=f"slot_{i}"):
                            st.session_state.suggested_time = slot.start_time
                            st.info(f"💡 Go to Tasks tab and set time to {slot.start_time.strftime('%I:%M %p')}")
            else:
                st.warning("❌ No available slots found! Your day is fully booked.")
                st.info("💡 Try increasing the day end time or reducing task duration.")
        
        st.divider()
        
        # Smart suggestion
        st.markdown("### 🧠 Smart Time Suggestion")
        st.caption("Get AI-suggested best time based on task priority")
        
        c1, c2 = st.columns(2)
        with c1:
            suggest_duration = st.number_input("Task duration", 5, 240, 30, key="suggest_dur")
        with c2:
            suggest_priority = st.selectbox("Task priority", ["High", "Medium", "Low"], key="suggest_pri")
        
        if st.button("💡 Suggest Best Time"):
            temp_task = Task(
                title="temp",
                duration_minutes=suggest_duration,
                priority=priority_from_string(suggest_priority)
            )
            suggested = scheduler.suggest_best_time(temp_task)
            
            if suggested:
                st.success(f"**Suggested:** {suggested.start_time.strftime('%I:%M %p')} → {suggested.end_time.strftime('%I:%M %p')}")
                if suggest_priority == "High":
                    st.caption("🔴 High priority → Scheduled early in the day")
                elif suggest_priority == "Low":
                    st.caption("🟢 Low priority → Scheduled later in the day")
                else:
                    st.caption("🟡 Medium priority → Scheduled mid-day")
            else:
                st.warning("No slots available!")


# =============================================================================
# TAB: Analytics (last tab)
# =============================================================================
analytics_tab = tab5 if EXTENDED_VERSION else tab4

with analytics_tab:
    st.subheader("📊 Analytics")
    
    scheduler = Scheduler(owner=owner)
    all_tasks = owner.get_all_tasks()
    
    if not all_tasks:
        st.info("Add tasks to see analytics!")
    else:
        completed = len([t for t in all_tasks if t.is_complete])
        pending = len([t for t in all_tasks if not t.is_complete])
        recurring = len(scheduler.filter_recurring(all_tasks)) if hasattr(scheduler, 'filter_recurring') else 0
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Completed", completed)
        with c2:
            st.metric("Pending", pending)
        with c3:
            st.metric("Recurring", recurring)
        
        if all_tasks:
            progress = completed / len(all_tasks)
            st.progress(progress, text=f"{int(progress*100)}% complete")
        
        st.divider()
        
        # Per-pet stats
        for pet in owner.pets:
            with st.expander(f"{get_species_emoji(pet.species)} {pet.name}"):
                done = len(pet.get_completed_tasks())
                total = len(pet.tasks)
                if total > 0:
                    st.progress(done/total, text=f"{done}/{total} complete")
        
        # Conflicts
        st.divider()
        st.markdown("### ⚠️ Conflict Check")
        warnings = scheduler.detect_conflicts(all_tasks)
        display_conflict_warnings(warnings)


# =============================================================================
# FOOTER
# =============================================================================
st.divider()
c1, c2, c3 = st.columns(3)
with c1:
    st.caption("🐾 **PawPal+** Extended")
with c2:
    version = "v2.0 (Persistence + Slot Finder)" if EXTENDED_VERSION else "v1.0"
    st.caption(version)
with c3:
    st.caption("Built with Streamlit")
