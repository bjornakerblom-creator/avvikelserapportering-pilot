# Avvikelserapportering

Enkel app för att rapportera avvikelser, störningar och kundreklamationer –
byggd för Saferoads holländska verksamhet (PMF-Bergum, PMF-Veendam, Brasov).
Fungerar i valfri webbläsare på jobbdator eller privat mobiltelefon, utan
installation och utan inloggning mot företagets IT-miljö.

## Komma igång

1. Dubbelklicka på **setup.bat** (bara första gången per dator, eller efter
   uppdateringar av koden).
2. Dubbelklicka på **run_app.bat** för att starta appen. Den öppnas i ett
   eget fönster på datorn.
3. För att testa från mobilen: se till att mobilen är på samma Wi-Fi som
   datorn, ta reda på datorns IP-adress (`ipconfig`) och gå till
   `http://DIN-IP:8600` i mobilens webbläsare. Lägg till sidan på hemskärmen
   för en app-liknande genväg.

## Teknik

- **Backend**: Python (FastAPI + Uvicorn), SQLite-databas.
- **Frontend**: vanilla HTML/CSS/JS (ingen bundler), PWA (installerbar på
  hemskärm), Chart.js (CDN) för statistikdiagram.
- **Data**: databasfil och uppladdade bilagor lagras i
  `%LOCALAPPDATA%\Avvikelserapportering\data` – *inte* i denna OneDrive-mapp,
  eftersom OneDrive-synk och en levande SQLite-fil inte är en bra
  kombination. Enbart källkoden ligger i repot.

## Statistiksidan

Statistiksidan (`/stats.html`) är skyddad med en enkel delad PIN-kod (inte en
riktig inloggning) eftersom den visar sammanställd ärendedata. Standard-PIN
är `2026` och sparas i klartext i
`%LOCALAPPDATA%\Avvikelserapportering\data\stats_pin.txt` – öppna filen och
ändra koden om du vill byta den.

## Lägga till fler avdelningar

Avdelningar (Svets, Montering, Kapning, Sälj, Inköp, Ekonomi) kan utökas
direkt i appen via knappen "Lägg till avdelning" på registreringssidan – ingen
kodändring behövs. Vill du ha en översatt visningsnamn på det nya språken,
lägg till en rad under `"departments"` i respektive fil i
`frontend/assets/i18n/`.

## Framtida steg (valfritt)

Detta är en fristående prototyp som körs lokalt. Om det senare visar sig
finnas behov av att nå appen utanför det lokala nätverket, eller flytta in
den i Saferoads egen hostingmiljö, är det ett separat beslut som tas med
IT senare.

## Tillfällig extern testdrift (Render.com)

För att kunna testa på flera privata mobiler (inte bara på samma Wi-Fi) finns
en `Dockerfile` och `render.yaml` som gör det möjligt att köra appen tillfälligt
på Render.coms gratisnivå med en riktig https-adress. Detta är **inte** en
IT-godkänd lösning – bara ett sätt att pilottesta flödet innan ärendet tas
vidare till IT för riktig hosting.

- Sätt **endast in påhittade/test-ärenden** där, inga riktiga kunduppgifter.
- Gratisnivån saknar en beständig disk: databasen nollställs varje gång
  tjänsten startar om (t.ex. efter inaktivitet). Bra för att testa själva
  flödet, dåligt för att spara data över tid.
- Datamappen styrs av miljövariabeln `AVVIKELSER_DATA_DIR` (satt till `/data`
  i containern) – på din vanliga Windows-körning används fortfarande
  `%LOCALAPPDATA%\Avvikelserapportering\data` som tidigare, ingen skillnad
  för den dagliga användningen.
