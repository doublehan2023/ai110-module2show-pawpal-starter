# PawPal+ (Module 2 Project)

**PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.
<img width="920" height="713" alt="Screenshot 2026-03-29 at 6 41 03 PM" src="https://github.com/user-attachments/assets/7d6d16c1-1687-4f56-a4b4-d35f7f166f4c" />


## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

**Owner & Pet Setup**
Create an owner profile and register one or more pets with species, breed, and medical needs. Medical needs automatically elevate medication tasks in the priority queue.

**Task Management**
Add reusable care task templates (walk, feed, meds, groom, enrichment) with a name, duration, priority level, frequency, and preferred time window. Tasks are stored as templates and reused across planning cycles.

**Priority-Aware Scheduling**
The scheduler ranks tasks by priority (high → medium → low) before time-fitting begins. Medication tasks for pets with active medical needs receive an automatic boost above other high-priority tasks. On low-energy days, all low-priority tasks are dropped before scheduling starts.

**Greedy Time-Block Fitting**
Available time is defined as one or more `TimeBlock` windows. The scheduler places tasks greedily in priority order, matching each task to its preferred window first, then filling with non-matching tasks. Tasks that exceed the remaining block time or the daily task cap are deferred, not dropped.

**Chronological Sorting**
Any task list can be sorted by preferred time window (morning → afternoon → evening → no preference), with priority as a tiebreaker within each window. Used in the UI to display tasks as a readable daily timeline, separate from the urgency-based ranking used during scheduling.

**Task Filtering**
Query the task list by pet name, completion status, or both. Completion is resolved against live task history — a task is considered done only if a non-skipped log exists for today.

**Conflict Detection**
After scheduling, every pair of tasks is checked for time-window overlap using the standard interval test (`a.start < b.end AND b.start < a.end`). Each conflict produces a warning naming both tasks, their start–end times, and whether they belong to the same pet or different pets. Warnings are attached to every `DailyPlan` and surfaced in the UI with `st.warning`.

**Automatic Recurrence**
Marking a task complete logs the completion and registers a fresh copy (new ID) in the template list for its next due date — the following day for daily tasks, seven days out for weekly ones. `as-needed` tasks are not recurred automatically.

**Plain-English Explanation**
Every generated plan includes a reasoning string that describes why each task was scheduled or deferred, notes when medical urgency influenced ordering, and flags low-energy day adjustments.

---

## Smarter Scheduling

Beyond the baseline priority-and-time-block scheduler, four new features were added to `pawpal_system.py`:

### Task filtering (`Scheduler.filter_tasks`)
Query `task_templates` by pet name, completion status, or both.  Completion is resolved against live `task_history` — a task counts as done only if a non-skipped log exists for today.

```python
scheduler.filter_tasks(pet_name="Luna", completed=False)  # Luna's pending tasks
scheduler.filter_tasks(completed=True)                    # everything done today
```

### Chronological sort (`Scheduler.sort_by_time`)
Orders any task list by preferred time window (morning → afternoon → evening → no window), using priority as a tiebreaker within each window.  Independent of `rank_by_priority` — use this for readable timelines, use `rank_by_priority` when packing by urgency.

```python
ordered = scheduler.sort_by_time(scheduler.task_templates)
```

### Automatic recurrence (`CareTask.schedule_next_occurrence` + `Scheduler.complete_task`)
Marking a task complete with `complete_task` logs the completion *and* registers a fresh copy of the task (new UUID) in `task_templates` for the next due date — tomorrow for daily tasks, in seven days for weekly ones.  `as-needed` tasks are not recurred automatically.

```python
log, next_task = scheduler.complete_task(scheduled_task)
# next_task.get_next_due_date() → date of next occurrence
```

### Conflict detection (`Scheduler.detect_conflicts`)
Scans every pair of scheduled tasks for time-window overlap using the standard interval test (`a.start < b.end AND b.start < a.end`).  Returns a list of warning strings — one per conflict — labelled `[same pet]` or `[different pets]`.  Never raises; an empty list means the plan is conflict-free.  Also wired into `generate_plan` so warnings are attached to every `DailyPlan`.

```python
warnings = scheduler.detect_conflicts(plan.scheduled_tasks)
# e.g. "WARNING: 'Luna: arthritis meds' (08:00 AM–08:05 AM) overlaps with ..."
```

---

## Testing PawPal+

### Run the tests

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Test | What it verifies |
|---|---|
| `test_mark_complete_sets_completed_at` | `TaskLog.mark_complete()` stamps `completed_at` and clears skip state |
| `test_add_task_increases_pet_task_count` | `Pet.get_active_task_templates()` correctly filters tasks by pet |
| `test_sort_by_time_chronological_order` | Tasks are returned in window order: morning → afternoon → evening |
| `test_sort_by_time_no_window_goes_last` | Tasks with no preferred window sort after all windowed tasks |
| `test_complete_daily_task_creates_next_occurrence` | Completing a daily task adds exactly one new template with a fresh ID |
| `test_complete_as_needed_task_does_not_recur` | Completing an as-needed task returns `None` and does not grow templates |
| `test_detect_conflicts_flags_overlapping_tasks` | Overlapping scheduled tasks produce a warning naming both tasks |
| `test_detect_conflicts_adjacent_tasks_no_warning` | Back-to-back tasks that share only an endpoint produce no warning |

### Confidence Level: ★★★★☆ (4/5)

The core scheduling behaviors — sorting, recurrence, and conflict detection — are well-covered and all 8 tests pass. One star is withheld because the tests do not yet cover the full `generate_plan` pipeline end-to-end, `fit_to_time_blocks` overflow/deferral behavior, or the `is_due_today` weekly boundary edge case (task completed exactly 7 days ago).

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
