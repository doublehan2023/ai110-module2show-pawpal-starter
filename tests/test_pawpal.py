import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from pawpal_system import (
    Pet, Owner, CareTask, TaskLog, ScheduledTask,
    TimeBlock, OwnerConstraints, Scheduler,
)


def make_pet():
    return Pet(
        id="pet-1", name="Luna", species="dog", breed="Labrador",
        age=3, weight=28.0, owner_id="owner-1",
    )

def make_task(pet):
    return CareTask(
        id="task-1", pet_id=pet.id, pet=pet,
        name="Morning walk", task_type="walk",
        duration_minutes=30, priority="high", frequency="daily",
    )


def test_mark_complete_sets_completed_at():
    """mark_complete() should stamp completed_at with a datetime."""
    pet  = make_pet()
    task = make_task(pet)
    log  = TaskLog(id="log-1", task_id=task.id, task=task)

    assert log.completed_at is None      # not done yet

    log.mark_complete()

    assert log.completed_at is not None  # now stamped
    assert log.skipped is False          # not marked as skipped


def test_add_task_increases_pet_task_count():
    """get_active_task_templates() count should grow when a task is added."""
    pet       = make_pet()
    all_tasks = []

    assert len(pet.get_active_task_templates(all_tasks)) == 0

    task = make_task(pet)
    all_tasks.append(task)

    assert len(pet.get_active_task_templates(all_tasks)) == 1


# ---------------------------------------------------------------------------
# Helpers shared by the new tests
# ---------------------------------------------------------------------------

def make_owner():
    return Owner(id="owner-1", name="Alex", email="alex@example.com", phone="555-0100")


def make_scheduler(tasks, blocks, energy="medium", max_tasks=10):
    pet    = make_pet()
    owner  = make_owner()
    constraints = OwnerConstraints(
        available_time_blocks=blocks,
        energy_level=energy,
        max_tasks_per_day=max_tasks,
    )
    return Scheduler(
        owner=owner,
        pets=[pet],
        task_templates=tasks,
        constraints=constraints,
    )


def make_care_task(pet, *, task_id, name, priority, frequency="daily",
                   task_type="walk", duration_minutes=30, preferred_time_window=None):
    return CareTask(
        id=task_id, pet_id=pet.id, pet=pet,
        name=name, task_type=task_type,
        duration_minutes=duration_minutes,
        priority=priority, frequency=frequency,
        preferred_time_window=preferred_time_window,
    )


def make_block(start_hour, end_hour):
    today = datetime.now().replace(minute=0, second=0, microsecond=0)
    start = today.replace(hour=start_hour)
    end   = today.replace(hour=end_hour)
    return TimeBlock(start=start, end=end)


# ---------------------------------------------------------------------------
# 1. Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    """sort_by_time should return tasks in window order: morning → afternoon → evening."""
    pet = make_pet()
    scheduler = make_scheduler([], [])

    evening   = make_care_task(pet, task_id="t1", name="Evening walk",   priority="high",   preferred_time_window="evening")
    morning   = make_care_task(pet, task_id="t2", name="Morning feed",   priority="medium", preferred_time_window="morning")
    afternoon = make_care_task(pet, task_id="t3", name="Afternoon meds", priority="low",    preferred_time_window="afternoon")

    result = scheduler.sort_by_time([evening, morning, afternoon])

    assert [t.preferred_time_window for t in result] == ["morning", "afternoon", "evening"]


def test_sort_by_time_no_window_goes_last():
    """Tasks with no preferred_time_window should sort after all windowed tasks."""
    pet = make_pet()
    scheduler = make_scheduler([], [])

    no_window = make_care_task(pet, task_id="t1", name="Anytime task", priority="high",   preferred_time_window=None)
    morning   = make_care_task(pet, task_id="t2", name="Morning feed",  priority="medium", preferred_time_window="morning")

    result = scheduler.sort_by_time([no_window, morning])

    assert result[0].name == "Morning feed"
    assert result[1].name == "Anytime task"


# ---------------------------------------------------------------------------
# 2. Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_next_occurrence():
    """Completing a daily task should add exactly one new task to task_templates."""
    pet   = make_pet()
    block = make_block(8, 10)
    task  = make_care_task(pet, task_id="t1", name="Morning walk", priority="high", frequency="daily")

    scheduler = make_scheduler([task], [block])
    before    = len(scheduler.task_templates)

    scheduled_task = ScheduledTask(
        task_id=task.id, task=task,
        scheduled_time=block.start,
        duration_minutes=task.duration_minutes,
        priority=task.priority,
    )
    _, next_task = scheduler.complete_task(scheduled_task)

    assert next_task is not None, "daily task must produce a next occurrence"
    assert next_task.id != task.id, "next occurrence must have a new unique ID"
    assert len(scheduler.task_templates) == before + 1


def test_complete_as_needed_task_does_not_recur():
    """Completing an as-needed task must not add a new task to task_templates."""
    pet   = make_pet()
    block = make_block(8, 10)
    task  = make_care_task(pet, task_id="t2", name="Vet visit", priority="medium", frequency="as-needed")

    scheduler = make_scheduler([task], [block])
    before    = len(scheduler.task_templates)

    scheduled_task = ScheduledTask(
        task_id=task.id, task=task,
        scheduled_time=block.start,
        duration_minutes=task.duration_minutes,
        priority=task.priority,
    )
    _, next_task = scheduler.complete_task(scheduled_task)

    assert next_task is None
    assert len(scheduler.task_templates) == before


# ---------------------------------------------------------------------------
# 3. Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks whose time windows overlap should produce a conflict warning."""
    pet       = make_pet()
    scheduler = make_scheduler([], [])
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    task_a = make_care_task(pet, task_id="t1", name="Walk",  priority="high")
    task_b = make_care_task(pet, task_id="t2", name="Feed",  priority="medium")

    # Walk: 09:00–09:30, Feed starts at 09:15 — clear overlap
    st_a = ScheduledTask(task_id=task_a.id, task=task_a, scheduled_time=base_time,
                         duration_minutes=30, priority="high")
    st_b = ScheduledTask(task_id=task_b.id, task=task_b,
                         scheduled_time=base_time + timedelta(minutes=15),
                         duration_minutes=30, priority="medium")

    warnings = scheduler.detect_conflicts([st_a, st_b])

    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Feed" in warnings[0]


def test_detect_conflicts_adjacent_tasks_no_warning():
    """Tasks that share only an endpoint (back-to-back) must not be flagged."""
    pet       = make_pet()
    scheduler = make_scheduler([], [])
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    task_a = make_care_task(pet, task_id="t1", name="Walk", priority="high")
    task_b = make_care_task(pet, task_id="t2", name="Feed", priority="medium")

    # Walk: 09:00–09:30, Feed: 09:30–10:00 — adjacent, not overlapping
    st_a = ScheduledTask(task_id=task_a.id, task=task_a, scheduled_time=base_time,
                         duration_minutes=30, priority="high")
    st_b = ScheduledTask(task_id=task_b.id, task=task_b,
                         scheduled_time=base_time + timedelta(minutes=30),
                         duration_minutes=30, priority="medium")

    warnings = scheduler.detect_conflicts([st_a, st_b])

    assert warnings == []
