from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
import uuid

# Priority sort order — lower number = higher urgency
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Hour ranges for time-of-day windows
TIME_WINDOW_HOURS = {
    "morning":   (6,  12),
    "afternoon": (12, 17),
    "evening":   (17, 21),
}


# ---------------------------------------------------------------------------
# TimeBlock
# ---------------------------------------------------------------------------

@dataclass
class TimeBlock:
    start: datetime
    end: datetime

    def duration_minutes(self) -> int:
        """Return the length of this block in minutes."""
        return int((self.end - self.start).total_seconds() / 60)

    def overlaps_with(self, other: "TimeBlock") -> bool:
        """Return True if this block shares any time with another block."""
        return self.start < other.end and self.end > other.start


# ---------------------------------------------------------------------------
# OwnerConstraints
# ---------------------------------------------------------------------------

@dataclass
class OwnerConstraints:
    available_time_blocks: list[TimeBlock] = field(default_factory=list)
    energy_level: str = "medium"        # low | medium | high
    blackout_times: list[TimeBlock] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)  # e.g. {"no_tasks_before": "09:00"}
    max_tasks_per_day: int = 10

    def get_available_minutes(self) -> int:
        """Total schedulable minutes across all available blocks."""
        return sum(b.duration_minutes() for b in self.available_time_blocks)

    def is_time_available(self, slot: TimeBlock) -> bool:
        """True if slot falls inside an available block and doesn't hit a blackout."""
        in_blackout = any(slot.overlaps_with(b) for b in self.blackout_times)
        if in_blackout:
            return False
        return any(
            b.start <= slot.start and b.end >= slot.end
            for b in self.available_time_blocks
        )

    def apply_preferences(self, tasks: list["CareTask"]) -> list["CareTask"]:
        """Filter tasks based on energy level and day preferences."""
        filtered = list(tasks)

        # Low energy day: drop non-urgent low-priority tasks
        if self.energy_level == "low":
            filtered = [t for t in filtered if t.priority != "low"]

        return filtered


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    id: str
    name: str
    species: str
    breed: str
    age: int
    weight: float
    owner_id: str
    medical_needs: list[str] = field(default_factory=list)

    def get_care_requirements(self) -> list[str]:
        """Return a baseline list of care types this pet needs."""
        base = ["feed", "walk"] if self.species == "dog" else ["feed", "enrichment"]
        if self.medical_needs:
            base.append("meds")
        return base

    def get_active_task_templates(self, all_tasks: list["CareTask"]) -> list["CareTask"]:
        """Return tasks that belong to this pet."""
        return [t for t in all_tasks if t.pet_id == self.id]


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    id: str
    name: str
    email: str
    phone: str
    pets: list[Pet] = field(default_factory=list)
    constraints: Optional[OwnerConstraints] = None

    def add_pet(self, pet: Pet) -> None:
        """Append a pet to this owner's pet list."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove the pet with the given id from this owner's pet list."""
        self.pets = [p for p in self.pets if p.id != pet_id]

    def update_profile(self, **kwargs) -> None:
        """Update any owner field by keyword argument (e.g. name='Alex')."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


# ---------------------------------------------------------------------------
# CareTask
# ---------------------------------------------------------------------------

@dataclass
class CareTask:
    id: str
    pet_id: str
    pet: Pet
    name: str
    task_type: str              # walk | feed | meds | groom | enrichment
    duration_minutes: int
    priority: str               # high | medium | low
    frequency: str              # daily | weekly | as-needed
    preferred_time_window: Optional[str] = None   # morning | afternoon | evening
    notes: Optional[str] = None

    def is_due_today(self, logs: list["TaskLog"]) -> bool:
        """True if this task hasn't been satisfied yet based on its frequency."""
        today = date.today()
        task_logs = [l for l in logs if l.task_id == self.id and not l.skipped]

        if self.frequency == "daily":
            return not any(
                l.completed_at and l.completed_at.date() == today
                for l in task_logs
            )
        elif self.frequency == "weekly":
            week_ago = datetime.now() - timedelta(days=7)
            return not any(
                l.completed_at and l.completed_at >= week_ago
                for l in task_logs
            )
        else:  # as-needed — always surfaces unless done today
            return not any(
                l.completed_at and l.completed_at.date() == today
                for l in task_logs
            )

    def get_next_due_date(self) -> date:
        """Return the next calendar date this task will be due based on its frequency."""
        today = date.today()
        if self.frequency == "daily":
            return today + timedelta(days=1)
        elif self.frequency == "weekly":
            return today + timedelta(days=7)
        return today  # as-needed

    def estimate_duration(self) -> int:
        """Return the expected duration in minutes (uses the stored value)."""
        return self.duration_minutes


# ---------------------------------------------------------------------------
# TaskLog
# ---------------------------------------------------------------------------

@dataclass
class TaskLog:
    id: str
    task_id: str
    task: CareTask
    completed_at: Optional[datetime] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

    def mark_complete(self) -> None:
        """Stamp the current time as the completion time and clear any skip state."""
        self.completed_at = datetime.now()
        self.skipped = False
        self.skip_reason = None

    def mark_skipped(self, reason: str) -> None:
        """Record that this task was intentionally skipped today with a reason."""
        self.skipped = True
        self.skip_reason = reason
        self.completed_at = None

    def get_streak(self, all_logs: list["TaskLog"]) -> int:
        """Count consecutive days this task was completed without skipping."""
        task_logs = sorted(
            [l for l in all_logs if l.task_id == self.task_id and l.completed_at and not l.skipped],
            key=lambda l: l.completed_at,
            reverse=True,
        )
        streak = 0
        expected_day = date.today()
        for log in task_logs:
            if log.completed_at.date() == expected_day:
                streak += 1
                expected_day -= timedelta(days=1)
            else:
                break
        return streak


# ---------------------------------------------------------------------------
# ScheduledTask
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    task_id: str
    task: CareTask
    scheduled_time: datetime
    duration_minutes: int
    priority: str
    can_defer: bool = True

    def defer(self) -> "CareTask":
        """Signal that this task should be removed from the plan."""
        self.can_defer = False
        return self.task

    def complete(self) -> TaskLog:
        """Mark this task done and return a TaskLog entry."""
        return TaskLog(
            id=str(uuid.uuid4()),
            task_id=self.task_id,
            task=self.task,
            completed_at=datetime.now(),
        )

    def swap(self, other: "ScheduledTask") -> None:
        """Swap the scheduled times of two tasks."""
        self.scheduled_time, other.scheduled_time = other.scheduled_time, self.scheduled_time


# ---------------------------------------------------------------------------
# DailyPlan
# ---------------------------------------------------------------------------

@dataclass
class DailyPlan:
    date: date
    owner: Owner
    pet: Pet
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    deferred_tasks: list[CareTask] = field(default_factory=list)
    reasoning: str = ""

    @property
    def total_time_minutes(self) -> int:
        """Always computed from scheduled tasks — never drifts out of sync."""
        return sum(t.duration_minutes for t in self.scheduled_tasks)

    def summarize(self) -> str:
        """One-paragraph plain-English summary of the day's plan."""
        lines = [
            f"Plan for {self.owner.name} & {self.pet.name} — "
            f"{self.date.strftime('%A, %B %d')}",
            f"Scheduled: {len(self.scheduled_tasks)} tasks "
            f"({self.total_time_minutes} min total)",
        ]
        for st in self.scheduled_tasks:
            lines.append(
                f"  [{st.priority.upper():6}] {st.task.name:<30} "
                f"{st.scheduled_time.strftime('%I:%M %p')}  ({st.duration_minutes} min)"
            )
        if self.deferred_tasks:
            lines.append(f"Deferred: {len(self.deferred_tasks)} tasks (not enough time today)")
            for t in self.deferred_tasks:
                lines.append(f"  • {t.name} ({t.duration_minutes} min)")
        return "\n".join(lines)

    def explain(self) -> str:
        """Return the plain-English reasoning produced by the Scheduler."""
        return self.reasoning


# ---------------------------------------------------------------------------
# Scheduler  —  the planning brain
# ---------------------------------------------------------------------------

@dataclass
class Scheduler:
    owner: Owner
    pets: list[Pet]
    task_templates: list[CareTask]
    constraints: OwnerConstraints
    task_history: list[TaskLog] = field(default_factory=list)

    # -- Step 1 --------------------------------------------------------------

    def analyze_due_tasks(self) -> list[CareTask]:
        """Return all tasks that are due today across every pet."""
        return [t for t in self.task_templates if t.is_due_today(self.task_history)]

    # -- Step 2 --------------------------------------------------------------

    def rank_by_priority(self, tasks: list[CareTask]) -> list[CareTask]:
        """Sort tasks: priority (high→low), then medical needs first, then duration (short first)."""
        def sort_key(task: CareTask):
            priority_score = PRIORITY_ORDER.get(task.priority, 1)
            medical_boost = -1 if task.task_type == "meds" and task.pet.medical_needs else 0
            return (priority_score + medical_boost, task.duration_minutes)

        return sorted(tasks, key=sort_key)

    # -- Step 3 --------------------------------------------------------------

    def fit_to_time_blocks(
        self, tasks: list[CareTask], constraints: OwnerConstraints
    ) -> list[ScheduledTask]:
        """
        Greedily assign tasks to available time blocks.
        Tasks with a preferred_time_window are placed in matching blocks first.
        Returns only the tasks that fit; caller derives deferred list from the remainder.
        """
        scheduled: list[ScheduledTask] = []
        remaining = list(tasks)
        sorted_blocks = sorted(constraints.available_time_blocks, key=lambda b: b.start)

        for block in sorted_blocks:
            if not remaining:
                break
            if len(scheduled) >= constraints.max_tasks_per_day:
                break

            current_time = block.start
            block_window = self._time_window_for(block.start.hour)

            # Within this block: prefer tasks whose window matches, then others
            preferred = [t for t in remaining if t.preferred_time_window == block_window]
            others    = [t for t in remaining if t.preferred_time_window != block_window]
            ordered   = preferred + others

            for task in ordered:
                if len(scheduled) >= constraints.max_tasks_per_day:
                    break
                task_end = current_time + timedelta(minutes=task.duration_minutes)
                if task_end <= block.end:
                    scheduled.append(ScheduledTask(
                        task_id=task.id,
                        task=task,
                        scheduled_time=current_time,
                        duration_minutes=task.duration_minutes,
                        priority=task.priority,
                    ))
                    current_time = task_end
                    remaining.remove(task)

        return scheduled

    # -- Step 4 --------------------------------------------------------------

    def explain_decisions(
        self, scheduled: list[ScheduledTask], deferred: list[CareTask]
    ) -> str:
        """Produce a plain-English explanation of every scheduling decision."""
        lines = []

        if not scheduled:
            return "No tasks could be scheduled today — check available time blocks or task list."

        lines.append(
            f"Scheduled {len(scheduled)} task(s) using "
            f"{sum(s.duration_minutes for s in scheduled)} of "
            f"{self.constraints.get_available_minutes()} available minutes."
        )

        for st in scheduled:
            reason = f"{st.task.name} is {st.task.priority}-priority"
            if st.task.task_type == "meds" and st.task.pet.medical_needs:
                reason += " and involves medication (bumped to top)"
            if st.task.preferred_time_window:
                reason += f"; prefers {st.task.preferred_time_window}"
            lines.append(f"  ✓ {st.task.name}: {reason}.")

        if deferred:
            lines.append(
                f"Deferred {len(deferred)} task(s) — not enough time or hit daily task limit:"
            )
            for t in deferred:
                lines.append(f"  ✗ {t.name} ({t.duration_minutes} min, {t.priority} priority)")

        if self.constraints.energy_level == "low":
            lines.append("Note: low-energy day — all low-priority tasks were skipped.")

        return "\n".join(lines)

    # -- Orchestrator --------------------------------------------------------

    def generate_plan(self) -> DailyPlan:
        """Run the full pipeline and return a DailyPlan with reasoning."""
        due_tasks      = self.analyze_due_tasks()
        filtered_tasks = self.constraints.apply_preferences(due_tasks)
        ranked_tasks   = self.rank_by_priority(filtered_tasks)
        scheduled      = self.fit_to_time_blocks(ranked_tasks, self.constraints)

        scheduled_ids  = {st.task_id for st in scheduled}
        deferred       = [t for t in ranked_tasks if t.id not in scheduled_ids]
        reasoning      = self.explain_decisions(scheduled, deferred)

        return DailyPlan(
            date=date.today(),
            owner=self.owner,
            pet=self.pets[0] if self.pets else None,
            scheduled_tasks=scheduled,
            deferred_tasks=deferred,
            reasoning=reasoning,
        )

    # -- Helpers -------------------------------------------------------------

    @staticmethod
    def _time_window_for(hour: int) -> Optional[str]:
        """Map an hour (0–23) to a time window label, or None if outside defined windows."""
        for window, (start, end) in TIME_WINDOW_HOURS.items():
            if start <= hour < end:
                return window
        return None
