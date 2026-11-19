# Memory and config files

`/setup` copies the files in this folder into a project's `docs/agents/`, unchanged. This README is the one file it never copies.

One file the project gets in `docs/agents/` isn't here: `harness.md`. It holds values only the project knows (the Owner, the machine account, the test command, the level), so `/setup` fills it in from [`skills/setup/harness-template.md`](../../../skills/setup/harness-template.md) instead of copying a file with placeholder values. A copied placeholder would look valid, and every skill would follow it faithfully. When the file is missing, skills suggest `/setup` once and continue with safe defaults.

See [`docs/levels.md`](../../../docs/levels.md) for everything each level includes.
