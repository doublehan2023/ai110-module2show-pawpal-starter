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
# Tasks  (mix of pets, priorities, and preferred time windows)
# ---------------------------------------------------------------------------
today = datetime.now().replace(second=0, microsecond=0)

tasks = [
    # Luna — dog tasks
    CareTask(
        id="t1", pet_id="pet-1", pet=luna,
        name="Luna: morning walk",
        task_type="walk",        duration_minutes=30,
        priority="high",         frequency="daily",
        preferred_time_window="morning",
    ),
    CareTask(
        id="t2", pet_id="pet-1", pet=luna,
        name="Luna: arthritis meds",
        task_type="meds",        duration_minutes=5,
        priority="high",         frequency="daily",
        preferred_time_window="morning",
        notes="Give with food",
    ),
    CareTask(
        id="t3", pet_id="pet-1", pet=luna,
        name="Luna: evening walk",
        task_type="walk",        duration_minutes=30,
        priority="medium",       frequency="daily",
        preferred_time_window="evening",
    ),
    # Mochi — cat tasks
    CareTask(
        id="t4", pet_id="pet-2", pet=mochi,
        name="Mochi: breakfast",
        task_type="feed",        duration_minutes=10,
        priority="high",         frequency="daily",
        preferred_time_window="morning",
    ),
    CareTask(
        id="t5", pet_id="pet-2", pet=mochi,
        name="Mochi: puzzle toy",
        task_type="enrichment",  duration_minutes=15,
        priority="medium",       frequency="daily",
        preferred_time_window="afternoon",
    ),
    CareTask(
        id="t6", pet_id="pet-2", pet=mochi,
        name="Mochi: grooming brush",
        task_type="groom",       duration_minutes=10,
        priority="low",          frequency="weekly",
        preferred_time_window="evening",
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
