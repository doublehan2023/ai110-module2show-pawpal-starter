import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, CareTask, TaskLog


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
