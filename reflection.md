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

**Constraints considered:**
1. **Time Budget**: Tasks are capped at `daily_limit_minutes`
2. **Priority**: HIGH tasks scheduled before MEDIUM and LOW
3. **Scheduled Time**: Tasks sorted chronologically when time-based view needed
4. **Conflicts**: Overlapping tasks are detected and warned about

I decided priority matters most because critical care (medications, urgent needs) 
should never be skipped, even if it means lower-priority enrichment activities 
get excluded.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff**: The conflict detection algorithm checks for overlapping time windows 
(duration-aware), not just exact time matches. This is more thorough but has O(n²) 
time complexity.

**Why reasonable**: For typical pet care scenarios (5-15 tasks/day), O(n²) is 
negligible. The benefit of catching all overlaps outweighs the cost of slightly 
more computation. A pet owner would rather see all conflicts than miss one.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI primarily in three ways:

1. **Debugging subtle bugs** — When `remove_task` and `remove_pet` were silently dropping tasks, I described the symptom ("some tasks aren't being removed correctly") and asked the AI to explain what could go wrong when modifying a list inside a loop. It correctly identified list mutation during iteration as the cause and explained why a list comprehension rebuild is the standard fix.

2. **Implementing algorithms from stubs** — For `detect_conflicts`, I described what a conflict means (two time windows that overlap) and asked for pseudocode before writing any code. The AI produced the pairwise comparison pattern (`start_a < end_b and start_b < end_a`) and the overlap duration calculation. Understanding the logic before seeing the code made it easier to verify.

3. **Design clarification** — When `Owner.get_all_tasks()` returned a flat list with no way to tell which pet each task belonged to, I asked the AI how to link a task back to its pet without redesigning all the classes. It suggested adding `pet_name` to `Task`, populated automatically inside `Pet.add_task()`.

The most helpful prompts were specific and narrow: "here is the bug I'm seeing, here is the function, what is wrong?" rather than open-ended requests like "make my code better."

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When I asked the AI to implement `sort_by_priority`, its first suggestion sorted only by `priority.value` descending. I noticed that tasks with the same priority would come out in arbitrary order — making the output non-deterministic and difficult to test reliably. The AI hadn't considered this edge case. I added the secondary sort key on `scheduled_time` (with `datetime.max` as a fallback for unscheduled tasks) myself, then verified it manually by checking that two HIGH-priority tasks at different times consistently appeared in chronological order within the same priority tier.

---

## 4. Testing and Verification
**a.What you tested**
- What behaviors did you test?
- Why were these tests important?

I tested:
1. **Sorting correctness**: Tasks are returned in chronological order when sorted by time
2. **Recurrence logic**: Marking a daily task complete creates a new task for tomorrow (using `timedelta(days=1)`)
3. **Conflict detection**: Scheduler flags overlapping time windows, not just exact matches
4. **Filter correctness**: Filter by pet, status, priority all return correct subsets
5. **Schedule generation**: Respects time budget and prioritizes HIGH tasks

These tests are important because:
- Sorting bugs would show the wrong daily schedule to users
- Recurrence bugs would cause missed or duplicate tasks
- Conflict detection prevents double-booking time slots
- Filter bugs would hide or show wrong tasks in the UI

**b. Confidence**
- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm highly confident (5/5) that the scheduler works correctly because:
- All 47 tests pass
- Tests cover both happy paths and edge cases
- Each algorithm (sort, filter, conflict) has dedicated test coverage

Edge cases I would test next with more time:
- Daylight saving time transitions for recurring tasks
- Very large task lists (1000+ tasks) for performance
- Concurrent modifications (multiple users)
- Timezone-aware scheduling


---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The part I'm most satisfied with is the conflict detection and schedule generation working together as a coherent system. `detect_conflicts` catches overlapping time windows using a duration-aware pairwise comparison, and `generate_schedule` enforces the daily time budget while respecting priority order — neither feature was in the original stub, and both required real algorithmic thinking to get right. Seeing 47 tests pass across sorting, filtering, recurrence, and conflict logic gave me confidence that the system actually behaves correctly, not just most of the time.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would redesign the `generate_schedule` algorithm from a greedy approach to a proper constraint-based one. The current greedy method (sort by priority, add tasks until the time budget is full) can miss better combinations — for example, one HIGH-priority task of 90 minutes might block two MEDIUM tasks totaling 60 minutes that together provide more coverage. A knapsack-style dynamic programming approach would find the optimal task set within the time budget. I would also add timezone-aware `scheduled_time` handling, since the current `datetime` objects are naive and would break for owners across time zones or during daylight saving transitions.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important thing I learned is that AI is most useful when you already understand the problem well enough to evaluate its output. When I asked vague questions ("make my code better"), the suggestions were generic and sometimes wrong. When I asked narrow, specific questions ("here is the bug, here is the function, what is wrong?"), the AI gave precise, verifiable answers. The moment I caught the missing secondary sort key on `scheduled_time` — something the AI didn't suggest on its own — reinforced that AI is a fast first-draft tool, not a correctness guarantee. Designing the system yourself first, then using AI to fill in implementation details, produced better results than asking AI to design for you.
