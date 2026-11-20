# pitaya

Small, composable skills for developing with coding agents under human review, with protection that grows by level.

This folder is what the `pitaya` plugin installs. Once installed, the skills appear as `/pitaya:<skill>`.

## Start

1. In your project, run `/pitaya:setup`. It asks a few questions and installs the Level 1 defaults without overwriting anything: an `AGENTS.md` map, the harness config, the memory files, permissions, four hooks and a tests workflow.
2. Cut the project into milestones with `/pitaya:plan --roadmap`, design a milestone with `/pitaya:design M1` (Level 2 and up), and cut it into tickets with `/pitaya:plan M1`. Build a ticket with `/pitaya:build` and have it checked with `/pitaya:verify`. At Level 3, `/pitaya:autopilot` runs a whole milestone.

## Cloud sessions

Claude Code cloud sessions (claude.ai/code, or the desktop app's cloud sessions) have no `/plugin` command and don't load the plugins installed on your own machine. Install pitaya in the cloud environment instead: in **Settings → Environments**, open the environment the project's sessions use and add these lines to its setup script (replace `<owner>` with the pitaya repository's owner):

```bash
claude plugin marketplace add <owner>/pitaya#v0.1.10
claude plugin install pitaya@pitaya
```

The `#v0.1.10` is a release tag: the setup script runs with your repository's access on every new container, so it should install what was released, not whatever the default branch holds that day. To upgrade, change the tag in the setup script (the [changelog](CHANGELOG.md) lists the releases); new sessions get that version.

The setup script runs each time a session's container is built fresh, so every new session in that environment has the plugin, with the same `/pitaya:<skill>` names as on your machine. Check it in a new session by typing `/pitaya:help`. A cloud session is told to push only to its own assigned branch, while pitaya's checks need `plan/<slug>`, `ticket/<id>-<slug>`, `milestone/M<n>` and `sync/<slug>`, and the skills also use `setup/<slug>` and `evidence/<PR>-<short sha>`: the "Branches" section `/setup` puts in `AGENTS.md` grants them once, and the skills use that grant without asking. Until it's there, start each session by allowing them, for example "Use the branch names the pitaya skills ask for; you may create and push them."; put the same sentence in the environment's standing instructions if it has any. An unattended session that finds neither the section nor anyone to ask opens a `needs-owner` issue and stops instead of waiting. A resumed session keeps the version it was built with. Project hooks in `.claude/settings.json` run in cloud sessions too. A cloud session often runs unattended, and unattended work needs a machine account: connect the environment to GitHub as that account, not as yourself ([why](docs/concepts/autonomy.md#unattended-work-needs-a-machine-account)). Where `gh` can't reach GitHub, the skills use the session's GitHub tools.

## Read next

- [What each level includes](docs/levels.md): every skill, file and recipe, by level.
- [What each level should have](docs/suggestion.md), and what each component achieves.
- [Guardrail recipes](docs/guardrails/README.md) for Levels 2 and 3.
- [Concepts](docs/concepts/README.md): roles, autonomy, escalation, access, states and layout.
- [Changelog](CHANGELOG.md).

## License

[MIT No Attribution](LICENSE)
