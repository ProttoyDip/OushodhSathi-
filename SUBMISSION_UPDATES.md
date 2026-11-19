# Submission updates (CloudCamp form)

Replacement text for each submission field, true to the code on branch `features/rag-graph-calls`
(November 2026). Paste each block into its field; every block is under 1,500 characters. Numbers come
from the results files named in brackets, never typed by hand.

---

## Retrieval & RAG

Contextual hybrid retrieval for Sathi, the in-app Bangla guide: every guide entry gets a fixed context header (section, screen, its questions in Bangla and English) before embedding, then keyword search (RapidFuzz) and vector search (NVIDIA nemotron-3.5-embed-1b) are fused with reciprocal rank fusion (k = 60). A safety guard runs first, so medical and emergency questions never reach retrieval; names are removed before anything is embedded. On 79 questions, recall@1: keyword 90%, vector 94%, hybrid 95% (95% CI 88-98%) [eval/help_retrieval_results.json].

Graph RAG for the pharmacist: the case summary model receives only numbered facts from the medicine knowledge graph plus the rule findings, and every sentence must cite a fact id; uncited sentences are deleted, then the usual safety checks run, with the older summary as the fallback.

Agentic multi-step brand lookup: an unknown Bangladeshi brand is searched on medicine sites (Tavily, then Perplexity) and a model must cite a numbered result; the answer stays marked "web unverified".

Remove from the form: Late Chunking and "Naive RAG" (not implemented).

## Vector DB

pgvector on Supabase Postgres: table help_chunks with vector(1024) embeddings and an HNSW index using cosine distance. Re-indexing embeds only chunks whose content hash changed. Locally and in CI (no database, no keys) the same interface stores vectors in SQLite and falls back to keyword search.

## Graph

A medicine knowledge graph built with NetworkX in memory from the app's reference tables only: brands, generics, drug classes, the triple-whammy groups, interactions, AGS Beers rules, kidney-dose rules, anticholinergic scores and WHO AWaRe groups (about 160 nodes). Every edge records the table row it came from. A snapshot is persisted to Postgres (kg_nodes, kg_edges). It is not a graph database: the graph is small enough to rebuild in under a second, and free hosting has no room for Neo4j. The graph explains findings ("Why?" for pharmacists, an MCP tool); it never creates them: a test checks that the rules engine gives identical results with it loaded.

## Agent frameworks notes

Pydantic-AI (backend/app/agent.py) runs the photo-reading agent: typed output, tool calls to match each brand to its generic, and a fallback chain of models. Safety findings never come from an agent: a deterministic rules engine creates every flag, and a pharmacist or doctor confirms each one before the family sees it. An MCP server (mcp/server.py) exposes four read-only tools.

Remove the sentence "No agent framework".

## LLM usage commentary

Every task walks a provider chain, so a rate limit or an outage falls through to the next model: NVIDIA's API first (Nemotron vision for photos, Nemotron text for lookups and wording), then free OpenRouter models that are tested with a one-token call before use, then other routers, then Ollama on the machine. Bangla speech to text uses Whisper large-v3 hosted by NVIDIA. Embeddings use NVIDIA nemotron-3.5-embed-1b (bge-m3 was retired by NVIDIA in August 2026, so the project moved off it). Models never see patient names or phone numbers, and no model decides a safety finding.

## Open-source tools

FastAPI, Pydantic, Pydantic-AI, Next.js, next-intl, Motion, Recharts, Supabase Postgres, pgvector, NetworkX, RapidFuzz, nvidia-riva-client (Whisper via NVIDIA Riva), psycopg, httpx, Pillow, cryptography, scikit-learn (evaluation and the gated missed-dose model), and the Model Context Protocol Python SDK.

## Embeddings / model serving

Embeddings: NVIDIA nemotron-3.5-embed-1b through NVIDIA's API (input type query or passage, 2048 dimensions truncated to 1024 and re-normalised), stored in pgvector. Model serving: hosted APIs (NVIDIA, OpenRouter) with Ollama as the local fallback; the API runs on Render, the frontend on Vercel. Every feature still works with no keys at all: keyword search replaces vectors, and fixed templates replace model wording.

## Evaluation & Quality Measurement

Real-photo strip reading: evaluation in progress. 40 real medicine photos from the team are collected and privacy-checked; 0 are labelled so far, and no accuracy figure is published until at least 25 are labelled. Synthetic benchmark (computer-drawn images, not real-photo accuracy): on 30 images with 45 medicines, brand read 40/45 (89%, 95% CI 76%-95%), expiry 19/25 (76%, 95% CI 57%-88%); on 20 synthetic BP screens, systolic read exactly 100% and diastolic 100%. It also measured overconfidence: 3 of the model's 5 misreads came with confidence of 0.9 or more, so the 0.75 "please check" cut-off flagged only 2 of 5. Sathi safety (83 cases, no model): medical questions to a pharmacist 33/33, emergencies 10/10, rule-breaking refused 5/5. Guide retrieval recall@1: hybrid 95% (95% CI 88%-98%) vs keyword 90%. Handwritten-prescription images for future runs: Badhon D.R. et al., Mendeley Data V2, 2026, doi:10.17632/tg2hm7n2bs.2, CC BY 4.0. All numbers come from results files in eval/.

## Solution description: the voice-call sentence

Replace the voice-call sentence with: "A daily Bangla check-in, by recorded phone call (press 1 taken, 2 not taken, 9 emergency) or by WhatsApp message with buttons, is built and can be tried in the browser simulators; connecting a phone provider and a WhatsApp Business number is the next step." Use "now calls families every day" only after a provider is live and tested.

---

## Claims to confirm or remove yourself

The repository cannot show these. Keep each one only if you can back it up outside the code:

- Graphify, Caveman, Kimi, Lovable, v0, Canvas or other build tools named in the form
- "78% of the UI was built with AI"
- Prompt caching (the code caches model responses in its own database; it does not use provider prompt caching)
- User testing with families (no pilot results exist yet; the pilot file has no real households)
- Late Chunking and "Naive RAG" (not implemented)
- Daily calls to real phones (simulator only until a provider is chosen)
- Any strip-reading accuracy figure (none measured yet)
