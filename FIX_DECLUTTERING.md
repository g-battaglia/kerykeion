# Fix decluttering modern chart — Neptune scavalca pianeti vicini

## 1. Contesto generale

Kerykeion è una libreria Python per astrologia che genera chart SVG tramite `ChartDrawer`. Supporta due stili di rendering:

- **classic** — template XML storico (`chart.xml`) con glifi su cerchi concentrici; decluttering in `kerykeion/charts/draw_planets.py` tramite grouping con threshold 3.4°.
- **modern** — rendering from-scratch in viewBox 100×100 con 5 anelli concentrici (cusps → ruler → planets → house-numbers → aspects); decluttering in `kerykeion/charts/draw_modern.py` tramite spreading loop a 5 pass.

Nel rendering astrologico il **decluttering** serve a spaziare angolarmente i glifi di pianeti troppo vicini tra loro (cluster/stellium) così da evitare sovrapposizioni illeggibili. Il glifo viene spostato dalla sua posizione zodiacale reale a una "display position", e si disegna una linea tether (indicator line) dalla posizione reale al glifo spostato per mantenere la correttezza visiva.

**Vincolo fondamentale**: il decluttering deve **preservare l'ordine zodiacale** dei pianeti. Se due pianeti sono a 5° e 10° Acquario, il glifo a 5° deve apparire visualmente prima di quello a 10° lungo la wheel. Violare questo invariante rende la chart ingannevole.

## 2. Il bug

### Segnalazione utente

Issue GitHub (screenshot allegato): chart con `style="modern"`. Cluster di pianeti in Acquario + Pesci. Nettuno (~5° Acquario) dovrebbe essere posizionato tra il Nodo Lunare (~3° Aqua) e Venere (10° Aqua). Invece viene renderizzato **all'estremità destra del cluster**, oltre Urano (17° Aqua), vicino al confine Aqua/Pesci.

Tutti gli altri pianeti del cluster sono in ordine progressivo corretto — solo Nettuno è fuori posto. Stile classic non riproduce il bug (algoritmo diverso).

### Impatto

- Chart ingannevole: l'ordine visuale dei glifi non corrisponde all'ordine zodiacale reale.
- Confonde l'interprete astrologico (che ragiona per progressione di gradi).
- Si riproduce per qualunque configurazione con ≥3 pianeti a distanza reciproca ~8° (stellium stretti tipici in astrologia, non un caso limite). Bug sistemico, non eccezione.

### File coinvolto

- `kerykeion/charts/draw_modern.py`
  - Linea 68: `PLANET_MIN_SEPARATION = 8.0` (costante)
  - Linee 617-689: `_resolve_planet_collisions` (funzione bacata)
  - Linea 826: call site in `_draw_planet_ring`

## 3. Root cause

### Algoritmo attuale

```python
def _resolve_planet_collisions(planets_with_angles, min_separation=8.0):
    sorted_planets = sorted(planets_with_angles, key=lambda p: p["angle"])
    n = len(sorted_planets)
    for p in sorted_planets:
        p["display_angle"] = p["angle"]

    for _pass in range(5):
        changed = False
        # 1. Re-sort per display_angle ogni pass
        indices = sorted(range(n), key=lambda i: sorted_planets[i]["display_angle"])

        # 2. Trova largest gap (serve come "cut" del cerchio in sequenza lineare)
        best_gap = -1.0
        best_gap_pos = 0
        for k in range(n):
            k_next = (k + 1) % n
            gap = _normalize_angle(
                sorted_planets[indices[k_next]]["display_angle"]
                - sorted_planets[indices[k]]["display_angle"]
            )
            if gap > best_gap:
                best_gap = gap
                best_gap_pos = k

        # 3. Walk forward dal gap, push se troppo vicini
        start_k = (best_gap_pos + 1) % n
        walk = [(start_k + j) % n for j in range(n)]

        for j in range(1, n):
            prev_i = indices[walk[j - 1]]
            curr_i = indices[walk[j]]
            prev_a = sorted_planets[prev_i]["display_angle"]
            curr_a = sorted_planets[curr_i]["display_angle"]
            diff = _normalize_angle(curr_a - prev_a)
            if diff < sep:
                sorted_planets[curr_i]["display_angle"] = _normalize_angle(prev_a + sep)
                changed = True

        if not changed:
            break
    return sorted_planets
```

### Perché fallisce

Il problema è la combinazione di:

1. **Push sempre in avanti** di `sep` — se lo spazio tra `prev` e il successivo `next` è ancora minore di `sep`, il push su `curr` fa **scavalcare** `next`.
2. **Diff calcolato con `_normalize_angle`** che restituisce valori in `[0, 360)`. Quando `curr_display` è stato appena pushato oltre `next_display`, la distanza da `curr` (nuovo prev al passo successivo) a `next` wrappa a ~359°. Il check `if diff < sep` fallisce → il `next` scavalcato non viene pushato a sua volta.
3. **Re-sort per `display_angle` ogni pass**: il pianeta scavalcato risale davanti a quello che lo ha scavalcato, ma il walk riprende con il pianeta scavalcante già spostato avanti. Il push si propaga pass dopo pass, spingendo il pianeta originalmente "primo del cluster" sempre più avanti finché non scavalca tutto il cluster.

Il risultato: il pianeta il cui push iniziale ha scavalcato un vicino è quello che finisce ultimo del gruppo — l'opposto di dove dovrebbe stare.

### Trace completo con dati del cluster reale

Configurazione cluster (sep = `PLANET_MIN_SEPARATION` = 8.0°):

| Pianeta | abs_pos / angle |
|---------|-----------------|
| Node    | 303° (3° Aqua)  |
| Neptune | 305° (5° Aqua)  |
| Venus   | 310° (10° Aqua) |
| Uranus  | 317° (17° Aqua) |
| Sun     | 337° (7° Pesci) |
| Mercury | 345° (15° Pesci)|

**Pass 1** — walk ordine originale (da dopo il largest gap, assumiamo walk comincia dal Node):
- Neptune: `diff=2 < 8` → push `display = 303 + 8 = 311°` **(scavalca Venus 310)**
- Venus: `prev=Neptune 311`, `curr=Venus 310`, `diff = _normalize(310 - 311) = 359°`. `359 > 8` → **no push**. Venus rimane 310°.
- Uranus: `prev=Venus 310`, `diff=7 < 8` → push `318°`.
- Sun, Mercury: diff ok, no push.

Stato post-pass-1: Node 303, **Venus 310**, **Neptune 311** (scavalcante), Uranus 318, Sun 337, Mercury 345.

**Pass 2** — re-sort per display_angle → ordine: Node, Venus, Neptune, Uranus, Sun, Mercury.
- Venus: `prev=Node 303`, `diff=7 < 8` → push `311°`.
- Neptune: `prev=Venus 311`, `diff=0 < 8` → push `319°` **(scavalca Uranus 318)**.
- Uranus: `diff = _normalize(318 - 319) = 359 > 8` → **no push**.
- Sun, Mercury: ok.

Stato post-pass-2: Node 303, Venus 311, Uranus 318, **Neptune 319**, Sun 337, Mercury 345.

**Pass 3** — re-sort → Node, Venus, Uranus, Neptune, Sun, Mercury.
- Venus: `diff=8` (equal, non strict) → no push.
- Uranus: `diff=7 < 8` → push `319°`.
- Neptune: `prev=Uranus 319`, `diff=0 < 8` → push `327°`.

Stato post-pass-3: Node 303, Venus 311, Uranus 319, **Neptune 327**, Sun 337, Mercury 345.

**Pass 4**: stable, nessun push, loop esce.

**Output finale**: Neptune a display_angle 327° (oltre Uranus, vicino al confine Aqua/Pesci). Corrisponde esattamente al bug visivo dell'issue. Ordine zodiacale violato: Node, Venus, Uranus, Neptune, Sun, Mercury invece del corretto Node, Neptune, Venus, Uranus, Sun, Mercury.

## 4. Ricostruzione del momento storico

### Correzione rispetto all'ipotesi iniziale

L'ipotesi iniziale "fine Febbraio / inizio Marzo 1999" è **sbagliata**. Verificando le effemeridi reali del repo (`AstrologicalSubjectFactory` nel venv del progetto), quella configurazione non torna nel 1999:

- a fine Febbraio 1999 Mercurio è troppo avanti in Pesci (~25°), non ~15°;
- Venere non è a ~10° Acquario;
- Marte non è a ~10°59' Ariete;
- il nodo in Acquario mostrato nello screenshot non è il north node.

Il punto cerchiato nello screenshot è coerente invece con il **South Node** in Acquario, non con il North Node. Questo è anche coerente con i default del progetto: nelle chart modern sono attivi i true nodes, inclusi `True_South_Lunar_Node` e `True_North_Lunar_Node`.

Riferimenti codice:

- `kerykeion/settings/config_constants.py:209-223` — `DEFAULT_ACTIVE_POINTS` include `True_North_Lunar_Node` e `True_South_Lunar_Node`
- `kerykeion/schemas/kr_models.py:562-566` — i campi reali del subject model sono `true_north_lunar_node`, `true_south_lunar_node`, ecc.

### Data storica corretta

La chart dell'issue combacia molto bene con **26 Febbraio 2000**, non con il 1999.

Configurazione osservata nel repo per `2000-02-26`:

- `Sun` ~7° Pesci
- `Mercury` ~15° Pesci **retrogrado**
- `Venus` ~10° Acquario
- `Mars` ~10°59' Ariete
- `Uranus` ~17°57' Acquario
- `Neptune` ~5°15' Acquario
- `True_South_Lunar_Node` ~3°09' Acquario

L'allineamento più stretto con i gradi visibili nello screenshot cade circa attorno a **2000-02-26 07:30 UTC**:

- `Sun 7.003° Pis`
- `Mercury 15.339° Pis RX`
- `Venus 10.019° Aqu`
- `Mars 10.822° Ari`
- `Uranus 17.947° Aqu`
- `Neptune 5.245° Aqu`
- `True_South_Lunar_Node 3.155° Aqu`

Per un test end-to-end il punto importante non è l'ora esatta, ma scegliere una data che riproduca davvero il cluster. Una scelta robusta e semplice è:

- **fixture storico consigliato**: `2000-02-26 12:00 UTC`
- **fixture storico "best visual match"**: `2000-02-26 07:30 UTC`

Nota: per il fix non serve dipendere dalla chart storica. Il bug si attiva per qualunque cluster con ≥3 pianeti entro ~8° reciproci. Il test primario deve quindi essere sintetico e unitario; la data storica serve come regression/integration test secondario.

## 5. Fix proposto

File singolo: `kerykeion/charts/draw_modern.py`, funzione `_resolve_planet_collisions` (linee 617-689).

### Strategia

Due cambi minimi e chirurgici:

1. **Mantenere l'ordine originale (angolo reale) lungo tutti i pass** — non re-sortare per `display_angle` ogni volta. Il sort iniziale è la "verità zodiacale" e definisce l'ordine che il walk deve seguire.
2. **Trigger del push anche quando `diff > 180°`** — questa condizione indica che `curr` è apparentemente "indietro" rispetto a `prev` lungo il walk (= prev è stato pushato oltre curr in un pass precedente). Impossibile in un walk monotono, quindi forziamo la ribase di `curr` a `prev + sep`.

### Pseudocodice della fix

```python
def _resolve_planet_collisions(planets_with_angles, min_separation=PLANET_MIN_SEPARATION):
    if not planets_with_angles:
        return planets_with_angles

    max_possible_separation = 320.0 / len(planets_with_angles)
    sep = min(min_separation, max_possible_separation)

    # Sort ONCE per true zodiacal angle. Questo ordine NON cambia.
    sorted_planets = sorted(planets_with_angles, key=lambda p: p["angle"])
    n = len(sorted_planets)
    for p in sorted_planets:
        p["display_angle"] = p["angle"]

    for _pass in range(5):
        changed = False

        # Largest gap su display_angle correnti, ma indicizzato per ordine ORIGINALE
        best_gap = -1.0
        best_gap_pos = 0
        for k in range(n):
            k_next = (k + 1) % n
            gap = _normalize_angle(
                sorted_planets[k_next]["display_angle"]
                - sorted_planets[k]["display_angle"]
            )
            if gap > best_gap:
                best_gap = gap
                best_gap_pos = k

        start_k = (best_gap_pos + 1) % n
        walk = [(start_k + j) % n for j in range(n)]

        for j in range(1, n):
            prev_k = walk[j - 1]
            curr_k = walk[j]
            prev_a = sorted_planets[prev_k]["display_angle"]
            curr_a = sorted_planets[curr_k]["display_angle"]
            diff = _normalize_angle(curr_a - prev_a)
            # Push quando troppo vicino OPPURE quando curr appare "dietro" prev
            # (wraparound indica un pass precedente ha spinto prev oltre curr).
            if diff < sep or diff > 180.0:
                sorted_planets[curr_k]["display_angle"] = _normalize_angle(prev_a + sep)
                changed = True

        if not changed:
            break

    return sorted_planets
```

### Verifica fix sul cluster reale

Con fix applicata, sep=8°, cluster reale equivalente:

**Pass 1** — walk su ordine originale: South Node, Neptune, Venus, Uranus, Sun, Mercury.
- Neptune: `diff≈2 < 8` → push `SouthNode + 8°`.
- Venus: `diff = _normalize(310 - 311) = 359 > 180` → push 319°.
- Uranus: `diff = _normalize(317 - 319) = 358 > 180` → push 327°.
- Sun: `diff = 337 - 327 = 10 > 8` → no push.
- Mercury: `diff = 8` (equal, non strict, non > 180) → no push.

Stato post-pass-1: SouthNode, Neptune, Venus, Uranus, Sun, Mercury restano in ordine progressivo. **Ordine preservato.**

**Pass 2**: stable, esce.

Il fix funziona e mantiene l'invariante di ordine zodiacale.

### Caveat

Il fix rende il decluttering più "aggressivo" in cluster stretti: tutti i pianeti dello stellium vengono pushati in avanti a catena, non solo il primo. Questo è il comportamento corretto — nell'algoritmo precedente, il push cascading veniva "interrotto" dal bug di wrap, lasciando alcuni pianeti nella loro posizione reale e spingendone altri fuori. Ora il push si propaga uniformemente e l'ordine è sempre corretto.

Conseguenze visuali: i glifi in stellium stretti saranno più distanti dalla loro posizione reale (su cui c'è già la linea tether indicator). Nessuna modifica alle coordinate dei planet glyphs individuali — solo gli angoli di rotazione cambiano.

## 6. File critici

- `kerykeion/charts/draw_modern.py:617-689` — funzione `_resolve_planet_collisions` (unica da modificare)
- `kerykeion/charts/draw_modern.py:68` — costante `PLANET_MIN_SEPARATION` (non modificare in questa fix)
- `tests/core/test_chart_drawer.py` — test integration esistenti modern (template per eventuale regression test storico)
- `tests/core/test_modern_decluttering.py` — **nuovo file dedicato consigliato** per il regression test unitario del bug
- `tests/data/svg/` — snapshot SVG baseline (eventualmente da rigenerare per modern se cambia significativamente)

## 7. Test plan

### 7.0 Ordine di implementazione obbligatorio

Per rendere la regressione verificabile anche tornando al commit precedente, la sequenza corretta è:

1. **Aggiungere prima un nuovo unit test dedicato**, in un file nuovo separato.
2. Eseguire il test sul codice attuale: deve **fallire** e riprodurre il bug.
3. Solo dopo applicare la fix in `draw_modern.py`.
4. Rieseguire il test dedicato: deve **passare**.
5. Rieseguire la suite modern rilevante per controllare regressioni collaterali.

Questo punto è importante: il test non deve essere scritto dopo la fix, ma prima, così resta una prova concreta del difetto storico.

### 7.1 Unit test — root cause (nuovo file dedicato)

Nuovo test in **file dedicato** `tests/core/test_modern_decluttering.py` che:

1. Costruisce un fixture sintetico del cluster del bug con 6 pianeti a `angle` noti.
2. Chiama `_resolve_planet_collisions(planets, min_separation=8.0)`.
3. Verifica l'**invariante corretto**:
   - si ordina il risultato per `angle` reale;
   - si cerca il **largest gap** nei `display_angle` risultanti;
   - si "taglia" la sequenza in quel punto;
   - dopo il taglio, la sequenza dei `display_angle` deve essere monotonicamente crescente;
   - tutti i gap adiacenti nella sequenza linearizzata devono essere `>= sep`.

Importante: il caso wrap non va modellato come "≈360°" tra coppie adiacenti. Nel cerchio il wrap corretto è semplicemente il **largest gap ciclico**; il test deve tagliare lì e poi controllare la monotonia lineare.

Poiché `_resolve_planet_collisions` usa solo `angle` e aggiunge `display_angle`, il fixture può essere volutamente minimale: non serve creare veri `KerykeionPointModel` nel test unitario.

```python
def test_resolve_planet_collisions_preserves_zodiacal_order():
    planets = [
        {"angle": 303.0, "point": "South_Node", "color": "#000"},
        {"angle": 305.25, "point": "Neptune", "color": "#000"},
        {"angle": 310.0, "point": "Venus", "color": "#000"},
        {"angle": 317.0, "point": "Uranus", "color": "#000"},
        {"angle": 337.0, "point": "Sun", "color": "#000"},
        {"angle": 345.0, "point": "Mercury", "color": "#000"},
    ]

    resolved = _resolve_planet_collisions(planets, min_separation=8.0)

    by_angle = sorted(resolved, key=lambda p: p["angle"])
    displays = [p["display_angle"] for p in by_angle]

    # Find cyclic largest gap, then linearize after that cut.
    ...

    assert linearized == sorted(linearized)
    assert all(b - a >= 8.0 for a, b in zip(linearized, linearized[1:]))
```

Questo test deve:

- **fallire sul commit vecchio** con l'algoritmo attuale;
- **passare dopo la fix**.

### 7.2 Integration test — chart storica

Generare una chart modern per la data storica corretta e verificare nell'SVG che Nettuno sia tra `True_South_Lunar_Node` e Venere.

Data consigliata:

- `2000-02-26 12:00 UTC` per semplicità e stabilità

Meglio usare il **wheel-only SVG** per minimizzare rumore e differenze inutili:

- `ChartDrawer(...).generate_wheel_only_svg_string(style="modern")`

L'asserzione deve lavorare sui `transform="rotate(...)"` dei `ChartPoint` del cluster:

- `True_South_Lunar_Node`
- `Neptune`
- `Venus`
- `Uranus`

e verificare che l'ordine dei `display_angle` linearizzati sul largest gap sia quello corretto.

```python
def test_neptune_ordering_2000_stellium():
    s = AstrologicalSubjectFactory.from_birth_data(
        "Bug Repro", 2000, 2, 26, 12, 0,
        "London", "GB",
        lng=0.0, lat=51.5, tz_str="UTC", online=False,
        suppress_geonames_warning=True,
    )
    d = ChartDataFactory.create_natal_chart_data(s)
    svg = ChartDrawer(chart_data=d).generate_wheel_only_svg_string(style="modern")
    # Parse rotazioni glifi planet e asserisci ordine.
    ...
```

### 7.3 Regressione snapshot

```bash
pytest tests/core/test_chart_drawer.py -k modern
```

Se snapshot modern cambiano, ispezionare visivamente i diff e rigenerare baseline.

Nota pratica: il fix cambia il layout solo dove ci sono cluster stretti. È plausibile che alcuni baseline modern cambino. Va bene, ma prima il controllo deve essere semantico:

- ordine zodiacale preservato;
- nessun glifo scavalca i vicini;
- tether lines ancora coerenti con la posizione reale.

### 7.4 Verifica manuale

```bash
python -c "
from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

s = AstrologicalSubjectFactory.from_birth_data('Bug Repro', 2000, 2, 26, 12, 0,
    'London', 'GB', lng=0.0, lat=51.5, tz_str='UTC', online=False,
    suppress_geonames_warning=True)
d = ChartDataFactory.create_natal_chart_data(s)
ChartDrawer(chart_data=d).save_svg(output_path='/tmp', filename='repro', style='modern')
"
```

Aprire `/tmp/repro.svg` (browser / Inkscape) e verificare Neptune tra `True_South_Lunar_Node` e Venus.

## 8. Piano operativo finale

1. Creare `tests/core/test_modern_decluttering.py` con il nuovo regression test unitario sintetico.
2. Eseguire solo quel test e confermare che **fallisce** sul codice attuale.
3. Applicare la fix in `kerykeion/charts/draw_modern.py`.
4. Rieseguire il test dedicato e confermare che **passa**.
5. Aggiungere, se utile, il test storico `2000-02-26` basato su wheel-only SVG.
6. Eseguire `pytest tests/core/test_chart_drawer.py -k modern`.
7. Ispezionare eventuali diff nei baseline modern e rigenerarli solo dopo verifica visiva.

## 9. Note

- Nessuna API pubblica modificata. `_resolve_planet_collisions` è funzione privata. `get_type_hints()` non impattato (vincolo monetizzazione FastAPI rispettato).
- Nessun cambio a modelli, aspetti, dati, classic style. Il fix è strettamente localizzato al decluttering modern.
- Eventuali snapshot SVG che cambiano sono frutto di rendering corretto: accettabile rigenerarli previa verifica visiva.
