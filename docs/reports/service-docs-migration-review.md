# Service Docs Migration Review

This working report is the subjective companion to the service-docs migration
validator. It captures human documentation review notes that should not be baked
into `scripts/check-service-docs-migration`.

## Scope

The validator answers whether a service satisfies the mechanical convention:
app docs, manifest metadata, live endpoints, and central docs-site wrapper.

This report answers softer questions:

- Does the repo documentation fit the homelab service documentation convention?
- Is the README enough to orient future work?
- Are architecture, configuration, or security notes missing where they matter?
- Are there follow-up improvements that are useful but not required before
  calling the migration complete?

App-owned documentation stays in the app repo. This report should summarize and
link; it should not copy app Markdown into `homelab-config`.

## Review Categories

Use these categories for each service:

- `required before calling migrated`: issues that should block declaring the
  service migrated even if endpoints exist.
- `recommended follow-up`: improvements that would make the repo easier to
  maintain but do not block the migration.
- `optional polish`: nice-to-have clarity, examples, schemas, or formatting.

## Service Reviews

Add one section per reviewed service while a migration campaign is active.
Remove or archive stale notes after the follow-up work is complete.

### Pirate Radio

- `required before calling migrated`: none.
- `recommended follow-up`: none blocking after deployed strict live validation.
- `optional polish`: enrich OpenAPI response schemas and examples for backlog,
  library, and progress endpoints if those become external integration
  contracts.
