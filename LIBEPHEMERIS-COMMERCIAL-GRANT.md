> **Status: DRAFT internal memorandum.** Not legally effective until reviewed,
> dated, and signed. Not legal advice.

# libephemeris commercial-grant election for the Kerykeion commercial edition

## Purpose

Kerykeion's default ephemeris backend is **libephemeris**, pinned in
`pyproject.toml`. libephemeris is published under the SPDX expression
`AGPL-3.0-only OR LicenseRef-LibEphemeris-Commercial` and is authored by the same
copyright holder as Kerykeion. This memo records the election of the commercial
grant for the Kerykeion commercial edition, and the pass-through of that grant to
Kerykeion commercial customers, so that a closed-source or SaaS deployment of
Kerykeion does not inherit libephemeris's AGPL obligations (including AGPL §13
network source disclosure).

## Election

I, Giacomo Battaglia, sole copyright holder of both Kerykeion and libephemeris,
elect the `LicenseRef-LibEphemeris-Commercial` grant for libephemeris as
incorporated in the Kerykeion commercial edition, covering both distributed
software and SaaS use; and I grant each Kerykeion commercial licensee a
pass-through libephemeris commercial license for the same scope as their
Kerykeion commercial license.

## Conditions / open items (pre-GA)

- **Pin a final release.** Kerykeion currently pins `libephemeris==3.0.0rc1` (a
  release candidate). Before commercial GA, repin to the final
  `libephemeris==3.0.0` once published. Note that the dual-license election is
  declared in libephemeris's bundled license files (`LICENSING.md` / `NOTICE.md`):
  the PEP 639 `License-Expression` metadata field carries the single
  `AGPL-3.0-only` term, while the `OR LicenseRef-LibEphemeris-Commercial` election
  lives in those files — confirm both on repin. *(As of this draft no final 3.0.0
  exists on PyPI — the latest is `3.0.0rc1`; re-check before GA.)*
- **Title check.** libephemeris's own provenance supports this grant: sole human
  author; only permissive (MIT) vendored components; JPL DE440/DE441 public-domain
  data; the last copyleft module retired by a June-2026 clean-room rewrite. Keep
  its `NOTICE.md` / `THIRD_PARTY_NOTICES.md` on file as the provenance record.

## Signature

    Giacomo Battaglia   ___________________________   Date: ______________
