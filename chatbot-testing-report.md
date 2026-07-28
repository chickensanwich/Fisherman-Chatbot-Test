# Fisherman Chatbot — How It Works & Test Results

*Prepared 2026-07-28. Tests run against the live deployment at fisherman-chatbot.onrender.com.*

## 1. How the chatbot works

Each message sent to `/chat` goes through this pipeline:

1. **Language detection.** Bengali is detected directly from its Unicode script (fast and 100% reliable). Everything else goes through `langdetect`, which defaults to Indonesian whenever it isn't confident — Indonesian is the primary market, English is secondary, Bengali is a legacy option.
2. **Translation to English (if needed).** Indonesian/Bengali messages are machine-translated to English for the answer-generation step. This runs concurrently with step 3, not after it.
3. **Keyword extraction.** An LLM call reads the message and extracts candidate entities (fish, gear, rituals, social roles, beliefs, etc. — an open-ended list, not a fixed vocabulary).
4. **Entity resolution against the live graph.** The system fetches the actual entity names currently in the knowledge graph and, only if the extracted keywords don't already match one directly, asks a second LLM call to bridge local/foreign terms (e.g. "punggawa") to whatever the graph actually calls that entity (e.g. "Patrons"). This step exists specifically because the graph is populated by a separate, external document-ingestion pipeline this app doesn't control — entity names in it are whatever phrase that pipeline extracted, in whatever language, so a static translation list can't keep up.
5. **Graph fact retrieval.** A Cypher query walks 1–2 hops out from the matched entity and collects the facts, explicitly excluding the ingestion pipeline's internal bookkeeping relationships (`HAS_CHUNK`, `MENTIONS`) so only real facts reach the model.
6. **Answer generation.** A final LLM call answers strictly from the retrieved facts (explicitly instructed not to guess or hallucinate), with both the translated *and* original untranslated message included, plus a note confirming which graph entities are relevant — this bridges cases where translation mangled a specific term.
7. **Translation back (if needed), save, respond.**

If no facts are found at any point, the chatbot returns a fixed "I don't have that information" reply in the user's language rather than guessing.

## 2. What's actually in the knowledge base right now

This is worth stating plainly, because it isn't what the system prompt's framing (fish/bait/gear/location) would suggest: **the graph currently contains no generic fishing data (no fish species, bait, or gear facts).** Everything in it comes from three ingested ethnographic documents about **traditional Indonesian fishing communities**:

- *Patorani* flying-fish-roe fishing (South Sulawesi) — rituals, taboos, timing, social roles
- Local ecological knowledge and fishing practices on Barrang Lompo Island
- Livelihoods of ornamental coral fishermen in South Sulawesi — patron-client (*punggawa*) dynamics

93 distinct entities were found across categories: Ritual, Rule/Taboo, Belief, Role, Group, Time, Season, Policy, Practice, Resource, Skill, System. All testing below was designed around this actual content, not the generic fishing facts the prompt implies.

## 3. Test methodology

27 questions were sent to the live `/chat` endpoint: matched English/Indonesian pairs, in four styles —
- **Direct** ("What is Apparuru?") — names the entity explicitly
- **Indirect** ("What ritual is performed before a boat departs?") — describes it without naming it
- **Compound** — asks it to synthesize multiple linked facts
- **Trap** — asks about generic fishing content (bait, net size) that does **not** exist in the graph, to check for hallucination

## 4. Results

| Category | Result |
|---|---|
| Direct named-entity questions (Apparuru, Barzanji, kasipalli, pamali, sesajen, beliefs) | **10/10 correct**, in both languages |
| Compound/multi-hop synthesis questions | **2/2 correct** — genuinely strong; correctly linked ritual + timing + taboo into one coherent answer in both languages |
| Trap questions (bait, net size — not in graph) | **3/3 correctly declined** — no hallucination |
| Indirect/descriptive questions (no entity named) | **0/4 answered** — consistently failed in both languages, despite the underlying facts existing in the graph |
| "punggawa" specifically | **Inconsistent** — succeeded once (via alias resolution to "Patrons"), failed 2/3 other times, in both languages |
| Response time | 4–18s typical; one compound question took 45s (longer synthesis, not an error) |

## 5. Key findings

**Strength — direct questions and complex reasoning both work well.** Naming the thing you want ("What is kasipalli?") is highly reliable, and the model handles genuine multi-hop synthesis (connecting a ritual, its timing, and a taboo into one answer) impressively well in both languages.

**Strength — no hallucination.** Every trap question about content that isn't in the graph was correctly declined rather than invented, in both languages, every time.

**Weakness — indirect/descriptive phrasing has low recall.** "What are fishermen forbidden from bringing on board?" fails even though the exact facts (no tombstones, no black glutinous rice, no mortar) exist under "kasipalli" — because nothing in that phrasing names an extractable entity for the retrieval step to latch onto. This is a real limitation: the system is keyword/entity-driven, not full semantic search, so a user has to get reasonably close to the graph's own vocabulary.

**Data limitation, not a code bug — "punggawa" is a fragmented entity.** Investigated directly: the graph has a `Role: punggawa` node with **zero relationships**, and a separate `Group: Patrons` node that **does** have the connected belief fact. These are two disconnected nodes for what's conceptually the same social role. Asking about "Patrons" works; asking about "punggawa" sometimes works (when resolution maps it to "Patrons") and sometimes doesn't (when it matches the empty node directly instead). This traces back to how the external ingestion pipeline extracted entities, not to anything in this app's retrieval code.

## 6. Bottom line

The chatbot reliably answers direct questions about content that's actually in its knowledge base, synthesizes multi-fact answers well, and correctly refuses to make things up — in both English and Indonesian equally. Its main soft spot is indirect/descriptive questions that don't name an entity, and it can give inconsistent answers for the small number of entities that the (externally-managed) ingestion pipeline split across multiple disconnected graph nodes.
