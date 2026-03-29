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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
