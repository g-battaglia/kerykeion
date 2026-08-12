# Kerykeion Agent Skill

A cross-platform [Agent Skill](https://agentskills.io/) that teaches AI coding
agents the real kerykeion v6 API — factories, chart types, aspects, backends,
sidereal modes, predictive and traditional techniques — so generated code uses
the current public surface instead of guessed method names.

Works with any skills-aware agent: Claude Code, Cursor, Codex, Copilot,
Gemini CLI, Windsurf, Cline, and others.

## Install

With [skills.sh](https://skills.sh/):

```bash
npx skills add g-battaglia/kerykeion
```

Or copy the folder manually into your agent's skills directory:

```bash
# Claude Code
cp -r skills/kerykeion /path/to/your-project/.claude/skills/kerykeion

# Codex
cp -r skills/kerykeion /path/to/your-project/.agents/skills/kerykeion

# Generic agentskills.io layout (Cursor and others)
cp -r skills/kerykeion /path/to/your-project/skills/kerykeion
```

## What's inside

```
kerykeion/
├── SKILL.md          Entry point: mental model, routing table, top traps
├── references/       One file per API domain (subjects, charts, aspects,
│                     backends, predictive, mundane events, traditional, ...)
│                     plus api-index.md, the full name → file coverage map
├── scripts/
│   ├── quickstart.py Offline end-to-end sanity check (run it to verify install)
│   └── env_report.py Backend / env-var / ephemeris-coverage diagnostic
└── LICENSE           AGPL-3.0 (the skill is licensed like the library)
```

## Authoring rules (for kerykeion contributors)

The canonical copy of this skill lives at `skills/kerykeion/` in the
[kerykeion repository](https://github.com/g-battaglia/kerykeion) and is
maintained under three mechanical gates:

- `poe docs:check` — every name exported by `kerykeion.__all__` must appear in
  the skill corpus.
- `poe docs:snippets` (or the focused
  `python scripts/test_markdown_snippets.py --skill`) — every ```` ```python ````
  block is executed in isolation. A block must be fully self-contained and run
  offline on a default install, or carry `# doc-snippet: no-run` as its first
  line.
- `tests/core/test_agent_skill_contract.py` — validates frontmatter, the
  vendored license, reference reachability, and version references.

Any change to public behavior (exports, defaults, error contracts, warnings)
must update this skill **in the same commit**.

## License

AGPL-3.0-only, same as kerykeion itself — see the vendored [LICENSE](LICENSE)
file. For commercial licensing without copyleft obligations, or the hosted
[Astrologer API](https://www.kerykeion.net/astrologer-api), contact
kerykeion.astrology@gmail.com.
