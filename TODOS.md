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

---


## Debtors: Account Category conversion (Open Item ↔ Balance Brought Forward) has no side effects

**What:** Manual (§2.1 [212.htm]): converting a debtor from Open Item
(`acctype='O'`) to Balance Brought Forward should clear all open item
transactions after confirmation (and requires a file re-index). Converting
BBF → Open Item should open an entry screen to capture all outstanding
transactions as new open items.

**Why:** Found auditing `apps/debtors` against the manual.
`DebtorViewSet.convert_category` (`views.py:354-378`, line numbers as of
before this audit's edits) just sets `debtor.acctype = new_category` and
saves — no side effects either direction.

**Pros:** Closes a real gap — today, converting a debtor's account category
leaves stale/inconsistent `Debtopen` records (or none at all) relative to
what the new category expects.

**Cons:** Real design work: O→BBF needs a decision on what happens to
existing `Debtopen` balances (fold outstanding `balancedue` into the
aging buckets by their current `ageflag`, presumably, but that's a design
choice not stated anywhere in code today). BBF→O needs to synthesize
`Debtopen` records from the aging buckets (`d30`..`d180`), but the bucket
model only carries a total per period, not the individual transactions
that made it up — the manual's DOS version handled this by having the
operator manually re-key each outstanding transaction, which doesn't
map cleanly onto a single API call.

**Context:** Debtors module audit, `prompt.txt` Phase 2, module 2 of 9.

**Depends on / blocked by:** None.

---

## Debtors: `DebtorOpenItem` model appears to be entirely dead code

**What:** `debtors.DebtorOpenItem` (`models.py:383-465`) — a redesigned,
same-table (`db_table='debtopen'`) alternative to `debtors.Debtopen` with
extra computed fields (`due_date`, `fully_paid`) — is never imported or
referenced by `views.py`, `services.py`, or `serializers.py`. The entire
live open-item code path (`DebtopenViewSet`, `DebtorService.post_debtran`,
`DebteopenSerializer`) uses `Debtopen` exclusively.

**Why:** Found while investigating item 3 above, and directly relevant to
this session's earlier legacy-DBF-import work: `import_debtor_open_items_
from_dbf.py` originally targeted `DebtorOpenItem` on the reasoning that it
was "the" open-item model — corrected to target `Debtopen` as part of this
audit (see the command's own updated docstring for the full story). No real
data was lost (`debtopen.dbf` has 0 live records in the current `pdf/`
export), but the underlying "which model is real" ambiguity should be
resolved properly, not just worked around in the importer.

**Pros:** Removing dead code prevents this exact mistake from recurring —
anyone else reading the models file has no way to know `DebtorOpenItem` is
inert without grepping for call sites themselves.

**Cons:** Deleting a model means a migration (`RemoveModel`), and since both
models share the same underlying `db_table='debtopen'` name pattern, double-
check there's no clever routing/multi-table trick making `DebtorOpenItem`
secretly load from the same rows as `Debtopen` before removing it (looked
likely-not on a first pass, but this needs a careful second look, not a
quick delete, given the shared table name is unusual and could be
intentional multi-table inheritance rather than dead duplication).

**Context:** Debtors module audit, `prompt.txt` Phase 2, module 2 of 9.

**Depends on / blocked by:** None, but low urgency — it's inert, not
actively causing incorrect behavior (unlike the `post_debtran` open-item
condition bug, which was fixed directly this session).

---

## Debtors: Prompt Payment Discount message never surfaced on invoices

**What:** Manual (§2.1 [211.htm]): when `Debtor.discount_printable='Y'`, an
invoice should display a calculated prompt-payment-discount value/message
(computed from `Debtor.terms` + `Debtor.pdisc`) — "pay within N days for X%
off."

**Why:** Found auditing `apps/debtors` against the manual. `pdisc` and
`discount_printable` exist on the model and are exposed read-only in
`DebtorDetailSerializer`, but nothing in `apps/pos` invoice
creation/serialization computes or attaches this message anywhere.

**Pros:** Straightforward calculation (`terms`/`pdisc` already exist) if
the API is the right layer for it.

**Cons:** This is fundamentally a *print/statement* concern ("appears on
invoice") — this audit hasn't yet surveyed how/where BlueOlive actually
renders a printable invoice (PDF generation? frontend-rendered from the API
JSON? no such system found in `apps/pos` so far). Implementing this
correctly depends on locating that rendering path first, which is out of
this module's scope — logged rather than guessed at.

**Context:** Debtors module audit, `prompt.txt` Phase 2, module 2 of 9.

**Depends on / blocked by:** Needs the invoice print/statement rendering
path identified first (may surface naturally during the Utilities module
audit, module 8 of 9, which covers Statement Print).

---

## Stock Control: bulk price adjustment by Department or Supplier

**What:** Manual (§3.1 [313.htm]): adjust Cost or Selling prices for every
stock item in a department, or every item supplied by a creditor, in one
operation — increase/decrease by a % or a flat Rand amount, targeting a
specific price level (1/2/3) or all three.

**Why:** Found auditing `apps/stock_control` against the manual. No
endpoint, service, or management command does this anywhere in the repo —
pricing is only ever editable one `StockItem` at a time today.

**Pros:** Real, frequently-used documented operation (price adjustments
tend to happen in bulk when a supplier changes their price list, not item
by item).

**Cons:** Real design work, not a local fix: needs a preview/dry-run step
before committing (bulk-mutating potentially hundreds of items should not
be a single blind POST), an audit trail of what changed, and a decision on
how it interacts with `SpecialDeal`/`FuturePricing` records already
scheduled for affected items.

**Context:** Stock Control module audit, `prompt.txt` Phase 2, module 3 of 9.

**Depends on / blocked by:** None, but should share design with the Set
Maximum Discount bulk item below — same filtering/targeting mechanism
(department or supplier), different field being mutated.

---

## Stock Control: bulk "Set Maximum Discount" by Department or Supplier

**What:** Manual (§3.1 [313.htm]): set `maximum_discount_percent` across
every stock item in a department, or every item from a supplier (optionally
scoped to one department within that supplier), in one operation.

**Why:** Same audit. `maximum_discount_percent` (already enforced at POS —
see the Module 1 audit) is only ever set per-item; no bulk-set path exists.

**Pros:** Straightforward compared to the price-adjustment item above — one
field, no proportional-math edge cases.

**Cons:** Still needs the same "which items get touched" targeting
mechanism and a decision on whether it overwrites items that already have a
custom (non-default) discount cap, or only fills in items still at the
default.

**Context:** Stock Control module audit, `prompt.txt` Phase 2, module 3 of 9.

**Depends on / blocked by:** Share design with the bulk price adjustment
item above.

---

## Stock Control: department-wide Special Deals

**What:** Manual (§3.1 [312.htm]): apply a special-pricing period to an
entire department at once (increase/decrease by % or Rand, specific price
levels, start/end dates) — distinct from the existing per-item `SpecialDeal`
facility.

**Why:** Same audit. `SpecialDeal` (`models.py:259`) is strictly one row per
`StockItem`; no department-scoped equivalent exists.

**Pros:** Real documented facility, same bulk-operation family as the two
items above.

**Cons:** Needs a decision on representation: a new `DepartmentSpecialDeal`
model that fans out into per-item `SpecialDeal` rows at creation time (
simplest, reuses existing `SpecialDeal`-consuming code like POS pricing
lookups), vs. a department-level record that `SpecialDeal` lookups need to
additionally check at read time (more invasive, touches every price lookup
call site).

**Context:** Stock Control module audit, `prompt.txt` Phase 2, module 3 of 9.

**Depends on / blocked by:** None.

---

## GRN: supplier surcharge (e.g. transport) never apportioned to line costs

**What:** Manual (§3.2 [321.htm]): a Goods Received Note supports an extra
"Surcharge" amount (e.g. transport charges), excl. VAT, that gets apportioned
across all line items and factored into their landed cost.

**Why:** Found while auditing Stock Control's Incoming Stock transaction
against the manual. `Creditor.surcharge_amount` exists and is captured on
GRN-related serializers (`apps/creditors/serializers.py`), but nothing
apportions it across `PurchaseOrderReceiptLine`/GRN line items or folds it
into `unit_cost`/`cost_price` — grep for "apportion" across the whole repo
returns nothing. This sits at the boundary of Stock Control, Purchase
Orders, and Creditors (the manual describes the same GRN-like flow
appearing in more than one of those modules), so properly scoping the fix
needs those modules' audits too.

**Pros:** Affects landed cost accuracy — without apportionment, GP%
calculations on received stock are wrong whenever a surcharge is captured.

**Cons:** Needs a design decision on apportionment method (by value, by
quantity, by weight — the manual doesn't specify which) and where in the
receiving flow it should apply, given the flow is implemented across
multiple apps.

**Context:** Stock Control module audit, `prompt.txt` Phase 2, module 3 of
9. Revisit during the Purchase Orders (module 6) and Creditors (module 4)
audits, since the receiving code that would need to change lives in
`apps/purchase_orders`, not `apps/stock_control`.

**Depends on / blocked by:** Creditors module audit (module 4) and
Purchase Orders module audit (module 6) — both touch the actual GRN
receiving code path.

---

## Creditors: "Pay and Update" — combined GRN/expense capture + immediate till payment

**What:** Manual (§4.2 [421.htm]/[423.htm]): when receiving stock (GRN) or
capturing a supplier expense invoice, an option lets the operator pay the
supplier immediately "out of the current day's cash sale money" — one
action that posts the invoice AND payment to the supplier, reduces till
cash, increases payouts, receives items into stock, updates VAT controls,
and updates the Day End report, all together.

**Why:** Found auditing `apps/creditors` against the manual. Confirmed via
repo-wide grep (no hits for `pay_and_update`/`pay_immediately`/`from_till`
across `apps/creditors`, `apps/purchase_orders`, `apps/pos`): GRN/expense
capture and supplier payment are always two fully independent transactions
today. `GoodsReceivedNoteViewSet.post_grn` and `CreditorInvoiceViewSet.
post_invoice` only flip `is_posted`/`posted_at` — no payment, no till
interaction.

**Pros:** Closes a real documented workflow — useful for the common small-
cash-purchase case (e.g. paying a delivery driver cash on the spot).

**Cons:** Genuinely cross-module (creditors + pos till/cashbook + stock
receiving), and touches till cash balance directly — needs careful design
given real money is involved, not a local fix. Needs a decision on how
"increases payouts" maps onto the existing `pos.Payout`/`pos.CashControl`
models.

**Context:** Creditors module audit, `prompt.txt` Phase 2, module 4 of 9.

**Depends on / blocked by:** Cash Book module audit (module 5) and POS's
till/`CashControl` model — should inform how the till-side of this gets
implemented.

---

## Creditors: `ExpenseCategoryTransaction` has no write path; "Returns - Expense Categories" has no endpoint

**What:** Two related gaps found together: (a) `ExpenseCategoryTransaction`
is documented in its own model comment as "written by posting engine," but
no such engine/service/signal exists anywhere in `apps/creditors` — the
model is read-only in the API (`ExpenseCategoryTransactionViewSet` is a
`ReadOnlyModelViewSet`) with nothing ever creating rows in it. (b) The
manual's "Returns - Expense Categories" facility (credit notes against a
non-stock expense category, e.g. an Advertising account credit) has no
endpoint at all — `CreditorCreditNote`/`CreditorCreditNoteLineItem` only
support `stock_item` lines, not `expense_category` lines.

**Why:** Found auditing `apps/creditors` against the manual §4.2
[423.htm]/[424.htm]. "Invoice Capture - Expense" (the non-stock invoice
side) does work correctly (`CreditorInvoiceViewSet` with `expense_category`
line items) — it's specifically the transaction-ledger write-through and
the *returns* side that are missing.

**Pros:** Closes a real gap in expense tracking — `ExpenseCategoryMonthlyBalance`
(which the DBF import populated from legacy `supexp.dbf` data) has no live
app code keeping it current going forward.

**Cons:** Needs a decision on what the "posting engine" actually is —
should posting a `CreditorInvoice`/`CreditorCreditNote` with an
expense-category line automatically create the corresponding
`ExpenseCategoryTransaction` (a signal, matching this codebase's existing
signal-based patterns), or is this an explicit separate action? The
Returns side also needs a model decision: extend
`CreditorCreditNoteLineItem` to optionally reference an `expense_category`
instead of a `stock_item` (mirroring how `CreditorInvoiceLineItem` already
does this), or a parallel line-item type.

**Context:** Creditors module audit, `prompt.txt` Phase 2, module 4 of 9.

**Depends on / blocked by:** None.

---

## Creditors: `CreditorPayment.is_unallocated` exists but doesn't gate any distinct behavior

**What:** Manual (§4.2 [425.htm]) describes "Unallocated Payments" as a
distinct facility — a payment with no transaction to allocate against,
explicitly not apportioned to any outstanding item (e.g. paying before an
invoice arrives).

**Why:** Found auditing `apps/creditors`. `CreditorPayment.is_unallocated`
exists and is filterable, but nothing branches on it — the
`creditor_payment_post_save` signal always creates a negative
`CreditorOpenItem` for every payment regardless of the flag (which is
arguably correct either way, since an unallocated payment still needs to
exist as an available credit balance), and "leaving a payment unallocated"
today just means never calling the separate `allocate()` action — it works
by omission, not by a designed state. Lower-confidence finding than the
others in this module — the underlying mechanics may already be adequate;
what's missing is explicit modeling/surfacing of the distinction the manual
describes.

**Pros:** Would make "this payment is intentionally unallocated" vs "this
payment hasn't been allocated yet" a real, queryable distinction instead of
an assumption.

**Cons:** Low urgency — nothing is functionally broken today. Needs
someone to decide whether the distinction is worth modeling explicitly
before doing anything here.

**Context:** Creditors module audit, `prompt.txt` Phase 2, module 4 of 9.

**Depends on / blocked by:** None.

---

## Debtors: "Unallocated Payment" facility doesn't exist at all (unlike Creditors)

**What:** Manual describes "Unallocated Receipts on Open Item Debtors" as a
documented facility (a receipt with no transaction to allocate against —
e.g. a deposit for an item not yet invoiced), same concept as Creditors'
`is_unallocated`.

**Why:** Found auditing `apps/cash_book` against the manual (this facility
is documented under both the Debtors module and the Cash Book module — one
underlying gap). `creditors.CreditorPayment.is_unallocated` exists as a
field (even if underused — see the Creditors module TODO above); grepping
`apps/debtors` (models + serializers) found no "unallocated" concept at
all, not even an inert field.

**Pros:** Closes a real, documented facility that today doesn't exist for
debtors even in the minimal "field exists but unused" form Creditors has.

**Cons:** Should be designed together with the Creditors
`is_unallocated` item above rather than independently, since they're the
same underlying concept on two sides of the same coin (money in vs. money
out).

**Context:** Cash Book module audit, `prompt.txt` Phase 2, module 5 of 9.

**Depends on / blocked by:** Should land together with the Creditors
`is_unallocated` TODO above.

---

## RD (dishonoured) cheque handling — technique may not translate safely to Debtors

**What:** Manual's documented technique for reversing a bounced cheque:
"Capture this receipt as an unallocated payment with a negative (minus)
value." No dedicated RD-cheque concept exists — it's just a sign
convention on the generic unallocated-payment entry.

**Why:** Found auditing Cash Book/Debtors/Creditors together. For
Creditors, nothing blocks a negative `amount_paid` mechanically
(no `MinValueValidator`), so the manual's technique might work as-is once
unallocated payments are supported. For Debtors, `DebtorTransaction.clean()`
derives `signed_amount` from `is_credit`/`is_debit` classification rather
than trusting the raw sign of the entered amount — a receipt (`RCP`) is
already forced to `-abs(total_amount)`, so entering a *negative* RCP total
would double-negate rather than produce the intended reversal. This needs
verification with an actual test case, not just code reading — flagged as
uncertain, not confirmed broken.

**Pros:** N/A — this is a risk flag, not a proposed feature.

**Cons:** If confirmed broken, needs either a dedicated RD-cheque
reversal path (safer, more explicit) rather than relying on the legacy
sign-flip technique, which doesn't cleanly map onto how this codebase
already computes signed amounts.

**Context:** Cash Book module audit, `prompt.txt` Phase 2, module 5 of 9.

**Depends on / blocked by:** Should be resolved alongside the two
unallocated-payment items above, since RD-cheque handling is described as a
variant of that same facility.

---

## "Offsetting"/contra transactions — no explicit support, unconfirmed whether it works mechanically

**What:** Manual describes settling two opposite transactions against each
other without cash changing hands: process a payment/receipt with Amount
Paid = Nil, then allocate multiple open items against each other so the net
allocated balance is zero.

**Why:** Found auditing Cash Book/Creditors together. No "offset"/"contra"
concept exists anywhere in `cash_book`, `debtors`, or `creditors`. A
zero-amount `CreditorPayment` isn't blocked by validation (no
`MinValueValidator`, no `amount > 0` check), but whether the
`OpenItemAllocation` UI/API actually supports selecting and netting
multiple open items in one zero-value transaction is unconfirmed — this
needs an actual attempted allocation flow, not just a model-field read, to
verify.

**Pros:** N/A — investigation flag, not a proposed feature yet.

**Cons:** Low urgency compared to the settlement-discount and open-item
items above — contra transactions are a less frequently used accounting
technique. Worth a design decision on whether it's worth building explicit
support for, or leaving as an emergent capability of the existing
allocation mechanism (if it turns out to already work).

**Context:** Cash Book module audit, `prompt.txt` Phase 2, module 5 of 9.

**Depends on / blocked by:** None — independent investigation.

---

## Purchase Orders: non-stock ("Expense Category") PO lines have no model support

**What:** The manual describes ordering against a non-stock Expense Category
(e.g. "Stationery," "Advertising") as well as stock items, so goods-received
processing can post directly to an expense account instead of updating
stock. `PurchaseOrderLine.stock_item` is a required-in-practice FK to
`stock_control.StockItem` (blank/null only as a transitional flag) with no
expense-category alternative anywhere in `apps/purchase_orders`.

**Why:** Found during the Purchase Orders module audit (manual §6). Same
underlying gap as the Creditors module's `ExpenseCategoryTransaction`
write-path TODO above — a PO/GRN raised against an expense category would
need to flow into that same (currently nonexistent) posting engine rather
than touching `StockItem` quantities/costs at all.

**Pros:** Closes a real ordering workflow (non-stock purchases via PO,
e.g. ordering stationery through the same supplier-order process as stock)
that currently has no path at all — the only workaround today is creating a
placeholder `StockItem`, which pollutes stock data and is wrong for costing.

**Cons:** Should not be designed in isolation — needs to land together with
(or after) the Creditors expense-category posting engine decision above, so
a PO line's eventual GRN/receipt has somewhere real to post to. Also needs
a `PurchaseOrderLine` model decision mirroring the Creditors one: optional
`expense_category` FK alongside `stock_item`, mutually exclusive.

**Context:** Purchase Orders module audit, `prompt.txt` Phase 2, module 6 of 9.

**Depends on / blocked by:** Creditors' `ExpenseCategoryTransaction` posting-engine TODO above — should be designed together.

---

## General Ledger: no two-phase Batch/Post workflow — journal entries never touch account balances at all

**What:** Manual (§7.2 [721.htm], [724.htm]): entering a Journal Entry saves
it into a **batch** — it is NOT posted to the account yet. A separate
"Batch Update" step later posts ALL journal entries in the selected
batch(es) to the real account balances, and only balanced batches (total
debits == total credits) may be saved/posted. In the current app: `GLMast`
account balances (`period1`…`period13`) are stored fields, not a live
aggregate, but nothing in `apps/general_ledger` ever writes to them —
`GLTranViewSet` (a bare `ModelViewSet`) just inserts a `GLTran` row and
stops; there's no `services.py`/`signals.py` in this app at all. `GLBatch`
— the model that actually matches the legacy "unposted batch" concept
(`postdate`, `postime`, `period` fields) — exists but has zero API surface:
no serializer, no ViewSet, no URL route, no admin registration, so it
can't be created or posted through any exposed interface today. The only
place in the whole codebase that actually posts a `GLTran` and updates
`GLMast` balances is `apps/rentals/services.py`'s `LedgerPostingService`,
whose own docstring says it "bypasses the manual GLBatch staging table,
which exists for human-entered batches awaiting review, not automated
system postings" — confirming even that one working integration treats
`GLBatch` as unimplemented rather than using it.

**Why:** Found during the General Ledger module audit (manual §7.2). This
is the single biggest gap in this module — manual GL journal entry
currently does nothing to account balances (a silent no-op), and there is
no unposted/review stage for the one working posting path (rentals) either.

**Pros:** This is core double-entry bookkeeping integrity — without it, the
`GLMast.periodN` balance fields, Trial Balance, Income Statement, and
Balance Sheet (see the Enquiries TODO below) have no reliable source of
truth for manually-entered transactions.

**Cons:** Substantial design/build effort, not a local fix: needs (a) a
`GLBatch` API (serializer/ViewSet/URLs) with debit==credit balance
validation before save, (b) a "Batch Update" action that, for each tagged
batch, creates the corresponding `GLTran` rows and updates `GLMast.periodN`
atomically, then marks the batch posted (`postdate`/`postime`), and (c) a
decision on whether `apps/rentals`' direct-post pattern should be migrated
onto this same batch mechanism or intentionally remain a separate
"automated system posting" fast path (as its docstring already argues).

**Context:** General Ledger module audit, `prompt.txt` Phase 2, module 7 of 9.
While investigating this, also found and fixed a live crash bug: `GLTranSerializer`/
`GLTranViewSet` referenced fields (`drorcr`, `capturedat`, `postdate`, `postime`,
`period`) that belong to `GLBatch`, not `GLTran` — the API was apparently
copy-pasted from an intended `GLBatch` endpoint that was never built. Fixed by
renaming to `GLTran`'s real fields (`type` instead of `drorcr`) and removing the
`unposted`/`period_summary` actions, which relied on state `GLTran` doesn't
track — those belong to the `GLBatch` work above, not a quick rename.

**Depends on / blocked by:** None, but the Integration Mapping TODO below
should be designed alongside this, since both modules/Creditors-etc.
integration and manual journal entry would flow through the same
batch/post mechanism.

---

## General Ledger: no Integration mapping — Debtors/Stock/Creditors/Cash Book never post into the GL

**What:** Manual (§7.1 [714.htm], Integration): a configuration step maps
each transaction type from the Debtors, Stock Control, Creditors, and Cash
Book modules to specific Dr/Cr GL account numbers and a narration, used
when those modules' transactions are transferred into the GL — and
"failing to check [every entry has a Dr and Cr account] will result in the
integration being aborted." No such mapping model/config exists anywhere
in the codebase, and grepping `apps/debtors`, `apps/creditors`,
`apps/cash_book`, `apps/stock_control` for any reference to
`general_ledger`/`GLMast`/`GLTran`/`GLBatch` returns zero matches — none of
these four modules post into the GL today. The only real GL-posting
integration in the codebase is `apps/rentals/services.py`'s
`LedgerPostingService`, which hardcodes its own account numbers via a
bespoke `RentalSettings` model (`deposits_held_accno`, `cash_accno`,
`sales_revenue_accno`, etc.) — a one-off pattern for one module, not a
reusable "map any transaction type to GL accounts" facility the other four
could share.

**Why:** Found during the General Ledger module audit (manual §7.1). This
means the entire modern system's Debtors/Stock/Creditors/Cash Book activity
currently has no path into the General Ledger at all — the GL is
functionally disconnected from the rest of the app.

**Pros:** This is the mechanism that makes the GL an actual general ledger
(a single source of truth fed by every subsidiary module) rather than an
isolated, manually-maintained module. Also directly needed by the
Creditors `ExpenseCategoryTransaction` posting-engine TODO above, which
already anticipates GL-style postings for expense-category transactions.

**Cons:** Large, cross-cutting design decision spanning 5 apps, not a local
fix: needs a mapping model (transaction type → Dr account, Cr account,
narration template, per shop/tenant since GL accounts are shop-scoped), a
decision on whether posting happens synchronously (in each module's
`services.py`, mirroring the `rentals` pattern) or via a generic signal/
event dispatched to `general_ledger`, and should be sequenced after the
Batch/Post workflow TODO above so there's somewhere correct to post to.

**Context:** General Ledger module audit, `prompt.txt` Phase 2, module 7 of 9.

**Depends on / blocked by:** General Ledger's Batch/Post workflow TODO
above — should land first or alongside, so posted transactions have a real
destination.

---

## General Ledger: Enquiries (Trial Balance, Income Statement, Balance Sheet, Ledger Account view) are missing; Report Formats modeled but unwired

**What:** Manual (§7.3) documents five GL enquiry reports, none of which
exist as endpoints today: (1) **Ledger Account** — all entries + opening
balance + running balance for one account over a period (closest existing
analog, `GLTranViewSet.by_account`, returns a flat unordered list with no
opening/running balance); (2) **Outstanding Batches** — list of unposted
batches (blocked on the Batch/Post workflow TODO above — there's no
"unposted" concept to list yet); (3) **Trial Balance** — by account or
name order, with an exclude-zero-balances option and YTD values (no
endpoint exists; `GLMastViewSet.summary` only gives aggregate totals, not
a per-account listing); (4) **Income Statement** — with six layout
variants (Current/YTD, Current/Last Year, Current/Budget, 12-month budget,
budget variance, 12-month actuals) — `GLMast.lastyearN` fields exist but
are never read anywhere, and `GLSpreadViewSet.variance_analysis` supplies
some raw numbers but nothing renders an actual Income Statement; (5)
**Balance Sheet** — as-of-date with zero-balance/account-number display
options — `GLMastViewSet.by_account_type(type='B')` is just a filtered
account list, not a balance sheet. Both (4) and (5) are also documented
with CSV export (`Incstat.csv`/`balsheet.csv`) — no CSV/export logic
exists anywhere in this app. Separately, the `GLRep` model (report-line
layout: Heading/Total/Detail/Subtotal per line, with `GLMast.repline`
linking each account to its report line — exactly the legacy "accounts
auto-inserted into layout by account number" mechanism) is fully modeled
but has no serializer, ViewSet, URL, or admin registration, so it's
currently dead schema with nothing reading or writing it.

**Why:** Found during the General Ledger module audit (manual §7.3). This
module has essentially no reporting surface today beyond raw transaction
CRUD and a couple of aggregate summaries — none of the actual accounting
reports a bookkeeper would use exist.

**Pros:** These are core, frequently-used GL reports (Trial Balance and
the Income Statement/Balance Sheet pair in particular are month-end/
management-reporting staples) — closing this gap has high day-to-day
value once the account data flowing into the GL is trustworthy (see the
Batch/Post and Integration TODOs above).

**Cons:** Meaningful build effort across five report actions plus wiring
`GLRep`; Trial Balance/Income Statement/Balance Sheet arguably give more
accurate numbers once the Batch/Post workflow is real (right now `GLTran`
rows never update `GLMast.periodN`, so any report built today would either
have to compute live aggregates from `GLTran` directly — ignoring
`GLMast`'s stored balances entirely — or report stale/zero balances).
Sequencing after the Batch/Post TODO avoids building reports against data
that's known to be incomplete.

**Context:** General Ledger module audit, `prompt.txt` Phase 2, module 7 of 9.

**Depends on / blocked by:** General Ledger's Batch/Post workflow TODO
above, for reports to have real balance data to show.

---

## General Ledger: Standing Journals are single-legged and have no "run" action; Budgets have no year-over-year history

**What:** Two smaller gaps in the same area: (a) Manual (§7.1 [713.htm]):
a Standing Journal is a two-sided recurring template (an account leg + a
contra leg) that must balance, run on a frequency (Monthly/Quarterly/
Bi-Annual/Annual/Continuous), and gets "applied" via a Standing Journal
Update routine (§7.2 [722.htm]) that posts real entries to the accounts.
The current `GLStJnl` model has only **one leg per row** (a single
`accno`/`drorcr`/`amount` — no contra account, no grouping that enforces
two rows balance against each other), `frequency` is a raw
`IntegerField(1-9)` with no semantic Monthly/Quarterly/etc. meaning, and
`GLStJnlViewSet` has no "run"/"update"/"post" action anywhere — its
`active_journals` filter only reports which journals are due, it doesn't
execute anything. (b) Manual (§7.1 [712.htm]): Budgets are per-account
monthly values; the current app stores them as `budget1`…`budget12` flat
columns directly on `GLMast` — no dedicated `Budget` model, so each year's
budget entry overwrites the previous year with no history, and the
`GLSpread` snapshot table (used by `variance_analysis`) is never kept in
sync with `GLMast.budgetN` by any signal or service.

**Why:** Found during the General Ledger module audit (manual §7.1/§7.2).

**Pros:** Standing Journals are a real time-saver for recurring entries
(e.g. monthly depreciation, rent) in the legacy system — worth preserving.
Budget history matters for the Income Statement's "Current Budget Variance
Year to Date Budget Variance" variant (see the Enquiries TODO above).

**Cons:** Standing Journal fix depends on the Batch/Post workflow TODO
above (the "run" action needs somewhere to post to). Budget history is
lower urgency — a `GLBudget(accno, year, month, amount)` model would fix
it but is a schema decision with migration implications for the existing
flat `budget1`…`budget12` columns.

**Context:** General Ledger module audit, `prompt.txt` Phase 2, module 7 of 9.

**Depends on / blocked by:** General Ledger's Batch/Post workflow TODO
above, for the Standing Journal "run" action specifically.

---

## Utilities: Costing Method / Pricing Method (`CostingCategory`) exist but do nothing

**What:** Manual (§8.1 [81.htm], System Parameters — Tax Codes and Costing):
a system-wide Costing Method (A=Average or L=Last Cost, for stock costing
and Gross Profit calculations) and Pricing Method (I=Inclusive or
E=Exclusive of VAT). `CostingCategory` (`apps/settings/models.py:625-741`)
has exactly these fields (`costing_method`, `pricing_method`), but they're
an orphaned reference table — only ever read/written by their own CRUD
endpoints, never consulted by `apps/stock_control`'s actual cost/markup/GP
calculations.

**Why:** Found during the Utilities module audit (manual §8.1). This means
the "Average cost vs Last cost" choice — which fundamentally changes how
Gross Profit is calculated on every sale — currently has no effect at all;
the app presumably always behaves as one fixed method regardless of what's
configured.

**Pros:** Correct GP reporting depends on this being consistent with what
the business has configured — currently silent/wrong is worse than not
having the setting at all, since it implies a choice that isn't honored.

**Cons:** Needs a design decision on scope: is costing method a single
global setting (as the manual implies) or genuinely per-`CostingCategory`
(as the model structure suggests, i.e. different stock categories could
use different methods)? Wiring it also means auditing every place
`StockItem` cost/markup is calculated (`apps/stock_control/signals.py`,
services) to branch on the configured method instead of assuming one.

**Context:** Utilities module audit, `prompt.txt` Phase 2, module 8 of 9.

**Depends on / blocked by:** None.

---

## Utilities: Password/permission hierarchy is flat, not the legacy 3-tier structure

**What:** Manual (§8.1 [81.htm], Password Maintenance): a three-level
hierarchy — Global password (gates access to Password Maintenance itself),
Module passwords (block an operator from an entire module), and Function
passwords (Maintenance/Transactions/Enquiry/Report, per module). The
current app has two disconnected, coarse-grained schemes instead:
`ShopUser.role` (a single flat ADMIN/MANAGER/STAFF/CASHIER value) and
`apps/cash_book/permissions.py`'s own separate group-based scheme
(Cashier/Accountant/Admin/GLSupervisor/FinanceDirector) — neither ties to
the other, and neither has the module×function granularity the manual
describes.

**Why:** Found during the Utilities module audit (manual §8.1).

**Pros:** Finer-grained access control matters for a multi-operator retail/
accounting environment — e.g. letting a cashier process transactions in
Debtors without letting them access Debtors Maintenance (delete accounts,
change credit limits).

**Cons:** A real permissions-model redesign, not a local fix — needs a
decision on whether to build this as Django permission groups (one per
module×function combination) or a bespoke hierarchy model, and how it
should unify with `cash_book`'s existing separate scheme rather than
adding a third, uncoordinated permission system.

**Context:** Utilities module audit, `prompt.txt` Phase 2, module 8 of 9.

**Depends on / blocked by:** None.

---

## Utilities: Tax Control / VAT201 reconciliation report is cash-book-only, not cross-module

**What:** Manual (§8.2 [82.htm]): a monthly Tax Control Report that
reconciles VAT across the whole business — aggregating VAT on Debtors'
Invoices/Cash Sales/Laybye Sales/Other Income, Creditors' Credit
Notes/Settlement Discounts/Invoices/Other Expenses, and Cash Book's Other
Income/Expenses, into named categories (A–F) matching the SARS VAT201
form's line items, specifically so it can be reconciled against each
module's own Transaction Report before submission. The current app's only
VAT breakout, `CashBookReportService.get_monthly_summary()`
(`apps/cash_book/business_services.py:495-560`), computes `vat_input`/
`vat_output` split by `audit_type` — but only from Cash Book transactions;
it never touches Debtor invoices, POS cash sales, laybye, or Creditor
credit notes/settlement discounts.

**Why:** Found during the Utilities module audit (manual §8.2). VAT201
reconciliation is a real monthly SARS compliance obligation — the current
report only shows a fraction of the picture needed to complete it
correctly.

**Pros:** Compliance-relevant, well-specified — the manual gives the exact
category breakdown (A–F) needed, unlike some of the vaguer legacy
facilities.

**Cons:** Requires touching four modules (Debtors, Creditors, Cash Book,
POS) to gather each category's VAT total for a period — more of a
reporting-aggregation build than a single-module fix. Should reuse each
module's own transaction VAT fields rather than recomputing VAT
independently, to avoid a reconciliation report that can't actually
reconcile against its own source data.

**Context:** Utilities module audit, `prompt.txt` Phase 2, module 8 of 9.

**Depends on / blocked by:** None.

---

## Utilities: File Clearance (bulk-wipe utilities) missing; Consolidated Expenditure report missing

**What:** Two smaller gaps: (a) Manual (§8.4 [84.htm]): File Clearance —
"Zero Values" (delete all transactions and reset values to zero for a
module's current period, keeping masterfile data), "Create New Files"
(destroy all data in a module and start blank), "Archive Files" (delete
archived-period data to free space) — explicitly flagged in the manual
itself as "a DANGEROUS operation... only to be run after consulting with
Accpick Support and a backup has been done." No equivalent exists in the
current app. (b) Manual (§8.5 [85.htm]): Consolidated Expenditure — a
report combining Creditors Expense + Cash Book Expense transactions by
category, for a specific month or Year-to-Date. The closest existing
endpoint, `apps/creditors/views.py:701-708`'s `by_category`, is a raw
filtered list from Creditors only — no aggregation, no Cash Book, no
period parameter.

**Why:** Found during the Utilities module audit (manual §8.4/§8.5).

**Pros:** Consolidated Expenditure is a genuinely useful, low-risk report,
and connects directly to the Creditors `ExpenseCategoryTransaction`
write-path gap and the General Ledger Integration-mapping gap logged
above — all three are facets of "expense data needs a real cross-module
home." File Clearance has much lower urgency and real destructive risk.

**Cons:** File Clearance is dangerous by the manual's own admission —
building it needs explicit safeguards (confirmation flow, audit logging,
probably restricted to a superuser-only management command rather than an
API endpoint) designed in from the start, not bolted on. Low priority
unless there's an actual operational need for it (e.g. clearing test/demo
data). Consolidated Expenditure should be sequenced after the
`ExpenseCategoryTransaction` posting-engine TODO (Creditors module) so
there's reliable per-category expense data to aggregate.

**Context:** Utilities module audit, `prompt.txt` Phase 2, module 8 of 9.

**Depends on / blocked by:** Consolidated Expenditure depends on
Creditors' `ExpenseCategoryTransaction` posting-engine TODO. File
Clearance is independent but low priority.

---

## Utilities: Period End gaps — Age Debtors Credit Balances flag, Include Cash Book flag, Archive-a-Year

**What:** Three related gaps found auditing `apps/settings/period_end_services.py`
against manual §8.7: (a) the manual's Month End has an "Age Debtors Credit
Balances" Yes/No option (default No) — `DebtorService.age_balances()`
(`apps/debtors/services.py:405-429`) unconditionally shifts every debtor's
aging buckets forward with no such toggle, and the manual doesn't fully
explain what the option changes about the shift (unlike the interest-
charging module's analogous, clearly-defined `charge_credit_balances`
flag added earlier this session), so it wasn't guessed at here. (b) Month
End has an "Include Cash Book" Yes/No option — `MonthEndService.run_month_end()`
(`apps/settings/period_end_services.py:291-363`) never references Cash
Book at all, in either direction; Cash Book has its own, entirely separate
archiving command (`apps/cash_book/management/commands/archive_transactions.py`)
with no toggleable integration into the unified Month End flow. (c)
"Archive-a-Year" moves a completed year's data out of the live dataset
into a separate archive (so day-to-day tables stay small and fast, while
old data stays queryable read-only) — no equivalent exists anywhere;
`YearEndService` (`apps/settings/period_end_services.py`) advances the
financial year and resets the current period, but never relocates or
archives the prior year's transactional data.

**Why:** Found during the Utilities module audit (manual §8.7). Also
while in this file: found and fixed a real bug in the same service —
`_generate_department_ytd`/`_generate_sales_area_ytd` (Year End) computed
each department's/sales area's year-to-date sales and profit correctly
but then discarded the result instead of saving it to
`SalesDepartment.sales_ytd`/`profit_ytd` (or the `SalesArea` equivalents)
— those display fields (read in `apps/settings/views.py:185-187,262-266`)
were therefore always zero. Fixed by persisting the already-computed
values; left `SalesArea.commission_ytd` alone since commission itself is
a pre-existing separate stub (`commission_earned` is hardcoded to
`Decimal('0')` in the monthly stats generator, `period_end_services.py:493`,
with its own "could be calculated from sales" comment) — not something to
invent as a side effect of this fix.

**Pros:** (a) and (b) are both small, well-defined additions once their
exact semantics are confirmed. (c) Archive-a-Year matters for long-term
performance as transaction tables grow.

**Cons:** (a) needs the exact legacy semantics of "aging a credit balance"
confirmed before implementing (does it mean credit balances stay in the
current bucket instead of shifting, or that they're excluded from the
shift entirely, or something else?) — guessing wrong here would silently
corrupt debtor aging data, which is why it wasn't done inline. (b) needs a
decision on whether Cash Book period-end should be invoked in-process from
`MonthEndService`, or remain intentionally separate given it already has
its own bank-reconciliation-gated workflow (the manual itself says Cash
Book should wait until "Bank Statement has been reconciled"). (c) is the
most substantial: in this multi-tenant, schema-per-shop Postgres
architecture, "archive a year" doesn't map cleanly to the legacy's
"copy DOS data directory" mechanic — needs its own design (e.g. a
partition/cold-storage strategy) rather than a literal port.

**Context:** Utilities module audit, `prompt.txt` Phase 2, module 8 of 9.

**Depends on / blocked by:** None — three independent gaps grouped by
manual section.

---

## Utilities: Data Integrity Report — mostly not applicable or already covered; remaining piece blocked on GL integration

**What:** Manual (§8.8 [88.htm]): validates Duplicate Stock Codes, Stock
Markups, Stock Movements, and Account Balances/Codes, auto-adjusting
markup % when cost changed but selling price didn't. Auditing this against
the current app: **Duplicate Stock Codes** is structurally impossible
today — `StockItem.stock_code` is `unique=True, primary_key=True`
(`apps/stock_control/models.py:16`), so the DB itself already enforces
what the legacy check had to scan for at runtime. **Markup auto-adjust**
already exists — `apps/stock_control/signals.py:16-31`'s `pre_save` signal
recalculates markup from current cost/selling price on every `StockItem`
save, which functionally covers the "cost changed, selling price didn't"
case. What's genuinely missing is **Account Balance integrity** (do
Debtor/Creditor stored balance fields reconcile against their transaction
history?) and **Stock Movement integrity** (do `StockItem.quantity_on_hand`
values reconcile against summed `StockTransaction` movements?) — neither
exists, and a General Ledger equivalent would be premature: General
Ledger's own audit (module 7) already found that no module posts into the
GL at all today, so a GL balance-integrity check would trivially report
"everything out of sync" until that gap is closed.

**Why:** Found during the Utilities module audit (manual §8.8). Worth
recording explicitly *why* two of the four legacy checks aren't being
built, so a future pass doesn't mistake "not built" for "not investigated."

**Pros:** Debtor/Creditor balance reconciliation and stock movement
reconciliation are the two pieces with genuine standalone value — closer
in spirit to the `resync_po_quantities` and `validate_balances` (cash
book) commands already built this session, which this could follow as a
pattern.

**Cons:** Needs the same care those two commands needed: a precise
definition of "the authoritative source" to reconcile against (for
Debtors: sum of which transaction/open-item records equals
`total_balance`? For stock: sum of which `StockTransaction` types equals
`quantity_on_hand`?) confirmed against the actual ledger-posting code
before writing a scan, not assumed. The GL portion should wait for the
Integration-mapping TODO (module 7) to land first.

**Context:** Utilities module audit, `prompt.txt` Phase 2, module 8 of 9.

**Depends on / blocked by:** GL portion blocked on General Ledger's
Integration-mapping TODO (module 7). Debtor/Creditor/Stock portions are
independent but need their reconciliation source confirmed first.

---

## Utilities: Day End has no cashier/till-clearing step

**What:** Manual (§8.6 [86.htm], step 4: "Check Cashier Values have been
Cleared"): after Day End reports print, cashier/till values for the day
should be verified as zeroed before the day is considered closed. In the
current app, `apps/cash_book/models.py`'s `DailyTillTransaction` is a
legacy-DBF-import mirror table (per its own docstring), not a live
cashier/till balance — grepping `apps/cash_book` for cashier/till logic
found only the import path, the model, tests, and a permission-group label
("Cashier"); no clearing routine exists anywhere, and `DayEndService.run_day_end()`
(`apps/settings/period_end_services.py`) has no step that touches it.

**Why:** Found during the Utilities module audit (manual §8.6), alongside
the Day End Report persistence gap (now fixed this module — see the new
`DayEndReport` model/`day-end-reports` endpoint, addressing the manual's
separate "Printing a Previous Day End Report" facility).

**Pros:** Would close the loop on Day End actually verifying the day is
balanced, not just summarizing it.

**Cons:** Needs a prior design decision this session didn't have enough
information to make safely: what does a live "till/cashier balance" even
mean in this architecture? Is it POS-session-scoped (each cashier login
has an expected cash total), or a single shop-wide till? No such concept
currently exists to "clear" — it would need to be designed, not just
wired up.

**Context:** Utilities module audit, `prompt.txt` Phase 2, module 8 of 9.

**Depends on / blocked by:** None, but needs a till/cashier-balance data
model decision before implementation.

---

## Gas Controller (rentals): `apps/rentals` is a different product from the legacy Gas Controller, not a rewrite of it

**What:** The reconstructed legacy Gas Controller spec (no real manual —
recovered from program strings, `gas_gen.acc`) describes a **delivery-note-
driven cylinder exchange and hire business**: a driver delivers full
cylinders and collects empties against a client account on a given date/
area/salesman (with an explicit "Cylinder Exchange Only, no charge" vs.
"priced delivery" distinction); outstanding delivery notes are later
batch-converted into Tax Invoices via a pre-invoice "Invoice Line-up"
review; a reconciliation step matches taken-vs-returned cylinder movements
and flags clients with an outstanding cylinder balance; clients can have
negotiated contract pricing; and a Month-End routine charges a recurring
**Hire Charge** on cylinders a client is still holding, emails PDF hire
invoices, and gates on all delivery notes being invoiced first.

`apps/rentals`, by contrast, is an explicitly greenfield **deposit-based
single-SKU checkout/return system** — its own docstrings say so directly
(`models.py:4-8`: "No COBOL equivalent exists for this concept... built
greenfield"; `services.py:5-6` cites `/plan-eng-review` and
`/plan-ceo-review` design sessions from 2026-07-28). A customer checks out
N cylinders against a cash deposit and later returns them (refund),
doesn't return them (written off or billed for replacement at an ad-hoc
price), or disputes the outcome. As a result, essentially every legacy
Gas Controller behavior is absent by design, not by oversight: no
delivery-note model (taken/returned/area/salesman/exchange-only), no
batch invoice-from-delivery-notes step, no per-client running cylinder-
balance/reconciliation, no contract pricing, no bulk price-change utility,
5 of 6 legacy reports (only "Outstanding Deposits" exists, via
`management/commands/report_outstanding_deposits.py`), no gas-specific
Month-End/hire-charge routine (`apps/settings/period_end_services.py`'s
`MonthEndService` has zero awareness of rentals), and no price-sync-from-
Stock-Master utility. Separately, `RentalTransaction`s never create a
`debtors.DebtorTransaction`, so rental deposit/replacement activity never
appears on a customer's normal debtor statement or aging — it only shows
up in `GLTran`/`GLMast` postings and the rentals app's own report, which
cuts against even the legacy spec's own framing of "not a separate
accounting system." Stock quantity changes (`services.py:164-165,232-233`)
also mutate `StockItem.quantity_on_hand` directly rather than through a
`stock_control.StockTransaction` row, unlike every other stock-decrementing
module (`pos`, `stock_control`, `purchase_orders`) — so cylinder movements
leave no stock-movement audit trail.

**Why:** Found during the final module audit (Gas Controller / rentals,
`prompt.txt` module 9 of 9). This needed to be surfaced explicitly rather
than either (a) silently treated as "already done" because *a* rentals app
exists, or (b) torn up and rebuilt to match the legacy spec without
confirming that's actually wanted — `apps/rentals` reads as a deliberate,
reviewed product decision (clean code, real tests, no dead code or TODOs
found anywhere in it per this audit), not an unfinished port.

**Pros:** The deposit/checkout model that exists is well-built — clean
double-entry GL posting (`LedgerPostingService`, with proper
`select_for_update()` row locking), a deliberate double-submit guard, full
atomic rollback semantics, and real debtor/stock FKs (not disconnected
mock data). If the deposit-based model is the intended product going
forward, most of this TODO may be moot rather than a gap to close.

**Cons:** This is the largest scope question in the whole Phase 2 audit —
it isn't a bounded fix or even a single coherent feature, it's "is this
app solving the right problem." Before building any of the missing
legacy behaviors (delivery notes, hire charges, contract pricing, etc.),
someone needs to confirm whether the business actually runs a delivery-
note/hire-charge model (matching the old DOS system) or the deposit-
checkout model that was actually built — building toward the wrong one
would waste the larger effort here. The two smaller, lower-risk pieces
worth doing regardless of that answer are: (1) creating a
`stock_control.StockTransaction` row alongside every direct
`quantity_on_hand` mutation, matching the rest of the codebase's audit-
trail convention; (2) deciding how (or whether) rental activity should
surface on normal debtor statements/aging via `DebtorTransaction`.

**Context:** Gas Controller (rentals) module audit, `prompt.txt` Phase 2,
module 9 of 9 — the final module of this audit pass.

**Depends on / blocked by:** A product-scope decision (delivery-note/
hire-charge model vs. the existing deposit-checkout model) blocks
everything except the two smaller pieces noted in Cons, which are
independent.

---

## Debtors: `charge_interest_batch` is all-or-nothing — one blocked debtor aborts interest for every debtor in the run

**What:** `DebtorService.charge_interest_batch()` (`apps/debtors/services.py`)
loops over every debtor with `dintflag='Y'` inside a single
`@transaction.atomic` block, calling `post_debtran()` for each one to post
the interest charge. `post_debtran()` raises a bare `ValueError` if
`debtor.is_blocked`. Since the whole loop shares one atomic block, a single
blocked debtor partway through the batch rolls back interest charges for
every debtor already processed in that same run — a month-end job defeated
entirely by one bad account, with the only error surfaced being a generic
`ValueError` that doesn't say which debtor caused it.

**Why:** Found during adversarial review of the new `charge_debtor_interest`
management command (added this session as the first real caller of
`charge_interest_batch` — confirmed via repo-wide grep that no caller
existed anywhere before this command). The batch-abort behavior itself is
pre-existing service logic, but this command is what makes it reachable in
production for the first time, so it's the right moment to flag rather than
silently ship a footgun.

**Pros:** Real fix is small in scope (one method) — this is about picking
the right failure semantics, not building new infrastructure.

**Cons:** Needs a design decision, not a guess: should a blocked debtor be
skipped-and-logged (so the rest of the batch still gets its interest
charged, with a summary of who was skipped and why), or should the whole
run still abort but with a clear error naming the specific debtor that
blocked it (so an operator can unblock/exclude them and re-run)? Both are
reasonable — this needed the actual operator workflow decided, not assumed.

**Context:** Found during `/review`'s adversarial pass on the Phase 2 audit
branch (`phase2-module-audit-gas-app`), Debtors module (module 2 of 9).

**Depends on / blocked by:** None.

---

## Cash Book: debtor receipts / creditor payments always post as CASH — no "default bank account" concept exists

**What:** This session wired `DebtorService.post_receipt` and
`creditors/signals.py`'s `creditor_payment_post_save` to post a matching
`CashBookTransaction` (audit_type 1/3) — the priority gap the Cash Book
audit flagged ("Receipts from Debtors and Payments to Creditors never post
to the Cash Book at all"). Both postings use `account_type="CASH"`
unconditionally, even when the underlying receipt/payment was clearly
electronic (e.g. `CreditorPayment.payment_method.code` is `EFT`, not
`CASH`).

**Why:** `CashBookTransaction.clean()` requires a `bank_account_number`
whenever `account_type="BANK"`, and no "default/primary bank account" field
or setting exists anywhere in the codebase (checked `apps/settings`,
`apps/cash_book`) to supply one automatically. Guessing an account number
would silently misattribute real money movements to the wrong bank
account, which is worse than the current, honest "always cash till"
simplification.

**Pros:** Closes the real, spec-called-out integration gap now, without
inventing bank-account data that doesn't exist. `CreditorPayment` already
carries `payment_method` (CASH/CHQ/EFT/...), so once a default account
setting exists, deriving `account_type`/`bank_account_number` from it is a
small follow-up, not a redesign.

**Cons:** Every debtor receipt and creditor payment currently shows up in
the Cash Book's CASH till, not the correct BANK account, whenever payment
was actually electronic — the till's cash balance will over-state real
cash-on-hand for any shop that takes EFT/card debtor receipts or pays
suppliers by EFT.

**Context:** Cash Book module audit follow-up (priority gap fix),
`phase2-module-audit-gas-app` branch, 2026-08-30.

**Depends on / blocked by:** Needs a "default bank account per tenant/
payment method" setting designed first (likely on `PaymentMethod` or a new
Cash Book parameters model) before the account_type derivation can be
fixed.
