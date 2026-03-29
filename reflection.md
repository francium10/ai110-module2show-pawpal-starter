# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I designed four classes: Task (dataclass for care activities with priority/duration), Pet (holds pet info and associated tasks), Owner (manages pets and time availability), and Scheduler (algorithmic logic for generating optimized daily plans).

The initial UML showed simple relationships:
- Owner "1" → "*" Pet (one owner has many pets)
- Pet "1" → "*" Task (one pet has many tasks)
- Scheduler "1" → "1" Owner (scheduler operates on one owner)


**b. Design changes**

Yes, the design changed in several meaningful ways during implementation:

1. **`Task` gained a `pet_name` field** — The original design had no link from a task back to its pet. Once `Owner.get_all_tasks()` returned a flat list, there was no way to tell which pet each task belonged to. Adding `pet_name: Optional[str]` to `Task` (automatically set when `Pet.add_task()` is called) solved this without adding complexity elsewhere.

2. **`remove_task` and `remove_pet` were rewritten to avoid list mutation during iteration** — The initial skeleton used `list.remove()` inside a `for` loop over the same list. This is a known Python bug: modifying a list while iterating it causes items to be skipped. Both methods were replaced with list comprehension rebuilds, which are safe and correct.

3. **`generate_schedule` was extended to respect `daily_limit_minutes`** — The `Scheduler` class had a `daily_limit_minutes` field but the original stub returned all tasks with no cap. The implementation now accumulates task durations and stops adding tasks once the owner's time budget is reached, making the field actually functional.

4. **`detect_conflicts` was implemented with duration-aware overlap checking** — Originally a stub returning an empty list, it now compares `scheduled_time` windows across all timed tasks and returns any pair that overlaps based on start time AND duration, not just exact time matches.

5. **`sort_by_priority` gained a secondary sort key** — The original sorted only by `priority.value` descending. Tasks with the same priority would come out in arbitrary order — making the output non-deterministic and difficult to test reliably. A secondary sort key on `scheduled_time` (with `datetime.max` as a fallback for unscheduled tasks) makes the output deterministic and time-aware.

6. **`Frequency` enum replaced boolean `is_recurring`** — The original design had a simple `is_recurring: bool`. This was expanded to a `Frequency` enum (ONCE=0, DAILY=1, WEEKLY=7, BIWEEKLY=14) to support multiple recurrence options. The numeric values enable easy timedelta calculation: `timedelta(days=frequency.value)`.

7. **`ConflictWarning` dataclass added** — The original design had `detect_conflicts()` return `List[Task]`. This was changed to return `List[ConflictWarning]` — a new dataclass that holds both conflicting tasks plus the overlap duration and a human-readable message.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

**Constraints considered:**
1. **Time Budget**: Tasks are capped at `daily_limit_minutes` — the owner's available time
2. **Priority**: HIGH tasks scheduled before MEDIUM and LOW
3. **Scheduled Time**: Used as secondary sort key and for conflict detection
4. **Conflicts**: Overlapping tasks are detected and warned about (but not auto-resolved)

**How I decided which constraints mattered most:**

I decided priority matters most because critical care (medications, urgent medical needs) should never be skipped, even if it means lower-priority enrichment activities get excluded. A pet owner would rather complete all the essential tasks and skip "play time" than run out of time for medication.

The greedy algorithm reflects this: it sorts by priority first, then fills the schedule until the time budget is exhausted. This guarantees HIGH priority tasks are always scheduled (if time permits any tasks at all).


**b. Tradeoffs**

**Tradeoff 1: O(n²) Conflict Detection**

The conflict detection algorithm checks every pair of timed tasks for overlap. This is O(n²) time complexity where n is the number of tasks with scheduled times.

*Why this tradeoff is reasonable:* For typical pet care scenarios (5–15 tasks per day), O(n²) is negligible — checking 15×15 = 225 pairs takes milliseconds. The benefit of catching ALL overlaps outweighs the cost of slightly more computation. A pet owner would rather see all conflicts than miss one because we optimized prematurely.

If PawPal+ scaled to hundreds of tasks, we could optimize with interval trees (O(n log n)), but that complexity isn't justified for the current use case.

**Tradeoff 2: Greedy vs Optimal Scheduling**

The scheduler uses a greedy algorithm: sort by priority, add tasks until budget is exhausted. This doesn't guarantee the mathematically optimal schedule (that would require dynamic programming or knapsack-style optimization).

*Why this tradeoff is reasonable:* For pet care, "optimal" is about respecting the owner's priorities, not maximizing total minutes scheduled. If an owner has 60 minutes and two HIGH priority tasks (30 min each), they want BOTH scheduled — not replaced by three MEDIUM priority tasks that total 60 minutes. The greedy approach matches user expectations.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI tools (Claude/Copilot) primarily in three ways:

1. **Debugging subtle bugs** — When `remove_task` and `remove_pet` were silently dropping tasks, I described the symptom ("some tasks aren't being removed correctly") and asked the AI to explain what could go wrong when modifying a list inside a loop. It correctly identified list mutation during iteration as the cause and explained why a list comprehension rebuild is the standard fix.

2. **Implementing algorithms from stubs** — For `detect_conflicts`, I described what a conflict means (two time windows that overlap) and asked for pseudocode before writing any code. The AI produced the pairwise comparison pattern (`start_a < end_b and start_b < end_a`) and the overlap duration calculation. Understanding the logic before seeing the code made it easier to verify correctness.

3. **Design clarification** — When `Owner.get_all_tasks()` returned a flat list with no way to tell which pet each task belonged to, I asked the AI how to link a task back to its pet without redesigning all the classes. It suggested adding `pet_name` to `Task`, populated automatically inside `Pet.add_task()`.

4. **Test generation** — For Phase 5, I described the behaviors I wanted to verify and asked the AI to generate test cases. It produced comprehensive tests including edge cases I hadn't considered (zero-duration tasks, exact budget matches, tasks at midnight).

**The most helpful prompts were specific and narrow:** "Here is the bug I'm seeing, here is the function, what is wrong?" rather than open-ended requests like "make my code better."


**b. Judgment and verification**

**Example 1: Rejecting naive sort_by_priority**

When I asked the AI to implement `sort_by_priority`, its first suggestion sorted only by `priority.value` descending:

```python
return sorted(tasks, key=lambda t: -t.priority.value)
```

I noticed that tasks with the same priority would come out in arbitrary order — making the output non-deterministic and difficult to test reliably. The AI hadn't considered this edge case.

I modified it myself to include a secondary sort key on `scheduled_time`:

```python
return sorted(tasks, key=lambda t: (-t.priority.value, t.scheduled_time or datetime.max))
```

Then I verified it manually by checking that two HIGH-priority tasks at different times consistently appeared in chronological order within the same priority tier.

**Example 2: Verifying conflict detection logic**

The AI suggested the overlap condition `start_a < end_b and start_b < end_a`. Before accepting it, I drew out several test cases on paper:
- Two tasks at exact same time (conflict) ✓
- Task A ends exactly when B starts (no conflict) ✓
- Task A ends 1 minute after B starts (conflict) ✓
- One task completely contains another (conflict) ✓

This manual verification gave me confidence the algorithm was correct before writing tests for it.

---

## 4. Testing and Verification

**a. What you tested**

I tested the following behaviors:

1. **Sorting correctness** — Tasks returned in chronological order when sorted by time; HIGH priority before MEDIUM before LOW when sorted by priority
2. **Recurrence logic** — Marking a daily task complete creates a new task for tomorrow using `timedelta(days=1)`; weekly creates +7 days; biweekly creates +14 days
3. **Conflict detection** — Scheduler flags overlapping time windows, not just exact time matches; calculates overlap duration correctly
4. **Filter correctness** — `filter_by_pet()` returns only that pet's tasks; `filter_by_status()` correctly separates pending and completed
5. **Schedule generation** — Respects time budget; prioritizes HIGH tasks; excludes completed tasks by default
6. **Edge cases** — Empty lists, zero-duration tasks, exact budget matches, single task exceeding budget

**Why these tests are important:**
- **Sorting bugs** would show the wrong daily schedule to users
- **Recurrence bugs** would cause missed or duplicate tasks
- **Conflict detection** prevents double-booking time slots
- **Filter bugs** would hide or show wrong tasks in the UI
- **Edge cases** ensure the system doesn't crash on unusual inputs


**b. Confidence**

**Confidence level: ⭐⭐⭐⭐⭐ (5/5)**

I'm highly confident the scheduler works correctly because:
- All 47 tests pass
- Tests cover both happy paths and edge cases
- Each algorithm (sort, filter, conflict) has dedicated test coverage
- Integration tests verify full workflows end-to-end

**Edge cases I would test next with more time:**
1. **Daylight saving time transitions** — Does a daily task scheduled for 2:30 AM handle spring-forward correctly?
2. **Very large task lists** — Performance testing with 1000+ tasks
3. **Concurrent modifications** — What if two browser tabs modify the same Owner?
4. **Timezone-aware scheduling** — Tasks spanning midnight in different timezones
5. **Leap year edge cases** — Task scheduled for Feb 28 with weekly recurrence

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the **Scheduler class architecture**. By centralizing all algorithmic logic (sorting, filtering, conflict detection, schedule generation) in one class, the code is:

1. **Testable** — Each algorithm can be tested independently
2. **Composable** — Filters can be chained, sorts can be combined
3. **Maintainable** — Adding new algorithms (e.g., `sort_by_pet()`) is trivial
4. **UI-agnostic** — The same Scheduler works for CLI and Streamlit

The `filter_chain()` method is particularly elegant — it accepts any number of filter functions and applies them sequentially, enabling complex queries like "HIGH priority tasks for Mochi that are pending."


**b. What you would improve**

If I had another iteration, I would:

1. **Add data persistence** — Currently, all data is lost when the Streamlit app restarts. I'd add SQLite or JSON file storage.

2. **Implement smarter conflict resolution** — Currently, conflicts are detected and warned about, but the owner must resolve them manually. I'd add automatic suggestions: "Move 'Walk' 15 minutes earlier to avoid conflict."

3. **Add notification scheduling** — Integrate with calendar APIs to send reminders before scheduled tasks.

4. **Improve the scheduling algorithm** — The greedy approach works but could be enhanced with:
   - Time slot awareness (don't schedule walks at 2 AM)
   - Pet-specific constraints (cats can't be walked)
   - User preference learning over time

5. **Better recurring task handling** — Currently, completing a task immediately creates the next occurrence. I'd add a "batch completion" feature and handle the case where someone misses several days.


**c. Key takeaway**

**The most important thing I learned:** When collaborating with AI tools, **you must remain the architect**.

AI is incredibly good at:
- Implementing algorithms once you describe them
- Generating boilerplate code
- Suggesting fixes for specific bugs
- Writing test cases

But AI doesn't:
- Understand your project's goals
- Make design tradeoffs that match user needs
- Notice when its suggestion breaks invariants elsewhere
- Know which edge cases matter for YOUR use case

The `sort_by_priority` example perfectly illustrates this. The AI gave a correct implementation for sorting by priority — but it didn't know that my tests required deterministic output, or that my UI would look broken if same-priority tasks appeared in random order. I had to add the secondary sort key myself.

**Being the "lead architect" means:**
1. Define WHAT you want before asking HOW to build it
2. Verify every AI suggestion against your design constraints
3. Ask narrow, specific questions ("why is this test failing?") not broad ones ("make it better")
4. Trust the AI for implementation details, but own the design decisions

This project taught me that AI amplifies developer productivity, but it doesn't replace developer judgment. The human must remain in control of the architecture.
