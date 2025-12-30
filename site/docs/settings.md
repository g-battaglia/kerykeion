---
title: 'Settings'
category: 'Core'
description: 'Global configuration settings for Kerykeion'
tags: ['docs', 'settings', 'config']
order: 13
---

# Settings (`kerykeion.settings`)

This module handles the global configuration for Kerykeion calculations and cache management.

## Accessing Settings

You can retrieve the current settings instance using `get_settings()`.

```python
from kerykeion.settings import get_settings

settings = get_settings()
print(settings.json_dir)
```

## `KerykeionSettingsModel`

The settings are defined by a Pydantic model that controls various aspects of the library's behavior.

### Key Configuration Options

- **Directories**:
  - `json_dir`: Directory to store JSON output (default: "json").
  - `cache_dir`: Directory to store cache files (default: "cache").

_(See `settings_models` for the full list of configurable options)_
