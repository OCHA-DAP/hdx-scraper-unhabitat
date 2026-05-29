# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**hdx-scraper-unhabitat** downloads data from the [UN Habitat site](https://data.unhabitat.org/) and creates global and country level datasets in HDX. It fetches datasets for open spaces, urban transport, spatial growth of cities, housing/slums, and basic services.

## Commands

Install dependencies:
```bash
uv sync
```

Run the scraper:
```bash
uv run python -m hdx.scraper.unhabitat
```

Run tests:
```bash
uv run pytest
```

Run a single test:
```bash
uv run pytest tests/test_unhabitat.py
```

Lint check:
```bash
pre-commit run --all-files
```

## Architecture

The pipeline in `__main__.py`:

1. **`main`** — Verifies HDX write access, then iterates over a list of dataset names.
2. **`UNHabitat`** — Fetches data from the UN Habitat API, generates HDX datasets, and uploads them.

### Key design points

- **Config files**: Dataset metadata lives in `src/hdx/scraper/unhabitat/config/` (`hdx_dataset_static.yaml`, `project_configuration.yaml`).
- **Datasets**: `open_spaces`, `urban_transport`, `spatial_growth_cities`, `housing_slums`, `basic_services`.

## Environment

Requires `~/.hdx_configuration.yaml` with HDX credentials, or env vars: `HDX_KEY`, `HDX_SITE`, `USER_AGENT`, `EXTRA_PARAMS`, `TEMP_DIR`, `LOG_FILE_ONLY`.

Requires `~/.useragents.yaml` with a `hdx-scraper-unhabitat` entry.

## Collaboration Style

- Be objective, not agreeable. Act as a partner, not a sycophant. Push back when you disagree, flag tradeoffs honestly, and don't sugarcoat problems.
- Keep explanations brief and to the point.
- Don't rely on recalled knowledge for facts that could be stale (API behaviour, library versions, external systems). Search or read the actual source first.

## Scope of Changes

When fixing a bug or addressing PR feedback, change only what is necessary to resolve the specific issue. Do not refactor surrounding code, rename variables, adjust formatting, or make improvements in the same commit unless they are directly required by the fix.
