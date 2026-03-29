# PawPal+ Project Reflection

## 1. System Design

- Add a pet
- Schedule a walk
- See today's tasks
- Check finished tasks


**a. Initial design**

My initial design centered on separating **data** (what exists) from **logic** (what decides). I identified 8 classes organized around the core loop: an owner has pets, pets have tasks, tasks get scheduled into a daily plan.

The classes and their responsibilities:

- **Owner** — stores profile info and links to their pets
- **Pet** — holds pet details and medical needs; knows what care it requires
- **CareTask** — a reusable task template (e.g. "daily walk, 30 min, high priority"); knows if it's due today
- **TaskLog** — records each completed or skipped instance of a task; tracks streaks and history
- **OwnerConstraints** — captures the owner's available time blocks, energy level, and preferences for a given day
- **Scheduler** — the planning brain; reads due tasks, task history, and constraints, then produces a ranked, time-fitted plan
- **DailyPlan** — the output: an ordered list of scheduled tasks, a deferred list, and a plain-English reasoning string
- **ScheduledTask** — a CareTask placed at a specific time slot within the plan



**b. Design changes**

Yes, the design changed in several ways after reviewing the initial skeleton for missing relationships and logic bottlenecks.

**1. Replaced string IDs with direct object references**
The initial design linked classes using string IDs (e.g. `pet_id` on `CareTask`, `task_id` on `TaskLog`, `owner_id` on `DailyPlan`). This meant every method that needed related data had to do a manual lookup. The fix was to store direct object references alongside the IDs — `CareTask` now holds a `pet: Pet`, `TaskLog` holds a `task: CareTask`, and `DailyPlan` holds `owner: Owner` and `pet: Pet` directly. This makes traversal natural and avoids external lookup logic scattered across methods.

**2. `is_due_today()` now accepts task history**
Originally, `CareTask.is_due_today()` had no access to past completions, so it couldn't correctly handle tasks with `frequency = "daily"` (a task already done today shouldn't be scheduled again). The fix was to add a `logs: list[TaskLog]` parameter so the method can check whether the task was already completed today.

**3. `total_time_minutes` became a computed property**
The initial design stored `total_time_minutes` as a plain field on `DailyPlan`. This could silently drift out of sync if `scheduled_tasks` was modified after the plan was created. Converting it to a `@property` that sums durations from `scheduled_tasks` ensures it's always accurate with no maintenance burden.

**4. `fit_to_time_blocks()` now takes `OwnerConstraints` explicitly**
The original signature only accepted a list of tasks, so `preferred_time_window` on each `CareTask` could never be matched against the owner's actual time blocks. Passing `constraints` explicitly gives the method everything it needs to honor time preferences.

**5. `generate_plan()` now chains sub-methods explicitly**
The initial design left `generate_plan()` as a single opaque stub. The fix was to have it explicitly call `analyze_due_tasks()` → `rank_by_priority()` → `fit_to_time_blocks()` → `explain_decisions()` in sequence, passing return values between steps. This makes the scheduling pipeline transparent and each step independently testable.

**6. `Owner` now links directly to `OwnerConstraints`**
The `Scheduler` originally held `Owner` and `OwnerConstraints` as separate, unrelated fields. Adding `constraints: OwnerConstraints` directly to `Owner` means constraints are always reachable from the owner object, which will matter if multi-owner or re-planning scenarios are added later.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four layers of constraints:

1. **Time blocks** — `OwnerConstraints.available_time_blocks` defines when the owner is free. Tasks are only placed inside these windows; nothing spills outside them.
2. **Task priority** — each `CareTask` carries a `priority` field (`high`, `medium`, `low`). High-priority tasks are sorted to the front of the queue before time-fitting begins.
3. **Medical urgency** — medication tasks (`task_type = "meds"`) for pets with active `medical_needs` receive an extra sort boost, placing them ahead of other high-priority tasks.
4. **Preferred time window** — tasks declare a preferred window (`morning`, `afternoon`, `evening`). Within each time block, matching tasks are placed first; non-matching tasks fill remaining space.
5. **Energy level** — `OwnerConstraints.energy_level = "low"` drops all low-priority tasks before scheduling begins.
6. **Daily task cap** — `max_tasks_per_day` hard-stops placement once the limit is reached.

Time and priority were treated as the most important because they represent hard limits — if there's no time or the owner is overwhelmed, no amount of preference matters. Medical urgency was elevated above standard priority because skipping medication has real health consequences. Preferred time windows were kept as soft hints rather than hard filters so the scheduler can still fill gaps rather than leave time unused.

**b. Tradeoffs**

The scheduler uses a **greedy first-fit algorithm**: it iterates tasks in priority order and places each one at the next available slot, moving on if it doesn't fit. It never backtracks or tries alternative orderings to find a better-packing solution.

The tradeoff is scheduling quality vs. simplicity. A greedy approach can waste available time — for example, a 30-minute task that doesn't fit in the last 25 minutes of a block causes that slot to go unused, even if a 20-minute task later in the queue would have fit perfectly. A backtracking or bin-packing algorithm would solve this, but it is significantly more complex to implement and harder to debug.

For a pet care app, this tradeoff is reasonable. Task counts are small (typically under 10 per day), the stakes of a suboptimal plan are low (a task defers to tomorrow, not a crisis), and the greedy output is predictable and easy to explain to the owner. A scheduling algorithm that is fast and transparent is more valuable here than one that is optimal but opaque.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used throughout the project as a design partner and implementation accelerator:

- **Design brainstorming** — asking the AI to identify where the current logic felt manual or overly simple surfaced concrete gaps (unused fields, no-op methods, hardcoded rules) that became the improvement roadmap.
- **Algorithm suggestions** — the AI proposed the list of scheduling improvements and explained the tradeoffs between greedy vs. backtracking approaches before any code was written.
- **Implementation** — new methods (`filter_tasks`, `sort_by_time`, `complete_task`, `detect_conflicts`, `schedule_next_occurrence`) were implemented with the AI, with each method tested in `main.py` immediately after.
- **Debugging** — when the conflict demo labeling produced `(original)` for next-occurrence tasks, the AI traced the shared-list mutation bug and explained why `tasks` and `scheduler.task_templates` pointed to the same object.

The most helpful prompts were specific and grounded in the actual code: "identify where this class feels overly simple" was more useful than "suggest improvements," because the AI could reason about what was already there rather than generating generic ideas.

**b. Judgment and verification**

When the AI implemented `complete_task`, it appended the next occurrence to `self.task_templates` — which is the same list object passed in from `main.py`. The AI flagged this as a side-effect in the docstring but did not change the design.

Before accepting it, I verified the behavior by printing `len(scheduler.task_templates)` before and after calling `complete_task`, and by checking whether the `tasks` variable in `main.py` also grew (it did). This confirmed the shared-reference behavior was real, not theoretical. The decision to keep it was deliberate — the mutation is intentional and documented — but it required adding `original_task_ids = {t.id for t in scheduler.task_templates}` before the completion demo to snapshot IDs before they changed, which the AI had not accounted for in the original demo code.

---

## 4. Testing and Verification

**a. What you tested**

- **Priority ordering** — verified that high-priority and medication tasks appear before medium and low tasks in the generated plan.
- **Time-block fitting** — confirmed that tasks are placed sequentially within available blocks and deferred when no time remains.
- **`filter_tasks` with `completed=False`** — after calling `complete_task` on two tasks, verified that those tasks no longer appear in the pending filter and that their next occurrences do.
- **`sort_by_time` ordering** — tasks were intentionally inserted in evening→afternoon→morning order and the sort output was checked against the expected morning→evening sequence.
- **`detect_conflicts` with forced overlap** — two tasks were manually assigned the same `scheduled_time` and the warning output was verified to name both tasks and their time windows.
- **Recurrence** — checked that `task_templates` grew by exactly 2 after completing one daily and one weekly task, and that the new instances had different IDs from the originals.

These tests were important because the scheduler's correctness is entirely behavioral — there is no UI feedback loop during development, so `main.py` print output was the only way to confirm that each method did what its docstring claimed.

**b. Confidence**

Moderately confident in the happy-path behaviors covered by `main.py`. The greedy scheduler, filtering, sorting, recurrence, and conflict detection all produce correct output for the test cases written.

Edge cases that would be worth testing next:
- A time block too short for even the shortest task (should defer everything gracefully)
- Two pets sharing a task type at the exact same scheduled time but belonging to different owners
- A weekly task completed 6 days ago — should it surface as due today?
- `filter_tasks(completed=True)` when `task_history` is empty — should return an empty list, not crash
- `detect_conflicts` on an empty list or a single-task list — should return `[]` without error

---

## 5. Reflection

**a. What went well**

The separation between data classes (`Pet`, `CareTask`, `TaskLog`) and the scheduling pipeline (`Scheduler`, `DailyPlan`) held up well throughout the additions. Each new method had a natural home — filtering and sorting belong on `Scheduler` because it owns both `task_templates` and `task_history`; recurrence logic belongs on `CareTask` because it knows its own frequency. None of the additions required restructuring existing classes, which suggests the original design boundaries were drawn in the right places.

**b. What you would improve**

The `fit_to_time_blocks` algorithm is the weakest part of the system. The greedy first-fit approach can leave significant available time unused when a large task fails to fit and smaller tasks behind it could have. The next iteration would replace this with a simple best-fit scan: after a task fails to fit at the current cursor, continue checking remaining tasks in the block before moving to the next block. This would not require a full backtracking solver but would recover most of the wasted time in realistic schedules.

The `preferred_time_window` field would also benefit from being a soft score rather than a binary partition — a morning task placed in the afternoon is still better than deferring it entirely, but the current implementation treats window mismatch as a tie rather than a penalty.

**c. Key takeaway**

The most important lesson was that **designing for transparency is more valuable than designing for optimality** in a user-facing scheduling tool. A greedy algorithm that produces an explainable plan the owner can understand and trust is more useful than a sophisticated optimizer whose decisions feel arbitrary. The `explain_decisions` method, the conflict warnings, and the plain-English docstrings all exist for the same reason: the owner needs to understand why their pet's day was planned the way it was, not just receive a list of tasks. Building the explanation layer as a first-class part of the system — not an afterthought — shaped every other design decision.
