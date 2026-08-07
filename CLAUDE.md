
## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
- Author a backlog-ready spec/issue → invoke /spec

## Deferred scope — read before starting new sector work

- **Grocery sector**: no committed customer, no code beyond a sector-agnostic
  `barcode` field on `StockItem`. Before designing scale integration, expiry/
  batch tracking, or anything else grocery-specific, read the Open Questions
  section of `~/.gstack/projects/BootCodex-BlueOlive/accpi-main-design-20260729-001256.md`
  — talk to 3-5 real grocery shop owners first, per that doc's Assignment.
