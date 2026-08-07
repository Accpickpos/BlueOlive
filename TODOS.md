# TODOS

## Per-cylinder serial/asset tracking for LPG rentals

**What:** Add serial numbers / asset tags to individual LPG cylinders, so each
physical unit has its own record and inspection/maintenance history — not just
an aggregate count per customer.

**Why:** Some LPG regulatory regimes require inspection tracking per physical
cylinder (pressure test dates, condition history), not just "how many cylinders
does this customer have out." The first BlueOlive milestone (per-customer
aggregate deposit tracking) doesn't need this, but it may become a hard
requirement depending on jurisdiction.

**Pros:**
- Enables per-unit inspection/maintenance compliance if required.
- Enables tracing a specific cylinder's rental history across customers.

**Cons:**
- `StockItem` (stock_control/models.py:12) currently has no serial/asset-tag
  field — this touches a core app used by every existing gas/tyre/hardware
  customer, not just the new `rentals` app.
- Adds real complexity (per-unit queries, indexing) that the pilot doesn't need.

**Context:** Raised during `/plan-eng-review` Performance Review (Issue 1,
2026-07-28) while scoping the LPG rental/deposit milestone from the
`/office-hours` design doc (`accpi-main-design-20260728-222103.md`). Per-customer
aggregate tracking was chosen for the first milestone because it fits the
existing quantity-based `StockItem` model with no new tracking concept. Revisit
if a real regulatory requirement surfaces, or if a customer explicitly asks for
per-unit history.

**Depends on / blocked by:** Nothing blocking — this is additive to the chosen
aggregate-tracking approach, not a prerequisite for it.

---

## Async/Celery-based ledger posting with idempotency

**What:** If BlueOlive later needs offline-first/sync connectivity, the
synchronous same-DB-transaction posting model (rentals → `LedgerPostingService`
→ general_ledger, all inside one `atomic()` block) won't work, and posting needs
to move to an async/queued model with idempotency keys and retry logic.

**Why:** `/plan-eng-review` Architecture Issue 1 found that tenant scoping is
set per-request by `SchemaMiddleware` (tenancy/schema_middleware.py:32-58) via
PostgreSQL `search_path`, and does NOT propagate to Celery workers. Synchronous
posting was chosen for the first milestone. Correction from cross-model review:
`tenancy/tasks.py:15` already has a working pattern for this exact problem
(explicit schema re-derivation inside the task) — so this is not a hard
blocker on async, it's a solved-elsewhere problem. Synchronous was kept
anyway because it's less machinery for one customer/one sector, not because
async was infeasible. Revisit if the connectivity-model decision (still open
in the design doc) resolves toward offline-first/sync — at that point, follow
the `tenancy/tasks.py` pattern directly rather than re-solving it.

**Pros:**
- Resilience if a shop's connection drops mid-sale (offline-first).
- Avoids blocking a real counter sale on a slow/unavailable DB.

**Cons:**
- Reintroduces the tenant-schema-propagation risk that going synchronous
  specifically avoided — must follow the `tenancy/tasks.py` explicit-schema
  pattern carefully.
- Idempotency keys, retry logic, and dead-letter handling all need real design
  work, not just "make it async."

**Context:** Raised during `/plan-eng-review` Architecture Review (Issue 1,
2026-07-28) while scoping the LPG rental/deposit milestone. Directly gated on
the connectivity-model decision still open in the `/office-hours` design doc.

**Depends on / blocked by:** Blocked by the connectivity-model decision
(online-only vs. offline-first/sync) — see design doc Open Questions.

---

## Customer-facing reminders (SMS/email) for overdue rental deposits

**What:** Notify a customer before or when their LPG cylinder rental deposit
becomes overdue, via SMS or email.

**Why:** Raised during `/plan-ceo-review` Selective Expansion cherry-pick
(2026-07-28) as a genuine platform-potential idea — the existing `messaging`
app (backend/core/apps/messaging/) is internal staff-to-staff chat
(`Conversation`/`Message` models keyed to `AUTH_USER_MODEL` participants), not
a customer notification channel, so this is a real new capability, not a
trivial reuse.

**Pros:**
- Reduces overdue rentals proactively instead of relying on the shop owner
  checking the "Outstanding Deposits" report (T8) manually.
- Platform potential: the same reminder infrastructure could serve other
  future sectors (tyre-fitment appointment reminders, etc.) once it exists.

**Cons:**
- Requires a new external dependency (SMS/email provider integration).
- Touches customer contact data — needs its own privacy/consent handling.
- Not needed to prove the core rental/deposit model works for the pilot.

**Context:** Deferred specifically because it fails the acceptance criterion
used for this milestone (real cost + new external dependency), not because
it "doesn't prove the core model" — that framing was corrected during
`/plan-ceo-review` adversarial review (2026-07-28) to keep the accept/defer
logic auditable against one consistent test. The dependency note below is a
separate, secondary fact (when this COULD be built), not part of why it was
deferred.

**Depends on / blocked by:** Sequencing only, not the deferral reason: T3
(rental state model) and T8 (Outstanding Deposits report) would need to land
first, since reminders need the overdue-state concept those establish.

---

## Revisit LedgerPostingService's interface shape after sector #2 ships

**What:** Check whether `LedgerPostingService` (built as a formal in-process
API contract for the LPG rentals milestone, with only one caller) actually
fits once a second sector app (tyre or hardware) is built, or whether it
needs reshaping.

**Why:** Raised during `/plan-ceo-review` Section 10 (Long-Term Trajectory,
2026-07-28). The formal contract was built ahead of a second caller, against
`/plan-eng-review`'s recommendation to defer it until a second sector app
existed to validate the interface shape. Not re-litigating that decision —
it's made — but the risk (interface designed for one caller often gets
reshaped once a second caller arrives) should be checked, not assumed away.

**Pros:**
- Catches interface drift early, before a third/fourth sector app compounds
  any wrong assumptions baked into the first version.

**Cons:**
- None to tracking this — it's a checkpoint, not new work, until sector #2
  actually starts.

**Context:** Trigger condition: when work on sector app #2 (tyre or hardware)
begins, check `LedgerPostingService`'s actual usage against its original
design before extending it.

**Depends on / blocked by:** Blocked by sector #2 actually starting — not
actionable until then.
