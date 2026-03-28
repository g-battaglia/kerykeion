# Kerykeion v6.0 — Advanced Features Roadmap

## Contesto

Roadmap per le feature avanzate di Kerykeion v6.0, con l'obiettivo di coprire il 100% delle capacita' Swiss Ephemeris.
Aggiornato dopo un audit completo del codebase attuale (v5.12.7 + branch v6.0).

### Stato attuale gia' implementato (v5.12/v6.0)
- Declinazione per tutti i punti celesti (via `FLG_EQUATORIAL`)
- Velocita' giornaliera per tutti i punti (incluse cuspidi)
- 23 stelle fisse con magnitudine apparente
- Mean Lilith + True Lilith (SE ID 12 e 13)
- Eclissi solari/lunari con visibilita' locale e percentuale di oscuramento (`EclipseFactory`)
- Nodi planetari, eventi eliacali, occultazioni
- 48 modi siderali + ayanamsa custom
- Prospettive: geocentrica, eliocentrica, topocentrica, planetocentrica (6 corpi)
- Settori Gauquelin per tutti i punti
- Dignita' essenziali, Nakshatra, fenomeni planetari
- Transiti con `TransitsTimeRangeFactory` e `TransitEventModel`
- Azimut/altitudine solare (per classificazione diurna/notturna)

---

## FASE 1: Quick Wins (complessita' bassa, valore alto)

### 1. Pianeti "Out of Bounds" (OOB) e Aspetti di Declinazione
**Stato:** Declinazione gia' calcolata. Manca solo il flag OOB e gli aspetti di declinazione.
- Aggiungere `is_out_of_bounds: Optional[bool]` a `KerykeionPointModel`
- Calcolare usando l'obliquita' vera dell'epoca via `swe.calc_ut(jd, swe.ECL_NUT)`
- Aggiungere `declination_aspects()` a `AspectsFactory` per paralleli/contra-paralleli
- Aggiungere `"parallel"` e `"contra_parallel"` a `AspectName`

### 2. Coordinate Baricentriche
**Stato:** `swe.FLG_BARYCTR` disponibile in pyswisseph, non ancora cablato.
- Aggiungere `"Barycentric"` a `PerspectiveType`
- Aggiungere un `elif` in `ephemeris_context()` con `iflag |= swe.FLG_BARYCTR`

### 3. Parametri di Nutazione/Obliquita'
**Stato:** `swe.calc_ut(jd, swe.ECL_NUT)` gia' chiamato in `relocated_chart_factory.py`.
- Creare `NutationObliquityModel` con obliquita' vera/media, nutazione in longitudine/obliquita'
- Esporre via `calculate_nutation: bool = False` su `ChartConfiguration`

---

## FASE 2: Feature Moderate (1-2 settimane)

### 4. Stelle Fisse Dinamiche con Auto-Discovery
**Stato:** 23 stelle hardcoded. `sefstars.txt` bundled con ~1000 stelle.
- **Breaking change v6:** Sostituire le 23 stelle hardcoded con parametro `active_fixed_stars: List[str]`
- Le stelle diventano una lista dinamica su `AstrologicalBaseModel` (`fixed_stars: List[KerykeionPointModel]`)
- Fornire preset: `BEHENIAN_STARS`, `ROYAL_STARS`, `DEFAULT_FIXED_STARS` (le 23 attuali)
- Creare `FixedStarDiscoveryFactory.find_prominent_stars(subject, orb=1.0)` per auto-discovery

### 5. Raffinamento Transiti Esatti
**Stato:** `TransitsTimeRangeFactory.get_transit_events()` esiste con `exact_moment`. Precisione limitata alla risoluzione della griglia.
- Aggiungere bisezione sub-step per trovare il vero momento esatto (precisione sub-secondo)
- Parametro opt-in: `refine_exact_moments: bool = False`
- 10-15 iterazioni di bisezione con `swe.calc_ut()` a JD interpolati

### 6. Local Space: Azimut/Altitudine per tutti i pianeti
**Stato:** `swe.azalt()` gia' usato per il Sole.
- Aggiungere `azimuth: Optional[float]` e `altitude: Optional[float]` a `KerykeionPointModel`
- Flag: `calculate_local_space: bool = False` su `ChartConfiguration`
- Calcolare via `swe.azalt()` per ogni pianeta quando abilitato

### 7. Varianti Lilith (Interpolata + Priapo)
**Stato:** Mean Lilith e True Lilith gia' implementate.
- Aggiungere `Interpolated_Lilith`, `Mean_Priapus`, `True_Priapus` a `AstrologicalPoint`
- Priapo = `(lilith.abs_pos + 180) % 360` (aritmetica)
- Lilith Interpolata = interpolazione tra Mean e True

---

## FASE 3: Feature Maggiori (2-4 settimane)

### 8. Direzioni Primarie
- Trigonometria custom: ascensione obliqua, poli delle cuspidi, archi di direzione
- Swiss Ephemeris NON ha funzione built-in — tutto calcolo manuale
- Metodo Placido come default, Tolemeo come alternativa
- `PrimaryDirectionsFactory` come factory standalone

### 9. Astro-Cartografia (Griglia ACG)
- `AstroCartographyFactory` che computa linee planetarie su griglia geografica
- Per ogni pianeta: trovare le longitudini dove il pianeta e' su ASC/DSC/MC/IC
- Risoluzione configurabile

---

## Da Posticipare
- **Asteroidi Custom da Elementi Kepleriani:** Problemi di thread safety con `seorbel.txt`, accuratezza degradante. Implementare solo su richiesta specifica.

---

## Note

### Feature gia' completate (rimosse dal piano originale)
- **Visibilita' Eclissi Locali:** 100% implementata in `EclipseFactory` con `search_from_location()`, `SolarEclipseModel.obscuration`, `LunarEclipseModel.magnitude_umbral`
