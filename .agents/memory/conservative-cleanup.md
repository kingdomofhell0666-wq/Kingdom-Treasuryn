---
name: Conservative cleanup policy
description: Safety decisions for Kingdom Treasury cleanup and persistent economy data.
---

The bot must preserve economy data across token rotation, guild departure, and cleanup scans. Cleanup is report-first; uncertainty keeps the item. Automatic removal is restricted to generated Python caches after an external backup and explicit administrator confirmation.

**Why:** The project contains live Discord economy data, dashboard integrations, archived rollback sources, and dynamic registrations. Textual absence of a reference is not enough evidence that a file is safe to remove, and startup-triggered resets can silently destroy user balances.

**How to apply:** Keep source modules, databases, migrations, manifests, configuration, archives, assets, and generated API contracts report-only unless a future change establishes an explicit, reviewed migration or deletion policy. Require both Discord Administrator visibility and a server-side Administrator check for destructive maintenance commands.