# Audit Kerykeion: Analisi Architetturale, Ottimizzazione e Refactoring

Questo documento rappresenta un'analisi esplorativa, manuale e profonda del codice di **Kerykeion**. Lo scopo è identificare ottimizzazioni prestazionali, risolvere il debito tecnico e proporre un piano di refactoring che **NON introduca breaking changes** e **MANTENGA inalterata l'API pubblica**.

---

## 1. Architettura Generale e "God Objects"

Il progetto soffre della presenza di classi "God Object" enormi, che si occupano di troppe responsabilità contemporaneamente.

### `AstrologicalSubjectFactory` (astrological_subject_factory.py)
- **Problema**: Il file supera le 2.000 righe e la classe fungo come "God Object". Il metodo `from_birth_data` accetta oltre 25 argomenti ed esegue un calcolo monolitico di tutti gli elementi (Pianeti, Case, Nodi, Stelle fisse, Parti Arabe).
- **Codice Duplicato**: I calcoli interni per l'Ascendente, il Medio Cielo e il calcolo dei singoli pianeti condividono pattern molto simili che vengono ripetuti (es. controllo attributi retrogradi, calcoli decani/case).
- **Proposta di Refactoring (Safe)**: 
  Senza cambiare la firma di `from_birth_data`, la logica interna (`_calculate_single_planet`, `_calculate_houses`, `_calculate_arabic_part`) può essere estratta in classi Calculator indipendenti all'interno di un nuovo sottomodulo.
  La factory diventerà un semplice *Facade* che orchestra queste chiamate.

### `ChartDrawer` e SVG Rendering
- **Problema**: L'analisi suggerisce che la generazione di SVG contiene variabili inutilizzate. (`n_active = max(self._count_active_planets(), 1)` viene dichiarata a riga 2194 e non utilizzata). Inoltre `ruff` individua diverse f-string senza formattazioni reali (`draw_planets.py`).
- **Proposta di Refactoring (Safe)**: 
  Rafforzare la separazione tra *calcolo delle posizioni sul canvas* e *rendering SVG finale*. Molte logiche ripetitive possono approfittare di metodi ausiliari condivisi.

---

## 2. Ottimizzazione delle Prestazioni (Performance)

### Ripetizioni nelle Chiamate Ephemeris (SwissEphemeris)
- **Problema**: SwissEphemeris (`swe`) viene interrogato ripetutamente per lo stesso Julian Day in scenari come le "Synastry" o calcoli di transito estesi (`TransitsTimeRangeFactory`). 
- **Soluzione**: Applicare un pattern di *Memoization* (es. `functools.lru_cache`) interno, per mappare:
  `(julian_day, planet_id, iflag) -> result`. Questo farà bypassare i calcoli C per lo stesso istante di tempo.

### Gestione Caching GeoNames
- **Problema**: `FetchGeonames` viene chiamato online se non bypassato. C'è una cache (sqlite), ma le chiamate rallentano il costruttore principale inutilmente a volte.
- **Soluzione**: Eseguire la fetch in lazy-loading o async.

---

## 3. Disordine e Polizia del Codice (Linting & Typing)

### Analisi Statica (Ruff e Mypy)
L'esecuzione di Mypy e Ruff ha evidenziato piccoli ma fastidiosi debiti tecnici:
1. **Unused Imports & Variables**: 
   - `datetime.timedelta` in `moon_phase_details/factory.py:31` non è utilizzato.
   - `n_active` in `chart_drawer.py:2194` mai utilizzato.
2. **F-Strings Senza Variabili**:
   - Identificate in `draw_planets.py` (righe 881, 943, 1065). Appesantiscono la valutazione a runtime.
3. **Typing Error (Mypy)**:
   - Trovati 14 errori, specificatamente iterazioni tipate male come argument type `object` dove ci si aspetta `Literal['classic', 'modern']` e booleani in `chart_drawer.py`.
- **Soluzione**: Uniformare le definizioni TypeHint e rimuovere le string format inutili.

### `utilities.py`
- **Problema**: Il file raggruppa parser di stringhe (`normalize_zodiac_type`), parsing SVG (`inline_css_variables_in_svg`), algoritmi matematici (`circular_mean`) e wrapper temporali (`datetime_to_julian`).
- **Proposta di Refactoring (Safe)**: 
  Creare moduli specializzati (`time_utils.py`, `svg_utils.py`). In `utilities.py` riesportarli esattamente come sono oggi per mantenere compatibilità all'API senza breaking changes.

---

## 4. Pianificazione delle Estrazioni Internal

Per aderire strettamente alla regola **NO BREAKING CHANGES** e **MAI CAMBIARE L'API PUBBLICA**:

1. **Step 1: Code Formatting & Type Checks Correction**
   Patch di tutti i 14 warn Mypy e log alert di Ruff. Modifiche sicure che migliorano l'intellisense.

2. **Step 2: Estrazione Utility Invisibili**
   Suddividere `utilities.py` in singoli file tematici in una cartella interna `_utils/` e re-importarli nell'originario `utilities.py`.

3. **Step 3: Internal Calculators per AstrologicalSubjectFactory**
   Trasformare code chunk massicci di calcolo (es. nodi, aspect etc.) isolandoli in `_calculators/`. Le interfacce native restano integre, delegando logic processing solo internamente.

4. **Step 4: Astrazione dei Renderer in ReportGenerator**
   La logica `if-else` può essere ripulita tramite pattern Strategy senza alcun fastidio verso la sintassi che usa l'utente attualmente (`ReportGenerator(model).generate_report()`).
