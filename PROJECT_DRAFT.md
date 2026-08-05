# Udkast til Weapon Merchant-projektet

## 1. Projektets formål
Dette projekt er et letvægts fantasy-testværktøj til at eksperimentere med AI-drevne handlende og verdensinteraktioner uden at skulle ind i Unreal. Frontenden eksisterer primært for at teste dialog, handelsopførsel, lore-integration og grundlæggende spilsystemer i et simpelt browserbaseret miljø.

## 2. Hvad der allerede findes

### Kernesystemet
- En FastAPI-backend i [merchant_main.py](merchant_main.py)
- Ruter til:
  - startside/byplads
  - smedje, apotek, general store
  - auktionshus
  - karakteroprettelse
  - samtale med købmænd
  - grundlæggende salgsscenarie for købmænd
  - udstilling og køb af auktioner

### Købmandssystem
- Logikken for samtaler med købmænd er implementeret i [merchants/merchant_data.py](merchants/merchant_data.py)
- Prompt-opbygning håndteres i [merchants/prompts.py](merchants/prompts.py)
- Købmandssvar kan bruge:
  - lore-drevne prompts
  - fallback-svar, når AI-tjenesten ikke er tilgængelig
  - hukommelse pr. spiller, så samtaler kan føles vedvarende
- Der findes også valgfri Arduino-serial-understøttelse til at sende købmandssvar til hardware.

### Verden og lore-indhold
- By- og købmand-lore ligger under [lore](lore)
- Projektet indeholder allerede struktureret indhold for flere regioner og byer, blandt andet:
  - Castle Town Buglia
  - Hamern
  - Ursk
  - By-lore-mapper som Buglia, Conla, Edvin, Nevdad og Mareen
- JSON-filer for købmænd findes til shopspecifikke personligheder og beholdninger.

### Økonomi og progression
- Guild-prislogik er defineret i:
  - [guilds/main_guild_data.py](guilds/main_guild_data.py)
  - [guilds/branch_guild_data.py](guilds/branch_guild_data.py)
  - [guilds/town_guild_data.py](guilds/town_guild_data.py)
- Spillet har grundlæggende regler for varepriser og købmandskøb/salg.
- Oprettelse af spillere og klassehåndtering er implementeret i [character/main_class_data.py](character/main_class_data.py)

### Auktionshus
- Flowet for at oprette og købe auktioner findes i [auction_house/auction_data.py](auction_house/auction_data.py)
- Auktiondata er gemt i [auction_house/auction_house.json](auction_house/auction_house.json)
- Der er grundlæggende støtte til at oprette varer, gennemse auktioner og købe dem.

### Frontend-sider
- Statiske HTML-sider findes i [static](static)
- Aktuelle sider inkluderer:
  - [static/town_square.html](static/town_square.html)
  - [static/gerik_smithy.html](static/gerik_smithy.html)
  - [static/elara_apothecary.html](static/elara_apothecary.html)
  - [static/finn_general_store.html](static/finn_general_store.html)
  - [static/auction_house.html](static/auction_house.html)
  - [static/create_character.html](static/create_character.html)

### Deployment
- Containerstøtte er sat op med [Dockerfile](Dockerfile) og [docker-compose.yml](docker-compose.yml)

## 3. Hvad der allerede virker godt
- Projektet har en klar struktur og en stærk fantasy-identitet.
- Købmandssystemet er mere end en simpel chatbot; det bruger lore og kontekst baseret på sted.
- Appen understøtter allerede en nyttig testcyklus for samtaler, karakteroprettelse og auktioninteraktioner.
- Indholdslaget er relativt rigt for et prototypeprojekt og egner sig godt til hurtig AI-eksperimentering.

## 3.5 Pros og Cons
### Pros
- Klar idé og fokus: Projektet er tydeligt defineret som en AI-drevet fantasy-købmandsprototype og fungerer godt som testplatform for dialog og handel.
- Struktur og modenhed: Backenden virker allerede som en fungerende FastAPI-app med ruter til by, butikker, auktion og karakteroprettelse.
- Lore og verden: Der er et solidt indholdslag med byer, towns og købmandspersonligheder i `lore/`.
- Købmandssystem med hukommelse: Chatflowet husker spillerens samtalehistorik pr. købmænd, hvilket giver mere vedvarende interaktion.
- Fallback og robusthed: Der er fallback-svar, hvis AI-modellen ikke reagerer, hvilket gør oplevelsen mere stabil.
- Container/opsætning: `Dockerfile` og `docker-compose.yml` viser, at projektet kan køres og deployes som container.

### Cons
- Frontend er ret simpel: Statiske HTML-sider fungerer, men UI/UX er begrænset og ikke integreret i en samlet app-oplevelse.
- Uensartet dataflow: Spillerinventar, købmænd og auktion er kun delvist forbundet; der mangler et samlet gameplay-flow.
- Manglende fejlhåndtering: Mange API-endpoints returnerer bare simple fejlmeddelelser uden validering eller statuskoder.
- AI-afhængighed uden fallback til lokal logik: `run_ollama()` kan bryde hele købmandsflowet, hvis modellen ikke er installeret eller går ned.
- Prompt- og datahåndtering kan blive spagetti: Promptbyggeren blander lore, merchant JSON, fallback og priser i én funktion, hvilket gør det sværere at udvide.
- Tests og dokumentation mangler: Der er ikke tydelige tests eller en README, som gør det svært for andre at forstå og bidrage.

## 4. Hvad der stadig mangler

### Spillets fuldendelse
- Brugen af spillerens inventar er kun delvist forbundet til resten af systemerne.
- Auktionhuset fungerer, men håndtering af annullering og udløb behøver polish.
- Regler for købmandskøb og -salg kunne udvides ud over den grundlæggende prismodel.

### Brugeroplevelse
- Frontenden kunne forbedres med bedre tilstandshåndtering, glattere UI-flow og tydeligere feedback på handlinger.
- Karakteroprettelse kunne udvides med mere detaljeret progression og udstyrslogik.
- By- og købmandssiderne kunne føles mere sammenhængende og interaktive.

### Indhold og verdenbygning
- Flere købmænd, byer, quests og genstande kunne tilføjes.
- Lore kunne forbindes mere dybt til gameplay-hændelser og købmandopførsel.
- Det nuværende indhold er et godt fundament, men behøver mere dybde og variation.
- Visionen er at bygge en regionsbaseret verden med 9 regioner, 9 hovedstæder og et stort netværk af byer, hvor alt hænger sammen via regional logik.
- Regionerne skal have egne ressourcer og priser: jern er billigt tæt på store miner, grøntsager er billigere hvor der dyrkes meget, og transport over lange afstande øger prisen.
- Guilden kan fungere som markedsaggregator og handelskanal, så varer købes og sælges gennem guild-priser med lokale og globale prisforskelle.
- Der skal være flere transportmuligheder: spillerens egen mount, køb af vogn/carriage, handelskaravane og mulige fastere ruter, som hver især påvirker tid og omkostning.
- Dynamiske classes bør være et fleksibelt system med klasse-templates, stats-modifikatorer og mulighed for at ændre opbygning over tid, ikke en statisk klasseliste.
- Drops skal være dynamiske, baseret på loot-tables, region, monster-type og event-status. Unikke items kan markedføres som one-of-a-kind og skal trackes centralt i verdensstaten.
- Secret quests og random dungeons skal genereres som enkelttilfælde: instanser uden foruddefinerede templates, som kun opstår én gang og derefter opdaterer verdenstilstanden, uanset om spilleren fuldfører dem eller ej.
- Systemet bør skille "verdenens topologi" fra "spilinteraktion": regioner, byer og ruter er metadata, mens quests, loot, dungeons og unikke genstande er event-drevne objekter med tilstand.

### Regional økonomi og transport
- Lav prisregulering baseret på lokal produktion, efterspørgsel og distance. Eksempel: jern fra en mines region er billig i hjemregionen og dyrt i fjerne regioner.
- Guildpriser kan indeholde regionale multiplikatorer, transportomkostninger og lokale skatter, så en vare har forskellig værdi alt efter hvor den handles.
- Transportmuligheder bør give gameplay-valg: hurtig, dyr vogntransport; langsom, billig karavane; eller fleksibel, personligt rideudstyr.
- Transport kan også skabe events: ruteangreb, handelskaravane-missioner, forsinkelser pga. vejr og ekstra profit for risikofulde leverancer.
- Tilføj teleportation som en låst funktion, der kun kan bruges efter, at spilleren har besøgt stedet mindst én gang.
- Forskellige regioner kan have specialvarer og færdigheder, hvilket gør rejser mellem hovedstæder og byer meningsfulde.

### Pros og cons ved regionsbaseret økonomi og unikke events
#### Pros
- Meget større dynamik: verden føles levende, når ressourcepriser varierer efter region og dag.
- Mere strategisk gameplay: spillere vælger ruter, transport og markeder ud fra pris og risiko.
- Høj genafspilningsværdi: unikke items og secret quests skaber historier, som ikke gentages på samme måde.
- Bedre lore-integration: økonomi, guildsystem og byer får en naturlig forklaring gennem produktionscentre og handel.
- Forskellige transportsystemer kan blive en spilmekanik i sig selv med karavaner, mount og handelstider.

#### Cons
- Complexity: systemet kræver flere data-tabeller og mere logik til at beregne pris, transport og unikke item-tilstand.
- Balancering: sværere at sikre at priser og drops føles fair på tværs af 9 regioner og forskellige transportmuligheder.
- State management: unikke items og single-instance dungeons kræver pålidelig verdenskontrol, ellers kan verden blive inkonsistent.
- Debugging: flere dynamiske komponenter betyder flere edge cases, især når spillere rejser langt eller bruger flere transportsystemer.
- Implementeringstid: det er ambitiøst og kan være bedre at bygge i faser med et simpelt region- og guild-økonomisystem først.

### Tilgang
- Begynd med at definere 9 regioner og deres hovedstader samt de største ressourcespecialer i hver region.
- Implementér først en simpel regional prismodel og guild markup, og tilføj transportpenge/distancer senere.
- Byg dynamiske classes og drops som separate systemer, så de kan bruges uafhængigt af økonomi og world state.
- Tilføj unikke items og dungeon-instanser som et lag oven på den grundlæggende regionsmodel, så du undgår for meget samtidighed i startfasen.

## 5. Forslag til næste milepæle

### Fase 1: stabilisering af kernen
- Gør auktionhus-flowet mere komplet
- Forbedre persistence og håndtering af inventar
- Tilføj tydeligere beskeder ved fejl og succes

### Fase 2: forbedring af oplevelsen
- Poler web-siderne
- Tilføj rigere købmandsinteraktioner
- Forbind flere spilsystemer sammen

### Fase 3: udvid verdenen
- Tilføj flere byer, købmænd og quests
- Introducer flere fortællingsdrevne hændelser og NPC-opførsel
- Udvid økonomi- og progressionstystemer

## 6. Kort projektoversigt
Dette er allerede en solid prototype med et stærkt tema og en anvendelig struktur. Den fungerer godt som en browserbaseret testsandbox for AI-købmandsadfærd og fantasyverdensinteraktioner, selvom frontenden er bevidst enkel og ikke hovedproduktet.

## 7. De bedste umiddelbare fokusområder
1. Færdiggør auktionhus-flowet.
2. Gør spillerinventar og købmandshandel mere sammenhængende.
3. Hold frontenden enkel og fokuseret på AI-testning.
4. Tilføj dokumentation og grundlæggende tests.
5. Udvid verdensindholdet gradvist.

## 8. Unreal Engine 5.0 og stort kort
Hvis du vil overføre projektet til Unreal Engine 5.0 og tænke i et kort på 3000 x 3000 km, er det vigtigste at gøre det til en streamet, segmenteret verden i stedet for én enkelt stor oversigt.
- Brug Unreal World Partition og Level Streaming/Level Instances til at dele kortet op i mindre celler, og load kun de områder, spilleren faktisk er i.
- Et 3000 x 3000 km kort i Unreal er ekstremt stort. På standarden 1 UU = 1 cm svarer det til 30 mia. uu, hvilket kan give floating-point præcisionsproblemer. Overvej at skalere verdenen ned til 1 UU = 1 m eller 1 UU = 10 m, eller at repræsentere hele oververdenen som en strategisk, abstrakt zone.
- Brug World Origin Shifting for at holde spillerens nærmiljø præcist og undgå positionstab ved store koordinater.
- Del verdenen op i mindre landskaber/landscape-proxies, fx 5x5 km eller 10x10 km celler, og strøm dem dynamisk.
- Hold gameplay- og AI-systemer adskilt fra rå verdenstørrelse: købmands- og lore-logik kan godt køre på et mindre scenerum, mens den store verden kun er struktur og rejsemål.
- Praktisk anbefaling: lav et konceptuelt 3000 km verdenskort, men fokuser på detaljerede zoner og byer som strømmende, genbrugelige noder i stedet for at modellere hver kvadratmeter.

## 9. Datamodel og gameplan
### Region/økonomi-objekter
Definér regioner som data, ikke hardcodet logik. Eksempel:
```json
{
  "region_id": "northmount",
  "name": "Northmount",
  "capital": "Frosthold",
  "resource_profile": {
    "iron": {"base_price": 80, "supply": 1.4},
    "vegetables": {"base_price": 20, "supply": 0.8}
  },
  "trade_modifiers": {
    "export_tax": 1.05,
    "import_demand": 1.2,
    "transport_cost_per_km": 0.02
  },
  "connected_regions": ["eastvale", "stormpass"]
}
```

### Byer og besøg
Hver by gemmer besøgsstatus, så teleportation kun åbnes efter første besøg:
```json
{
  "city_id": "stormport",
  "region_id": "eastvale",
  "name": "Stormport",
  "is_capital": false,
  "visited": false,
  "teleport_unlocked": false
}
```
Når spilleren ankommer første gang, sæt `visited = true` og `teleport_unlocked = true`.

### Transportmodeller
Definér transport som valgmulighed med tid, omkostning og risiko:
```json
{
  "transport": {
    "walk": {"speed_kmph": 5, "cost": 0, "risk": 0.1},
    "mount": {"speed_kmph": 12, "cost": 10, "risk": 0.08},
    "carriage": {"speed_kmph": 20, "cost": 50, "risk": 0.05},
    "caravan": {"speed_kmph": 10, "cost": 30, "risk": 0.15}
  }
}
```

### Guild-marked og regional prisberegning
Sælger du jern i en fjerntliggende region, skal prisen regnes ud fra:
- lokal basepris
- regional supply/demand
- afstand og transportmodifikator
- guild-commission

Formel eksempel:
`markedpris = base_price * region_modifier * distance_modifier * guild_fee`

### Dynamiske classes og loot
Hold classes som templates og builds som data:
```json
{
  "class_template": "battle_mage",
  "modifiers": {"strength": 0.8, "magic": 1.3, "stamina": 1.0},
  "available_skills": ["flame_strike", "shadow_shield"]
}
```

Loot og unikke items:
- Drops genereres ud fra region, monster-type og event.
- Unikke items registreres centralt i verdensstaten.
- Hvis et unique item spawnes, markér det som "claimed".

### Secret quest / random dungeon-instans
Brug instansobjekter, der kun eksisterer én gang:
```json
{
  "dungeon_instance_id": "riftdepths_001",
  "origin_region": "southplain",
  "spawned_at": "2026-07-30T14:00:00Z",
  "status": "active",
  "cleared": false,
  "unique_reward_id": "riftcore_amulet"
}
```
Efter afvikling eller fail sættes `status` til `completed` eller `failed`, og instansen fjernes fra aktiv pool.

### TP-unlock flow
1. Spiller ankommer til en ny by/region.
2. System markerer `visited=true`.
3. Når byen er besøgt, låses teleportation op i det globale rejsekort.
4. TP kan kun bruges til byer, der allerede er besøgt.

### Implementeringsfaser
1. Basislag:
  - 9 regioner og 9 hovedstæder
  - regionale priser og guild-styring
  - transportmuligheder og afstandsbaserede omkostninger
  - besøgs- og TP-status
2. Gameplay-lag:
  - dynamiske classes og fleksible builds
  - dynamiske drops og loot-tables
  - region-specifikke varer og specialprodukter
3. Event-lag:
  - unikke items tracked globalt
  - secret quests og single-instance dungeons
  - transport-events (ruteangreb, vejr, forsinkelser)

### Hvorfor dette er et godt udgangspunkt
- Det giver dig en klar, data-drevet arkitektur, som er let at udvide.
- Du adskiller verdenens struktur fra gameplay-logik.
- Det gør det lettere at lave 9 regioner med forskellige økonomier, samtidig med at du kan tilføje unikke events senere.
