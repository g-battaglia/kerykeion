# Explicit coefficient sources

The LibEphemeris backend accepts `KERYKEION_LEB_MODE=db` and `routed` in
addition to the existing modes. These choices require a compatible LibEphemeris
build exposing the public `calculation_session()` hook; requesting them on an
older build fails explicitly. Install its optional PostgreSQL extra and configure
published datasets/tier routes through LibEphemeris, not chart arguments.

`ephemeris_session()` keeps the existing lock, flags and nesting guard. Inside
that lock it enters the synchronous library coefficient scope, exits the scope
before resetting state, and preserves connection pools/file handles. Chart
calls and scan/refinement calls can share bounded inputs within that logical
scope; remote inputs do not become a cross-request cache.

A caught optional-point or refinement storage failure prevents successful scope
exit. The original source category survives station-factory normalization.
Ordinary input/coverage errors keep their existing behavior. Do not wrap an
asynchronous `await` in this synchronous session or remove the lock as part of
backend configuration.

Point provenance recognizes `DB` and `Mixed` as coefficient-based sources,
independently of transport. Coverage and reviewed status come from the actual
serving source only when that source attests the whole calculation. Mixed
results and every routed result leave the single-reader coverage/review fields
unknown: the target-date reader cannot attest other support epochs or datasets.
Dataset publication alone does not prove a reviewed artifact.
The public factory signatures, chart fields and astronomical reductions are
unchanged. Existing backend versions without the public hook retain their old
behavior when an existing mode is selected.

Targeted regressions live in `tests/core/test_coefficient_session.py`, alongside
the existing backend-path and provenance tests. They cover one chart owner,
optional-point failure, transit-refinement catches, station normalization and
unchanged nesting rejection, and conservative provenance across support sources.

This review branch selects an immutable public source archive of the compatible
coefficient implementation. The coefficient-session tests fail, rather than
silently skip, if that declared dependency lacks the required public hook.
Before publishing a package release, replace the snapshot reference with the
actual compatible released version; no release or deployment is implied here.
