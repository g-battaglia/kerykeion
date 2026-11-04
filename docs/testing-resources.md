# Resource-safe validation

Pytest runs serially by default. CPU count is not a memory budget: `pytest -n auto`
previously launched 18 workers on this machine, each independently retaining native
astronomical data. Parallel execution is now an explicit choice, for example
`uv run pytest -n 2`; choose it only after measuring the per-worker workload.
Cold-import checks also default to one subprocess. `--jobs 2` opts into two probes.

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

The configuration and allocation mechanism explain the observed memory pressure.
No matching OS panic or OOM diagnostic was available for the reported freeze, so
this does not claim that every machine/application crash has the same cause.
The available Python crash reports were from the previous day and identified a
`curl-impersonate` allocator failure, not the native ephemeris reader.
