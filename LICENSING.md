> **Status: DRAFT.** Not legally effective until reviewed and signed by a
> qualified IP / open-source attorney. This describes an *intended*
> dual-licensing model for Kerykeion; it is not legal advice or a binding offer.

# Licensing

Kerykeion is intended to be **dual-licensed**: the same codebase is offered
under two alternative grants, and you choose the one you use it under.

## 1. Open source — AGPL-3.0

The default license is the [GNU Affero General Public License v3](LICENSE)
(AGPL-3.0). It is free for any use — including commercial use — as long as you
comply with its terms, most notably: if you distribute the software, or make a
modified version available to users over a network, you must make the
corresponding source code available under the AGPL.

The packages published on PyPI are AGPL-3.0.

## 2. Commercial license

Organizations that cannot or do not want to comply with the AGPL — for example,
embedding Kerykeion in a closed-source product, or running a SaaS without source
disclosure — can obtain a commercial license from the copyright holder instead.
See [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md).

- Contact: Giacomo Battaglia — <kerykeion.astrology@gmail.com>

## How the dual license works

- Giacomo Battaglia is the copyright holder of Kerykeion. External contributions
  are assigned to the maintainer under the CLA (see [CONTRIBUTING.md](CONTRIBUTING.md)),
  which is what enables the dual grant.
- **Scope of the commercial grant.** The commercial license applies to the state
  of the code at an identified reference tag/commit of this repository — not to
  the Git history, and not to previously published AGPL releases.
- **Past AGPL releases stay AGPL.** Versions already published under AGPL-3.0
  remain available under AGPL-3.0; those grants are irrevocable. This is the
  standard dual-license model (cf. Qt, MySQL): old releases stay open, while the
  current and future code may additionally be offered commercially.
- **Bundled assets.** The chart glyphs bundled in the package are public-domain
  (Symbola), SIL OFL 1.1 (Noto Sans Symbols 2), or clean-room originals; see
  [NOTICE](NOTICE). The OFL components require their notice to travel with any
  distribution, including the commercial edition.
- **Runtime backend.** The default ephemeris backend, `libephemeris`, is itself
  dual-licensed (`AGPL-3.0-only OR LicenseRef-LibEphemeris-Commercial`) and is
  authored by the same maintainer; the commercial edition elects its commercial
  grant — see [LIBEPHEMERIS-COMMERCIAL-GRANT.md](LIBEPHEMERIS-COMMERCIAL-GRANT.md).
  The optional Swiss Ephemeris backend (`pyswisseph`) is never used on the
  default path and requires a separate license from Astrodienst AG for closed use.

## Commercial delivery

A commercial recipient receives a snapshot of the tree at the reference tag
(e.g. via `git archive` of the tag, **without** the `.git` history). Note that
the public repository is mirrored on both GitHub and GitLab.

## Contributions

External contributions are accepted only under the CLA in
[CONTRIBUTING.md](CONTRIBUTING.md), which assigns copyright to the maintainer so
the contribution can be distributed under **both** grants.
