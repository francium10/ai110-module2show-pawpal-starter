# PawPal+ Final UML Diagram

## Class Diagram (Mermaid.js)

```mermaid
classDiagram
    direction TB
    
    %% Enums
    class Priority {
        <<enumeration>>
        LOW = 1
        MEDIUM = 2
        HIGH = 3
        +__str__() str
    }
    
    class Frequency {
        <<enumeration>>
        ONCE = 0
        DAILY = 1
        WEEKLY = 7
        BIWEEKLY = 14
        +__str__() str
    }
    
    %% Core Classes
    class Task {
        +title: str
        +duration_minutes: int
        +priority: Priority
        +frequency: Frequency
        +scheduled_time: datetime
        +is_complete: bool
        +pet_name: str
        --
        +is_recurring: bool «property»
        +mark_complete() Task
        +mark_incomplete() void
        +reschedule(new_time) void
        -_create_next_occurrence() Task
        +__str__() str
    }
    
    class Pet {
        +name: str
        +species: str
        +age: int
        +tasks: List~Task~
        --
        +add_task(task) void
        +remove_task(title) bool
        +get_pending_tasks() List~Task~
        +get_completed_tasks() List~Task~
        +__str__() str
    }
    
    class Owner {
        +name: str
        +available_minutes: int
        +pets: List~Pet~
        --
        +add_pet(pet) void
        +remove_pet(name) bool
        +get_pet(name) Pet
        +get_all_tasks() List~Task~
        +get_pending_tasks() List~Task~
        +__str__() str
    }
    
    class ConflictWarning {
        +task_a: Task
        +task_b: Task
        +message: str
        +overlap_minutes: int
        +__str__() str
    }
    
    class Scheduler {
        +owner: Owner
        +daily_limit_minutes: int
        --
        «Sorting»
        +sort_by_time(tasks) List~Task~
        +sort_by_priority(tasks) List~Task~
        +sort_by_duration(tasks, ascending) List~Task~
        --
        «Filtering»
        +filter_by_pet(tasks, pet_name) List~Task~
        +filter_by_status(tasks, completed) List~Task~
        +filter_by_priority(tasks, priority) List~Task~
        +filter_by_time_range(tasks, start, end) List~Task~
        +filter_recurring(tasks) List~Task~
        +filter_chain(tasks, *filters) List~Task~
        --
        «Conflict Detection»
        +detect_conflicts(tasks) List~ConflictWarning~
        +get_conflict_free_tasks(tasks) Tuple
        --
        «Recurring Management»
        +complete_task_with_recurrence(pet, task) Task
        +get_recurring_tasks() List~Task~
        --
        «Schedule Generation»
        +generate_schedule(include_completed) List~Task~
        +generate_schedule_by_time() List~Task~
        +get_total_scheduled_minutes(tasks) int
        +assign_times(tasks, start) List~Task~
        --
        «Formatting»
        +format_schedule(tasks) str
        +format_conflicts(warnings) str
    }
    
    %% Relationships
    Owner "1" --> "*" Pet : owns
    Pet "1" --> "*" Task : has
    Scheduler "1" --> "1" Owner : schedules for
    Scheduler ..> ConflictWarning : creates
    Task --> Priority : has
    Task --> Frequency : has
    
    %% Notes
    note for Task "mark_complete() returns next Task
    if recurring, using timedelta"
    
    note for Scheduler "Algorithms:
    - Priority-based greedy scheduling
    - O(n²) conflict detection
    - Chain filtering pattern"
```

## Sequence Diagram: Generate Schedule

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant S as Scheduler
    participant O as Owner
    participant T as Task
    
    UI->>S: generate_schedule()
    S->>O: get_pending_tasks()
    O-->>S: List[Task]
    S->>S: sort_by_priority(tasks)
    
    loop For each task (by priority)
        S->>S: Check if fits in daily_limit_minutes
        alt Fits
            S->>S: Add to schedule
        else Doesn't fit
            S->>S: Skip (excluded)
        end
    end
    
    S-->>UI: scheduled_tasks
    
    UI->>S: assign_times(schedule, start_time)
    
    loop For each scheduled task
        S->>T: reschedule(current_time)
        S->>S: current_time += duration
    end
    
    UI->>S: detect_conflicts(schedule)
    S-->>UI: List[ConflictWarning]
```

## Sequence Diagram: Complete Recurring Task

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant S as Scheduler
    participant P as Pet
    participant T as Task
    
    UI->>S: complete_task_with_recurrence(pet, task)
    S->>T: mark_complete()
    T->>T: is_complete = True
    
    alt task.frequency != ONCE and scheduled_time exists
        T->>T: _create_next_occurrence()
        Note over T: Uses timedelta(days=frequency.value)
        T-->>S: next_task
        S->>P: add_task(next_task)
        S-->>UI: next_task
    else Non-recurring or no time
        T-->>S: None
        S-->>UI: None
    end
```

## Data Flow Diagram

```mermaid
flowchart TD
    subgraph Input
        A[User adds tasks via UI]
        B[Set priorities & frequencies]
        C[Set time budget]
    end
    
    subgraph Processing
        D[Scheduler.sort_by_priority]
        E[Scheduler.generate_schedule]
        F[Scheduler.detect_conflicts]
        G[Scheduler.assign_times]
    end
    
    subgraph Output
        H[Optimized Schedule]
        I[Conflict Warnings]
        J[Excluded Tasks]
    end
    
    A --> D
    B --> D
    C --> E
    D --> E
    E --> F
    E --> G
    F --> I
    G --> H
    E --> J
    
    style D fill:#e1f5fe
    style E fill:#e1f5fe
    style F fill:#ffcdd2
    style G fill:#e1f5fe
```

---

## Key Design Decisions

1. **Task.pet_name field**: Added to maintain back-reference when tasks are flattened via `Owner.get_all_tasks()`

2. **Frequency enum**: Replaced boolean `is_recurring` with enum for multiple recurrence options (DAILY=1, WEEKLY=7, BIWEEKLY=14)

3. **ConflictWarning dataclass**: Encapsulates conflict info including overlap duration calculation

4. **Scheduler as algorithm container**: All sorting/filtering/scheduling logic centralized in one class

5. **Immutable sorting**: All sort/filter methods return new lists, don't modify originals
