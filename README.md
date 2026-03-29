# 🐾 PawPal+ 

**Smart Pet Care Management System with Intelligent Scheduling**

PawPal+ is a Streamlit application that helps pet owners plan and manage daily care tasks using intelligent scheduling algorithms. It features priority-based scheduling, conflict detection, recurring task automation, and comprehensive filtering and sorting capabilities.

---

## 📸 Demo

*Screenshot placeholder - add your app screenshot here:*

```markdown
<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank">
  <img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' />
</a>
```

---

## ✨ Features

### Core Functionality
| Feature | Description |
|---------|-------------|
| **Multi-Pet Support** | Manage tasks for multiple pets (dogs, cats, birds, rabbits) |
| **Task Management** | Add, edit, complete, and delete care tasks |
| **Time Budgeting** | Set daily available minutes for pet care |
| **Progress Tracking** | Visual progress bars and completion statistics |

### 🧠 Smart Scheduling Algorithms

#### Priority-Based Scheduling
- Tasks sorted by priority: **HIGH → MEDIUM → LOW**
- Same-priority tasks use scheduled time as tiebreaker
- Greedy algorithm fills schedule until time budget reached

```python
# Algorithm: sort_by_priority()
# Key: (-priority.value, scheduled_time or datetime.max)
```

#### Sorting Methods
| Method | Description | Use Case |
|--------|-------------|----------|
| `sort_by_time()` | Chronological order | View your day timeline |
| `sort_by_priority()` | HIGH first, then time | Optimized scheduling |
| `sort_by_duration()` | Shortest/longest first | Time slot planning |

#### Filtering Methods
| Method | Description |
|--------|-------------|
| `filter_by_pet(tasks, pet_name)` | Tasks for specific pet |
| `filter_by_status(tasks, completed)` | Pending or completed |
| `filter_by_priority(tasks, priority)` | HIGH/MEDIUM/LOW only |
| `filter_by_time_range(tasks, start, end)` | Within time window |
| `filter_recurring(tasks)` | Recurring tasks only |
| `filter_chain(tasks, *filters)` | Combine multiple filters |

### 🔄 Recurring Task Automation

Tasks can be set to repeat automatically:

| Frequency | Days Added | Example |
|-----------|------------|---------|
| `DAILY` | +1 day | Morning walk |
| `WEEKLY` | +7 days | Grooming session |
| `BIWEEKLY` | +14 days | Vet checkup |

When you complete a recurring task, the next occurrence is **automatically created** using Python's `timedelta`:

```python
next_time = scheduled_time + timedelta(days=frequency.value)
```

### ⚠️ Conflict Detection

The scheduler detects overlapping tasks and warns you:

- **Duration-aware**: Checks if time windows overlap (not just start times)
- **Overlap calculation**: Shows exactly how many minutes conflict
- **Same-pet vs cross-pet**: Identifies conflict type
- **Visual warnings**: Clear UI alerts with resolution tips

```python
# Algorithm: O(n²) pairwise comparison
# Conflict condition: start_a < end_b AND start_b < end_a
```

---

## 📁 Project Structure

```
pawpal-starter/
├── app.py               # Streamlit UI (4 tabs)
├── pawpal_system.py     # Core classes: Task, Pet, Owner, Scheduler
├── main.py              # CLI demo / algorithm showcase
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── reflection.md        # Design reflection document
├── docs/
│   └── uml_final.md     # Final UML diagrams (Mermaid.js)
└── tests/
    ├── __init__.py
    ├── test_pawpal.py   # Pytest test suite
    └── run_tests.py     # Standalone test runner
```

---

## 🚀 Setup

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone or navigate to project
cd pawpal-starter

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the App

```bash
streamlit run app.py
```

### Run CLI Demo

```bash
python main.py
```

---

## 🧪 Testing PawPal+

### Running Tests

**With pytest installed:**
```bash
pip install pytest
python -m pytest tests/test_pawpal.py -v
```

**Without pytest (standalone runner):**
```bash
python tests/run_tests.py
```

### Test Coverage

The test suite includes **47 tests** covering:

| Category | Tests | Coverage |
|----------|-------|----------|
| Task | 11 | Creation, completion, recurring, reschedule |
| Pet | 7 | Add/remove tasks, pending/completed filtering |
| Owner | 7 | Add/remove pets, aggregation methods |
| Sorting | 4 | By time, priority, duration |
| Filtering | 6 | By pet, status, priority, chain |
| Conflicts | 6 | Overlap detection, same/different pets |
| Schedule | 5 | Time limits, priority ordering |
| Integration | 2 | Full workflows |
| Edge Cases | 3 | Zero duration, budget limits |

### Confidence Level

⭐⭐⭐⭐⭐ **(5/5 stars)**

All 47 tests pass. The suite covers happy paths, edge cases, and algorithm correctness.

---

## 🏗️ Architecture

### Data Model

```
Owner
 └── name: str
 └── available_minutes: int (daily budget)
 └── pets: List[Pet]
       └── name, species, age
       └── tasks: List[Task]
             └── title, duration_minutes
             └── priority: Priority (LOW | MEDIUM | HIGH)
             └── frequency: Frequency (ONCE | DAILY | WEEKLY | BIWEEKLY)
             └── scheduled_time: datetime | None
             └── is_complete: bool
             └── pet_name: str (back-reference)
```

### Scheduler Role

`Scheduler` wraps an `Owner` and provides all algorithmic operations:
- Sorting and filtering (returns new lists, doesn't mutate)
- Schedule generation with time budget constraints
- Conflict detection with detailed warnings
- Recurring task management

See `docs/uml_final.md` for complete class and sequence diagrams.

---

## 📋 UI Tabs

| Tab | Purpose |
|-----|---------|
| **📝 Manage Tasks** | Add tasks, mark complete, handle recurring |
| **📅 Smart Schedule** | Generate optimized schedule, see conflicts |
| **🔍 Filter & Sort** | Explore sorting/filtering algorithms |
| **📊 Analytics** | Per-pet stats, progress, conflict analysis |

---

## 🤖 AI-Assisted Development

This project was built using AI assistance (GitHub Copilot / Claude) with the developer(Francis Lufwendo) as **lead architect**:

- **Design decisions**: Human-driven class structure and algorithm choices
- **Implementation**: AI-assisted code generation with human verification
- **Debugging**: AI helped identify subtle bugs (list mutation during iteration)
- **Testing**: AI generated test cases, human verified coverage

See `reflection.md` for detailed AI collaboration notes.

---

## 📄 License

This project was created for educational purposes as part of a software engineering course.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- AI assistance from GitHub Copilot and Claude
- Course: Module 2 - Object-Oriented Design with AI
