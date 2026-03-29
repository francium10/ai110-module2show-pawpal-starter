# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
I designed four classes: Task (dataclass for care activities with priority/duration), Pet (holds pet info and associated tasks), Owner (manages pets and time availability), and Scheduler (algorithmic logic for generating optimized daily plans).


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, the design changed in several meaningful ways during implementation:

1. **`Task` gained a `pet_name` field** — The original design had no link from a task back to its pet. Once `Owner.get_all_tasks()` returned a flat list, there was no way to tell which pet each task belonged to. Adding `pet_name: Optional[str]` to `Task` (automatically set when `Pet.add_task()` is called) solved this without adding complexity elsewhere.

2. **`remove_task` and `remove_pet` were rewritten to avoid list mutation during iteration** — The initial skeleton used `list.remove()` inside a `for` loop over the same list. This is a known Python bug: modifying a list while iterating it causes items to be skipped. Both methods were replaced with list comprehension rebuilds, which are safe and correct.

3. **`generate_schedule` was extended to respect `daily_limit_minutes`** — The `Scheduler` class had a `daily_limit_minutes` field but the original stub returned all tasks with no cap. The implementation now accumulates task durations and stops adding tasks once the owner's time budget is reached, making the field actually functional.

4. **`detect_conflicts` was implemented** — Originally a stub returning an empty list, it now compares `scheduled_time` windows across all timed tasks and returns any pair that overlaps based on start time and duration.

5. **`sort_by_priority` gained a secondary sort key** — The original sorted only by `priority.value`. Tasks with the same priority were returned in arbitrary order. A secondary sort by `scheduled_time` (with `datetime.max` as a fallback for unscheduled tasks) makes the output deterministic and time-aware.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
