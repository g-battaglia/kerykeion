# Resource-safe validation

The final four-PR beta qualification covers **14,662 unique cases**, with
**491.9 MiB** maximum sampled RSS in the complete test suites and **644.0 MiB**
in `poe check`. See the [final qualification](../release_notes/v6.1.0b1-validation.md).
The earlier measurements below retain their original scope.

Pytest runs serially by default. CPU count is not a memory budget: `pytest -n auto`
previously launched 18 workers on this machine, each independently retaining native
astronomical data. Parallel execution is now an explicit choice, for example
`uv run pytest tests/core -m 'not online' -n 2`; choose it only after measuring the per-worker workload.
Cold-import checks also default to one subprocess. `--jobs 2` opts into two probes.
Isolated Python documentation snippets likewise default to one subprocess;
`scripts/test_markdown_snippets.py --jobs 2` explicitly enables two at a time.

## A bounded full-range run

```sh
LIBEPHEMERIS_PRECISION=extended uv run poe test:bounded
```

This runs the offline tests in one process with libephemeris's indexed LEB reader,
which reads needed data instead of retaining a full owned file image. The same
extended dataset, dates, calculations and assertions are used. Installed datasets
must remain unchanged during the run. The library's normal reader default and
snapshot behavior are unchanged: the opt-in belongs only to this task.

The watchdog samples the command and its descendants every 100 ms. Above 1 GiB of
summed RSS it terminates the tree, escalates to kill after one second, and exits
125. Normal command exit codes and output are preserved. Interrupts and POSIX
termination signals clean up the command rather than leaving it running in the
background. POSIX commands run at lower CPU priority when permitted.

This is a sampled stop threshold, not a hard OS allocation limit: a brief spike
can exceed it before the next sample. Shared pages may be counted in multiple
processes, so the sum is deliberately conservative. To use a different threshold:

```sh
LIBEPHEMERIS_PRECISION=extended LIBEPHEMERIS_LEB_READER=indexed \
  uv run python scripts/run_resource_limited.py --rss-limit-mib 768 -- \
  python -m pytest tests/ --tier=extended -m 'not online' -n 0
```

Only development tooling depends on `psutil`; installed library users gain no new
runtime dependency. The watchdog can also supervise `poe check` or another command.

## What caused the memory risk

The interrupted `poe check` log records `created: 18/18 workers`. Its pytest options
inherited `-n auto`. Libephemeris's owned reader uses `std::fs::read` to retain an
immutable native byte image; these are separate allocations in separate Python
processes. Python allocation tracing does not account for those native buffers.

The local extended LEB partitions total **2.677 GiB**: core 1.074, apogee 1.379,
exotics 0.218 and asteroids 0.006 GiB. Loading all partitions in all 18 workers can
therefore require **48.19 GiB for file images alone**, exceeding the machine's
48 GiB before Python, decoded caches, the OS or applications. This is a capacity
calculation, not an attempt to reproduce that dangerous allocation.

An earlier monitored owned-reader run was stopped at approximately 1,385 MiB
before completing even the targeted tests. A base-date probe with the owned
reader used 148.7 MiB RSS while Python's traced allocation peak was only 34.4 MiB;
the same probe with indexed reads used 100.0 MiB and produced identical values.

With indexed reads and one process, the complete optimized extended suite passed:
**14,331 passed, 72 skipped**, sampled process-tree peak **408.7 MiB**. The three
GeoNames online tests passed separately at **211.8 MiB**. All 1,470 stored owned-
reader output hashes/model comparisons also match the indexed-reader run.

## System diagnostics from the actual freezes

Sanitized fields are retained in [the evidence summary](testing-resource-evidence.json);
raw machine reports, UUIDs, stack addresses and unrelated process details are not
committed.

- **2026-11-04 05:55:18 CET:** the kernel panic reports no watchdog check-ins
  for **94 seconds**. Its memory snapshot has only **14.3 MiB free**, a **25.8 GiB
  compressor**, and 35 `python3.12` processes; 25 report more than 1 GiB apiece.
- **06:00:08 CET**, after the reboot: a Jetsam event identifies `python3.12` as
  the largest process. It records 22 such processes and **51.3 GiB of accounted
  process pages**. It also records 147 terminations with reason
  `vm-compressor-space-shortage`.

Accounted process pages and sums of per-process resident figures are not unique
physical RAM; shared/compressed memory prevents treating them as a physical total.
The snapshots nevertheless document severe memory exhaustion, in addition to the
18-worker command log and the reader's per-process allocation mechanism. The
immediate reboot mechanism was the kernel watchdog timeout. These findings support
memory oversubscription as the cause of the validation freezes without claiming
that every unrelated crash has that cause. The previous day's `curl-impersonate`
allocator crashes are separate diagnostics.

## Initial combined validation

The two PRs were merged in a temporary verification checkout. The new
`poe test:bounded` path completed **14,341 passed, 72 skipped**, including all ten
resource-runner tests, at **415.0 MiB sampled process-tree peak RSS**. The extended run's 72 skips consist of 50 unavailable mean-node reference entries,
13 medium-only range-edge cases, four textual comparisons of minified geometry
covered by separate symbol checks, three inapplicable reference frames and two
optional font/rendering assets. The medium-only cases were then run in the proper
configuration: **26 passed, no skips**, at **108.3 MiB** sampled peak. The three
online tests passed separately.

The full `poe check` sequence also passed with serial/indexed execution and a
1 GiB watchdog: Ruff, mypy, pyright, structural/fresh imports, 7,913 core tests,
1,155 baseline-gate tests, CLI smoke, all 39 runnable CLI examples and the generated
manpage check. Its sampled process-tree peak was **581.8 MiB**.

## Final strict coverage audit

The later verification combines this fix, optimization PR #273 and
[test-coverage PR #275](https://github.com/g-battaglia/kerykeion/pull/275), with
`-n 0 -W error`, indexed reads and the same 1 GiB sampled watchdog. The extended
suite, including online tests and optional font/PNG checks, passed **14,404 tests**
with **13 medium-specific skips** at **489.1 MiB** peak. All 13 skipped identifiers
passed in the medium configuration (**26 passed, zero skipped**, **160.5 MiB** peak).

Across profiles, **all 14,417 unique collected cases passed at least once**:
zero unverified cases, failures or unexpected warnings. Counts overlap across
profiles and must not be added as unique tests. PR #275 closes the earlier mean-
node, fixed-reference and minified-geometry gaps without changing golden fixtures
or numerical tolerances. Its [report and reproduction commands](validation-completeness.md)
include source commits and the matching identifier-set hashes. Test and benchmark
commands were sequential; no automatic worker pool was used.
