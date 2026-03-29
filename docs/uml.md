classDiagram
    class Owner {
        +str name
        +int available_minutes
        +List~Pet~ pets
        +add_pet(pet: Pet)
        +remove_pet(pet_name: str) bool
        +get_all_tasks() List~Task~
        +get_pending_tasks() List~Task~
        +get_pet(pet_name: str) Pet
    }
    
    class Pet {
        +str name
        +str species
        +int age
        +List~Task~ tasks
        +add_task(task: Task)
        +remove_task(task_title: str) bool
        +get_pending_tasks() List~Task~
    }
    
    class Task {
        +str title
        +int duration_minutes
        +Priority priority
        +bool is_recurring
        +datetime scheduled_time
        +bool is_complete
        +str pet_name
        +mark_complete()
        +mark_incomplete()
        +reschedule(new_time: datetime)
    }
    
    class Scheduler {
        +Owner owner
        +int daily_limit_minutes
        +generate_schedule() List~Task~
        +detect_conflicts(tasks) List~Task~
        +sort_by_priority(tasks) List~Task~
        +assign_times(tasks, start)
        +format_schedule(tasks) str
    }
    
    Owner "1" --> "*" Pet : owns
    Pet "1" --> "*" Task : has
    Scheduler "1" --> "1" Owner : schedules for
```

### 2. **Test File Location**
Move `test_pawpal.py` into a `tests/` folder:
```
PawPal+/
├── tests/
│   ├── __init__.py      # Create this (empty file)
│   └── test_pawpal.py   # Move here