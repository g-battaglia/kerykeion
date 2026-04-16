# GLM Audit — Kerykeion v5.12.7

> Analisi approfondita condotta da GLM-5.1 su tutto il codebase di Kerykeion.
> Data: 14 Aprile 2026

---

## Sommario Esecutivo

Il progetto Kerykeion è una libreria Python 3.9+ per astrologia, basata su Swiss Ephemeris (`pyswisseph`), Pydantic v2 per i modelli, e generazione di chart SVG. Utilizza un pattern factory con `AstrologicalSubjectFactory`, `ChartDataFactory`, `AspectsFactory`, ecc. La legacy API v4 è mantenuta tramite wrapper in `backword.py`. Build system: Hatchling. Linting: Ruff. Type checking: MyPy + Pyright.

**Risultato complessivo:** Il codebase è funzionale e ben strutturato nella sua architettura generale. Tuttavia presenta problemi di duplicazione significativa (specialmente nel modulo charts ~9400 linee), potenziali rischi di importazione circolare, problemi di performance legati a deepcopy e concatenazione stringhe, e diverse lacune nella tipizzazione e gestione errori.

---

## 1. Importazione Circolare (ALTA PRIORITÀ)

**File:** `kerykeion/schemas/kr_models.py` linee 35-52

`schemas/kr_models.py` importa da `kerykeion.schemas` (il `__init__.py` del package) che a sua volta importa da `kr_models.py` — creando un ciclo `A importa B, B importa A`. Funziona a runtime grazie al caching dei moduli Python, ma è fragile.

**Fix:** In `kr_models.py`, importare direttamente da `kr_literals.py` invece che dal package `__init__`.

---

## 2. Duplicazione Massiva nel Modulo Charts

### 2.1 Funzioni quasi-identiche in coppia

6 coppie di funzioni quasi identiche in `charts_utils.py` e `draw_planets.py` (main vs secondary grid/indicator functions).

### 2.2 Controlli tipo chart inconsistenti

42 controlli del tipo di chart tramite stringhe letterali sparsi in tutto il modulo, con pattern inconsistenti.

### 2.3 Algoritmi di collision-resolution duplicati

Due algoritmi indipendenti per risolvere sovrapposizioni planetarie: uno in `draw_planets.py`, uno in `draw_modern.py`.

### 2.4 Dead code wrapper

`draw_single_cusp_comparison_grid` in `charts_utils.py` è un wrapper pass-through al 100% — non aggiunge alcuna logica.

---

## 3. Problemi di Performance

### 3.1 Concatenazione stringhe O(n²)

Tutto il modulo charts usa `+=` su stringhe per generazione SVG. Questo è O(n²) per via dell'immutabilità delle stringhe Python. Dovrebbe usare `io.StringIO` o lista + `"".join()`.

### 3.2 No caching template

I template SVG vengono letti da disco ad ogni generazione. Dovrebbero essere cachati in memoria con `functools.lru_cache`.

### 3.3 Deepcopy non necessaria di LANGUAGE_SETTINGS

`deepcopy` dell'intero dizionario `LANGUAGE_SETTINGS` (~1743 linee) ad ogni chiamata di caricamento settings, anche quando non ci sono override forniti. Dovrebbe copiare solo se ci sono effettive modifiche.

### 3.4 Funzione `_deep_merge()` duplicata

La stessa funzione `_deep_merge()` è definita identica in entrambi `kerykeion_settings.py` e `translations.py`.

---

## 4. Sicurezza dei Tipi (Type Safety)

### 4.1 Stringhe letterali al posto di ChartType

42 controlli del tipo di chart usano stringhe letterali (`"Natal"`, `"Synastry"`, ecc.) invece del tipo `ChartType` Literal già definito.

### 4.2 ActiveAspect come TypedDict

`ActiveAspect` è un `TypedDict` in mezzo a modelli Pydantic — incoerente con il resto del codebase.

### 4.3 Parametri tipizzati come `object`

In `moon_phase_details/factory.py`, i parametri `sun` e `moon` sono tipizzati come bare `object`.

### 4.4 Inconsistenza Union vs Optional

Uso misto di `Union[X, None]` vs `Optional[X]` senza motivo apparente.

### 4.5 Forward references non necessari

String forward references usati dove i tipi sono già importati.

---

## 5. Gestione Errori Mancante

### 5.1 Fallback silenzioso in safe_parse_iso_datetime()

`safe_parse_iso_datetime()` in `utilities.py` ritorna silenziosamente `datetime.now()` in caso di fallimento — potrebbe produrre risultati silenziosamente errati senza alcun warning.

### 5.2 Nessuna validazione in HouseComparisonFactory

`HouseComparisonFactory.__init__` non valida che i subject abbiano dati delle case.

### 5.3 Import dentro loop

`import re` dentro un loop body in `house_comparison_utils.py` linea 176.

---

## 6. Pulizia del Progetto Root (~206 MB di spazzatura)

### 6.1 File di log

5 file di log (8.9 MB totali): `lib-test.log`, `lib.log`, `log.log`, `swe-test.log`, `test.log`

### 6.2 Cache e coverage

`http_cache.sqlite`, `coverage.xml`, `htmlcov/` (191 MB)

### 6.3 Dist stale

`dist/` contiene build v6.0.0 alpha

### 6.4 Config ridondante

- `setup.cfg` (flake8) è ridondante — ruff in `pyproject.toml` lo copre
- `.coveragerc` è ridondante — `[tool.coverage]` in `pyproject.toml` lo copre

### 6.5 `.gitignore` mancante

Non ignora: `.ruff_cache/`, `cache/`, `.claude/`, `.opencode/`

### 6.6 `poe clean` incompleto

Non pulisce `*.log`, `http_cache.sqlite`, `cache/`

---

## 7. Problemi Schema/Modello

### 7.1 `kr_types/` è uno shim di backward-compat

L'intera directory `kr_types/` (6 file, 176 linee) è uno shim che re-esporta da `schemas/` con wildcard imports e deprecation warnings.

### 7.2 `schemas/__init__.py` export incompleti

Esporta solo 18 modelli ma ne sono definiti 30+. Codice esterno deve usare import diretti da sottomoduli.

### 7.3 `SubscriptableBaseModel.__delitem__` pericoloso

Può rimuovere field Pydantic required senza alcuna guardia.

### 7.4 Nessun modello frozen/strict

Nessun modello ha `frozen`, `strict`, o `extra="forbid"` — permettendo typos silenziosi e mutazioni non intenzionali.

### 7.5 `ChartTemplateModel` con 62 field individuali

62 campi `planets_color_N` invece di una lista/dict. Inefficiente e non scalabile.

### 7.6 `AstrologicalBaseModel` con 90+ field

Molto costoso da istanziare, e probabilmente dovrebbe essere spezzato in modelli più piccoli.

---

## 8. Lacune nelle Traduzioni

Le seguenti lingue mancano di chiavi: `cusp_position_comparison`, `transit_cusp`, `return_cusp`, `house`, `return_point`:
- Turco (TR)
- Russo (RU)
- Tedesco (DE)
- Hindi (HI)

---

## 9. Modulo Moon Phase

### 9.1 Tuple fragile

`_compute_lunar_phase_metrics()` ritorna una tupla di 9 elementi — estremamente fragile. Dovrebbe essere un NamedTuple o dataclass.

### 9.2 Classe mai istanziata

`MoonPhaseDetailsFactory` non viene mai istanziata — tutti i metodi sono classmethod/staticmethod. Dovrebbe essere un modulo con funzioni a livello di modulo.

---

## 10. Parametri Mutabili come Default

`DEFAULT_ACTIVE_POINTS` usato come valore di default per parametri in multipli posti. Se modificato, il default viene alterato per tutte le chiamate successive.

---

## Piano di Refactoring Priorizzato

### FASE 0 — Pulizia Progetto (zero rischio, zero impatto API)

| # | Azione | Dettaglio |
|---|--------|-----------|
| 0.1 | Aggiornare `.gitignore` | Aggiungere `.ruff_cache/`, `cache/`, `.claude/`, `.opencode/`, `*.log` |
| 0.2 | Rimuovere file spazzatura | `*.log` (5 files, 8.9 MB), `http_cache.sqlite`, `htmlcov/` (191 MB), `dist/` con v6.0.0 alpha |
| 0.3 | Rimuovere config ridondante | `setup.cfg` (flake8, già coperto da ruff in `pyproject.toml`), `.coveragerc` (già in `[tool.coverage]`) |
| 0.4 | Aggiornare `poe clean` | Aggiungere pulizia `*.log`, `http_cache.sqlite`, `cache/`, `.ruff_cache/` |

### FASE 1 — Fix Sicurezza & Correttezza (rischio basso, alto impatto)

| # | Azione | File | Dettaglio |
|---|--------|------|-----------|
| 1.1 | Fix importazione circolare | `schemas/kr_models.py:35-52` | Importare da `kr_literals.py` invece che da `schemas/__init__` |
| 1.2 | Spostare `import re` fuori dal loop | `house_comparison/house_comparison_utils.py:176` | `import re` dentro un `for` loop |
| 1.3 | Loggare warning in fallback | `utilities.py` | `safe_parse_iso_datetime()` ritorna `datetime.now()` silenziosamente |
| 1.4 | Parametro mutabile come default | Multiplo | `DEFAULT_ACTIVE_POINTS` — avvolgere in `None` + `if x is None` |
| 1.5 | Guard su `__delitem__` | `schemas/kr_models.py` | Prevenire rimozione field required |

### FASE 2 — Deduplicazione (rischio basso, medio impatto)

| # | Azione | File | Dettaglio |
|---|--------|------|-----------|
| 2.1 | Estrarre `_deep_merge()` shared | `settings/kerykeion_settings.py` + `settings/translations.py` | Funzione identica duplicata |
| 2.2 | Unificare algoritmi collision-resolution | `charts/draw_planets.py` + `charts/draw_modern.py` | Due algoritmi indipendenti |
| 2.3 | DRY charts_utils / draw_planets | `charts/charts_utils.py` + `charts/draw_planets.py` | 6 coppie quasi identiche |
| 2.4 | Rimuovere dead code wrapper | `charts/charts_utils.py` | `draw_single_cusp_comparison_grid` pass-through inutile |

### FASE 3 — Tipizzazione & Schemas (rischio medio, alto impatto mantenibilità)

| # | Azione | File | Dettaglio |
|---|--------|------|-----------|
| 3.1 | Usare `ChartType` Literal | Charts module | Sostituire 42 stringhe letterali |
| 3.2 | Convertire `ActiveAspect` a Pydantic | `schemas/kr_models.py` | L'unico TypedDict |
| 3.3 | Tipizzare `sun`/`moon` params | `moon_phase_details/factory.py` | Attualmente `object` |
| 3.4 | Uniformare Optional vs Union | Multiplo | Scegliere uno stile |
| 3.5 | Aggiungere `extra="forbid"` | `schemas/settings_models.py` | Prevenire typos silenziose |

### FASE 4 — Performance (rischio medio, alto impatto)

| # | Azione | File | Dettaglio |
|---|--------|------|-----------|
| 4.1 | Evitare deepcopy inutile | `settings/kerykeion_settings.py` | Copiare solo se ci sono override |
| 4.2 | Caching template SVG | Charts module | `lru_cache` per template |
| 4.3 | `io.StringIO` per SVG | Charts module | Sostituire `+=` con lista/StringIO |
| 4.4 | Factory → funzioni modulo | `moon_phase_details/factory.py` | Mai istanziata |

### FASE 5 — Charts Module Refactoring (rischio medio-alto, alto impatto)

| # | Azione | File | Dettaglio |
|---|--------|------|-----------|
| 5.1 | Spezzare `chart_drawer.py` (4615 linee) | `charts/chart_drawer.py` | Estrarre classi per tipo di chart |
| 5.2 | `ChartTemplateModel` → lista colori | `schemas/chart_template_model.py` | 62 campi → `planets_colors: List[str]` con backward-compat |
| 5.3 | Centralizzare costanti SVG | Charts module | Dimensioni, offset, colori sparsi |

### FASE 6 — Traduzioni (rischio basso, impatto utente)

| # | Azione | Dettaglio |
|---|--------|-----------|
| 6.1 | Completare chiavi mancanti | TR, RU, DE, HI: aggiungere chiavi mancanti |

---

## Struttura del Codebase Analizzato

### Core Factory Modules
- `kerykeion/__init__.py` — Public API exports
- `kerykeion/astrological_subject_factory.py` — Main subject factory (1700+ linee)
- `kerykeion/chart_data_factory.py` — Chart data assembly (573 linee)
- `kerykeion/composite_subject_factory.py` — Composite charts (403 linee)
- `kerykeion/ephemeris_data_factory.py` — Ephemeris time series (475 linee)
- `kerykeion/planetary_return_factory.py` — Solar/Lunar returns (797 linee)
- `kerykeion/relationship_score_factory.py` — Compatibility scoring (363 linee)
- `kerykeion/transits_time_range_factory.py` — Transit analysis (302 linee)

### Utility/Support Modules
- `kerykeion/utilities.py` — Core utilities (774 linee)
- `kerykeion/fetch_geonames.py` — GeoNames API client (258 linee)
- `kerykeion/context_serializer.py` — XML context serialization (1027 linee)
- `kerykeion/backword.py` — Legacy v4 API wrappers (828 linee)
- `kerykeion/report.py` — Text report generation (988 linee)

### Subpackage: Aspects
- `kerykeion/aspects/aspects_factory.py` — Aspect calculations (619 linee)
- `kerykeion/aspects/aspects_utils.py` — Aspect utility functions (224 linee)

### Subpackage: Charts (~9400 linee totali)
- `kerykeion/charts/chart_drawer.py` — Main chart drawer (4615 linee — monolite)
- `kerykeion/charts/charts_utils.py` — Chart utilities (2261 linee)
- `kerykeion/charts/draw_modern.py` — Modern chart style (1465 linee)
- `kerykeion/charts/draw_planets.py` — Planet drawing (1087 linee)

### Subpackage: Settings
- `kerykeion/settings/config_constants.py` — Constants and defaults (406 linee)
- `kerykeion/settings/chart_defaults.py`
- `kerykeion/settings/kerykeion_settings.py`
- `kerykeion/settings/translations.py`
- `kerykeion/settings/translation_strings.py` — ~1743 linee di dati traduzione

### Subpackage: Schemas/Models
- `kerykeion/schemas/kr_models.py` — Tutti i modelli Pydantic
- `kerykeion/schemas/kr_literals.py` — Type aliases e literals
- `kerykeion/schemas/settings_models.py` — Settings models
- `kerykeion/schemas/chart_template_model.py` — Chart template model
- `kerykeion/schemas/kerykeion_exception.py` — Exception class

### Subpackage: Legacy Types (backward compat shim)
- `kerykeion/kr_types/` — 6 file, tutti re-export wrapper con deprecation warnings

### Altri Subpackages
- `kerykeion/moon_phase_details/` — factory.py, utils.py
- `kerykeion/house_comparison/` — house_comparison_factory.py, house_comparison_utils.py

### Configurazione
- `pyproject.toml` — Config principale (295 linee)
- `setup.cfg` — Legacy flake8 config (21 linee, ridondante)
- `.coveragerc` — Legacy coverage config (17 linee, ridondante)
- `pyrightconfig.json`
- `.gitignore`

### Test Suite
- `tests/conftest.py` — Fixtures centralizzate (574 linee)
- `tests/core/conftest.py` — Core test helpers (286 linee)
- `tests/core/` — 25+ file di test
- `tests/data/` — Dati attesi e matrici di test
- `tests/data/configurations/` — Test parametrizzati per house systems, sidereal modes, perspectives, returns, ephemeris, composite

---

*Fine dell'analisi.*
