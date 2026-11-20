# pitaya

Small, composable skills for developing with coding agents under human review, with protection that grows by level.

This folder is what the `pitaya` plugin installs. Once installed, the skills appear as `/pitaya:<skill>`.

## Start

1. In your project, run `/pitaya:setup`. It asks a few questions and installs the Level 1 defaults without overwriting anything: an `AGENTS.md` map, the harness config, the memory files, permissions, four hooks and a tests workflow.
2. Cut the project into milestones with `/pitaya:plan --roadmap`, design a milestone with `/pitaya:design M1` (Level 2 and up), and cut it into tickets with `/pitaya:plan M1`. Build a ticket with `/pitaya:build` and have it checked with `/pitaya:verify`. At Level 3, `/pitaya:autopilot` runs a whole milestone.

## Cloud sessions

Claude Code cloud sessions (claude.ai/code, or the desktop app's cloud sessions) don't load plugins: they use only what the repository commits, such as `.claude/skills/`. Project hooks in `.claude/settings.json` still run. To use pitaya there, commit a copy of the plugin into `.claude/` once, from any session that can reach GitHub (replace `<owner>` with the pitaya repository's owner). The script ships from the release after 0.1.0; add `--branch v<version>` to the clone to pin a release once one includes it.

```bash
git clone --depth 1 https://github.com/<owner>/pitaya /tmp/pitaya
python3 /tmp/pitaya/plugin/skills/setup/scripts/vendor_plugin.py --target . --check
python3 /tmp/pitaya/plugin/skills/setup/scripts/vendor_plugin.py --target .
```

It copies `skills/`, `docs/` and `templates/` into `.claude/` and records each file's hash in `.claude/pitaya.json`. Each skill is copied as `pitaya-<name>`, so it can't collide with Claude Code's built-in commands or your own skills: a `build` skill of your own stays as it is. The script never overwrites a file it didn't write; one in its way is reported as `differs` and left alone. An older copy of pitaya made by hand (unprefixed folders such as `.claude/skills/build/`) isn't touched either: if you haven't changed it, delete it so the two copies don't confuse anyone. Commit the copy through a pull request; start a new session if the skills don't appear. Type the skills with a hyphen instead of the colon: `/pitaya-setup`, `/pitaya-plan`, `/pitaya-help`. Where `gh` can't reach GitHub, the skills use the session's GitHub tools. To upgrade, run the script from the newer version with `--upgrade`: it replaces only copies it recorded and nobody edited.

## Read next

- [What each level includes](docs/levels.md): every skill, file and recipe, by level.
- [What each level should have](docs/suggestion.md), and what each component achieves.
- [Guardrail recipes](docs/guardrails/README.md) for Levels 2 and 3.
- [Concepts](docs/concepts/README.md): roles, autonomy, escalation, access, states and layout.
- [Changelog](CHANGELOG.md).

## License

[MIT No Attribution](LICENSE)
