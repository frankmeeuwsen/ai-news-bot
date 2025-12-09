# AI News Digest - 17 december 2025

## AI Agents & Autonomous Systems

### Booking.com bouwde agent-systeem voor de hype begon en verdubbelde nauwkeurigheid

**Reisplatform combineert kleine en grote modellen voor snelheid en betrouwbaarheid**

Booking.com ontwikkelde zijn agent-systeem al voordat de term 'AI agents' populair werd. Het bedrijf gebruikt een hybride aanpak: kleine, gespecialiseerde modellen voor snelle antwoorden en grote taalmodellen voor complexe vragen. Deze strategie leverde een verdubbeling van de nauwkeurigheid op bij het herkennen van klantvragen en verhoogde de efficiëntie van menselijke medewerkers met 1,5 tot 1,7 keer. Het systeem detecteert automatisch wat klanten zoeken - zoals jacuzzi's, wat nu een veel gevraagd filter blijkt. Booking.com vermijdt 'one-way doors': beslissingen die je later niet meer terug kunt draaien, en houdt zijn systeem zo flexibel mogelijk om snel te kunnen aanpassen aan nieuwe ontwikkelingen.

[Bron: VentureBeat AI](https://venturebeat.com/ai/booking-coms-agent-strategy-disciplined-modular-and-already-delivering-2)

### Anthropic verbindt Claude Code met Slack voor automatisch programmeerwerk

**Ontwikkelaars sturen coding-opdrachten direct vanaf berichtendienst**

Anthropic lanceert een integratie waarmee ontwikkelaars Claude Code kunnen gebruiken zonder Slack te verlaten. Je tagt @Claude in een kanaal of thread, en het systeem analyseert of het een programmeer-opdracht betreft. Zo ja, dan start Claude automatisch een codesessie, verzamelt context uit eerdere berichten, kiest de juiste repository en post updates terug in de thread. Het systeem genereert uiteindelijk een pull request die ontwikkelaars kunnen reviewen. Deze functie bouwt voort op het succes van Claude Code, dat zes maanden na lancering al 1 miljard dollar omzet genereert bij klanten als Netflix, Spotify en Salesforce. De Slack-integratie is vanaf nu beschikbaar als onderzoekspreview voor teams die Claude Code op het web gebruiken.

[Bron: VentureBeat AI](https://venturebeat.com/ai/anthropics-claude-code-can-now-read-your-slack-messages-and-write-code-for) | [The Verge AI](https://www.theverge.com/news/839817/anthropic-claude-code-slack-integration)

### Simpele AI-agents verslaan experts bij optimaliseren biomedische beeldanalyse

**Onderzoek toont dat eenvoudige agent-architecturen beter presteren dan complexe systemen**

Onderzoekers ontdekten dat eenvoudige AI-agents consistente betere resultaten behalen dan menselijke experts bij het aanpassen van beeldverwerkingssoftware voor wetenschappelijke datasets. Het team ontwikkelde een evaluatieframework voor drie biomedische imaging-pipelines en testte verschillende agent-ontwerpen. Complexe agent-architecturen bleken niet universeel beter te presteren dan simpele varianten. De gegenereerde code van eenvoudige agents overtrof oplossingen van menselijke experts en wordt nu ingezet in productieomgevingen. Dit onderzoek biedt een praktische routekaart voor het ontwerpen van agents die productieniveau kunnen halen.

[Bron: arXiv Computer Vision](https://arxiv.org/abs/2512.06006)

## Large Language Models & Foundation Models

### Anthropic lanceert Opus 4.5: krachtiger en vijf keer goedkoper

**Nieuw model verlengt gesprekken en verlaagt API-prijzen drastisch**

Anthropic introduceert Claude Opus 4.5, het krachtigste model uit de nieuwe generatie. Het bedrijf verlaagt tegelijk de API-prijzen van 15 dollar naar 5 dollar per miljoen tokens input en van 75 dollar naar 25 dollar per miljoen tokens output - een prijsdaling van 67 procent. Opus 4.5 draait op alle drie de grote cloudplatforms en in de desktop-apps van Anthropic. Het model ondersteunt langere gesprekken, wat een veelgehoorde klacht van gebruikers adresseert. Deze update maakt Opus-niveau capaciteiten toegankelijk voor meer gebruikers en bedrijven die voorheen de kosten te hoog vonden.

[Bron: Ars Technica AI](https://arstechnica.com/ai/2025/11/anthropic-introduces-opus-4-5-cuts-api-pricing-and-enables-much-longer-claude-chats/)

### Zhipu AI lanceert GLM-4.6V: open-source vision model met native tool-gebruik

**Chinees AI-model combineert beeld en tekst met directe toegang tot tools**

Zhipu AI introduceert GLM-4.6V, een open-source model dat tekst en afbeeldingen begrijpt en direct tools kan gebruiken zonder tussenliggende stappen. Het systeem komt in twee varianten: GLM-4.6V (106 miljard parameters) voor krachtige cloud-servers en GLM-4.6V-Flash (9 miljard parameters) voor snelle, lokale toepassingen. Het model verwerkt teksten tot 128.000 tokens (vergelijkbaar met een boek van 300 pagina's) en haalt betere scores dan vergelijkbare modellen: 88,2 punten bij wiskundige vraagstukken tegenover 84,6 van de vorige versie. Bij website-navigatie scoort het 81,0 punten, waar concurrenten rond 68,4 blijven steken. Het model kost 0,30 dollar per miljoen tokens input en 0,90 dollar output, wat het goedkoper maakt dan veel alternatieven. Zhipu AI geeft het vrij onder MIT-licentie, waardoor bedrijven het kunnen gebruiken zonder licentiekosten.

[Bron: VentureBeat AI](https://venturebeat.com/ai/z-ai-debuts-open-source-glm-4-6v-a-native-tool-calling-vision-model-for)

### Nanbeige4-3B doorbreekt grenzen voor kleine taalmodellen

**3 miljard parameter model evenaart veel grotere systemen**

Het Chinese Nanbeige presenteert Nanbeige4-3B, een compact taalmodel dat ondanks zijn bescheiden formaat concurreert met veel grotere modellen. Het team trainde het systeem op 23 biljoen tokens en verfijnde het met 30 miljoen instructies. Ze ontwikkelden een Fine-Grained Warmup-Stable-Decay trainingsschema dat de datamix gedurende verschillende fases progressief verfijnt. Na supervised fine-tuning paste het team een nieuwe Dual Preference Distillation methode toe, waarbij hun vlaggenschip-redeneermodel kennis overdraagt aan het kleinere model. Een laatste fase met reinforcement learning versterkte zowel redeneervermogen als menselijke afstemming. De modelbestanden staan open op Hugging Face voor ontwikkelaars die ermee willen experimenteren.

[Bron: arXiv NLP](https://arxiv.org/abs/2512.06266)

### Transformer-bedenker Vaswani lanceert Rnj-1 programmeermodel

**Essential AI's nieuwe model overtreft grotere concurrenten op SWE-bench test**

Ashish Vaswani, mede-uitvinder van de transformer-architectuur, presenteert Rnj-1 via zijn bedrijf Essential AI. Het nieuwe open-source programmeermodel presteert significant beter op de SWE-bench Verified test dan veel grotere alternatieven. SWE-bench test hoe goed AI-systemen echte softwareproblemen oplossen door code te schrijven en aan te passen. Vaswani's team focust op efficiëntie: het model behaalt topresultaten met minder parameters dan de concurrentie. Deze aanpak sluit aan bij Vaswani's eerdere werk aan de transformer-architectuur, die de basis legde voor moderne taalmodellen. Essential AI deelt de modelgewichten open source, zodat ontwikkelaars het kunnen gebruiken en aanpassen.

[Bron: The Decoder](https://the-decoder.com/transformer-co-creator-vaswani-unveils-high-performance-rnj-1-coding-model/)

## Multimodal AI

### Google lanceert Gemini 3 Pro: sterkste model voor visuele taken

**Nieuw model zet nieuwe standaard voor multimodale capaciteiten**

Google introduceert Gemini 3 Pro, dat volgens het bedrijf het beste model ter wereld is voor multimodale taken. Het systeem combineert tekst-, beeld-, video- en audioherkenning in één model. Gemini 3 Pro overtreft voorgangers op benchmarks voor visuele vraagbeantwoording, grafiekherkenning en documentanalyse. Het model verwerkt langere contexten dan eerdere versies en biedt nauwkeurigere resultaten bij complexe visuele redeneertaken. Google positioneert Gemini 3 Pro als de nieuwe standaard voor ontwikkelaars die geavanceerde vision AI nodig hebben. Het model is vanaf nu beschikbaar via Google's API en draait op alle grote cloudplatforms.

[Bron: Google AI Blog](https://blog.google/technology/developers/gemini-3-pro-vision/)

## Research & Academic Breakthroughs

### Onderzoekers identificeren 'weakness of will' als risicofactor voor AI-agents

**Akrasia-benchmark meet wanneer modellen eigen beslissingen tegenspreken**

Wetenschappers introduceren het concept 'akrasia' - zwakte van de wil - als lens voor het analyseren van inconsistent gedrag bij AI-systemen. Ze ontwikkelden een Akrasia Benchmark met vier testcondities die meten wanneer een model zijn eerdere beslissingen tegenspreekt. De test meet wanneer lokale antwoorden botsen met eerder geformuleerde doelen - vergelijkbaar met hoe mensen soms tegen beter weten in handelen. Dit micro-niveau akrasia kan volgens de onderzoekers opschalen naar macro-niveau instabiliteit in multi-agent systemen, wat geïnterpreteerd kan worden als 'scheming' of opzettelijke misalignment. Het onderzoek verbindt klassieke filosofische theorieën over wilskracht met de opkomende wetenschap van agentische AI en biedt een empirische brug tussen filosofie, psychologie en AI-onderzoek.

[Bron: arXiv AI](https://arxiv.org/abs/2512.05449)

### Studie pleit voor mens-AI samenwerking boven zelf-verbeterende AI

**Co-superintelligence veiliger en effectiever dan autonome zelfverbetering**

Onderzoekers stellen dat co-improvement - samenwerking tussen menselijke onderzoekers en AI - een beter doel is dan volledig autonome AI-zelfverbetering. Ze introduceren het concept 'co-superintelligence': AI-systemen die specifiek ontworpen zijn om met menselijke onderzoekers samen te werken aan AI-onderzoek, van ideevorming tot experimenten. Deze aanpak zou zowel AI-systemen als mensen veiliger superintelligentie geven door hun symbiose. Het team betoogt dat het focussen op menselijke onderzoekers in de loop niet alleen sneller resultaten oplevert, maar ook inherent veiliger is dan systemen die autonoom opereren. De studie suggereert dat het verbeteren van AI's vermogen om met mensen samen te werken prioriteit moet krijgen boven volledig autonome capaciteiten.

[Bron: arXiv AI](https://arxiv.org/abs/2512.05356)

## Product Launches & Updates

### Hugging Face lanceert Transformers v5 met vereenvoudigde modeldefinities

**Nieuwe versie stroomlijnt AI-ontwikkeling met eenvoudigere code**

Hugging Face introduceert Transformers v5, een grote update van zijn populaire AI-bibliotheek. De nieuwe versie vereenvoudigt hoe ontwikkelaars AI-modellen definiëren en gebruiken. Transformers v5 elimineert veel boilerplate-code en maakt het makkelijker om modellen aan te passen aan specifieke toepassingen. De bibliotheek ondersteunt duizenden open-source modellen en wordt gebruikt door miljoenen ontwikkelaars wereldwijd. Deze update verlaagt de drempel voor teams die productie-ready AI willen bouwen zonder diepgaande expertise. Hugging Face behoudt backward compatibility met eerdere versies, zodat bestaande projecten blijven werken.

[Bron: Hugging Face Blog](https://huggingface.co/blog/transformers-v5)

### OpenAI schakelt promotie-berichten in ChatGPT uit na gebruikersklachten

**Bedrijf trekt advertentie-achtige app-promoties terug**

OpenAI heeft promotie-berichten in ChatGPT uitgeschakeld nadat gebruikers klaagden over advertenties in de chatbot. Het bedrijf toonde in-app berichten die bedrijven als Peloton en Target promootten. Chief Research Officer Mark Chen bevestigde op X dat OpenAI werkt aan het verbeteren van de gebruikerservaring. De berichten leken op advertenties, hoewel OpenAI niet bevestigde of bedrijven betaalden voor de plaatsingen. Gebruikers reageerden negatief op wat zij zagen als commercialisering van de chatinterface. OpenAI geeft aan de functie te heroverwegen voordat een eventuele herintroductie.

[Bron: The Verge AI](https://www.theverge.com/news/839882/openai-chatgpt-ads-app-promo-messages-turned-off)

## Robotics & Autonomous Vehicles

### Wayve lanceert GAIA-3 wereldmodel voor autonome rijvalidatie

**Generatief model simuleert zeldzame verkeerssituaties voor veiliger testen**

Wayve introduceert GAIA-3, een nieuwe generatie van zijn wereldmodel voor het valideren van zelfrijdende AI. Het systeem simuleert dynamische rijscenario's die te zeldzaam of te gevaarlijk zijn om in de echte wereld te testen. GAIA-3 is groter en capabeler dan voorganger GAIA-2 en specifiek gebouwd voor het evalueren van moderne end-to-end rijsystemen. Huidige testmethoden vertrouwen sterk op gecontroleerde testbanen die de complexiteit van echte verkeerssituaties niet kunnen nabootsen. Generatieve wereldmodellen lossen dit op door AI-modellen te laten leren, plannen en beslissingen nemen in realistische maar veilige gesimuleerde omgevingen. Het model is vanaf nu beschikbaar voor ontwikkelaars die autonome rijsystemen willen valideren.

[Bron: Autonomous Vehicle News](https://www.autonomousvehicleinternational.com/news/ai-sensor-fusion/wayves-gaia-3-generative-world-model-now-available-for-autonomous-driving-validation.html)

## Enterprise & Industry Applications

### OpenAI claimt dat generatieve AI kenniswerkers 40 tot 80 minuten per dag bespaart

**Bedrijfsrapport toont productiviteitswinst bij enterprise-klanten**

OpenAI publiceert een bedrijfsrapport waarin het stelt dat generatieve AI kenniswerkers dagelijks 40 tot 80 minuten bespaart. Het rapport baseert zich op data van enterprise-klanten die OpenAI's tools gebruiken voor verschillende taken. De tijdsbesparing komt voort uit geautomatiseerde e-mail, documentanalyse, code-generatie en onderzoek. OpenAI presenteert deze cijfers als bewijs dat AI-investeringen meetbare productiviteitswinst opleveren voor bedrijven. Het rapport bevat casestudies van bedrijven in verschillende sectoren, van financiën tot technologie. Critici wijzen erop dat OpenAI's eigen onderzoek mogelijk een rooskleuriger beeld schetst dan onafhankelijke studies zouden tonen.

[Bron: The Decoder](https://the-decoder.com/openai-claims-generative-ai-saves-knowledge-workers-40-to-80-minutes-a-day/)

### Tavily presenteert Deep Research: state-of-the-art onderzoekssysteem

**AI-onderzoekstool bereikt nieuwe standaard voor diepgaande analyse**

Tavily lanceert Deep Research, een AI-systeem dat volgens het bedrijf een nieuwe standaard zet voor geautomatiseerd onderzoek. De tool combineert meerdere bronnen, factcheckt informatie en genereert gestructureerde rapporten. Deep Research overtreft bestaande systemen bij het verzamelen en synthetiseren van informatie uit academische papers, nieuwsartikelen en databases. Het systeem hanteert een multi-stap aanpak: het formuleert onderzoeksvragen, verzamelt data, analyseert bevindingen en presenteert conclusies met bronvermelding. Tavily richt zich op professionals die diepgaand onderzoek moeten doen maar tijd willen besparen op het zoeken en filteren van informatie. De tool is beschikbaar via API voor integratie in bestaande workflows.

[Bron: Hugging Face Blog](https://huggingface.co/blog/Tavily/tavily-deep-research)

## Work and Creativity

### 70 procent van creatieven verbergt AI-gebruik uit angst voor stigma

**Anthropic-onderzoek toont spanning tussen productiviteit en sociale acceptatie**

Een nieuw onderzoek van Anthropic onthult dat 70 procent van creatieve professionals hun AI-gebruik verbergt voor collega's uit vrees voor stigmatisering. Ondanks dat deze professionals zelf baat hebben bij AI-tools, vrezen velen voor hun baan en reputatie als bekend wordt dat ze AI gebruiken. Het onderzoek toont een spanning tussen de praktische voordelen - tijdsbesparing, betere resultaten - en sociale druk om volledig menselijk werk te leveren. Veel creatieven gebruiken AI voor brainstormen, eerste concepten en routine-taken, maar presenteren het eindresultaat alsof het volledig handmatig gemaakt is. Deze spanning beïnvloedt hoe snel AI-tools worden geadopteerd in creatieve industrieën en roept vragen op over transparantie en waardering van werk in het AI-tijdperk.

[Bron: The Decoder](https://the-decoder.com/70-of-creative-professionals-hide-ai-use-from-colleagues-due-to-stigma-anthropic-study-finds/)

---

*Generated by [AI News Bot](https://github.com/giftedunicorn/ai-news-bot) - Your AI-powered news assistant*