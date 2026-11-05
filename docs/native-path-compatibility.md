# Native path compatibility

The published Kerykeion 6.1.0b2 / LibEphemeris 4.0.0b2 pair forwards an empty
path from default sessions and legacy lunar helpers. Native lookup then raises
`DataNotFoundError` in `get_library_path()` and `release_data_cache()`. This is
reproduced with both unmodified published packages as a negative control.

## Integration contract

All Kerykeion calls to `set_ephe_path` now live in the backend adapter. Native
empty/default selections preserve the engine's discovery and warm readers.
Adapter-owned explicit selections restore native defaults only when still owned;
unrelated external overrides are retained. Lunar and solar helpers share these
rules and do not replace the selected path inside an active native session.
Swiss Ephemeris retains its previous per-helper path application.

LibEphemeris 4.0.0b4 normalizes an empty path to `"."` in the Rust runtime,
preserving the old Python engine's `abspath("")` current-directory behavior.
`None` restores default discovery. This supersedes the prepared native b3
interpretation of empty as default; its source tag remains immutable. The
integration never relies on the empty sentinel.
The Kerykeion correction also works with native b2, whose direct empty setter
remains defective in that already-published distribution.

## Regression coverage

The sealed embedded-base probe uses a temporary empty data directory with no
downloads. It checks five repeated sessions, default and configured paths,
legacy lunar-phase calls, explicit paths inside sessions, external overrides,
both affected maintenance functions and exact before/after calculation results.
Controls cover ten planets on five dates, twelve houses on five dates, five
sidereal solar positions and the same lunar-phase search. Mocked backend cases
also detect an empty setter call even when the newer native engine would accept
it, and preserve the Swiss path contract.

The focused set passes with LibEphemeris b2 and b4 on Python 3.12.13 and 3.14.7
(macOS ARM64). All four environments produce the same calculation-control hash.
The original reported Fedora Asahi ARM64 environment uses Python 3.14.10; that
exact platform/interpreter is not claimed as a local test result.
Machine-readable evidence: [native-path-compatibility.json](native-path-compatibility.json).

Run the portable probe against an installed candidate on Linux or another host:

```sh
python tests/data/native_path_probe.py
```

It prints the actual platform, interpreter, package identity, source hashes and
calculation hash. A superseded candidate that still forwards an empty native
path fails explicitly rather than being masked by native acceptance of empty paths.


The complete extended/offline suites pass on both interpreters: 14,736 native
cases and 14,217 Swiss cases, with 28 and 547 explicit skips respectively and
three online cases deselected. Native b4 wheel qualification additionally passes
on Linux x86_64/ARM64 and Windows x86_64, Python 3.12/3.14; this does not claim the
complete Kerykeion suite ran on those hosts.

The matrix exposed a macOS exit-transition race in the unshipped development
watchdog. Cleanup now observes the unreaped leader briefly after `EPERM`, accepts
an observed zombie and still propagates persistent permission denial. No group
is re-signaled or reaped during this observation. All 20 focused watchdog tests
and ten independent cancellation runs pass per interpreter. Its ten 10 ms sleeps
form a nominal sleep budget, not a strict wall-clock bound. The Windows missing
executable test now captures file-descriptor output as well as Python streams;
Windows watchdog runtime execution remains a separate qualification task.
