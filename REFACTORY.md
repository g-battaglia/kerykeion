# Kerykeion v6 — Piano di Refactoring e Ottimizzazione

> **Versione:** 6.0.0a24 | **Branch:** `alpha/v6` | **Data analisi:** 2026-04-16
>
> **Principio guida:** Nessun breaking change, nessuna regressione su edge case.
> Ogni modifica deve produrre output identico al precedente.
> `poe test:core` e' il **gate minimo**, non il gate sufficiente per chiudere un refactor.

## Vincoli non negoziabili

- **Retrocompatibilita' totale**: nessuna modifica a API pubbliche, nomi esportati, shape dei modelli,
  semantics dei flag, ordine dei risultati o comportamento documentato.
- **Output stabile**: dove esistono fixture/golden file, l'output deve restare identico. Le baseline non
  vanno rigenerate per "far passare" un refactor; prima si spiega il delta, poi eventualmente si decide.
- **Nessuna rimozione di dipendenze o path pubblici** senza una necessita' esplicita. In particolare,
  `scour` **non va rimosso**: il piano assume continuita' tramite fork compatibile.
- **Le ottimizzazioni numeriche non sono "safe" solo perche' matematicamente plausibili**: devono essere
  validate anche su codepath sidereal, topocentric, heliocentric, planetocentric e date storiche.
- **Le ottimizzazioni di performance non devono peggiorare la leggibilita' strutturale**: si preferiscono
  refactor piccoli e locali nei path caldi, non sweep repo-wide a basso ROI.

---

## Sommario

- [Contesto e architettura](#contesto-e-architettura)
- [Benchmark di riferimento](#benchmark-di-riferimento)
- [TIER 0 — Cleanup puro](#tier-0--cleanup-puro-zero-rischio)
- [TIER 1 — Ottimizzazioni sicure](#tier-1--ottimizzazioni-sicure-logica-identica)
- [TIER 2 — Ottimizzazioni moderate](#tier-2--ottimizzazioni-moderate-test-mirati-necessari)
- [TIER 3 — Ottimizzazioni avanzate](#tier-3--ottimizzazioni-avanzate-rischio-più-alto)
- [TIER 4 — Architetturali (fuori scope)](#tier-4--architetturali-fuori-scope-per-ora)
- [Impatto stimato](#impatto-stimato)
- [Strategia di esecuzione](#strategia-di-esecuzione)

---

## Contesto e architettura

### Backend ephemeris (libephemeris con LEB)

Tutte le chiamate standard `swe.calc_ut()` utilizzano il backend **LEB** (file `.leb` precomputati
con polinomi di Chebyshev). **Skyfield non viene mai usato per i calcoli standard** — si attiva
come fallback esclusivamente per `swe.gauquelin_sector()`.

La catena di chiamata per un singolo subject (18 active points di default):

```
from_birth_data()  ~1.57ms totali
  ├── _calculate_time_conversions()     pytz.timezone() + UTC conversion
  ├── _calculate_houses()               1x swe.houses_ex2()  ~0.17ms
  ├── _calculate_single_planet() x13    13x swe.calc_ut(ECLIPTIC) + 13x swe.calc_ut(EQUATORIAL)
  ├── _compute_is_diurnal()             1x swe.calc_ut(Sun) + 1x swe.azalt()  ← Sun già calcolato
  ├── _calculate_derived_points()       Puro calcolo aritmetico (opposite +180°)
  └── model_copy(update=...)            Pydantic model update per optional calculations
```

**Totale chiamate `calc_ut` per subject: 29** (13 ECLIPTIC + 13 EQUATORIAL + 1 ECL_NUT + 1 Sun diurnal + 1 extra True_Node EQUATORIAL).

### Pydantic v2 e `SubscriptableBaseModel`

Tutti i modelli dati ereditano da `SubscriptableBaseModel(BaseModel)` che aggiunge:

```python
def __getitem__(self, key): return getattr(self, key)
```

Questo permette accesso dict-style `model["field"]` su modelli Pydantic, ma è **~1.5x più lento**
dell'accesso diretto `model.field`. Viene usato intensivamente nei path caldi
(`aspects_utils.py`, `charts_utils.py`).

**ATTENZIONE:** In alcuni codepath (specialmente `charts_utils.py`), vengono passati **plain `dict`**
e non modelli Pydantic. Cambiare `obj["key"]` in `obj.key` senza un audit completo di ogni call site
causerebbe `AttributeError` sui dict. Questa modifica è classificata come **TIER 3 (alto rischio)**.

### Generazione SVG

Il rendering SVG usa template-based string substitution:

1. Template SVG caricato da file (con `@lru_cache(maxsize=8)`)
2. Dati calcolati e inseriti via `string.Template.substitute()`
3. Post-processing opzionale: `scour` (78ms) o regex-only (3ms)

Il bottleneck principale SVG e' `draw_aspect_grid()` in `charts_utils.py:1063` con complessita' **O(n^3)**:
per ogni cella nella griglia triangolare, fa uno scan lineare di TUTTI gli aspetti.

---

## Benchmark di riferimento

Valori misurati con `scripts/benchmark.py` su macchina di sviluppo:

| Operazione | Tempo |
|---|---|
| Subject creation (`from_birth_data`) | ~1.57ms |
| Aspect calculation (18 points, 6 aspects) | ~0.45ms |
| SVG Natal (con minify scour) | ~85ms |
| SVG Natal (senza minify) | ~7ms |
| `swe.houses_ex2()` singola | ~0.17ms |
| `swe.calc_ut()` singola (LEB) | ~0.04ms |
| `scourString()` su SVG reale | ~78ms |
| Regex minification su SVG reale | ~3ms |
| Import iniziale kerykeion (cold) | ~2s (1.3s numpy/skyfield) |
| Gauquelin sector (fallback Skyfield) | ~26.5ms |

**Nota importante:** questi numeri non sono tutti coperti automaticamente da `scripts/benchmark.py`.
Lo script corrente misura subject creation, aspects e SVG standard, ma **non** copre direttamente:
- cold import iniziale;
- costo isolato di `scour`;
- byte-size/minify stability;
- confronto byte-identico degli SVG minificati.

Per modifiche che toccano minify, SVG golden o path di import servono quindi benchmark e confronti mirati,
non solo il benchmark standard.

---

## TIER 0 — Cleanup puro (zero rischio)

Modifiche che non cambiano nessun comportamento: rimozione di codice morto, import inutilizzati,
e micro-correzioni stilistiche.

### 0.1 — Rimuovere 14 import `Path` inutilizzati

Dopo un refactoring, `pathlib.Path` e' rimasto importato ma non usato in molti factory module.

**File coinvolti:**

| File | Linea |
|---|---|
| `kerykeion/astro_cartography/acg_factory.py` | 21 |
| `kerykeion/eclipses/eclipse_factory.py` | 17 |
| `kerykeion/heliacal/heliacal_factory.py` | 21 |
| `kerykeion/moon_phase_details/utils.py` | 27 |
| `kerykeion/occultations/occultation_factory.py` | 35 |
| `kerykeion/planetary_nodes/nodes_factory.py` | 17 |
| `kerykeion/planetary_phenomena/phenomena_factory.py` | 18 |
| `kerykeion/planetary_return_factory.py` | 73 |
| `kerykeion/primary_directions/directions_factory.py` | 22 |
| `kerykeion/relocated_chart_factory.py` | 15 |

**Azione:** Rimuovere le righe `from pathlib import Path` in ognuno di questi file.

### 0.2 — Rimuovere import inutilizzati in chart_drawer.py

| Import | Linea | Motivo |
|---|---|---|
| `datetime.datetime` | 10 | Non usato nel file |
| `kerykeion.schemas.kr_models.ChartDataModel` | 50 | Importato ma mai referenziato |

### 0.3 — Rimuovere import inutilizzato in charts_utils.py

| Import | Linea | Motivo |
|---|---|---|
| `kerykeion.schemas.kr_models.HouseComparisonModel` | 24 | Non usato nel file |

### 0.4 — Rimuovere import inutilizzati in house_comparison_factory.py

| Import | Linea | Motivo |
|---|---|---|
| `kerykeion.schemas.AstrologicalSubjectModel` | 19 | Non usato |
| `kerykeion.schemas.PlanetReturnModel` | 19 | Non usato |

### 0.5 — Rimuovere import inutilizzato in moon_phase_details/factory.py

| Import | Linea | Motivo |
|---|---|---|
| `datetime.timedelta` | 31 | Non usato nel file |

### 0.6 — Compilare regex a livello modulo in utilities.py

**File:** `kerykeion/utilities.py`, linea 800

**Problema attuale:** `re.compile()` viene chiamato dentro un `for style_block in style_blocks` loop
nella funzione `inline_css_variables_in_svg()`. Il pattern e' invariante e dovrebbe essere
compilato una sola volta a livello modulo.

**Codice attuale (linea 800):**
```python
for style_block in style_blocks:
    css_variable_pattern = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;]+);")
    for match in css_variable_pattern.finditer(style_block):
        ...
```

**Codice target:**
```python
# A livello modulo, fuori dalla funzione:
_CSS_VARIABLE_PATTERN = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;]+);")

# Dentro la funzione:
for style_block in style_blocks:
    for match in _CSS_VARIABLE_PATTERN.finditer(style_block):
        ...
```

### 0.7 — Eliminare 3 lambda `should_calculate` duplicate

**File:** `kerykeion/astrological_subject_factory.py`, linee 1540, 1750, 2061

**Problema:** Tre metodi diversi definiscono la stessa identica lambda wrapper:
```python
should_calculate = lambda point: AstrologicalSubjectFactory._should_calculate(point, active_points)
```

La lambda non fa altro che delegare al metodo statico `_should_calculate(point, active_points)` (linea 1481).

**Azione:** Sostituire ogni occorrenza di `should_calculate(point)` con la chiamata diretta
`AstrologicalSubjectFactory._should_calculate(point, active_points)`, oppure — piu' leggibile —
rinominare il metodo statico e usarlo direttamente. Eliminare le 3 definizioni di lambda.

---

## TIER 1 — Ottimizzazioni sicure (logica identica)

Queste modifiche producono risultati **matematicamente identici** ma con codice piu' efficiente.

### 1.1 — Cache `get_args(Houses)` a livello modulo

**File:** `kerykeion/utilities.py`, linea 328

**Problema:** `get_planet_house()` viene chiamato ~29 volte per subject. Ogni chiamata esegue
`get_args(Houses)` che internamente fa introspezione sul tipo `Literal` — costa ~0.25us per call
vs ~0.08us se cachato.

**Codice attuale:**
```python
def get_planet_house(planet_degree, houses_degree_ut_list):
    house_names = get_args(Houses)  # <-- chiamato ogni volta
    for i in range(len(house_names)):
        ...
```

**Codice target:**
```python
# A livello modulo:
_HOUSE_NAMES: tuple[str, ...] = get_args(Houses)

def get_planet_house(planet_degree, houses_degree_ut_list):
    for i in range(len(_HOUSE_NAMES)):
        start_degree = houses_degree_ut_list[i]
        end_degree = houses_degree_ut_list[(i + 1) % len(houses_degree_ut_list)]
        if is_point_between(start_degree, end_degree, planet_degree):
            return _HOUSE_NAMES[i]
    ...
```

**Stessa cosa per** `get_args(LunarPhaseEmoji)` e `get_args(LunarPhaseName)` alle linee 481 e 499.

### 1.2 — Eliminare chiamata EQUATORIAL `calc_ut` duplicata per ogni pianeta

**File:** `kerykeion/astrological_subject_factory.py`, linea 1684-1691

**Problema:** Per ogni pianeta vengono fatte **2 chiamate** a `swe.calc_ut()`:
1. ECLIPTIC (per longitudine, latitudine, velocita')
2. EQUATORIAL (solo per estrarre la declinazione)

La declinazione si puo' calcolare analiticamente dalle coordinate eclittiche + obliquita' dell'eclittica:

```
sin(delta) = sin(epsilon) * sin(lambda) * cos(beta) + cos(epsilon) * sin(beta)
```

Dove:
- `delta` = declinazione
- `epsilon` = obliquita' eclittica (ottenibile da `swe.calc_ut(jd, SE_ECL_NUT, 0)` gia' chiamato 1 volta)
- `lambda` = longitudine eclittica (gia' calcolata)
- `beta` = latitudine eclittica (gia' calcolata)

**Riclassificazione:** questa ottimizzazione **non va trattata come safe by default**.
E' promettente, ma deve essere eseguita con validazione numerica estesa e quindi va pianificata come
**Fase 3 / TIER 2**, non insieme ai cleanup sicuri.

**Verifica richiesta:** non basta un confronto su chart tropicali standard. La parita' numerica va dimostrata
almeno su:
- Tropical / Apparent Geocentric
- True Geocentric
- Topocentric
- Heliocentric
- almeno un Sidereal mode
- almeno un codepath planetocentric (`calc_pctr`)

**Impatto:** Da 29 a ~16 chiamate `calc_ut` per subject (~45% in meno).

**Codice attuale (linee 1689-1694):**
```python
planet_calc = swe.calc_ut(julian_day, planet_id, iflag)[0]
planet_eq = swe.calc_ut(julian_day, planet_id, iflag | swe.FLG_EQUATORIAL)[0]
declination = planet_eq[1]
```

**Codice target:**
```python
planet_calc = swe.calc_ut(julian_day, planet_id, iflag)[0]
# Declination from ecliptic coords + obliquity (no extra calc_ut needed)
declination = math.degrees(math.asin(
    math.sin(math.radians(obliquity)) * math.sin(math.radians(planet_calc[0])) * math.cos(math.radians(planet_calc[1]))
    + math.cos(math.radians(obliquity)) * math.sin(math.radians(planet_calc[1]))
))
```

L'obliquita' (`obliquity`) non va solo letta in `_calculate_single_planet()`: per avere comportamento coerente,
la stessa logica va applicata anche ai codepath secondari che oggi ricalcolano la declinazione in modo separato
(prerequisiti delle Arabic Parts, nodi, fallback correlati). Una patch parziale introdurrebbe comportamento misto.

**Attenzione per `calc_pctr`:** Lo stesso pattern si applica ai calcoli planetocentrici
(linee 1683-1684). La formula analitica resta identica, va solo usata l'obliquita' corretta.

### 1.3 — Pre-build lookup dict per aspect settings

**File:** `kerykeion/aspects/aspects_utils.py`, linee 35-43

**Problema:** `get_aspect_from_two_points()` per ogni coppia di pianeti fa un **scan lineare**
di `aspects_settings` per trovare l'aspetto corrispondente. Con 6 aspetti default e ~153 coppie
(18 punti), sono ~918 confronti.

**Codice attuale:**
```python
for aspect in aspects_settings:
    aspect_degree = aspect["degree"]
    aspect_orb = aspect["orb"]
    if (aspect_degree - aspect_orb) <= distance <= (aspect_degree + aspect_orb):
        ...
```

**Approccio:** Non si puo' usare un dict diretto perche' il matching e' per range (degree +/- orb).
Pero' si puo' pre-ordinare per degree e usare binary search (`bisect`), oppure — visto che sono solo
6-11 aspetti — lasciar stare e concentrarsi sui bottleneck piu' grandi (1.2, 1.4).

**Alternativa pragmatica:** Pre-estrarre `degree` e `orb` come tuple per evitare il dict lookup
ripetuto dentro il loop.

**Priorita':** bassa. Questo punto non va anteposto ai bottleneck confermati (`1.4`, string building mirato,
validazione del refactor declinazione).

```python
# Pre-process una sola volta:
_settings_tuples = [(a["degree"], a["orb"], a["name"]) for a in aspects_settings]

# Nel loop hot:
for degree, orb, name in _settings_tuples:
    if (degree - orb) <= distance <= (degree + orb):
        ...
```

### 1.4 — `draw_aspect_grid` da O(n^3) a O(n^2 + k) con pre-index

**File:** `kerykeion/charts/charts_utils.py`, linee 1098-1123

**Problema:** Questo e' il **bottleneck #1 del rendering SVG** (58% del tempo).
Per ogni cella nella griglia triangolare degli aspetti, fa uno scan lineare di TUTTI gli aspetti
per cercare se esiste un aspetto tra `planet_a` e `planet_b`.

Con 18 pianeti attivi: 153 celle * ~50 aspetti = ~7650 confronti, piu' 866K chiamate a `__getitem__`.

**Codice attuale (linee 1118-1122):**
```python
for aspect in aspects:
    if (aspect["p1"] == planet_a["id"] and aspect["p2"] == planet_b["id"]) or (
        aspect["p1"] == planet_b["id"] and aspect["p2"] == planet_a["id"]
    ):
        svg_output += f'<use x="..." xlink:href="#orb{aspect["aspect_degrees"]}" />'
```

**Codice target:** Costruire un dizionario di lookup **prima** del loop:

```python
# Pre-build: O(k) dove k = numero aspetti
aspect_lookup: dict[tuple[int, int], dict] = {}
for aspect in aspects:
    key = (min(aspect["p1"], aspect["p2"]), max(aspect["p1"], aspect["p2"]))
    aspect_lookup[key] = aspect

# Nel loop: O(1) per cella
for planet_b in reversed_planets[index + 1:]:
    svg_output += f'<rect .../>'
    key = (min(planet_a["id"], planet_b["id"]), max(planet_a["id"], planet_b["id"]))
    if key in aspect_lookup:
        aspect = aspect_lookup[key]
        svg_output += f'<use x="..." xlink:href="#orb{aspect["aspect_degrees"]}" />'
```

**Impatto:** Da O(n^2 * k) a O(n^2 + k). Con valori reali: da ~7650 confronti a ~153 lookup O(1).

### 1.5 — `+=` string concatenation nei loop SVG con `list.append()` + `"".join()`

**File principali:**
- `kerykeion/charts/charts_utils.py` — **218 operazioni `+=`**, 0 `"".join()`
- `kerykeion/charts/draw_modern.py` — **83 operazioni `+=`**
- `kerykeion/charts/chart_drawer.py` — 36 operazioni `+=`
- `kerykeion/charts/draw_planets.py` — 9 operazioni `+=`

**Problema:** Ogni `svg_output += f'<...'` dentro un loop crea un **nuovo oggetto stringa** copiando
tutto il contenuto precedente. In Python le stringhe sono immutabili, quindi la complessita' di
n concatenazioni e' O(n^2) nel caso peggiore.

**I casi piu' critici:**

1. **`draw_aspect_grid()` — triple nested loop** (linee 1098-1123): Ogni iterazione del loop
   piu' interno aggiunge una riga SVG. Con la griglia triangolare, sono centinaia di allocazioni.

2. **`draw_houses_cusps_and_text_number()` — 11 `+=` per iterazione** (linee 1220-1252):
   Per ogni casa (12 iterazioni), 11 concatenazioni = 132 riallocazioni di stringa.

3. **`draw_transit_ring_degree_steps()` / `draw_degree_ring()`** (linee 888-936):
   72 iterazioni con 1 `+=` ciascuna.

4. **`draw_modern.py` — `_draw_cusp_ring()`** (linee 410-493):
   ~15 `+=` per iterazione * 12 case = ~180 riallocazioni.

**Pattern target:**
```python
# PRIMA (O(n^2)):
svg_output = ""
for item in items:
    svg_output += f'<rect x="{item.x}" .../>'

# DOPO (O(n)):
parts: list[str] = []
for item in items:
    parts.append(f'<rect x="{item.x}" .../>')
svg_output = "".join(parts)
```

**Nota:** `draw_planets.py` linea 781 usa GIA' il pattern corretto (`parts` list + `"".join()`).

**Correzione del piano:** non fare una sweep indiscriminata su tutti i `+=` del package. Limitarsi ai
codepath davvero caldi e facili da verificare:
1. `draw_aspect_grid()`
2. `draw_houses_cusps_and_text_number()`
3. `_draw_cusp_ring()` in `draw_modern.py`

Gli altri casi vanno toccati solo se mostrano guadagni misurabili o se migliorano chiaramente la leggibilita'.

### 1.6 — Evitare ri-calcolo Sun in `_compute_is_diurnal()`

**File:** `kerykeion/astrological_subject_factory.py`, linee 1873-1876

**Problema:** `_compute_is_diurnal()` chiama `swe.calc_ut(julian_day, 0, sun_tropical_flags)` per
ottenere la longitudine del Sole. Ma il Sole e' gia' stato calcolato in `_calculate_single_planet()`
poco prima.

**Codice attuale (linea 1875):**
```python
sun_tropical_flags = swe.FLG_SWIEPH | swe.FLG_SPEED
sun_calc = swe.calc_ut(julian_day, 0, sun_tropical_flags)[0]
sun_lon = sun_calc[0]
```

**Soluzione:** Passare la longitudine del Sole gia' calcolata come parametro. Attenzione pero':
il commento nel codice spiega che si usa intenzionalmente un calcolo **tropicale geocentrico**
indipendente dal `zodiac_type` del chart. Se il chart e' siderale, `data["sun"].abs_pos` sarebbe
in coordinate siderali, non tropicali.

**Azione sicura:** Solo se il chart e' **Tropical + Apparent Geocentric**, riusare il valore gia' calcolato.
In tutti gli altri casi, mantenere la chiamata separata. Aggiungere un parametro opzionale
`sun_tropical_lon: Optional[float] = None` al metodo.

### 1.7 — Unificare `_POINT_NUMBER_MAP` e `STANDARD_PLANETS` in `config_constants.py`

**File coinvolti:**
- `kerykeion/utilities.py`, linee 56-97: `_POINT_NUMBER_MAP`
- `kerykeion/astrological_subject_factory.py`, linee 88-122: `STANDARD_PLANETS`

**Problema:** Due dizionari quasi identici che mappano nomi di pianeti a ID Swiss Ephemeris.
Il commento in `utilities.py:52-55` spiega che la duplicazione e' intenzionale per evitare
circular import con `astrological_subject_factory.py`.

**Differenza chiave:** `_POINT_NUMBER_MAP` include entry extra non presenti in `STANDARD_PLANETS`:
- `Mean_South_Lunar_Node: 1000`
- `True_South_Lunar_Node: 1100`
- `White_Moon: 56`
- `Ascendant: 9900`, `Descendant: 9901`, `Medium_Coeli: 9902`, `Imum_Coeli: 9903`

**Soluzione:** Spostare entrambi i mapping in `kerykeion/settings/config_constants.py` (che non
importa da nessuno dei due moduli, quindi niente circular import). Poi importare da li'.

**Vincolo di retrocompatibilita':** se `STANDARD_PLANETS` continua a essere importato dall'esterno,
il nome deve restare disponibile in `astrological_subject_factory.py` come alias/import re-export.
Stesso principio per `_POINT_NUMBER_MAP` se si decide di centralizzarlo mantenendo il simbolo storico.

`config_constants.py` gia' contiene le costanti condivise della libreria — e' il posto naturale.

### 1.8 — Unificare costanti angoli in config_constants.py

**Duplicazione attuale:**

| Costante | File | Linea |
|---|---|---|
| `_ANGLES = ["Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"]` | `report.py` | 47 |
| `axial_points = {"Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"}` | `relocated_chart_factory.py` | 130 |
| `_MAIN_PLANETS = ["Sun", "Moon", ...]` | `report.py` | 45 |
| `_NODES = ["Mean_North_Lunar_Node", "True_North_Lunar_Node"]` | `report.py` | 46 |

**Azione:** Definire `AXIAL_POINTS`, `MAIN_PLANETS`, `LUNAR_NODES` in `config_constants.py`
(dove gia' esistono `DEFAULT_ACTIVE_POINTS`, `ALL_ACTIVE_POINTS` ecc.) e importarli dove servono.

---

## TIER 2 — Ottimizzazioni moderate (test mirati necessari)

Queste modifiche sono logicamente corrette ma toccano aree con piu' surface area di test.

### 2.1 — Ottimizzare `scour` tramite fork compatibile, mantenendo output stabile

**File:** `kerykeion/charts/chart_drawer.py`, linee 3912-3927

**Problema:** `scourString()` impiega **~78ms** per SVG — il 92% del tempo di rendering.
Il costo e' reale, ma il piano **non** puo' rimuovere `scour` o cambiare il path di minify di default,
perche' il vincolo e' mantenere output e retrocompatibilita'.

**Codice attuale:**
```python
if minify:
    try:
        template = scourString(template)     # ~78ms!
    except Exception as exc:
        logging.warning(...)
    template = template.replace('"', "'")    # ~1ms
    template = re.sub(r"\s+", " ", template) # ~1ms
    template = re.sub(r">\s+<", "><", template)
    template = template.strip()
```

**Direzione corretta:**

**A) Fork trasparente e byte-stable (target principale):**
- mantenere la stessa API (`scourString`);
- sostituire l'implementazione solo se il fork produce output identico sulle fixture rilevanti;
- non cambiare firma pubblica, flag esistenti o ordine delle trasformazioni.

**B) Fast path sperimentale solo opt-in (facoltativo):**
- ammesso solo dietro nuovo flag interno/non pubblico oppure tooling di benchmark;
- mai come default finche' non e' dimostrata equivalenza piena.

**Rischio:** il minify attuale e' coperto da golden SVG minificati. Anche differenze puramente
strutturali o di ordinamento attributi sono regressioni finche' il principio guida resta
"output identico".

**Nota:** nessuna rimozione di `scour` da `pyproject.toml` in questo piano.

### 2.2 — `report.py` sorting O(n*m) con dict lookup

**File:** `kerykeion/report.py`, linee 521-524

**Problema:** Per ogni nome nella lista di ordinamento, scansiona l'intera lista di punti:
```python
for name in _ANGLES + _MAIN_PLANETS + _NODES:
    sorted_points.extend([p for p in points if p.name == name])
```

Con 18 punti * 18 nomi = 324 confronti. Non e' un bottleneck critico, ma e' un pattern
migliorabile.

**Codice target:**
```python
points_by_name = {p.name: p for p in points}
for name in _ANGLES + _MAIN_PLANETS + _NODES:
    if name in points_by_name:
        sorted_points.append(points_by_name.pop(name))
sorted_points.extend(points_by_name.values())  # remaining points
```

### 2.3 — `dict(aspect)` da Pydantic v1 pattern in report.py

**File:** `kerykeion/report.py`, linee 155, 163

**Problema:** Usa `dict(aspect)` (pattern Pydantic v1/v2 compat) su modelli Pydantic v2.
Non e' un problema di correttezza oggi, ma `.model_dump()` e' il pattern esplicito e leggibile.

**Priorita':** cleanup, non performance-critical.

**Codice attuale:**
```python
self._active_aspects = [dict(aspect) for aspect in self.model.active_aspects]
```

**Codice target:**
```python
self._active_aspects = [aspect.model_dump() for aspect in self.model.active_aspects]
```

### 2.4 — Aspect factory: `range(len())` e cache accessi dict nel loop

**File:** `kerykeion/aspects/aspects_factory.py`, linee 327-348

**Problema:** Il loop usa `range(len())` con accesso per indice ripetuto. Migliora soprattutto la leggibilita'.

**Nota:** evitare di sostituire tutto con slicing (`active_points_list[first_idx + 1:]`) se l'obiettivo e'
la micro-performance, perche' lo slicing crea una lista temporanea.

**Codice attuale:**
```python
for first in range(len(active_points_list)):
    for second in range(first + 1, len(active_points_list)):
        first_name = active_points_list[first]["name"]
        second_name = active_points_list[second]["name"]
        ...
        first_speed = active_points_list[first].get("speed") or 0.0
```

**Codice target:**
```python
for first_idx, first_point in enumerate(active_points_list):
    for second_point in active_points_list[first_idx + 1:]:
        first_name = first_point["name"]
        second_name = second_point["name"]
        ...
        first_speed = first_point.get("speed") or 0.0
```

### 2.5 — `_merge_active_aspects_with_settings` O(n^2) con dict join

**File:** `kerykeion/aspects/aspects_factory.py`, linee 509-516

**Problema:** Nested loop con `dict()` copy ad ogni match:
```python
for aspect_setting in aspects_settings:
    for active_aspect in active_aspects:
        if aspect_setting["name"] == active_aspect["name"]:
            aspect_setting_copy = dict(aspect_setting)
            aspect_setting_copy["orb"] = active_aspect["orb"]
            filtered_settings.append(aspect_setting_copy)
            break
```

Con 11 settings * 6 active = 66 confronti + 6 `dict()` copies.

**Codice target:**
```python
active_orbs = {a["name"]: a["orb"] for a in active_aspects}
filtered_settings = []
for setting in aspects_settings:
    if setting["name"] in active_orbs:
        merged = dict(setting)
        merged["orb"] = active_orbs[setting["name"]]
        filtered_settings.append(merged)
```

Da O(n*m) a O(n+m).

### 2.6 — Rimuovere `list()` e `.copy()` non necessari

| File | Linea | Pattern | Azione |
|---|---|---|---|
| `aspects_factory.py` | 545 | `return list(all_aspects)` dove `all_aspects` e' gia' una lista | `return all_aspects` |
| `utilities.py` | 577 | `return degrees.copy()` per lista con <=1 elemento | `return degrees` (o `return list(degrees)` se serve copia) |
| `astrological_subject_factory.py` | 2310 | `.copy()` prima di `.extend()` su lista temporanea | Usare direttamente `calculated_planets + calculated_axial_cusps` |

**Correzione del piano:** ogni rimozione di copy/list va fatta solo dove il non-aliasing non e' parte
implicita del comportamento. Il ROI e' basso; non vale introdurre side effect sottili per guadagni minimi.

### 2.7 — Chart drawer: evitare dict copy inutile all'init

**File:** `kerykeion/charts/chart_drawer.py`, linee 1996-1997

```python
self.planets_settings = [dict(body) for body in celestial_points_settings]
self.aspects_settings = [dict(aspect) for aspect in aspects_settings]
```

**Verifica necessaria:** i due casi vanno separati.

- `self.planets_settings`: **la copia oggi serve**, perche' il codice marca i body attivi mutando
  `body["is_active"] = True`. Assegnare direttamente la lista originale introdurrebbe leakage sul config condiviso.
- `self.aspects_settings`: puo' essere candidata a rimozione della copia **solo se** si conferma che non viene mai mutata.

### 2.8 — Transit time range: list filtering con dict lookup

**File:** `kerykeion/transits_time_range_factory.py`, linea 423

```python
aspect_settings = [s for s in DEFAULT_CHART_ASPECTS_SETTINGS if s["name"] == aspect_name]
```

Questo e' dentro un loop di ricerca. Costruire un dict `{name: settings}` una sola volta
prima del loop.

---

## TIER 3 — Ottimizzazioni avanzate (rischio piu' alto)

Queste modifiche hanno impatto significativo ma richiedono analisi e test approfonditi.

### 3.1 — `pytz` -> `zoneinfo` (stdlib Python 3.9+)

**File:** `kerykeion/astrological_subject_factory.py` e moduli che usano `pytz`

**Problema:** `pytz.timezone()` ha overhead di lazy initialization ed e' ~3x piu' lento di
`zoneinfo.ZoneInfo()` (stdlib dal Python 3.9, kerykeion richiede >=3.12).

**Rischio ALTO:**
- `pytz` ha semantica diversa da `zoneinfo` per le transizioni DST storiche
- `pytz` richiede `.localize()` per "attaccare" la timezone, `zoneinfo` usa `datetime.replace(tzinfo=...)`
- Date storiche (pre-1970) potrebbero comportarsi diversamente
- La libreria di astrologia calcola spesso date storiche molto antiche

**Prerequisiti:**
1. Test con date storiche (e.g. 1800, 1900, 1950) in varie timezone
2. Confronto preciso dei risultati Julian Day con pytz vs zoneinfo
3. Verifica che `pytz` non sia usato anche da dipendenze (requests-cache lo usa?)

**Correzione del piano:** includere anche i codepath `moon_phase_details/*`, non solo
`astrological_subject_factory.py`, perche' anche li' la semantica `pytz.localize()` e' usata in modo esplicito.

**Se implementato:** Rimuovere `pytz` e `types-pytz` da `pyproject.toml`.

### 3.2 — `model["field"]` da `model.field` nei path caldi

**File principali:**
- `kerykeion/aspects/aspects_utils.py:222` — `subject[planet["name"].lower()]`
- `kerykeion/charts/charts_utils.py` — `planet_a["name"]`, `aspect["p1"]` ecc.

**Problema:** `model["field"]` su Pydantic model passa per `__getitem__` -> `getattr()`, ~1.5x
piu' lento dell'accesso diretto `.field`.

**Rischio ALTO:**
- In `charts_utils.py`, le funzioni ricevono parametri tipizzati come `list[dict]` — sono
  effettivamente dict, non Pydantic models. Cambiare `dict["key"]` in `dict.key` causerebbe
  `AttributeError`.
- In `aspects_utils.py:222`, `subject` e' tipizzato come `AstrologicalSubjectModel` (Pydantic)
  ma `planet` e' un dict da `celestial_points_settings`.
- Bisognerebbe fare un audit **completo** di ogni call site per determinare se l'oggetto e'
  un Pydantic model o un plain dict prima di cambiare la sintassi.

**Se implementato:** Solo su oggetti **certamente** Pydantic (non dict), e solo nei path caldi.

### 3.3 — `__slots__` su dataclass interne

**File:** `kerykeion/astrological_subject_factory.py`
- `ChartConfiguration` dataclass (linea 326)
- `LocationData` dataclass (linea 442)

**Problema:** Senza `__slots__`, ogni istanza dataclass ha un `__dict__` che occupa ~200 bytes extra.
Con `__slots__`, l'accesso agli attributi e' anche leggermente piu' veloce.

**Rischio:** Se qualche codice accede a `instance.__dict__` o usa `setattr()` dinamico,
l'aggiunta di `__slots__` lo romperebbe.

**Azione:** Aggiungere `@dataclass(slots=True)` (Python 3.10+, kerykeion richiede >=3.12).

**Priorita':** molto bassa. Il beneficio assoluto e' piccolo rispetto ai bottleneck confermati della libreria,
quindi non va anticipato rispetto ai refactor con ROI chiaro.

---

## TIER 4 — Architetturali (fuori scope per ora)

Menzione per completezza, da considerare in future versioni major.

### 4.1 — Lazy import numpy/skyfield

L'import iniziale di kerykeion impiega ~2s, di cui ~1.3s per la catena numpy -> skyfield.
Questa catena viene caricata da `libephemeris` anche se Skyfield viene usato solo come fallback
per `gauquelin_sector`.

**Possibile azione:** Lazy import in `libephemeris` stesso (upstream).

### 4.2 — Batch `calc_ut` per piu' pianeti

Attualmente si chiama `swe.calc_ut()` una volta per pianeta. Una API batch che calcoli
tutti i pianeti in una sola chiamata C eliminerebbe l'overhead Python per-call.

**Richiede:** Modifica a `libephemeris` (upstream).

### 4.3 — Caching `ephemeris_context()` tra subject multipli

`ephemeris_context()` fa setup/teardown del backend SwissEph per ogni subject. Se si calcolano
molti subject con la stessa configurazione (stesso `zodiac_type`, `perspective_type`, ecc.),
il context potrebbe essere condiviso.

**Richiede:** Rethink del lifecycle del backend.

---

## Impatto stimato

Le stime precedenti erano troppo ottimistiche per un piano a **retrocompatibilita' totale**.
La lettura corretta dei guadagni e' questa:

- **Cleanup puro (TIER 0):** impatto trascurabile sulle prestazioni, utile per ridurre rumore e maintenance cost.
- **SVG non minificato:** il guadagno piu' affidabile viene da `draw_aspect_grid` (`1.4`) e dalla conversione
  mirata dei loop string-building (`1.5`). Qui il miglioramento e' reale e difendibile.
- **Subject creation:** i guadagni restano modesti finche' `1.2` non passa una validazione completa.
  Prima di allora, aspettarsi miglioramenti incrementali, non un salto del 30%.
- **SVG minificato:** il tempo resta dominato da `scour`. Il vero guadagno dipende dal fork compatibile,
  non dalla sostituzione con regex-only, che e' fuori piano.

In sintesi, i win a maggiore confidenza sono:
1. `1.4` pre-index di `draw_aspect_grid`
2. `1.5` applicato solo ai loop SVG piu' caldi
3. `1.1` cache di introspezione `get_args()`

Il win potenzialmente piu' grande sul core numerico resta `1.2`, ma **solo dopo** validazione estesa.

## Matrice di validazione

Per garantire piena retrocompatibilita', la validazione va espansa per area. Il principio operativo e':
**piu' il refactor tocca numerica, rendering o compatibilita' cross-backend, piu' il gate deve salire**.

### Gate 0 — Obbligatorio per qualsiasi modifica

- `poe lint`
- `poe analyze`
- `poe typecheck`
- `poe test:core`

**Scopo:** bloccare regressioni immediate di sintassi, typing e comportamento core offline.

### Gate 1 — Refactor del core numerico (subject, aspetti, houses, declinazioni, transits)

Obbligatorio per modifiche in:
- `astrological_subject_factory.py`
- `utilities.py` se tocca logica houses/angles/time
- `aspects/*`
- `transits_time_range_factory.py`
- moduli che leggono o producono `declination`, `julian_day`, `houses`, `active_points`

Eseguire:
- `poe test:core`
- `poe test:base`
- `pytest tests/core/test_oob_and_declination_aspects.py -q`
- `pytest tests/core/test_transits.py -q`
- `pytest tests/core/test_subject_factory_parametrized.py -q`

Quando il refactor tocca coordinate, prospettive o backend:
- `pytest tests/core/test_planetocentric.py -q`
- `pytest tests/core/test_houses_positions.py -q`
- `pytest tests/core/test_planetary_positions.py -q`
- `poe test:compare` **se** entrambi i backend sono disponibili

**Scopo:** non limitarsi ai casi canonici di `test:core`, ma coprire anche house systems, sidereal modes,
perspectives, range temporali e differenze tra libephemeris e swisseph.

### Gate 2 — Rendering SVG / Chart layout / minify

Obbligatorio per modifiche in:
- `charts/charts_utils.py`
- `charts/chart_drawer.py`
- `charts/draw_modern.py`
- `charts/draw_planets.py`
- `utilities.py` se tocca SVG processing o CSS inlining

Eseguire:
- `poe test:core`
- `pytest tests/core/test_chart_drawer.py -q`
- `pytest tests/core/test_chart_parametrized.py -q`
- `pytest tests/core/test_utilities.py -q`
- `poe benchmark`

Se la modifica tocca minify, `scour`, template SVG o post-processing:
- confrontare anche gli SVG minificati golden gia' esistenti;
- usare gli script `regenerate:*` **solo per ispezione del delta**, non come criterio automatico di accettazione;
- verificare sia il path classic sia il path modern.

**Scopo:** prevenire regressioni strutturali, differenze di layout, drift nei chart parametrizzati e
peggioramenti prestazionali nei path caldi del rendering.

### Gate 3 — Report, snapshot testuali e documentazione eseguibile

Obbligatorio per modifiche in:
- `report.py`
- serializer/context/report snapshot
- formattazione testuale di date, coordinate, aspetti, case, output fixture

Eseguire:
- `poe test:core`
- `pytest tests/core/test_report.py -q`
- `poe docs:snippets`
- `poe docs:check`

Se necessario per audit del delta:
- `poe regenerate:reports`

**Scopo:** proteggere output user-facing non SVG, snapshot ASCII e snippet documentati.

### Gate 4 — Compatibilita' timezone / date storiche / BCE

Obbligatorio per modifiche in:
- conversioni orarie
- timezone handling
- DST ambiguity
- BCE / Julian Day conversion
- `pytz` / `zoneinfo`

Eseguire:
- `poe test:core`
- `pytest tests/core/test_astrological_subject.py -q`
- `pytest tests/core/test_bce_dates.py -q`
- `pytest tests/core/test_moon_phase_historical_verification.py -q`
- `poe test:medium`

**Scopo:** intercettare regressioni che spesso non emergono nei chart moderni standard ma rompono date
storiche, DST edge cases o calcoli astronomici di base.

### Gate RC — Release candidate per refactor ad alto impatto

Obbligatorio prima del merge dei refactor che toccano piu' moduli core oppure cambiano un hot path globale.

Eseguire:
- `poe quality`
- `poe test:medium`
- `pytest tests/core/test_chart_drawer.py -q`
- `pytest tests/core/test_chart_parametrized.py -q`
- `pytest tests/core/test_subject_factory_parametrized.py -q`
- `pytest tests/core/test_report.py -q`
- `poe benchmark`
- `poe test:compare` se l'ambiente ha entrambi i backend installati

Per cambi SVG/minify/report:
- confronto manuale dei delta generati da `regenerate:svg`, `regenerate:reports`, `regenerate:configurations`
- nessuna accettazione automatica di baseline nuove senza spiegazione del perche' il delta sia compatibile

**Scopo:** trattare il refactor come un piccolo release train, non come un semplice cleanup locale.

---

## Strategia di esecuzione

### Fase 1: TIER 0 (cleanup)
Applicare tutte le modifiche TIER 0 in un singolo commit.

**Gate richiesto:** Gate 0.

Nessun rischio atteso: solo rimozione di codice morto e micro-cleanup locali.

### Fase 2: TIER 1 (ottimizzazioni sicure)
Applicare una modifica alla volta, con commit separati e `poe test:core` dopo ciascuna:
1. Cache `get_args()` (1.1)
2. Pre-index `draw_aspect_grid` (1.4) — il piu' impattante per SVG
3. String concatenation -> list+join (1.5) — **solo nei loop caldi confermati**
4. Riuso Sun in `_compute_is_diurnal` (1.6) — solo nel caso Tropical + Apparent Geocentric
5. Unificare costanti (1.7, 1.8) — piu' refactoring che performance, con alias compatibili

**Gate consigliato per ogni step SVG/chart:**
- Gate 0 sempre
- Gate 2 per ogni modifica che tocca rendering, template o SVG utility

### Fase 3: TIER 2 (moderate)
Ogni modifica richiede test mirato:
- `1.2` (declinazione analitica):
  - Gate 0
  - Gate 1 completo
  - Gate RC prima del merge
- `2.1` (fork compatibile di `scour`):
  - Gate 0
  - Gate 2 completo
  - Gate RC se cambia il default path del minify
- `2.2-2.8`:
  - Gate 0
  - eventuale Gate 1 / Gate 2 / Gate 3 a seconda del modulo toccato

### Fase 4: TIER 3 (avanzate)
Solo dopo aver completato e validato TIER 0-2:
- 3.1 (pytz): Richiede test matrix con date storiche
- 3.2 (dict vs dot access): Richiede audit completo dei tipi
- 3.3 (slots): Verifica assenza di `__dict__` access

**Gate richiesto:** sempre Gate RC; per `3.1` anche Gate 4 completo.

### Regola finale di accettazione

Una modifica entra solo se soddisfa **tutti** i criteri seguenti:
- nessun breaking change osservabile;
- nessun delta inatteso nei golden file rilevanti;
- benchmark non peggiori sul path toccato;
- codice finale piu' semplice o almeno non piu' fragile di prima.
