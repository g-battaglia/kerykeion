# Report: Migrazione da pyswisseph a libephemeris

**Data**: 31 Gennaio 2026  
**Progetto**: Kerykeion  
**Obiettivo**: Sostituire pyswisseph (Swiss Ephemeris) con libephemeris (NASA JPL DE440)

---

## Sommario Esecutivo

La migrazione da pyswisseph a libephemeris e stata completata a livello di codice. L'analisi dei test ha rivelato che libephemeris offre precisione eccellente per i pianeti principali (< 1 arcsec), ma presenta due limitazioni significative: un range temporale ridotto (1550-2650 vs ~5000 BC-5000 AD) e una differenza sistematica nel calcolo del True Lunar Node (~83 arcsec).

---

## 1. Modifiche Effettuate

### File Modificati

| File                                        | Modifica                                                              |
| ------------------------------------------- | --------------------------------------------------------------------- |
| `kerykeion/astrological_subject_factory.py` | `import swisseph as swe` → `import libephemeris as swe`               |
| `kerykeion/charts/chart_drawer.py`          | `import swisseph as swe` → `import libephemeris as swe`               |
| `kerykeion/planetary_return_factory.py`     | `import swisseph as swe` → `import libephemeris as swe`               |
| `kerykeion/aspects/aspects_utils.py`        | `from swisseph import difdeg2n` → `from libephemeris import difdeg2n` |
| `tests/core/test_astrological_subject.py`   | 4 occorrenze: import e patch `swisseph` → `libephemeris`              |
| `scripts/test_markdown_snippets.py`         | `"swisseph"` → `"libephemeris"` nella lista dipendenze                |

### Stato Attuale

- **pyproject.toml**: Contiene ancora `pyswisseph>=2.10.3.1` (da rimuovere se si procede)
- **Test fixtures**: Generati con pyswisseph (da rigenerare con `poe regenerate:all`)

---

## 2. Risultati dei Test

### Statistiche Generali

| Categoria    | Conteggio |
| ------------ | --------- |
| Test passati | 4019      |
| Test falliti | 752       |
| Test skipped | 135       |
| **Totale**   | 4906      |

### Analisi dei Fallimenti

#### A) Date fuori range DE440 (~550 test)

Il file efemeride DE440.bsp copre solo il periodo **1549-12-21 → 2650-01-25**.

Test falliti per date storiche:

- `roman_100ad` - 100 d.C.
- `late_antiquity_400` - 400 d.C.
- `columbus_1492` - 1492
- `medieval_*` - varie date medievali
- `galileo_*` - pre-1550

**Errore tipico**:

```
ValueError: ephemeris segment only covers dates 1549-12-21 through 2650-01-25
```

#### B) Differenze di precisione (~200 test)

Test che falliscono per differenze numeriche tra i valori attesi (generati con pyswisseph) e quelli calcolati (libephemeris).

---

## 3. Analisi della Precisione

### Pianeti Principali (John Lennon, 1940)

| Pianeta | Differenza     | Valutazione |
| ------- | -------------- | ----------- |
| Sun     | +0.009 arcsec  | Eccellente  |
| Moon    | +0.17 arcsec   | Eccellente  |
| Mercury | -0.0002 arcsec | Eccellente  |
| Venus   | +0.03 arcsec   | Eccellente  |
| Mars    | +0.08 arcsec   | Eccellente  |
| Jupiter | +0.73 arcsec   | Eccellente  |
| Saturn  | -0.36 arcsec   | Eccellente  |
| Uranus  | +0.49 arcsec   | Eccellente  |
| Neptune | +0.02 arcsec   | Eccellente  |
| Pluto   | -0.44 arcsec   | Eccellente  |

**Conclusione**: Tutti i pianeti mostrano differenze < 1 arcsec, ben al di sotto della soglia percettibile per scopi astrologici.

### True Lunar Node

| Metrica                        | Valore                   |
| ------------------------------ | ------------------------ |
| Differenza osservata           | ~83 arcsec (~1.4 arcmin) |
| Differenza documentata (media) | ~72 arcsec               |
| Differenza documentata (max)   | ~260 arcsec              |

**Stato**: Comportamento atteso, non un bug.

### Moon Speed

| Metrica    | Valore              |
| ---------- | ------------------- |
| Differenza | -0.58 arcsec/giorno |

**Stato**: Differenza minima, accettabile.

---

## 4. Differenze Metodologiche

### Calcolo del True Lunar Node

| Aspetto             | Swiss Ephemeris             | libephemeris                    |
| ------------------- | --------------------------- | ------------------------------- |
| Sorgente efemeride  | Teoria lunare pre-calcolata | JPL DE440 via Skyfield          |
| Metodo calcolo nodo | Diretto dalla teoria lunare | Meccanica orbitale (h = r x v)  |
| Perturbazioni       | Integrate nella teoria      | Serie ELP2000-82B (90+ termini) |
| Precessione         | Modello interno             | IAU 2006 + correzione empirica  |
| Nutazione           | Modello interno             | IAU 2000A (1365 termini)        |

### Perche 83 arcsec di differenza?

La documentazione in `libephemeris/lunar.py` spiega:

> **Compared to Swiss Ephemeris:**
>
> - Modern dates (1900-2100): < 0.01 deg (36 arcsec) typical error
> - Mean error: ~0.02 deg (~72 arcsec)
> - Maximum error: ~0.07 deg (~260 arcsec) at edge cases

Le fonti principali di errore sono:

1. **Differenze nel modello di precessione**: ~0.001-0.003 deg (principale)
2. Precisione JPL DE: ~1 milliarcsec (trascurabile)
3. Modello di nutazione: sub-milliarcsecond (trascurabile)

---

## 5. Confronto Generale

| Caratteristica           | pyswisseph         | libephemeris           |
| ------------------------ | ------------------ | ---------------------- |
| **Range temporale**      | ~5000 BC → 5000 AD | 1550 → 2650            |
| **Precisione pianeti**   | Riferimento        | < 1 arcsec             |
| **Precisione True Node** | Riferimento        | ~72-83 arcsec          |
| **Licenza**              | GPL/LGPL           | MIT-friendly (JPL)     |
| **Sorgente dati**        | Swiss Ephemeris    | NASA JPL DE440         |
| **Manutenzione**         | Stabile            | Sviluppo attivo        |
| **Dipendenze**           | Bindings C         | Pure Python + Skyfield |

---

## 6. Opzioni per Procedere

### Opzione A: Completare migrazione a libephemeris

**Pro**:

- Licenza piu permissiva
- Precisione eccellente per date moderne (1550-2650)
- Basato su dati NASA JPL (standard astronomico)

**Contro**:

- Perde supporto per date storiche pre-1550
- Differenza ~83 arcsec nel True Node
- Richiede rigenerazione di tutti i test fixtures

**Azioni richieste**:

1. Rimuovere `pyswisseph>=2.10.3.1` da `pyproject.toml`
2. Eseguire `poe regenerate:all` per rigenerare fixtures
3. Adattare/skippare ~550 test con date storiche
4. Aggiornare documentazione con limitazioni temporali

### Opzione B: Tornare a pyswisseph

**Pro**:

- Nessuna perdita di funzionalita
- Range temporale completo
- True Node esatto

**Contro**:

- Licenza GPL/LGPL
- Nessun beneficio dalla migrazione

**Azioni richieste**:

1. Revertire tutte le modifiche agli import
2. Nessuna altra azione necessaria

### Opzione C: Approccio ibrido

**Pro**:

- Flessibilita massima
- Supporto per tutti i casi d'uso

**Contro**:

- Complessita di implementazione
- Due dipendenze da mantenere

**Azioni richieste**:

1. Mantenere entrambe le dipendenze
2. Implementare logica di fallback per date fuori range
3. Aggiungere warnings per l'utente

---

## 7. Raccomandazione

Per un utilizzo focalizzato su **astrologia moderna** (nativita dal 1550 in poi), **libephemeris e raccomandato** per:

1. Licenza piu permissiva (MIT-friendly vs GPL)
2. Precisione eccellente per i pianeti (< 1 arcsec)
3. Basato su standard NASA JPL DE440
4. La differenza nel True Node (~83 arcsec = ~0.023 deg) e trascurabile per scopi astrologici pratici

Per applicazioni che richiedono **supporto per date storiche** (antichita, medioevo, etc.), **pyswisseph rimane necessario**.

---

## 8. Comandi Utili

```bash
# Eseguire test solo per date moderne (nel range DE440)
uv run pytest tests/ -v -k "not (roman_ or antiquity or medieval or renaissance or columbus or galileo)" --tb=short

# Rigenerare tutti i fixtures (dopo decisione finale)
poe regenerate:all

# Verificare differenze specifiche
uv run pytest tests/core/test_planetary_positions.py -v --tb=long
```

---

## 9. File Chiave

| File                                                       | Descrizione                               |
| ---------------------------------------------------------- | ----------------------------------------- |
| `kerykeion/astrological_subject_factory.py`                | Calcoli astrologici principali            |
| `tests/data/expected_positions.py`                         | Valori attesi (generati con pyswisseph)   |
| `tests/core/test_planetary_positions.py`                   | Test posizioni planetarie                 |
| `pyproject.toml`                                           | Dipendenze del progetto                   |
| `.venv/lib/python3.10/site-packages/libephemeris/lunar.py` | Implementazione True Node in libephemeris |

---

_Report generato durante la sessione di migrazione pyswisseph → libephemeris_
