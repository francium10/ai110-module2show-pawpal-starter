# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a pet owner plan and manage daily care tasks for their pets using intelligent scheduling algorithms.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

---

## What Was Built

### Streamlit App (`app.py`)

The full interactive UI with three tabs:

| Tab | Feature |
|-----|---------|
| **Add Tasks** | Select a pet, fill out a task form (name, duration, priority, recurrence, optional time), and manage the task list per pet |
| **Generate Schedule** | Choose a start time, generate an optimized schedule with conflict detection, and mark tasks done inline |
| **Overview** | Per-pet stats (total/completed/pending), progress bars, priority breakdowns, and a full task table |

The **sidebar** lets the owner set their name, daily time budget (slider), and add/remove pets by species and age.

### Core Backend (`pawpal_system.py`)

Four main classes power the app:

#### `Task`
Represents a single care task.

| Attribute | Type | Description |
|-----------|------|-------------|
| `title` | `str` | Task name |
| `duration_minutes` | `int` | How long it takes |
| `priority` | `Priority` | LOW / MEDIUM / HIGH |
| `frequency` | `Frequency` | ONCE / DAILY / WEEKLY / BIWEEKLY |
| `scheduled_time` | `datetime` | Optional scheduled start |
| `is_complete` | `bool` | Completion status |
| `pet_name` | `str` | Which pet this belongs to |

Key methods: `mark_complete()` (auto-creates next occurrence for recurring tasks), `mark_incomplete()`, `reschedule(new_time)`.

#### `Pet`
Holds a pet's info and task list. Methods: `add_task()`, `remove_task()`, `get_pending_tasks()`, `get_completed_tasks()`.

#### `Owner`
Top-level container for all pets. Tracks daily time budget. Methods: `add_pet()`, `remove_pet()`, `get_pet()`, `get_all_tasks()`, `get_pending_tasks()`.

#### `Scheduler`
The scheduling "brain." Accepts an `Owner` and a `daily_limit_minutes` budget. See [Smarter Scheduling](#smarter-scheduling) below for full algorithm details.

### CLI Demo (`main.py`)

Run `python main.py` to see a fully narrated demonstration of every algorithm on sample data (two pets, eight tasks added intentionally out of order):

```
python main.py
```

Sections shown:
- Initial data (tasks in insertion order)
- Sorting by time / priority / duration
- Filtering by pet / priority / status / recurrence / chained filters
- Conflict detection with overlap minutes
- Recurring task completion and auto-next-occurrence creation
- Optimized schedule generation and chronological view
- Summary statistics

---

## Project Structure

```
pawpal-starter/
├── app.py               # Streamlit UI
├── pawpal_system.py     # Core classes: Task, Pet, Owner, Scheduler
├── main.py              # CLI demo / algorithmic showcase
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

Run the CLI demo:

```bash
python main.py
```

---

## Data Model Overview

```
Owner
 └── available_minutes (daily budget)
 └── pets: List[Pet]
       └── tasks: List[Task]
             └── priority: Priority (LOW | MEDIUM | HIGH)
             └── frequency: Frequency (ONCE | DAILY | WEEKLY | BIWEEKLY)
             └── scheduled_time: datetime | None
```

`Scheduler` wraps an `Owner` and operates on its tasks without modifying structure — all sort/filter methods return new lists.

---

## Smarter Scheduling

PawPal+ includes intelligent algorithms for optimized pet care planning:

### Sorting
- **By Time**: Chronological view of your day
- **By Priority**: Critical tasks first (HIGH → MEDIUM → LOW)
- **By Duration**: Plan around available time slots

### Filtering
- Filter tasks by specific pet, completion status, or priority level
- Chain multiple filters for complex queries

### Recurring Tasks
- Set tasks to repeat DAILY, WEEKLY, or BIWEEKLY
- When completed, the next occurrence is automatically created
- Uses Python's `timedelta` for accurate date calculation

### Conflict Detection
- Detects overlapping time windows (not just exact matches)
- Returns detailed warnings with overlap duration
- Identifies same-pet vs cross-pet conflicts
