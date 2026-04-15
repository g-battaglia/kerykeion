# GPT Audit

## Verdetto

Il progetto ha una base buona e un contratto pubblico abbastanza chiaro, ma internamente ha accumulato molta complessita tecnica. La buona notizia e che c'e molto spazio per ottimizzare, ripulire e rifattorizzare senza breaking changes, a patto di farlo per estrazione interna, deduplicazione e caratterizzazione dei comportamenti esistenti, non per riscrittura.

Questa analisi e stata costruita manualmente leggendo i moduli principali, i test che bloccano il comportamento e la documentazione che definisce il contratto pubblico.

## Ambito Letto Manualmente

Sono stati ispezionati direttamente almeno questi punti chiave:

- `pyproject.toml`, `README.md`, `MIGRATION_V4_TO_V5.md`, `TEST.md`
- `kerykeion/__init__.py`
- `kerykeion/backword.py`
- `kerykeion/astrological_subject_factory.py`
- `kerykeion/chart_data_factory.py`
- `kerykeion/composite_subject_factory.py`
- `kerykeion/planetary_return_factory.py`
- `kerykeion/ephemeris_data_factory.py`
- `kerykeion/transits_time_range_factory.py`
- `kerykeion/utilities.py`
- `kerykeion/fetch_geonames.py`
- `kerykeion/aspects/aspects_factory.py`, `kerykeion/aspects/aspects_utils.py`
- `kerykeion/relationship_score_factory.py`
- `kerykeion/house_comparison/house_comparison_utils.py`
- `kerykeion/report.py`
- `kerykeion/context_serializer.py`
- `kerykeion/schemas/kr_models.py`, `chart_template_model.py`, `settings_models.py`
- porzioni estese e critiche di `kerykeion/charts/chart_drawer.py`
- test chiave: backward compatibility, chart drawer, chart data factory, utilities, report, context serializer, geonames
- documentazione in `site/docs/*`

## Vincoli Non Negoziabili

Questi sono i vincoli che oggi il codice e i test rendono di fatto pubblici:

1. Gli export top-level in `kerykeion/__init__.py:49-136` sono API pubblica.
2. Le shim legacy in `kerykeion/backword.py` e `kerykeion/kr_types/__init__.py` sono ancora contratto supportato.
3. I nomi dei campi serializzati nei model Pydantic sono API pubblica, soprattutto in `kerykeion/schemas/kr_models.py`.
4. Il comportamento dict-like di `SubscriptableBaseModel` in `kerykeion/schemas/kr_models.py:56-77` non va rotto.
5. Le stringhe dei chart type sono vincolanti: `"Natal"`, `"Transit"`, `"Synastry"`, `"Composite"`, `"SingleReturnChart"`, `"DualReturnChart"`.
6. L'output SVG e i report testuali sono fortemente snapshot-locked dai test.
7. I fallback legacy su nomi nodali, import path e warning di deprecazione sono parte del comportamento atteso.

## Finding Principali

1. Il cuore computazionale e troppo monolitico.

   `kerykeion/astrological_subject_factory.py` concentra configurazione, geocoding, timezone handling, Swiss Ephemeris, case, pianeti, sect, ayanamsa e lunar phase in un unico flusso. I blocchi piu critici sono `:583-878`, `:1226-1370`, `:1372-1627`, `:1629-1928`.

   Questo e il principale bersaglio di refactor interno.

2. C'e duplicazione concreta nella logica di calcolo dei punti.

   `_calculate_single_planet()` e `_ensure_point_calculated()` replicano la stessa meccanica in `astrological_subject_factory.py:1372-1508`.

   Anche la declinazione dei nodi viene ricalcolata subito dopo averla gia calcolata in `:1758-1764`.

3. C'e una fragilita reale sui coordinate zero-valued.

   In piu punti `0.0` viene trattato come falsy:

   - `astrological_subject_factory.py:783-786`
   - `planetary_return_factory.py:335-339`
   - `planetary_return_factory.py:353-367`
   - `planetary_return_factory.py:377-383`

   Greenwich o coordinate sul meridiano zero meritano test di caratterizzazione prima di qualunque pulizia.

4. Il layer rendering e il punto di massimo debito tecnico.

   `kerykeion/charts/chart_drawer.py` pesa oltre 4600 righe ed e insieme orchestratore, calcolatore layout, builder template, loader file e writer.

   I duplicati piu evidenti sono:

   - `chart_drawer.py:2188-2311` e `:2791-2984` per stima larghezze/layout
   - `:4152-4156`, `:4329-4355`, `:4419-4425` per lettura template a ogni render

5. `ChartDataFactory` ha almeno un ramo stantio.

   In `kerykeion/chart_data_factory.py:134-135` esiste un controllo per `"Return"`, ma il resto del progetto usa `"SingleReturnChart"` e `"DualReturnChart"`.

   Non sembra rompere nulla oggi, ma e un chiaro odore di codice rimasto a meta.

6. `CompositeSubjectFactory` ha debito tecnico e un bug probabile.

   - `kerykeion/composite_subject_factory.py:157` e `:195-199` duplicano il calcolo dei punti comuni.
   - `:231-235` usa `other.chart_name`, ma l'attributo non esiste.
   - `:392-395` restituisce il model senza valorizzare `self.model`, nonostante l'attributo esista.

7. `RelationshipScoreFactory` non e idempotente sulla stessa istanza.

   Lo stato viene accumulato in `relationship_score_factory.py:118-123` e poi riusato in `:323-343`.

   Se `get_relationship_score()` viene invocato due volte sulla stessa istanza, il risultato puo accumularsi.

8. Ci sono parametri pubblici o semi-pubblici che oggi non fanno davvero quello che promettono.

   - `ephemeris_data_factory.py:329-347` documenta `as_model`, ma il metodo ritorna comunque `AstrologicalSubjectModel`.
   - `transits_time_range_factory.py:142` e `:181-182` memorizza `settings_file`, ma non lo usa.

9. `FetchGeonames` e migliorabile senza cambiare API.

   Manca un timeout esplicito nelle chiamate in `fetch_geonames.py:153-155` e `:202-205`.

   C'e anche l'alias typo `__get_contry_data` in `:230-231`.

10. C'e molta duplicazione del catalogo dei punti astrologici.

    Lo stesso universo di nomi vive in:

    - `schemas/kr_literals.py`
    - `schemas/kr_models.py`
    - `schemas/settings_models.py`
    - `settings/chart_defaults.py`
    - `context_serializer.py`
    - `report.py`

    Questo rende costoso aggiungere o correggere un singolo punto.

11. Il serializer XML e il report hanno liste hardcoded separate e potenzialmente divergenti.

    - `context_serializer.py:409-450` seleziona manualmente pianeti/assi/nodi.
    - `report.py:510-519` ordina i punti con un'altra logica.

    Ogni espansione futura richiede sincronizzazione manuale.

12. C'e duplicazione banale nei merge di configurazione.

    `_deep_merge` esiste sia in `settings/kerykeion_settings.py:41-48` sia in `settings/translations.py:52-61`.

13. `ChartTemplateModel` sembra piu rigido del necessario e maschera mismatch di tipo.

    In `schemas/chart_template_model.py:42-67` molte translate Y sono `int`, ma `ChartDrawer` passa float in `chart_drawer.py:3955-3963`.

    Oggi Pydantic assorbe la differenza, ma il design e fragile.

14. `find_common_active_points()` e semanticamente delicato.

    In `utilities.py:390-403` usa `sorted(set(a) & set(b))`.

    E semplice, ma perde l'ordine originale e impone un ordinamento alfabetico. I test oggi blindano quel comportamento, quindi non va cambiato senza un motivo forte.

15. La documentazione non e completamente allineata al codice.

    - `site/docs/context_serializer.md:31-39` mostra `date` e `time` separati, mentre il codice usa un solo attributo `date` con data+ora in `context_serializer.py:381-386`.
    - `site/docs/schemas.md:191-193` descrive `MoonPhaseOverviewModel.datestamp` come ISO 8601, ma il factory produce un formato RFC-like in `moon_phase_details/factory.py:502-509`.
    - `TEST.md:5` parla di 27 file di test, ma in `tests/core` oggi ce ne sono 28.

## Analisi Per Area

### 1. API pubblica e compatibilita

- L'esterno del package e buono. La pipeline `AstrologicalSubjectFactory -> ChartDataFactory -> ChartDrawer` e sensata e va preservata.
- `kerykeion/__init__.py` e chiaro e relativamente curato.
- Le shim legacy sono tante ma ben intenzionate. Il problema non e la loro esistenza: e che vanno trattate come codice di prodotto, non come transitorio trascurabile.
- `backword.py` e grosso, ma il suo vero rischio e che replica parti di orchestrazione invece di limitarsi a delegare.

### 2. Core calculations

- `AstrologicalSubjectFactory` e il vero dominio.
- Il pattern interno attuale e `dict mutabile + side effects`. Funziona, ma rende il refactor pericoloso.
- La parte migliore da estrarre senza toccare API e:
  - risoluzione location
  - conversione temporale
  - house calculation
  - single-point calculation
  - post-processing metadata
- `utilities.py` contiene pezzi solidi ma anche funzioni che sono ormai parte del contratto pubblico, quindi non sono piu semplici helper.

### 3. Rendering

- `ChartDrawer` e enorme ma non irrecuperabile.
- La vera strategia sicura qui non e cambiare template o output, ma:
  - isolare lettura template/CSS
  - isolare stima layout
  - isolare rendering pannelli dual-chart
  - ridurre duplicazione tra `Transit`, `Synastry`, `DualReturn`
- Il rischio maggiore non e la logica, ma alterare anche minimamente l'ordine o il formatting dell'SVG.

### 4. Modelli, serializer e report

- I model Pydantic sono il vero contratto dati.
- `SubscriptableBaseModel` e brutto da purista, ma oggi e importante per compatibilita.
- `context_serializer.py` e molto esplicito e quindi facile da capire, ma poco DRY.
- `report.py` ha una buona struttura generale, ma replica conoscenza del dominio gia presente altrove.

### 5. Aspects, house comparison, relationship

- `AspectsFactory` e abbastanza leggibile, ma si appoggia a helper troppo minimali e poco tipizzati.
- `aspects_utils.py` porta ancora segni di transizione (`TODO`, ritorni `dict`, accessi non tipati).
- `house_comparison_utils.py` ha duplicazioni semplici e default mutabili.
- `RelationshipScoreFactory` e un buon candidato a table-driven refactor interno, mantenendo intatti output e regole.

### 6. Ephemeris, transits, returns

- Buona separazione concettuale, ma c'e molto copy/paste.
- `EphemerisDataFactory` ha due loop quasi identici.
- `TransitsTimeRangeFactory` e lineare ma essenziale al punto da lasciare parametri inattivi.
- `PlanetaryReturnFactory` ha logica replicata rispetto al subject factory, soprattutto sul lato location/config.

### 7. Test e documentazione

- Il progetto ha una safety net forte.
- I test sono il miglior alleato per refactor non-breaking.
- Ma il loro costo e alto: gran parte del rendering e dei report e snapshot-locked.
- La docs sorgente e sdoppiata tra `site/docs/` e `docs/` generata, che aumenta il rischio di drift.

## Le Migliori Opportunita Di Refactor Senza Breaking Changes

1. Estrarre helper interni da `AstrologicalSubjectFactory` senza cambiare una singola signature pubblica.
2. Unificare in una sola funzione interna il calcolo dei punti, della declinazione e dell'assegnazione di casa.
3. Unificare la risoluzione location tra subject factory e planetary return factory.
4. Deduplicare i due loop di `EphemerisDataFactory`.
5. Rendere `RelationshipScoreFactory.get_relationship_score()` idempotente.
6. Centralizzare in un registry interno il catalogo dei punti astrologici, ma lasciando invariati nomi, export e shape dei model.
7. Caching interno dei template SVG e dei CSS.
8. Preindicizzazione degli aspetti per le griglie SVG.
9. Unificare `_deep_merge`.
10. Centralizzare iteratori e liste di punti usati da report e serializer.

## Cose Che Non Toccherei Subito

1. Le stringhe dei chart type.
2. L'ordine e il formatting dell'SVG.
3. L'ordine dei report testuali.
4. `find_common_active_points()` finche non esiste una migrazione deliberata.
5. Le shim `backword.py` e `kr_types` senza test dedicati gia verdi.
6. Le shape dei model Pydantic e i nomi dei campi serializzati.

## Piano Di Refactor Sicuro

### Fase 0: protezione prima di toccare

- Aggiungere test di caratterizzazione per:
  - coordinate `0.0`
  - doppia invocazione di `RelationshipScoreFactory.get_relationship_score()`
  - `CompositeSubjectFactory.__eq__`
  - `from_birth_data()` vs `from_iso_utc_time()`
  - esempi README ed esempi locali principali
- Congelare esplicitamente gli export top-level con test mirati.

### Fase 1: pulizia core a basso rischio

- Estrarre helper interni da `AstrologicalSubjectFactory`.
- Unificare il calcolo del singolo punto.
- Unificare la risoluzione location.
- Deduplicare `EphemerisDataFactory`.
- Rendere espliciti i parametri compatibili ma inattivi.

### Fase 2: pulizia analitica

- Rendere idempotente `RelationshipScoreFactory`.
- Passare a regole table-driven per il punteggio.
- Sostituire parsing e heuristic di case in `house_comparison_utils.py` con helper condivisi.
- Unificare le logiche punto -> attributo.

### Fase 3: rendering

- Cache template e CSS.
- Estrarre helper privati per layout width e height.
- Condividere blocchi `Transit`, `Synastry`, `DualReturn`.
- Solo dopo, valutare split piu profondi di `ChartDrawer`.

### Fase 4: docs e repo hygiene

- Allineare `site/docs/*` al comportamento reale.
- Chiarire il ruolo di `docs/` generata vs `site/docs/` sorgente.
- Aggiornare `TEST.md`.

## Priorita Pratica

Se l'obiettivo e massimizzare valore e minimizzare rischio, l'ordine consigliato e questo:

1. `AstrologicalSubjectFactory`
2. `EphemerisDataFactory` e `PlanetaryReturnFactory`
3. `RelationshipScoreFactory`
4. `context_serializer.py` e `report.py`
5. `ChartDrawer`
6. solo dopo le shim legacy

## Sintesi Finale

- Il progetto non ha bisogno di una riscrittura.
- Ha bisogno di una campagna di refactor interna, chirurgica, progressiva e test-driven.
- Le aree con il miglior rapporto beneficio/rischio sono core factory, ephemeris/returns, relationship score e duplicazioni settings/serializer/report.
- L'area piu fragile e il rendering SVG.
- Il contratto pubblico oggi e piu ampio di quanto sembri: export, model fields, compat shims, stringhe chart type, SVG/report output, dict-like access.

## Note Accessorie Di Igiene Del Repository

Durante la ricognizione sono emersi anche alcuni segnali di disordine non funzionale ma utili da ripulire in un secondo momento:

- presenza di `.DS_Store` in varie directory del repository, inclusa `site/docs/`
- documentazione generata in `docs/` e documentazione sorgente in `site/docs/`, con possibile duplicazione di manutenzione
- file di esempio locali presenti in `examples/` ma non chiaramente coperti da smoke test automatici
- untracked locale in `.opencode/`, che non ho toccato

Questi punti non richiedono cambi di API, ma aiuterebbero a ridurre rumore e deriva documentale.
