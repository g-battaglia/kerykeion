# Kerykeion CLI Agent Skill

A cross-platform [Agent Skill](https://agentskills.io/) that teaches AI coding
agents to drive **kerykeion from the terminal** — charts, techniques, events and
time series without writing Python.

Works with any skills-aware agent: Claude Code, Cursor, Codex, Copilot,
Gemini CLI, Windsurf, Cline, and others.

## What it covers

- the command tree (about fifty commands) and what each one needs;
- the output contract: text on a terminal, JSON in a pipe, payload on stdout,
  warnings always on stderr;
- the exit-code table, so a script branches on codes instead of matching
  messages;
- the profile store — where birth data is kept, its permissions, `--set` and
  `--snapshot`;
- `kerykeion call`, the guarded dispatcher that reaches every public factory
  the curated commands do not cover;
- the traps that silently produce a wrong chart (house-letter case, DST folds,
  UTC-only ranges, relocated charts needing all three location flags).

For writing **Python** against the library, use the sibling
[`kerykeion`](../kerykeion) skill instead. The two cross-reference each other.

## Install

The skill lives in the [kerykeion repository](https://github.com/g-battaglia/kerykeion),
not in the PyPI package. **While v6 is in alpha, take it from the `alpha/v6`
branch.**

```bash
# gate: skip
git clone --branch alpha/v6 --depth 1 https://github.com/g-battaglia/kerykeion.git
cd kerykeion

# Claude Code
cp -r skills/kerykeion-cli /path/to/your-project/.claude/skills/kerykeion-cli

# Codex
cp -r skills/kerykeion-cli /path/to/your-project/.codex/skills/kerykeion-cli

# Cursor, Windsurf, Cline and others: copy into the agent's skills directory.
```

The skill documents the CLI; using it also needs the CLI itself:

```bash
# gate: skip
pip install "kerykeion[cli]"
```

## Contents

```
SKILL.md                          the router: rules, traps, capability table
references/commands.md            every command and what it needs
references/io-and-exit-codes.md   formats, streams, --envelope, exit codes, info, doctor
references/profiles.md            the profile store, --set, --snapshot, PII
references/rendering.md           SVG appearance and report shaping
references/call-dispatcher.md     reaching any public factory
references/recipes.md             task-shaped examples for pipelines and CI
```

## License

AGPL-3.0, the same as kerykeion. The full text is vendored in `LICENSE`.
