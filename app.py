import uuid
from datetime import datetime, timedelta

import streamlit as st
from pawpal_system import (
    Pet, Owner, CareTask,
    TimeBlock, OwnerConstraints,
    DailyPlan, Scheduler,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation — only runs on first load
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

if "pets" not in st.session_state:
    st.session_state.pets = []

if "tasks" not in st.session_state:
    st.session_state.tasks = []   # list of CareTask objects

# ---------------------------------------------------------------------------
# Section 1 — Owner + Pet setup
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Info")

col_o, col_p, col_s = st.columns(3)
with col_o:
    owner_name = st.text_input("Owner name", value="Jordan")
with col_p:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_s:
    species = st.selectbox("Species", ["dog", "cat", "other"])

medical = st.text_input("Medical needs (comma-separated, or leave blank)", value="")

if st.button("Save owner & pet"):
    # Build Pet using Pet.add_pet() flow via Owner
    pet = Pet(
        id=str(uuid.uuid4()),
        name=pet_name,
        species=species,
        breed="",
        age=0,
        weight=0.0,
        owner_id="owner-1",
        medical_needs=[m.strip() for m in medical.split(",") if m.strip()],
    )

    owner = Owner(
        id="owner-1",
        name=owner_name,
        email="",
        phone="",
    )
    owner.add_pet(pet)               # ← Owner.add_pet()

    st.session_state.owner = owner
    st.session_state.pets  = owner.pets
    st.success(f"Saved {owner.name} with pet {pet.name} ({pet.species})")

if st.session_state.owner:
    st.caption(
        f"Current owner: **{st.session_state.owner.name}** | "
        f"Pets: {', '.join(p.name for p in st.session_state.pets)}"
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add tasks
# ---------------------------------------------------------------------------
st.subheader("Add a Care Task")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task name", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=30)
with col3:
    priority = st.selectbox("Priority", ["high", "medium", "low"])
with col4:
    time_window = st.selectbox("Preferred time", ["morning", "afternoon", "evening"])

task_type = st.selectbox("Task type", ["walk", "feed", "meds", "groom", "enrichment"])
frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])

if st.button("Add task"):
    if not st.session_state.pets:
        st.warning("Save an owner & pet first.")
    else:
        pet = st.session_state.pets[0]
        new_task = CareTask(
            id=str(uuid.uuid4()),
            pet_id=pet.id,
            pet=pet,
            name=task_title,
            task_type=task_type,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            preferred_time_window=time_window,
        )
        st.session_state.tasks.append(new_task)  # ← stores CareTask objects
        st.success(f"Added task: {new_task.name}")

if st.session_state.tasks:
    st.write("**Current tasks:**")
    st.table([
        {
            "Name": t.name,
            "Type": t.task_type,
            "Duration (min)": t.duration_minutes,
            "Priority": t.priority,
            "Frequency": t.frequency,
            "Time window": t.preferred_time_window or "—",
        }
        for t in st.session_state.tasks
    ])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Constraints
# ---------------------------------------------------------------------------
st.subheader("Your Availability Today")

col_a, col_b = st.columns(2)
with col_a:
    avail_hours = st.slider("Hours available (morning block)", min_value=1, max_value=8, value=2)
with col_b:
    energy = st.selectbox("Energy level", ["high", "medium", "low"], index=1)

max_tasks = st.number_input("Max tasks per day", min_value=1, max_value=20, value=6)

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# ---------------------------------------------------------------------------
st.subheader("Generate Today's Schedule")

if st.button("Generate schedule"):
    if not st.session_state.owner:
        st.warning("Please save an owner & pet first.")
    elif not st.session_state.tasks:
        st.warning("Please add at least one task first.")
    else:
        # Build constraints from UI inputs
        morning_start = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        constraints = OwnerConstraints(
            available_time_blocks=[
                TimeBlock(
                    start=morning_start,
                    end=morning_start + timedelta(hours=avail_hours),
                )
            ],
            energy_level=energy,
            max_tasks_per_day=int(max_tasks),
        )

        scheduler = Scheduler(
            owner=st.session_state.owner,
            pets=st.session_state.pets,
            task_templates=st.session_state.tasks,
            constraints=constraints,
        )

        plan: DailyPlan = scheduler.generate_plan()  # ← Scheduler.generate_plan()

        st.success(f"Scheduled {len(plan.scheduled_tasks)} tasks — {plan.total_time_minutes} min total")

        st.markdown("### Scheduled Tasks")
        for i, st_task in enumerate(plan.scheduled_tasks, 1):
            st.markdown(
                f"**{i}. {st_task.task.name}** — "
                f"`{st_task.scheduled_time.strftime('%I:%M %p')}` | "
                f"{st_task.duration_minutes} min | "
                f"priority: {st_task.priority}"
            )

        if plan.deferred_tasks:
            st.markdown("### Deferred (not enough time today)")
            for t in plan.deferred_tasks:
                st.markdown(f"- {t.name} ({t.duration_minutes} min, {t.priority})")

        st.markdown("### Why this plan?")
        st.info(plan.explain())   # ← DailyPlan.explain()
