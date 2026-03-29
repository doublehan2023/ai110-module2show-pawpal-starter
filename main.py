"""
main.py — manual testing ground for PawPal+ scheduling logic.
Run with: python main.py
"""

from datetime import datetime, timedelta
from pawpal_system import (
    Pet, Owner, CareTask,
    TimeBlock, OwnerConstraints,
    Scheduler,
)

# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------
luna = Pet(
    id="pet-1",
    name="Luna",
    species="dog",
    breed="Labrador",
    age=3,
    weight=28.0,
    owner_id="owner-1",
    medical_needs=["arthritis"],
)

mochi = Pet(
    id="pet-2",
    name="Mochi",
    species="cat",
    breed="Ragdoll",
    age=5,
    weight=4.5,
    owner_id="owner-1",
    medical_needs=[],
)

# ---------------------------------------------------------------------------
# Tasks  — added OUT OF ORDER to demo sort_by_time()
#   insertion order: evening → afternoon → no window → morning
# ---------------------------------------------------------------------------
today = datetime.now().replace(second=0, microsecond=0)

tasks = [
    # evening tasks first (intentionally out of order)
    CareTask(
        id="t3", pet_id="pet-1", pet=luna,
        name="Luna: evening walk",
        task_type="walk",        duration_minutes=30,
        priority="medium",       frequency="daily",
        preferred_time_window="evening",
    ),
    CareTask(
        id="t6", pet_id="pet-2", pet=mochi,
        name="Mochi: grooming brush",
        task_type="groom",       duration_minutes=10,
        priority="low",          frequency="weekly",
        preferred_time_window="evening",
    ),
    # afternoon task
    CareTask(
        id="t5", pet_id="pet-2", pet=mochi,
        name="Mochi: puzzle toy",
        task_type="enrichment",  duration_minutes=15,
        priority="medium",       frequency="daily",
        preferred_time_window="afternoon",
    ),
    # task with no preferred window
    CareTask(
        id="t7", pet_id="pet-1", pet=luna,
        name="Luna: vet check notes",
        task_type="meds",        duration_minutes=5,
        priority="medium",       frequency="as-needed",
        preferred_time_window=None,
    ),
    # morning tasks last (should end up first after sort)
    CareTask(
        id="t2", pet_id="pet-1", pet=luna,
        name="Luna: arthritis meds",
        task_type="meds",        duration_minutes=5,
        priority="high",         frequency="daily",
        preferred_time_window="morning",
        notes="Give with food",
    ),
    CareTask(
        id="t1", pet_id="pet-1", pet=luna,
        name="Luna: morning walk",
        task_type="walk",        duration_minutes=30,
        priority="high",         frequency="daily",
        preferred_time_window="morning",
    ),
    CareTask(
        id="t4", pet_id="pet-2", pet=mochi,
        name="Mochi: breakfast",
        task_type="feed",        duration_minutes=10,
        priority="high",         frequency="daily",
        preferred_time_window="morning",
    ),
]

# ---------------------------------------------------------------------------
# Owner + constraints (2-hr morning block, 1-hr evening block)
# ---------------------------------------------------------------------------
morning_start = today.replace(hour=8, minute=0)
evening_start = today.replace(hour=18, minute=0)

constraints = OwnerConstraints(
    available_time_blocks=[
        TimeBlock(start=morning_start, end=morning_start + timedelta(hours=2)),
        TimeBlock(start=evening_start, end=evening_start + timedelta(hours=1)),
    ],
    energy_level="medium",
    max_tasks_per_day=6,
)

jordan = Owner(
    id="owner-1",
    name="Jordan",
    email="jordan@example.com",
    phone="555-0100",
    pets=[luna, mochi],
    constraints=constraints,
)

# ---------------------------------------------------------------------------
# Conflict demo — two tasks that intentionally share the same start time
# ---------------------------------------------------------------------------
from pawpal_system import ScheduledTask as ST

conflict_time = today.replace(hour=8, minute=0)

conflicting_scheduled = [
    ST(
        task_id="t2",
        task=tasks[-2],   # Luna: arthritis meds  (morning, 5 min)
        scheduled_time=conflict_time,
        duration_minutes=5,
        priority="high",
    ),
    ST(
        task_id="t4",
        task=tasks[-1],   # Mochi: breakfast  (morning, 10 min)
        scheduled_time=conflict_time,   # same start → overlap
        duration_minutes=10,
        priority="high",
    ),
    ST(
        task_id="t3",
        task=tasks[0],    # Luna: evening walk — no overlap, starts after both above
        scheduled_time=conflict_time + timedelta(minutes=30),
        duration_minutes=30,
        priority="medium",
    ),
]

# ---------------------------------------------------------------------------
# Run scheduler
# ---------------------------------------------------------------------------
scheduler = Scheduler(
    owner=jordan,
    pets=[luna, mochi],
    task_templates=tasks,
    constraints=constraints,
    task_history=[],
)

plan = scheduler.generate_plan()

# ---------------------------------------------------------------------------
# Print today's schedule
# ---------------------------------------------------------------------------
print("=" * 55)
print(f"  PAWPAL+ — TODAY'S SCHEDULE")
print(f"  Owner : {jordan.name}")
print(f"  Pets  : {', '.join(p.name for p in jordan.pets)}")
print(f"  Date  : {plan.date.strftime('%A, %B %d %Y')}")
print("=" * 55)

for i, st in enumerate(plan.scheduled_tasks, 1):
    print(
        f"  {i}. {st.scheduled_time.strftime('%I:%M %p')}  "
        f"[{st.priority.upper():6}]  {st.task.name}  ({st.duration_minutes} min)"
    )

if plan.deferred_tasks:
    print("\n  -- Deferred (not enough time today) --")
    for t in plan.deferred_tasks:
        print(f"     • {t.name}  ({t.duration_minutes} min, {t.priority} priority)")

print("=" * 55)
print(f"  Total time : {plan.total_time_minutes} min / {constraints.get_available_minutes()} min available")
print("=" * 55)
print()
print(plan.explain())

if plan.warnings:
    print()
    for w in plan.warnings:
        print(f"  {w}")

# ---------------------------------------------------------------------------
# Conflict detection demo — run detect_conflicts() on the hand-crafted list
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("  CONFLICT DETECTION DEMO")
print("  (two tasks forced to the same start time)")
print("=" * 55)
print("  Scheduled tasks passed in:")
for st in conflicting_scheduled:
    end = st.scheduled_time + timedelta(minutes=st.duration_minutes)
    print(
        f"    • {st.task.name:<28} "
        f"{st.scheduled_time.strftime('%I:%M %p')}–{end.strftime('%I:%M %p')}"
    )
print()
demo_warnings = scheduler.detect_conflicts(conflicting_scheduled)
if demo_warnings:
    for w in demo_warnings:
        print(f"  {w}")
else:
    print("  No conflicts found.")

# ---------------------------------------------------------------------------
# Demo: sort_by_time()
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("  SORT_BY_TIME — tasks ordered morning → evening")
print("=" * 55)
sorted_tasks = scheduler.sort_by_time(tasks)
for i, t in enumerate(sorted_tasks, 1):
    window = t.preferred_time_window or "no window"
    print(f"  {i}. [{window:9}]  [{t.priority:6}]  {t.name}")

# ---------------------------------------------------------------------------
# Demo: filter_tasks()
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("  FILTER — Luna's tasks only")
print("=" * 55)
luna_tasks = scheduler.filter_tasks(pet_name="Luna")
for t in luna_tasks:
    print(f"  • {t.name}  ({t.preferred_time_window or 'no window'}, {t.priority})")

print()
print("=" * 55)
print("  FILTER — tasks NOT yet completed today")
print("=" * 55)
pending = scheduler.filter_tasks(completed=False)
for t in pending:
    print(f"  • {t.name}  ({t.priority})")

print()
print("=" * 55)
print("  FILTER — Luna's pending tasks (combined)")
print("=" * 55)
luna_pending = scheduler.filter_tasks(pet_name="Luna", completed=False)
for t in luna_pending:
    print(f"  • {t.name}  ({t.preferred_time_window or 'no window'}, {t.priority})")

# ---------------------------------------------------------------------------
# Demo: complete_task() — auto-schedules next occurrence
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("  COMPLETE_TASK — mark two tasks done, check recurrence")
print("=" * 55)

templates_before = len(scheduler.task_templates)
original_task_ids = {t.id for t in scheduler.task_templates}

# Complete a daily task and a weekly task.
# The weekly task may have been deferred, so wrap it in a ScheduledTask if needed.
from pawpal_system import ScheduledTask as ST

daily_st = next(st for st in plan.scheduled_tasks if st.task.frequency == "daily")

weekly_task = next(
    (st.task for st in plan.scheduled_tasks if st.task.frequency == "weekly"),
    next((t for t in plan.deferred_tasks if t.frequency == "weekly"), None),
)
weekly_st = next(
    (st for st in plan.scheduled_tasks if st.task.frequency == "weekly"),
    ST(
        task_id=weekly_task.id,
        task=weekly_task,
        scheduled_time=today,
        duration_minutes=weekly_task.duration_minutes,
        priority=weekly_task.priority,
    ) if weekly_task else None,
)

for st in filter(None, (daily_st, weekly_st)):
    log, next_task = scheduler.complete_task(st)
    due_label = next_task.get_next_due_date().strftime("%A, %B %d") if next_task else "—"
    recur_msg = (
        f"next occurrence registered (due {due_label})"
        if next_task
        else "no recurrence (as-needed)"
    )
    print(f"  ✓ Completed : {st.task.name}  [{st.task.frequency}]")
    print(f"    Log id    : {log.id[:8]}...")
    print(f"    Recurrence: {recur_msg}")
    print()

templates_after = len(scheduler.task_templates)
print(f"  task_templates before: {templates_before}  →  after: {templates_after}")
print(f"  ({templates_after - templates_before} new occurrence(s) added)")

print()
print("=" * 55)
print("  FILTER — tasks NOT yet completed (after marking two done)")
print("=" * 55)
still_pending = scheduler.filter_tasks(completed=False)
for t in still_pending:
    status = "(original)" if t.id in original_task_ids else "(next occurrence)"
    print(f"  • {t.name}  [{t.frequency}]  {status}")
