---
title: 'Constants'
category: 'Reference'
description: 'Exhaustive lists of available celestial points, aspects, and configuration constants.'
tags: ['docs', 'constants', 'planets', 'aspects', 'configuration']
order: 18
---

# Configuration Constants

Import from: `kerykeion.settings.config_constants`

This page lists the exhaustive options available for configuring Kerykeion charts.

## Celestial Points (`AstrologicalPoint`)

When customizing `active_points`, you can use any of the following string identifiers.

### Major Bodies

-   `Sun`
-   `Moon`
-   `Mercury`
-   `Venus`
-   `Mars`
-   `Jupiter`
-   `Saturn`
-   `Uranus`
-   `Neptune`
-   `Pluto`

### Lunar Nodes & Lilith

-   `Mean_North_Lunar_Node`
-   `True_North_Lunar_Node`
-   `Mean_South_Lunar_Node`
-   `True_South_Lunar_Node`
-   `Mean_Lilith`
-   `True_Lilith`

### Angles

-   `Ascendant`
-   `Medium_Coeli`
-   `Descendant`
-   `Imum_Coeli`
-   `Vertex`
-   `Anti_Vertex`

### Asteroids & Centaurs

-   `Chiron`
-   `Ceres`
-   `Pallas`
-   `Juno`
-   `Vesta`
-   `Pholus`

### Trans-Neptunian Objects (TNOs)

-   `Eris`
-   `Sedna`
-   `Haumea`
-   `Makemake`
-   `Ixion`
-   `Orcus`
-   `Quaoar`

### Arabic Parts

-   `Pars_Fortunae` (Part of Fortune)
-   `Pars_Spiritus` (Part of Spirit)
-   `Pars_Amoris` (Part of Eros)
-   `Pars_Fidei` (Part of Faith)

### Fixed Stars

-   `Regulus`
-   `Spica`

## Aspect Names (`AspectName`)

Identifiers for configuring `active_aspects`.

### Major Aspects

-   `conjunction` (0°)
-   `opposition` (180°)
-   `trine` (120°)
-   `square` (90°)
-   `sextile` (60°)

### Minor Aspects

-   `quintile` (72°)
-   `semi-sextile` (30°)
-   `semi-square` (45°)
-   `sesquiquadrate` (135°)
-   `biquintile` (144°)
-   `quincunx` (150°)

## Default Preset Constants

These lists are available for quick configuration.

### `DEFAULT_ACTIVE_POINTS`

Main planets, Chiron, Mean Lilith, Nodes, and Angles.

### `ALL_ACTIVE_POINTS`

Every point listed above.

### `DEFAULT_ACTIVE_ASPECTS`

Conjunction, Opposition, Trine, Square, Sextile, Quintile.

### `ALL_ACTIVE_ASPECTS`

All major and minor aspects listed above.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
