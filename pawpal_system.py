from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


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
        pass

    def get_active_task_templates(self) -> list["CareTask"]:
        pass


@dataclass
class Owner:
    id: str
    name: str
    email: str
    phone: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet_id: str) -> None:
        pass

    def update_profile(self, **kwargs) -> None:
        pass


@dataclass
class CareTask:
    id: str
    pet_id: str
    name: str
    task_type: str          # walk, feed, meds, groom, enrichment, etc.
    duration_minutes: int
    priority: str           # high, medium, low
    frequency: str          # daily, weekly, as-needed
    preferred_time_window: Optional[str] = None   # morning, afternoon, evening
    notes: Optional[str] = None

    def is_due_today(self) -> bool:
        pass

    def get_next_due_date(self) -> date:
        pass

    def estimate_duration(self) -> int:
        pass


@dataclass
class TaskLog:
    id: str
    task_id: str
    completed_at: Optional[datetime] = None
    skipped: bool = False
    skip_reason: Optional[str] = None

    def mark_complete(self) -> None:
        pass

    def mark_skipped(self, reason: str) -> None:
        pass

    def get_streak(self) -> int:
        pass


@dataclass
class TimeBlock:
    start: datetime
    end: datetime

    def duration_minutes(self) -> int:
        pass

    def overlaps_with(self, other: "TimeBlock") -> bool:
        pass


@dataclass
class OwnerConstraints:
    available_time_blocks: list[TimeBlock] = field(default_factory=list)
    energy_level: str = "medium"          # low, medium, high
    blackout_times: list[TimeBlock] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)   # e.g. {"no_tasks_before": "09:00"}
    max_tasks_per_day: int = 10

    def get_available_minutes(self) -> int:
        pass

    def is_time_available(self, slot: TimeBlock) -> bool:
        pass

    def apply_preferences(self, tasks: list[CareTask]) -> list[CareTask]:
        pass


@dataclass
class ScheduledTask:
    task_id: str
    task: CareTask
    scheduled_time: datetime
    duration_minutes: int
    priority: str
    can_defer: bool = True

    def defer(self) -> None:
        pass

    def complete(self) -> TaskLog:
        pass

    def swap(self, other: "ScheduledTask") -> None:
        pass


@dataclass
class DailyPlan:
    date: date
    owner_id: str
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    deferred_tasks: list[CareTask] = field(default_factory=list)
    total_time_minutes: int = 0
    reasoning: str = ""

    def summarize(self) -> str:
        pass

    def explain(self) -> str:
        pass


@dataclass
class Scheduler:
    owner: Owner
    pets: list[Pet]
    task_templates: list[CareTask]
    constraints: OwnerConstraints
    task_history: list[TaskLog] = field(default_factory=list)

    def analyze_due_tasks(self) -> list[CareTask]:
        pass

    def rank_by_priority(self, tasks: list[CareTask]) -> list[CareTask]:
        pass

    def fit_to_time_blocks(self, tasks: list[CareTask]) -> list[ScheduledTask]:
        pass

    def generate_plan(self) -> DailyPlan:
        pass

    def explain_decisions(self, plan: DailyPlan) -> str:
        pass
