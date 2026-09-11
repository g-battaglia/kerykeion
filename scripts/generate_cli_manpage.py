#!/usr/bin/env python3
"""Generate the kerykeion(1) man page from the CLI's own argparse tree.

The command tree is assembled at runtime (``kerykeion_cli.app.build_parser``),
so a hand-written page would drift the first time a command is renamed. This
script walks the same parser ``--help`` prints, renders deterministic roff
into ``cli/man/man1/kerykeion.1``, and that file ships as wheel data
(``share/man/man1``) — see ``poe man:generate`` and the anti-drift gate
``poe man:check``.

Per-command flags are deliberately not enumerated: the page is the map, and
``kerykeion <command> --help`` stays the reference for one command's flags,
exactly as its SEE ALSO section says.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANPAGE_PATH = ROOT / "cli" / "man" / "man1" / "kerykeion.1"
WIDTH = 72  # nroff renders at 80 columns; 72 leaves the classic margin

# One gloss per ExitCode member: a code the library gains without a line here
# must fail the gate loudly (KeyError) rather than ship undocumented.
_EXIT_GLOSSES = {
    0: "OK: success.",
    1: "UNEXPECTED: a bug; rerun with --traceback to see it.",
    4: "INVALID_INPUT: a flag or value is wrong; the message names it.",
    5: "KERYKEION_ERROR: the library refused the request.",
    6: "EPHEMERIS: outside ephemeris coverage, or the data files are unusable.",
    7: "NETWORK: GeoNames unreachable.",
    8: "SAMPLING_LIMIT: the series exceeds the sampling ceiling; nothing was computed.",
    9: "WARNINGS_AS_ERRORS: warnings were made fatal by --warnings-as-errors.",
    130: "INTERRUPTED: Ctrl-C.",
}

_EXAMPLES: list[tuple[str, list[str]]] = [
    (
        "Save a subject once, then reuse it everywhere with -s",
        [
            'kerykeion subject save ada --name "Ada Lovelace" --date 1900-12-10 --time 18:00 \\',
            "    --lat 51.5074 --lng -0.1278 --tz Europe/London --offline",
            "kerykeion natal -s ada",
        ],
    ),
    (
        "A terminal gets the text report, a pipe gets JSON - no extra flag",
        [
            "kerykeion natal -s ada | jq -r .sun.sign",
        ],
    ),
    (
        "An SVG wheel, themed, written to a file",
        [
            "kerykeion natal -s ada -f svg -o ada.svg --theme dark",
        ],
    ),
    (
        "A year of transits, as events",
        [
            "kerykeion transits -s ada --from 2026-01-01 --to 2026-12-31 --events",
        ],
    ),
    (
        "Ask the CLI what a flag accepts, read from the library at runtime",
        [
            "kerykeion info literals SiderealMode",
        ],
    ),
    (
        "Judge the install (exit 6 when it is genuinely broken)",
        [
            "kerykeion status --check",
        ],
    ),
]


def esc(text: str) -> str:
    """Escape for roff: backslash and hyphen are request/glyph syntax in man pages."""
    return text.replace("\\", r"\(rs").replace("-", r"\-")


def _prose(text: str) -> list[str]:
    """Wrap escaped prose, neutralising any line that would read as a roff request."""
    # The command docstrings quote flag names reST-style (``--orb``); man has no
    # backtick syntax, and rendering the markers literally would be noise.
    text = text.replace("``", "")
    lines = textwrap.wrap(esc(text), width=WIDTH) or [""]
    return [f"\\&{line}" if line.startswith((".", "'")) else line for line in lines]


def _version() -> str:
    """The CLI's own version, from the file the one-version gate already watches."""
    return tomllib.loads((ROOT / "cli" / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def _choices(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser] | None:
    """A parser's subcommand choices, or None when it has none (a leaf command)."""
    holder = getattr(parser, "_subparsers", None)
    if holder is None:
        return None
    for action in holder._group_actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices
    return None


def collect_commands(parser: argparse.ArgumentParser | None = None) -> list[str]:
    """Every command path the CLI accepts (``technique profections`` …), in tree order."""
    if parser is None:
        from kerykeion_cli.app import build_parser

        parser = build_parser()
    paths: list[str] = []
    for name, sub in (_choices(parser) or {}).items():
        nested = _choices(sub)
        if nested is None:
            paths.append(name)
        else:
            paths.extend(f"{name} {leaf}" for leaf in nested)
    return paths


def _command_entry(parser: argparse.ArgumentParser) -> list[str]:
    """One command as a tagged paragraph: its concise synopsis, then its description."""
    lines = [".TP", f".B {esc(parser.usage or parser.prog)}"]
    lines += _prose(parser.description or "")
    return lines


def render_manpage() -> str:
    """The full page, byte-for-byte stable for a given parser tree and version."""
    from kerykeion_cli.app import DESCRIPTION, build_parser
    from kerykeion_cli.diagnostics import _KNOWN_ENV
    from kerykeion_cli.errors import ExitCode

    root = build_parser()
    lines: list[str] = []
    add = lines.append

    add(r'.\" Generated by scripts/generate_cli_manpage.py - do not edit.')
    add(r'.\" Regenerate with `poe man:generate`; the gate is `poe man:check`.')
    # No date on purpose: a build day is unstable and a release day is a second
    # place the version would have to be kept in step.
    add(f'.TH KERYKEION 1 "" "kerykeion-cli {_version()}" "User Commands"')

    add(".SH NAME")
    add("kerykeion \\- astrology from the terminal")

    add(".SH SYNOPSIS")
    add(".B kerykeion")
    add(".RI [ global\\-flags ]")
    add(".I command")
    add(".RI [ command\\-flags ]")
    add(".PP")
    add(".B python \\-m kerykeion_cli")
    add(".I [the same arguments]")

    add(".SH DESCRIPTION")
    lines += _prose(DESCRIPTION)
    add(".PP")
    lines += _prose(
        "The payload always goes to stdout and warnings always to stderr, in every format, so a "
        "piped payload stays clean."
    )
    add(".PP")
    lines += _prose(
        "The engine is the library itself, in-process and offline: no key, no server. Save a subject "
        "once (kerykeion subject save NAME ...) and pass -s NAME to any command that needs one."
    )

    add(".SH GLOBAL FLAGS")
    add("These go before the command. A bare \\fBkerykeion\\fR prints help and exits 0.")
    for action in root._actions:  # registration order: -h, -V, --traceback, --warnings-as-errors
        if isinstance(action, argparse._SubParsersAction):
            continue
        add(".TP")
        add(f".B {esc(', '.join(action.option_strings))}")
        lines += _prose(action.help or "")

    add(".SH COMMANDS")
    lines += _prose(
        "The tree below is generated from the same parser behind --help, so it cannot fall out of "
        "step with it. A command's own flags are documented by kerykeion <command> --help, and "
        "kerykeion info lists every value the value-taking flags accept."
    )
    for name, sub in (_choices(root) or {}).items():
        nested = _choices(sub)
        if nested is None:  # a top-level command
            lines += _command_entry(sub)
        else:  # a group (technique, sky, subject, info): a subsection with its own commands
            add(f".SS {esc(name)}")
            lines += _prose(sub.description or "")
            for _, leaf in nested.items():
                lines += _command_entry(leaf)

    add(".SH OUTPUT FORMATS")
    for fmt, meaning in (
        ("text", "the ASCII report (the default on a terminal)"),
        ("json", "the Pydantic model_dump_json() payload (the default in a pipe)"),
        ("xml", "the to_context() document, the compact LLM-oriented serialisation"),
        ("svg", "an SVG chart wheel (chart commands)"),
    ):
        add(".TP")
        add(f".B {esc(fmt)}")
        lines += _prose(meaning)
    add(".PP")
    lines += _prose(
        "Resolution order: -f, then the suffix of -o, then $KERYKEION_CLI_FORMAT, then the "
        "terminal-or-pipe default. --envelope wraps a JSON payload with the version, backend and "
        "warnings for a consumer that only captures stdout."
    )

    add(".SH SUBJECT PROFILES")
    lines += _prose(
        "A profile is a small JSON recipe (written 0600, in a 0700 directory: birth data is "
        "personal) under $XDG_CONFIG_HOME/kerykeion/subjects/. subject save writes one; subject "
        "list, subject show, subject path and subject verify inspect it; -s <name> (and -S for a "
        "second subject) reuses it everywhere. A profile is a recipe, never a cached chart: every "
        "read rebuilds the subject, so it cannot go stale across versions."
    )

    add(".SH ENVIRONMENT")
    add(".TP")
    add(".B KERYKEION_CLI_FORMAT")
    lines += _prose("the default output format when -f and -o are absent (text, json, xml or svg).")
    add(".TP")
    add(".B XDG_CONFIG_HOME")
    lines += _prose("root of the profile store; defaults to ~/.config when unset.")
    add(".PP")
    lines += _prose(
        "The ephemeris backend is configured through the environment too; "
        f"{', '.join(_KNOWN_ENV)} select and shape it, and kerykeion status reports "
        "which values are in effect."
    )

    add(".SH FILES")
    add(".TP")
    add(".I $XDG_CONFIG_HOME/kerykeion/subjects/*.json")
    lines += _prose("the stored subject profiles.")

    add(".SH EXIT STATUS")
    lines += _prose("Exit codes are the contract: branch on the code, never on the message text.")
    for code in sorted(set(ExitCode) | {2}):
        add(".TP")
        add(f".B {code}")
        if code == 2:  # argparse's own SystemExit, not a member of ExitCode
            lines += _prose("usage: the argument parser rejected the command line.")
        else:
            name, meaning = _EXIT_GLOSSES[code].split(":", 1)
            lines += _prose(f"{name}:{meaning}")

    add(".SH EXAMPLES")
    for caption, commands in _EXAMPLES:
        add(".PP")
        lines += _prose(caption)
        add(".RS 4")
        add(".nf")
        for command in commands:
            add(esc(command))
        add(".fi")
        add(".RE")

    add(".SH SEE ALSO")
    for what, where in (
        ("the flags of one command", "kerykeion <command> --help"),
        ("every value the flags accept", "kerykeion info literals"),
        ("the complete CLI reference", "https://www.kerykeion.net/content/docs/cli/"),
        ("the library this command drives", "https://www.kerykeion.net"),
    ):
        add(".TP")
        add(f".B {esc(where)}")
        lines += _prose(what)

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write the page, or with --check fail when the committed one has drifted."""
    check = "--check" in (sys.argv[1:] if argv is None else argv)
    expected = render_manpage()
    if check:
        current = MANPAGE_PATH.read_text(encoding="utf-8") if MANPAGE_PATH.exists() else ""
        if current != expected:
            print(f"FAIL: {MANPAGE_PATH.relative_to(ROOT)} does not match the CLI's argparse tree")
            print("Regenerate it with: uv run poe man:generate")
            return 1
        print(
            f"man page OK: {MANPAGE_PATH.relative_to(ROOT)} matches the parser tree ({len(collect_commands())} commands)"
        )
        return 0
    MANPAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANPAGE_PATH.write_text(expected, encoding="utf-8", newline="")  # LF only: the wheel bytes stay reproducible
    print(f"wrote {MANPAGE_PATH.relative_to(ROOT)} ({len(collect_commands())} commands)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
