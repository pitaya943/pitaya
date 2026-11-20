# pitaya

Small, composable skills for developing with coding agents under human review, with protection that grows by level.

This folder is what the `pitaya` plugin installs. Once installed, the skills appear as `/pitaya:<skill>`.

## Start

1. In your project, run `/pitaya:setup`. It asks a few questions and installs the Level 1 defaults without overwriting anything: an `AGENTS.md` map, the harness config, the memory files, permissions, four hooks and a tests workflow.
2. Cut the project into milestones with `/pitaya:plan --roadmap`, design a milestone with `/pitaya:design M1` (Level 2 and up), and cut it into tickets with `/pitaya:plan M1`. Build a ticket with `/pitaya:build` and have it checked with `/pitaya:verify`. At Level 3, `/pitaya:autopilot` runs a whole milestone.

## Read next

- [What each level includes](docs/levels.md): every skill, file and recipe, by level.
- [What each level should have](docs/suggestion.md), and what each component achieves.
- [Guardrail recipes](docs/guardrails/README.md) for Levels 2 and 3.
- [Concepts](docs/concepts/README.md): roles, autonomy, escalation, access, states and layout.
- [Changelog](CHANGELOG.md).

## License

[MIT No Attribution](LICENSE)
