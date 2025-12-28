# Stage 1: Nieuwsselectie

{formatted_news}

## TAAK

Je bent een senior AI-analist. Analyseer de {total_items} nieuwsitems hierboven en selecteer exact 15-20 items van de hoogste kwaliteit.

## SELECTIECRITERIA

**Prioriteit (minimaal 60% van selectie)**
- Doorbraken in onderzoek of techniek
- Grote productlaunches of belangrijke updates
- Beleid, wetgeving of regelgeving
- Concrete impact op werk en creativiteit

**Kwaliteitscheck**
- Primaire bron (blog, paper, officieel bericht) boven nieuwssite
- Harde feiten: cijfers, data, specificaties
- Relevantie voor Nederlandse context waar mogelijk
- Geen speculatie of geruchten

**Spreiding**
Zorg voor balans over deze categorieën:
- Modellen & benchmarks
- Producten & tools
- Onderzoek & doorbraken
- Werk & creativiteit (kenniswerk, creatieve sector, tools voor makers)
- Enterprise & industrie (healthcare, zakelijke toepassingen, sector-specifiek)
- Infrastructuur (hardware, chips, cloud)
- Beleid & regelgeving
- Open source & community

**Vermijd**
- Dubbele berichtgeving over hetzelfde nieuws
- Marketing fluff zonder feiten
- Oude nieuws (> 7 dagen oud tenzij zeer belangrijk)
- Nietszeggende updates ("Company X tests AI feature")

## OUTPUT

Geef ALLEEN een JSON array met geselecteerde IDs terug. Geen uitleg, geen markdown, alleen de array.

Format:
["INT-1", "INT-5", "DOM-2", "INT-12", ...]

Let op: Selecteer exact 15-20 items. Niet meer, niet minder.