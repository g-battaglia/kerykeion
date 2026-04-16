# Piano di Refactoring Kerykeion - Analisi Completa (v2)

## Contesto

Kerykeion e' una libreria Python matura (v5.12.7, ~26.000 righe, 45 file Python) per calcoli astrologici. L'architettura factory-based e' ben strutturata, ma l'evoluzione incrementale ha introdotto: bug silenti, codice morto, duplicazioni significative (~800 righe duplicate), inconsistenze stilistiche e typo. L'analisi ha coperto OGNI riga di OGNI file del progetto.

**Vincoli assoluti:** ZERO breaking changes. ZERO modifiche all'API pubblica (`__all__` in `__init__.py` immutato). ZERO modifiche alle firme dei metodi pubblici.

---

## FASE 1: Bug Fixes (CRITICA)

### 1.1 - `composite_subject_factory.py:234`: `__eq__` referenzia attributo inesistente
**Problema:** `self.name == other.chart_name` ma `CompositeSubjectFactory` non ha attributo `chart_name`, solo `name` (riga 163). Causa `AttributeError` se `__eq__` viene invocato.
**Fix:** `other.chart_name` -> `other.name`

### 1.2 - `planetary_return_factory.py:335,354,362,378`: Falsy check su coordinate geografiche
**Problema:** `not lat` e `not lng` restituiscono `True` per `lat=0.0` o `lng=0.0`, che sono coordinate valide (intersezione equatore/meridiano di Greenwich). Codice affetto:
- Riga 335: `if geonames_username is None and online and (not lat or not lng or not tz_str):`
- Riga 354: `if not lat and not online:`
- Riga 362: `if not lng and not online:`
- Riga 378: `if (self.online) and (not self.tz_str) and (not self.lat) and (not self.lng):`
**Fix:** Sostituire `not lat` con `lat is None`, `not lng` con `lng is None` in tutte e 4 le righe. Per riga 378, usare `self.lat is None` e `self.lng is None`.

### 1.3 - `ephemeris_data_factory.py:329`: Parametro `as_model` accettato ma mai usato
**Problema:** `get_ephemeris_data_as_astrological_subjects(self, as_model: bool = False)` accetta `as_model` ma non lo usa mai nel corpo del metodo (righe 409-434). Il docstring dice che controlla se restituire model o raw subjects, ma il codice restituisce sempre la stessa cosa.
**Fix:** Rimuovere il parametro `as_model` dalla firma. NON e' API pubblica (metodo aggiunto di recente, non in `__all__`).

### 1.4 - `relationship_score_factory.py:315-343`: `get_relationship_score()` non e' rientrante
**Problema:** Il metodo muta `self.score_value`, `self.relationship_score_aspects`, `self.score_breakdown` accumulandoli. Chiamarlo due volte sulla stessa istanza raddoppia il punteggio.
**Fix:** Resettare lo stato all'inizio di `get_relationship_score()`: `self.score_value = 0`, `self.relationship_score_aspects = []`, `self.score_breakdown = []`.

### 1.5 - `charts_utils.py:968,1598`: CSS `stroke-width` dichiarato due volte
**Problema:** `style = f"stroke:{stroke_color}; stroke-width: 1px; stroke-width: 0.5px; fill:none"` - il primo `stroke-width: 1px` e' dead CSS, sovrascritto immediatamente.
**Fix:** Rimuovere `stroke-width: 1px;` lasciando solo `stroke-width: 0.5px`.

---

## FASE 2: Eliminazione Codice Morto (ALTA)

### 2.1 - `aspects_utils.py:186-197`: Funzione `planet_id_decoder` mai chiamata
**Problema:** Definita ma mai chiamata in nessun file del progetto. La factory degli aspetti usa un lookup dict inline.
**Fix:** Rimuovere la funzione. Non e' esportata in nessun `__init__.py`.

### 2.2 - `aspects_utils.py:34`: Variabile `aid` non usata
**Problema:** `for aid, aspect in enumerate(aspects_settings)` - `aid` mai usato.
**Fix:** `for aspect in aspects_settings:`

### 2.3 - `composite_subject_factory.py:237-248`: `__ne__` ridondante
**Problema:** Python genera automaticamente `__ne__` da `__eq__`.
**Fix:** Rimuovere il metodo `__ne__` e il suo docstring.

### 2.4 - `report.py:834-846`: `_format_date` deprecata e mai chiamata
**Problema:** Metodo statico annotato come deprecated nel docstring ("Use _format_date_iso()"), mai chiamato.
**Fix:** Rimuovere il metodo.

### 2.5 - `house_comparison_utils.py:100-101`: Check `None` morto
**Problema:** `if point is None: continue` a riga 101, ma `celestial_points` e' costruita filtrando gia' i None a riga 64 (`if point_obj is not None: celestial_points.append(point_obj)`). Il check e' irraggiungibile.
**Fix:** Rimuovere le righe 100-101.

### 2.6 - `planetary_return_factory.py:547-550`: `hasattr` superflui
**Problema:** `if hasattr(self, "custom_ayanamsa_t0") and self.custom_ayanamsa_t0 is not None:` - `custom_ayanamsa_t0` e' SEMPRE settato in `__init__` a riga 324, quindi `hasattr` e' sempre True.
**Fix:** Semplificare in `if self.custom_ayanamsa_t0 is not None:` (e idem per `custom_ayanamsa_ayan_t0`).

---

## FASE 3: Eliminazione Codice Duplicato (ALTA)

### 3.1 - `composite_subject_factory.py:157+195-198`: Doppia computazione active_points
**Problema:** `active_points` calcolato a riga 157 con `find_common_active_points()`, poi SOVRASCRITTO con loop manuale identico alle righe 195-198.
**Fix:** Rimuovere le righe 195-198. Il risultato di `find_common_active_points()` e' identico.

### 3.2 - `composite_subject_factory.py:330-333`: Ricalcolo common_planets
**Problema:** `_calculate_midpoint_composite_points_and_houses` ricalcola manualmente la lista dei pianeti comuni, identica a `self.active_points`.
**Fix:** Usare `self.active_points` direttamente.

### 3.3 - `astrological_subject_factory.py:1281+1726`: `should_calculate` definita due volte
**Problema:** Stessa funzione locale definita in `_calculate_houses` e `_calculate_planets`.
**Fix:** Estrarre come `@staticmethod` privato: `_should_calculate(point_name, active_points)`.

### 3.4 - `utilities.py:49-71` vs `astrological_subject_factory.py:84-106`: Mappe punto-ID sovrapposte
**Problema:** `_POINT_NUMBER_MAP` e `STANDARD_PLANETS` mappano entrambi nomi a ID Swiss Ephemeris con sovrapposizione.
**Fix:** Far derivare `_POINT_NUMBER_MAP` da `STANDARD_PLANETS` importandolo e aggiungendo solo le entry mancanti (South Nodes e Axial Cusps).

### 3.5 - `ephemeris_data_factory.py:294-313 vs 411-430`: Blocco `from_birth_data()` identico
**Problema:** Le stesse 18 righe di chiamata a `AstrologicalSubjectFactory.from_birth_data()` con 15 keyword arguments identici sono copiate in `get_ephemeris_data` e `get_ephemeris_data_as_astrological_subjects`.
**Fix:** Estrarre metodo privato `_create_subject_for_date(self, date: datetime) -> AstrologicalSubjectModel`.

### 3.6 - `settings/translations.py:52-61` vs `settings/kerykeion_settings.py:41-48`: `_deep_merge` duplicata
**Problema:** Stessa funzione ricorsiva in due file dello stesso package. Differiscono solo per `cast()` calls.
**Fix:** Tenere una sola copia. Spostare in `translations.py` (che non usa cast) e importare in `kerykeion_settings.py`.

### 3.7 - `house_comparison_utils.py:68-97`: Costruzione manuale lista cuspidi x2
**Problema:** Due liste da 12 elementi costruite manualmente accedendo a `.first_house.abs_pos` ... `.twelfth_house.abs_pos` per `house_subject` e `point_subject`. La funzione `get_houses_list()` (gia' importata a riga 16) fa esattamente questo.
**Fix:** Sostituire con `[h.abs_pos for h in get_houses_list(house_subject)]` e idem per `point_subject`. Elimina 24 righe.

### 3.8 - `draw_planets.py:498-683`: Funzioni di adjustment indicator duplicate
**Problema:**
- `_calculate_indicator_adjustments` (498-556) e `_calculate_secondary_indicator_adjustments` (624-683): corpo identico, differiscono solo nell'ultima riga (strategia di adjustment).
- `_apply_group_adjustments` (559-588) e `_apply_secondary_group_adjustments` (590-621): stessa struttura con valori numerici diversi.
**Fix:** Unificare `_calculate_indicator_adjustments` accettando la funzione di adjustment come parametro. Unificare `_apply_group_adjustments` accettando i fattori di spaziatura come parametri.

### 3.9 - `charts_utils.py:1318-1391`: `draw_main_house_grid`/`draw_secondary_house_grid` identiche
**Problema:** ~70 righe di codice identico. Differiscono solo per nomi parametro e default `x_position` (750 vs 1015).
**Fix:** Creare helper privato `_draw_house_grid_impl(...)`. Mantenere le due funzioni pubbliche come thin wrapper per API compatibility.

### 3.10 - `charts_utils.py:1400-1560`: `draw_main_planet_grid`/`draw_secondary_planet_grid` ~85% identiche
**Problema:** ~100 righe di codice near-identico. Differiscono per title rendering e default x_position.
**Fix:** Creare helper privato `_draw_planet_grid_impl(...)`. Mantenere wrapper pubblici.

### 3.11 - `charts_utils.py:576-617`: Funzioni di conversione coordinate duplicate
**Problema:** `convert_latitude_coordinate_to_string` e `convert_longitude_coordinate_to_string` hanno logica identica. Unica differenza: `north_label`/`south_label` vs `east_label`/`west_label`.
**Fix:** Creare helper privato `_convert_coordinate_to_string(coord, positive_label, negative_label)`. Le due funzioni pubbliche diventano one-liner wrapper.

### 3.12 - `chart_drawer.py:2188-2311+2791-2984`: Duplicazione calcolo larghezza
**Problema:** `_estimate_left_content_right_edge` e `_estimate_required_width_full` contengono ~200 righe di codice duplicato per calcoli width specifici per chart_type (Synastry, Transit, DualReturnChart).
**Fix:** Estrarre helper condiviso `_calculate_chart_type_width_components(...)`.

### 3.13 - `draw_modern.py:297-310+520`: Lista segni zodiacali duplicata
**Problema:** `_ZODIAC_SIGN_IDS` (riga 297) e `zodiac_abbrevs` (riga 520) sono la stessa lista.
**Fix:** Rimuovere `zodiac_abbrevs` a riga 520, usare `_ZODIAC_SIGN_IDS`.

### 3.14 - `context_serializer.py:518-520+581-583`: Serializzazione active config duplicata
**Problema:** Pattern identico di serializzazione `active_points`/`active_aspects` in `single_chart_data_to_context` e `dual_chart_data_to_context`.
**Fix:** Estrarre helper `_serialize_active_config(chart_data, lines)`.

---

## FASE 4: Semplificazione Logica Ridondante (MEDIA)

### 4.1 - `composite_subject_factory.py:174-177`: If/else inutile per sidereal_mode
**Problema:** `if x is not None: self.y = x; else: self.y = None` equivale a `self.y = x`.
**Fix:** `self.sidereal_mode = first_subject.sidereal_mode`

### 4.2 - `composite_subject_factory.py:203-219`: `__repr__` identico a `__str__`
**Fix:** `def __repr__(self): return self.__str__()`

### 4.3 - `utilities.py:273`: Lambda inutile
**Problema:** `normalize = lambda value: value % 360` usata 3 volte.
**Fix:** Inline le 3 chiamate direttamente con `value % 360`.

### 4.4 - `utilities.py:176`: `.format()` isolato
**Problema:** Unico uso di `.format()` in tutto il progetto. Tutto il resto usa f-string.
**Fix:** Convertire in f-string.

### 4.5 - `charts_utils.py:553,562,863,908`: Catene `or` per tipo chart
**Problema:** `if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "DualReturnChart"` ripetuto 4 volte.
**Fix:** `if chart_type in ("Transit", "Synastry", "DualReturnChart"):`

### 4.6 - `draw_planets.py:443`: Divisione per -1
**Problema:** `(int(seventh_house_degree) / -1) + int(point_degree + adjustment)` - la divisione per -1 e' un modo oscuro di negare.
**Fix:** `-int(seventh_house_degree) + int(point_degree + adjustment)`

### 4.7 - `draw_planets.py:480-490`: Tre branch che ritornano tutti 10
**Problema:** Per `external` view, le tre branches (righe 481, 483, 485) restituiscono tutte `10`.
**Fix:** Semplificare in `return 10` per il caso external.

### 4.8 - `kerykeion_settings.py:15-18`: Doppio Optional
**Problema:** `SettingsSource = Optional[Mapping[str, Any]]` e poi `load_settings_mapping(settings_source: Optional[SettingsSource] = None)` crea `Optional[Optional[...]]`.
**Fix:** Cambiare firma in `def load_settings_mapping(settings_source: SettingsSource = None)`.

### 4.9 - `charts_utils.py:568`: Concatenazione no-op
**Problema:** `return slice + "" + sign` - il `+ ""` non fa nulla.
**Fix:** `return slice + sign`

### 4.10 - `draw_modern.py:177-206`: Due dict identiche con tutti valori 0.9
**Problema:** `ZODIAC_OUTER_SCALE_MAP` e `ZODIAC_INNER_SCALE_MAP` sono dizionari da 12 entry con TUTTI valori `0.9`. Sono identici tra loro.
**Fix:** Usare una singola costante `_ZODIAC_DEFAULT_SCALE = 0.9` e `.get(sign, 0.9)` dove servono.

### 4.11 - `moon_phase_details/factory.py:88-90,223-225,288-289`: `getattr()` su modelli tipizzati
**Problema:** `getattr(subject, "lat", None)` su `AstrologicalSubjectModel` che ha `lat` come campo noto.
**Fix:** Accesso diretto: `subject.lat`.

---

## FASE 5: Typo nel Codice (MEDIA)

### 5.1 - `chart_drawer.py:1695`: `VIWBOX` -> `VIEWBOX`
**Problema:** `_TRANSIT_CHART_WITH_TABLE_VIWBOX` - typo nel nome costante.
**Fix:** Rinominare in `_TRANSIT_CHART_WITH_TABLE_VIEWBOX`. Aggiornare tutti i riferimenti interni (nessun riferimento esterno, e' privata).

### 5.2 - `chart_drawer.py:3776-3778`: `sings`/`sing` -> `signs`/`sign`
**Problema:** `sings = get_args(Sign)` e `for i, sing in enumerate(sings)` - variabili con nome sbagliato.
**Fix:** Rinominare in `signs` e `sign`.

### 5.3 - `charts_utils.py:1110,1124`: `kr:sing` -> `kr:sign`
**Problema:** Attributo SVG custom `kr:sing` dovrebbe essere `kr:sign` per coerenza con `draw_planets.py:753` e `draw_modern.py:450,943` che usano `kr:sign`.
**NOTA:** Potenziale breaking change per consumer SVG downstream che parsano l'attributo. Valutare con cautela.
**Fix:** Cambiare `kr:sing` in `kr:sign` se non ci sono consumer noti.

### 5.4 - `charts_utils.py:593,614`: `min` shadows builtin
**Problema:** `min = int((float(coord) - deg) * 60)` sovrascrive la builtin `min()`.
**Fix:** Rinominare in `minutes`.

---

## FASE 6: Standardizzazione Type Hints (MEDIA)

### 6.1 - Uso misto di `List`/`Dict`/`Tuple` (typing) vs `list`/`dict`/`tuple` (builtin)
**Problema:** Il progetto supporta Python >= 3.9 dove le forme native sono valide. L'uso e' inconsistente:
- Usano `List[...]` (vecchio stile): `aspects_factory.py`, `transits_time_range_factory.py`, `ephemeris_data_factory.py`, `kr_models.py`, `chart_data_factory.py`, `chart_drawer.py`, `draw_planets.py`, `backword.py`, `report.py`, `config_constants.py`, `astrological_subject_factory.py`, `moon_phase_details/factory.py`, `moon_phase_details/utils.py`
- Usano `list[...]` (nuovo stile): `house_comparison_factory.py`, `house_comparison_utils.py`, `relationship_score_factory.py`, `settings_models.py`
**Fix:** Migrare a `list[X]`, `dict[X,Y]`, `tuple[X]` in tutti i file. Per `kr_models.py` (Pydantic): funziona con Pydantic v2. Per `backword.py`: mantenere `List` nelle firme pubbliche legacy. Per file con `from __future__ import annotations` (report.py, translations.py, kerykeion_settings.py): gia' sicuro.

### 6.2 - Uso misto `Union[X, None]` vs `Optional[X]`
**Problema:** ~81 occorrenze di `Union[..., None]` sparse in 10 file. Caso specifico: `kr_models.py:461` usa `Union[SiderealMode, None]` in mezzo a campi `Optional[...]`.
**Fix:** Standardizzare su `Optional[X]` dove non c'e' `from __future__ import annotations`, `X | None` dove c'e'. File principali: `planetary_return_factory.py`, `ephemeris_data_factory.py`, `draw_modern.py`, `kr_models.py`.

### 6.3 - `kr_models.py`: Tipo Union ripetuto estraibile
**Problema:** `Union["AstrologicalSubjectModel", "CompositeSubjectModel", "PlanetReturnModel"]` appare in 5+ field annotations.
**Fix:** Estrarre alias: `AnySubjectModel = Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel]`.

---

## FASE 7: Traduzioni Mancanti (MEDIA)

### 7.1 - `translation_strings.py`: 4 chiavi mancanti in RU, TR, DE, HI
**Problema:** Le chiavi `cusp_position_comparison`, `transit_cusp`, `return_cusp`, `house` sono presenti in EN, FR, PT, IT, CN, ES ma MANCANO in RU, TR, DE, HI. Il fallback a EN funziona (tramite `get_translations`), ma e' un gap di localizzazione.
**Fix:** Aggiungere le 4 chiavi tradotte nei 4 blocchi linguistici.

### 7.2 - `translation_strings.py` vs `settings_models.py`: Drift tra dict e Pydantic model
**Problema:** Chiavi come `"ExternalNatal"`, `"cusp_position_comparison"`, `"transit_cusp"`, `"return_cusp"`, `"house"` esistono nel dizionario di traduzione ma NON hanno un campo corrispondente in `KerykeionLanguageModel`.
**Nota:** Questo e' un problema di design piu' ampio. Segnalare, non fixare in questa fase (richiederebbe estensione del model Pydantic = possibile breaking change).

---

## FASE 8: Pulizia Import (BASSA)

### 8.1 - Import usati solo in `__main__` block
**Problema:** Import a livello modulo usati solo in `if __name__ == "__main__":`:
- `transits_time_range_factory.py:59,63`: `datetime`, `timedelta`, `EphemerisDataFactory`
- `house_comparison_factory.py:19`: `AstrologicalSubjectFactory`
- `relationship_score_factory.py:48`: `AstrologicalSubjectFactory`
**Fix:** Spostare dentro il blocco `__main__`.

### 8.2 - `ephemeris_data_factory.py:69`: Import inutili `Dict`, `Any`
**Problema:** `Dict` e' usato solo in un'annotazione locale che puo' diventare `dict`. `Any` e' ancora necessario.
**Fix:** Rimuovere `Dict` da import e usare `dict[str, Any]`.

---

## FASE 9: Magic Numbers (BASSA)

### 9.1 - `utilities.py:492,497`: Latitudine polare 66.0
**Fix:** `_POLAR_LATITUDE_LIMIT = 66.0` in cima al modulo.

### 9.2 - `chart_drawer.py:2543-2554`: Costanti aspect column duplicate
**Problema:** `aspects_per_column = 14`, `translate_y = 273`, `line_height = 14`, `bottom_padding = 40`, `title_clearance = 18` sono hardcoded in `_adjust_height_for_extended_aspect_columns` e ri-hardcoded in `_calculate_full_height_column_capacity` (righe 3013-3036).
**Fix:** Definire come class constants `_ASPECT_LIST_LINE_HEIGHT`, `_ASPECT_LIST_TRANSLATE_Y`, etc.

### 9.3 - `ephemeris_data_factory.py:171-173`: Max limits
**Problema:** `730`, `8760`, `525600` come default senza nome.
**Fix:** Costanti modulo: `_MAX_DAYS = 730`, `_MAX_HOURS = 8760`, `_MAX_MINUTES = 525600`.

---

## FASE 10: Micro-ottimizzazioni (BASSA)

### 10.1 - `aspects_utils.py:5,35`: TODO da ripulire
**Fix:** Rimuovere TODO a riga 5 (documentazione ora esiste). Riformulare riga 35.

### 10.2 - `backword.py:156-158`: Import interno alla classe
**Fix:** Usare `datetime.utcnow()` dall'import gia' presente in cima al file.

### 10.3 - `draw_modern.py:214-216`: `_deg_to_rad()` wrappa `math.radians()`
**Problema:** Chiamata solo 2 volte, mentre `math.radians()` e' usata direttamente altrove.
**Fix:** Rimuovere `_deg_to_rad()`, usare `math.radians()` direttamente.

### 10.4 - `relationship_score_factory.py:150,183`: f-string in `logging.debug`
**Problema:** F-string valutata anche quando debug e' disabilitato.
**Fix:** `logging.debug("...", var)` con lazy formatting.

### 10.5 - `chart_drawer.py:4152,4329,4349,4419`: `Path(__file__).parent` ripetuto
**Fix:** Costante di modulo: `_MODULE_DIR = Path(__file__).parent`.

### 10.6 - `planetary_return_factory.py:525-526,552`: Nome variabile fuorviante
**Problema:** `solar_return_date_utc` usato anche per Lunar return.
**Fix:** Rinominare in `return_date_utc` e `return_astrological_subject`.

### 10.7 - `chart_drawer.py:3161`: Lista vs tupla
**Problema:** `self.chart_type in ["Transit", "DualReturnChart"]` usa list literal.
**Fix:** Usare tupla: `self.chart_type in ("Transit", "DualReturnChart")`.

### 10.8 - `report.py:510-512+526-529`: Lista nomi celestiali hardcoded e `.replace("_", " ")` ripetuto
**Problema:** Le liste `main_planets`, `nodes`, `angles` sono ricostruite ad ogni chiamata. Il pattern `.replace("_", " ")` appare 12+ volte nel file.
**Fix:** Estrarre costanti modulo `_MAIN_PLANETS`, `_NODES`, `_ANGLES`. Creare helper `_humanize(name: str) -> str` per il replace.

---

## Nota: Opportunita' di Refactoring Piu' Ampie (FUORI SCOPE)

Queste sono state identificate ma sono troppo invasive per questa fase:

1. **`aspects_factory.py:288-491`**: `_calculate_single_chart_aspects` e `_calculate_dual_chart_aspects` condividono ~60% del corpo. Unificarli richiederebbe un refactoring architetturale significativo.

2. **`chart_drawer.py`**: God class da 4615 righe. Gia' usa Strategy Pattern - decomposizione ulteriore richiederebbe ristrutturazione dell'intera pipeline SVG.

3. **`chart_template_model.py:120-374`**: 62 campi `planets_color_N`, 12 `zodiac_color_N`, 11 `orb_color_N` dovrebbero essere `list[str]` o `dict[int, str]`. Ma sono variabili di template SVG - cambiarli romperebbe il contratto template.

4. **`context_serializer.py:641-906`**: `moon_phase_overview_to_context` e' 265 righe con 6+ livelli di indentazione. Estrarre sotto-funzioni migliorerebbe la leggibilita' ma e' un refactoring ampio.

5. **`draw_modern.py:455-511`**: Duplicazione cusp ring upper/lower half (~55 righe quasi identiche). Refactoring possibile ma tocca logica SVG delicata.

---

## File Modificati (riepilogo)

| File | Fasi | Righe stimate |
|------|------|---------------|
| `composite_subject_factory.py` | 1.1, 2.3, 3.1, 3.2, 4.1, 4.2 | -40 |
| `planetary_return_factory.py` | 1.2, 2.6, 10.6 | ~15 |
| `ephemeris_data_factory.py` | 1.3, 3.5, 8.2 | -15 |
| `relationship_score_factory.py` | 1.4, 8.1, 10.4 | ~10 |
| `charts_utils.py` | 1.5, 3.9, 3.10, 3.11, 4.5, 4.9, 5.3, 5.4 | -80 |
| `aspects_utils.py` | 2.1, 2.2, 10.1 | -15 |
| `report.py` | 2.4, 6.1, 10.8 | -15 |
| `house_comparison_utils.py` | 2.5, 3.7 | -25 |
| `astrological_subject_factory.py` | 3.3, 6.1 | -10 |
| `utilities.py` | 3.4, 4.3, 4.4, 9.1 | ~5 |
| `settings/translations.py` | 3.6 | 0 |
| `settings/kerykeion_settings.py` | 3.6, 4.8, 6.2 | -10 |
| `draw_planets.py` | 3.8, 4.6, 4.7, 6.1 | -60 |
| `chart_drawer.py` | 3.12, 5.1, 5.2, 9.2, 10.5, 10.7 | -30 |
| `draw_modern.py` | 3.13, 4.10, 10.3 | -20 |
| `context_serializer.py` | 3.14 | -5 |
| `translation_strings.py` | 7.1 | +16 |
| `transits_time_range_factory.py` | 6.1, 8.1 | ~5 |
| `house_comparison_factory.py` | 8.1 | ~2 |
| `kr_models.py` | 6.1, 6.2, 6.3 | ~10 |
| `moon_phase_details/factory.py` | 4.11, 6.1 | ~5 |
| `moon_phase_details/utils.py` | 6.1 | ~5 |
| `config_constants.py` | 6.1 | ~5 |
| `backword.py` | 10.2 | ~2 |
| `aspects_factory.py` | 6.1 | ~5 |
| `chart_data_factory.py` | 6.1 | ~5 |

**Bilancio stimato: ~-300 righe nette (rimozione duplicazioni e codice morto)**

---

## Cosa NON Toccare

- **`__init__.py`**: `__all__` con 36 export immutato
- **`backword.py`**: firme metodi pubblici legacy immutate
- **`kr_types/`**: modulo deprecato (rimozione prevista v6.0)
- **`chart_template_model.py`**: campi numerati sono contratto template SVG
- **`translation_strings.py`**: solo aggiunte (7.1), nessuna rimozione
- **`charts/draw_modern.py`**: upper/lower half cusp logic (troppo delicata)
- **Test files**: nessuna modifica ai test, devono passare tal quali

---

## Verifica

Dopo OGNI fase:
```bash
poe lint && poe test:core
```

Al termine di tutte le fasi:
```bash
poe check  # lint + analyze + typecheck + test:core
poe test:base  # validazione piu' ampia
```

Verifiche aggiuntive:
1. `diff <(git show HEAD:kerykeion/__init__.py) kerykeion/__init__.py` - confermare che `__all__` e' immutato
2. `python -c "import kerykeion; print(kerykeion.__all__)"` - confermare che l'import funziona
3. Controllare che nessun file `.py` sia stato aggiunto o rimosso (solo modifiche)
