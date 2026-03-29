# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

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
