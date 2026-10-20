# Read-only block-entity investigation — 20 October 2026

The mismatch at **-9224,43,-5323** is confirmed in a snapshot from **20:04:54
Europe/Dublin**, before PR #54's deployment and before the current server process.
It was not first introduced by the PR #55 deployment. Its original cause remains
unknown; the C2ME stack frame identifies where it was noticed, not what caused it.

The exact location is chunk **-577,-333**, region **-19,-11**, region-local chunk
**31,19**. The investigation read the compressed chunk payload and NBT block-state
palette directly, without loading the chunk through Minecraft or writing any
region, block, block entity or snapshot. Two successive live payload reads had
identical SHA-256 hashes. The live server continued running; the reads are not a
whole-world frozen capture. The newest pre-error snapshot was verified `ro=true`.

| Source (Dublin time) | Block at location | Block entity at location |
| --- | --- | --- |
| Current live file, stable double read | minecraft:chest | None stored |
| Snapshot 20:46:52, before 20:50:57 error | minecraft:chest | minecraft:brushable_block |
| Snapshot 20:15:42 | minecraft:chest | minecraft:brushable_block |
| Snapshot 20:04:54, before PR #54 deployment | minecraft:chest | minecraft:brushable_block |
| Snapshot 19:40:40 | Region file absent | Cannot inspect this coordinate |
| Snapshot 19 October 01:00:01 | Region file absent | Cannot inspect this coordinate |

The three snapshots containing the mismatch have identical compressed chunk
payload SHA-256 `1d735208ca6be2995ead8425f711f7cf472d1bd430729bfc19c03a4da11a9b8d`.
The live payload hash is
`bd8fe17bd4b2fcfb29e3d6fd68092638eb1294fc4a682a04367aca79e859711c`.
DataVersion is 5023. The retained mismatched entity has loot-table metadata;
values were omitted from the report. See the sanitized
[evidence JSON](minecraft-block-entity-2026-10-20.evidence.json) for exact paths
and decoded position/type information.

The live save no longer contains the offending brushable-block entry. That is
consistent with the earlier failed block-entity load, but does not prove a correct
repair or preservation of chest/loot state. No repair, removal or regeneration
was performed by this investigation. Retain the snapshots; any restoration or
world repair requires a separate, evidence-based decision.
