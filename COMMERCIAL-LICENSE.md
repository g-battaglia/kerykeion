> **Status: DRAFT.** Not legally effective until reviewed and signed by a
> qualified IP / open-source attorney. The terms below are a starting point for
> negotiation, not a binding offer, and not legal advice.

# Kerykeion Commercial License

Kerykeion is dual-licensed. The default public grant is **AGPL-3.0** (see
[LICENSE](LICENSE) and [LICENSING.md](LICENSING.md)). Organizations that cannot
or do not want to comply with the AGPL — for example, embedding Kerykeion in a
closed-source product, or running a SaaS without source disclosure — can instead
obtain a commercial license.

## How to obtain a commercial license

Commercial-licensing terms are arranged **directly with the copyright holder**.
There is no online purchase or self-serve form — please get in touch and we will
work out the terms for your use case:

- **Licensor:** Giacomo Battaglia
- **Contact:** <kerykeion.astrology@gmail.com>

A commercial license typically covers the right to use, modify, and redistribute
Kerykeion in object or source form as part of your products without the AGPL's
source-disclosure obligations, scoped to your distribution model (per product /
per organization, distributed software vs. SaaS). Because the offering runs under
the commercial grant, AGPL §13 (network source disclosure) does not attach.

## What the grant covers

- The Kerykeion code owned by the Licensor at the identified reference tag.
- The default runtime backend, `libephemeris` (also the Licensor's project), is
  licensed **Apache-2.0** and already permits closed-source and commercial use.
  No pass-through grant is needed; the commercial customer must simply preserve
  its copyright, license and attribution notices, including its `NOTICE` file.

## What the grant does not cover

- Bundled glyph assets keep their own terms: public-domain (Symbola) and SIL OFL
  1.1 (Noto Sans Symbols 2); the OFL notice must accompany distributions (see
  [NOTICE](NOTICE)).
- The optional Swiss Ephemeris backend (`pyswisseph` / Astrodienst AG): a
  closed-source product using that backend needs a separate license from
  Astrodienst. It is never installed or used on Kerykeion's default path.

## Provenance

The chart-rendering subsystem uses original / clean-room and permissively
licensed glyph artwork and an independently authored drawing engine; provenance
is recorded in [NOTICE](NOTICE).
