# Skills

One directory per skill: `skills/<name>/SKILL.md`, plus any reference files the skill reads on demand. Skill bodies are written in English for agents (design decision O1); the documents a skill produces follow the project's configured language.

Every directory here must be listed in `.claude-plugin/plugin.json`, and every listed path must exist. `python3 scripts/check_skills.py` enforces both, along with these rules:

- **Frontmatter:** `name` (equal to the directory name) and `description` (at most 1024 characters) are required. Optional keys: `disable-model-invocation`, `argument-hint`, `allowed-tools`. Quote any value that contains `: ` or starts with a YAML indicator character.
- **Two kinds:**
  - **User-invoked** skills orchestrate a piece of work and set `disable-model-invocation: true`.
  - **Model-invoked** skills hold reusable discipline the agent reaches for on its own.

  A user-invoked skill may call model-invoked ones, but never another user-invoked skill in its own session: the model can't invoke a skill that sets `disable-model-invocation`.
- **Coordinators:** a coordinator, a skill whose job is to hand work on (`autopilot`), starts another user-invoked skill in one way: a new session whose prompt is that skill's slash command. Where it may fall back to a subagent or a background agent, or a session needs a second skill, it passes the path of that skill's `SKILL.md` to read and follow, never a summary of it.
- **Short:** each `SKILL.md` is at most 80 lines. Put details in a sibling file and point to it.
- **No personal data:** use fictional examples such as `example-owner` and `example-bot`.

The planned skills are in section 5 of the design document in the pitaya repository, which isn't shipped with the plugin.
