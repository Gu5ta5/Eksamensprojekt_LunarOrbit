# LunarOrbit - Interaktiv Månefase Visualisering

## Om Projektet

LunarOrbit er et professionelt uddannelsesværktøj til visualisering og udforskning af månefaser. Applikationen beregner månedata baseret på astronomiske algoritmer og viser en interaktiv brugergrænseflade med realtidsinformation om månens fase og belysning.

### Funktionalitet

- **Månefaseberegning**: Beregner pålidelig månefase og belysning for enhver dato baseret på veletablerede astronomiske algoritmer
- **Visuelle Repræsentationer**: Viser månens aktuelle fase ved hjælp af store emoji-tegn (150pt) for god synlighed
- **Vejrdata**: Integrerer Open Meteo API til at vise vejrinformation (temperatur, skydække) for den valgte lokation
- **Brugervenlig Interface**: Moderne dark-mode brugergrænseflade designet med CustomTkinter
- **Realtidsklokling**: Viser aktuel tid i øvre højre hjørne

## Teknologi Stack

- **Python 3.8+**
- **CustomTkinter 1.6+** - moderne GUI-bibliotek med dark-mode support
- **Requests** - HTTP-bibliotek til API-kald
- **Open Meteo API** - gratis vejr- og geokoderings-API

## Installation

### Forudsætninger

- Python 3.8 eller nyere
- pip (Python Package Manager)

### Trin-for-trin Installation

1. **Klon projektet** eller download filerne til din computer
   ```bash
   cd Eksamensprojekt_LunarOrbit
   ```

2. **Opret et virtuelt Python-miljø** (anbefalet):
   ```bash
   python -m venv .venv
   ```

3. **Aktivér det virtuelle miljø**:
   
   **Windows (PowerShell)**:
   ```bash
   .venv\Scripts\Activate.ps1
   ```
   
   **Windows (Command Prompt)**:
   ```bash
   .venv\Scripts\activate.bat
   ```
   
   **macOS/Linux**:
   ```bash
   source .venv/bin/activate
   ```

4. **Installer afhængigheder**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Eller installer manuelt:
   ```bash
   pip install customtkinter requests
   ```

## Kørsel af Applikationen

Når afhængigheder er installeret, kør applikationen:

```bash
python main.py
```

Applikationen åbner et grafisk vindue med månefasevisualisering og vejrdata.

## Projektstruktur

### Filbeskrivelser

- **main.py** (266 linjer)
  - Hovedapplikationskode
  - UI-controller der håndterer al GUI-logik
  - Initialiserer komponenter og event-loop

- **moon_api.py** (171 linjer)
  - MoonAPIClient-klasse til månefaseberegninger
  - Astronomiske algoritmer baseret på synodisk måned (29.530588 dage)
  - Integration med Open Meteo API for vejrdata
  - Bruger januar 6, 2000 (nymåne) som referencedato

- **boilerplate.py** (372 linjer)
  - DateUtils: Dato- og tidshåndterings-hjælpere
  - MoonConstants: Konstanter og fase-navne på dansk
  - Validators: Inputvalidering (dato, fase, belysning)
  - Formatters: Outputformatering (procent, koordinater)
  - MoonEngine: Månefaseberegninger og transformationer
  - MoonVisuals: Emoji-repræsentationer og visuelle mappinger

- **.gitignore**
  - Udelukker .venv, __pycache__ og .vscode fra Git-tracking

## Konfiguration

### Standardindstillinger

Applikationen bruger som standard **København koordinater**:
- Breddegrad: 55.6761°N
- Længdegrad: 12.5683°E

Vejrdata hentes for denne lokation. For at ændre lokation, rediger `MoonAPIClient` initialisering i `main.py`:

```python
self.api_client = MoonAPIClient(
    latitude=YOUR_LATITUDE,
    longitude=YOUR_LONGITUDE,
    location_name="Din By"
)
```

## Arkitektur & Design Principper

Projektet følger **Separation of Concerns** princippet med fire specialiserede moduler:

1. **main.py**: Kun UI-rendering og event-håndtering
2. **moon_api.py**: API-kommunikation og måneberegninger
3. **boilerplate.py**: Hjælpefunktioner og konstanter
4. **Hver klasse har enkelt ansvar** (Single Responsibility Principle)

## Astronomiske Algoritmer

### Månefaseberegning

Applikationen beregner månefase baseret på:

```
dage_siden_nymåne = dage_mellem(jan_6_2000, aktuel_dato)
dage_i_cyklus = dage_siden_nymåne % 29.530588
fase = dage_i_cyklus / 29.530588  [0-1 skala]
```

### Belysningsberegning

- **Fase 0.0-0.5** (voksende): `belysning = 100 * (2 * fase)`
- **Fase 0.5-1.0** (aftagende): `belysning = 100 * (2 * (1 - fase))`

### 8 Månefaser

| Fase | Emoji | Dansk Navn | Interval |
|------|-------|------------|----------|
| 0 | 🌑 | Nymåne | 0.0-0.125 |
| 1 | 🌒 | Voksende halvmåne | 0.125-0.25 |
| 2 | 🌓 | Første kvarter | 0.25-0.375 |
| 3 | 🌔 | Voksende gibbous | 0.375-0.5 |
| 4 | 🌕 | Fuldmåne | 0.5-0.625 |
| 5 | 🌖 | Aftagende gibbous | 0.625-0.75 |
| 6 | 🌗 | Sidste kvarter | 0.75-0.875 |
| 7 | 🌘 | Aftagende halvmåne | 0.875-1.0 |

## Requirements.txt

```
customtkinter==1.6.2
requests==2.32.5
```

## Fejlfinding

### Fejl: "ModuleNotFoundError: No module named 'customtkinter'"

**Løsning**: Installer CustomTkinter:
```bash
pip install customtkinter
```

### Fejl: "ModuleNotFoundError: No module named 'requests'"

**Løsning**: Installer Requests:
```bash
pip install requests
```

### Vejrdata vises ikke

**Årsag**: Muligvis ingen internetforbindelse eller Open Meteo API er utilgængelig
**Løsning**: Applikationen fungerer stadig uden vejrdata - månefaseberegninger fungerer offline

## API-Licens

- **Open Meteo API**: Gratis, uden API-nøgle nødvendig
- **CustomTkinter**: MIT-licens
- **Requests**: Apache 2.0-licens

## Forbedringer & Udviklinger

Mulige fremtidsforbedringer:
- Datovælger interface til at vælge specifik dato
- Graph med månefaseprogression over en måned
- Detaljer om kommende astronomiske begivenheder
- Moonrise/moonset tidspunkter
- Multisproget support

## Licens

Dette projekt er oprettet til uddannelsesformål.

## Kontakt & Support

For spørgsmål eller fejlrapporter, kontakt vedligeholder af projektet.
