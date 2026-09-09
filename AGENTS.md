# ZERO CALL repository work

Start with CODEX_START_HERE.md and the current BOOTSTRAP_STATUS.md. In this local
workspace the original 00-17 references are under local-reference (Git ignored).
Read 00_MASTER_RULE, 16_CODEX_TASK_RULE and 17_PROJECT_BOOTSTRAP_CHECKLIST there
before implementation. Do not publish or edit those original references.

Read the approved ZERO CALL master and task documents before changes. The current
implementation notes in docs are scoped addenda, not replacements for the original
00–17 definitions. Original references were supplied in the parent project and are
not published in this repository. If working without those references, retrieve
them from the project owner before making policy changes.

Keep common infrastructure independent of future service modules. Preserve existing
files, APIs, tables and data. Use explicit Alembic migrations, never create_all or
schema synchronization. Do not add authentication, roles, payments or public Account
endpoints as part of Account Foundation. Unconfirmed business rules stay NEED_REVIEW.

Use Python 3.12, the versions in requirements.lock, and the existing src layout.
Run pytest, ruff and the wheel build for changes. Tests must use temporary databases.
Never commit .env files, DB files, credentials or private reference documents.
Complete and report one task before starting another.
