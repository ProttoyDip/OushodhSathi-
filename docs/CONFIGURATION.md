# Configuration

Every setting the API reads, generated from [`backend/.env.example`](../backend/.env.example) by [`backend/scripts/gen_docs.py`](../backend/scripts/gen_docs.py); do not edit by hand.

Put values in `backend/.env` locally (never commit it) and in the Render environment when hosted. With nothing set, everything still runs: `DEMO_MODE=true`, SQLite, fixed templates instead of model wording, keyword search instead of vectors, and simulators for the check-in call and the WhatsApp message.
Settings marked **secret** are keys or tokens: keep them out of the repository, chats and screenshots.

## AI providers

| Setting | Default | What it does |
| --- | --- | --- |
| `NVIDIA_API_KEY` (secret) | unset | NVIDIA API catalog key (nvapi-...), tried first |
| `NVIDIA_MODEL` | unset | e.g. nvidia/nemotron-3-ultra-550b-a55b (lookup + Bangla) |
| `NVIDIA_VISION_MODEL` | unset | e.g. nvidia/nemotron-3.5-super-vl-120b-a12b (photos) |
| `NVIDIA_BASE_URL` | unset | blank = https://integrate.api.nvidia.com/v1 |
| `NVIDIA_ASR_FUNCTION_ID` | unset | Whisper large-v3 on build.nvidia.com: copy the function-id from https://build.nvidia.com/openai/whisper-large-v3/api (blank = voice uses the browser) |
| `NVIDIA_ASR_SERVER` | unset | blank = grpc.nvcf.nvidia.com:443 (the hosted Riva gRPC endpoint) |
| `OPENROUTER_API_KEY` (secret) | unset |  |
| `OPENROUTER_VISION_MODEL` | unset | blank = auto-pick a free image model |
| `OPENROUTER_TEXT_MODEL` | unset | blank = auto-pick a free text model |
| `NARAROUTER_BASE_URL` | unset | e.g. https://router.bynara.id/v1 |
| `NARAROUTER_API_KEY` (secret) | unset |  |
| `NARAROUTER_MODEL` | unset |  |
| `NARAROUTER_VISION_MODEL` | unset | optional: model for photos; "none" = text-only, skip for photos |
| `EXPLAB_BASE_URL` | unset | e.g. https://api.experientiallabs.ai/v1 |
| `EXPLAB_API_KEY` (secret) | unset |  |
| `EXPLAB_MODEL` | unset |  |
| `EXPLAB_VISION_MODEL` | unset | optional: model for photos; "none" = text-only, skip for photos |
| `AGENTROUTER_BASE_URL` | unset | e.g. https://agentrouter.org/v1 |
| `AGENTROUTER_API_KEY` (secret) | unset |  |
| `AGENTROUTER_MODEL` | unset |  |
| `AGENTROUTER_VISION_MODEL` | unset | optional: model for photos; "none" = text-only, skip for photos |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` |  |
| `OLLAMA_MODEL` | `qwen2.5:3b` |  |
| `OLLAMA_VISION_MODEL` | unset | optional: a local vision model (e.g. qwen2.5vl:3b) as the last scan fallback |
| `PERPLEXITY_API_KEY` (secret) | unset |  |
| `PERPLEXITY_EFFORT` | `fast` | Perplexity Agent API tier ("fast" = the old Sonar) |
| `TAVILY_API_KEY` (secret) | unset |  |

## Access, modes and photo privacy

| Setting | Default | What it does |
| --- | --- | --- |
| `REVIEWER_TOKEN` (secret) | unset | shared DEMO reviewer token; works only when DEMO_MODE=true |
| `DEMO_MODE` | `true` | false on the pilot server: personal reviewer logins only, no demo reset |
| `ADMIN_TOKEN` (secret) | unset | creates/revokes reviewer invites and re-issues lost family links (/admin) |
| `PRIVATE_VISION` | unset | blank = on when DEMO_MODE=false: photos only go to VISION_PROVIDERS |
| `VISION_PROVIDERS` | `nvidia,ollama` | providers allowed to see photos when PRIVATE_VISION is on |

## Photo reading

| Setting | Default | What it does |
| --- | --- | --- |
| `OCR_CHECK_DISABLED` | unset | 1 turns off the OCR second reader (uses NVIDIA_API_KEY; app/ocr_check.py) |

## Notifications

| Setting | Default | What it does |
| --- | --- | --- |
| `RESEND_API_KEY` (secret) | unset | optional: family emails ("results ready", weekly report) |
| `NOTIFY_FROM` | unset | e.g. OushodhSathi <hello@your-verified-domain> |
| `PUBLIC_APP_URL` | unset | frontend URL used in emails and invite links |
| `N8N_ALERT_WEBHOOK` | unset | optional: n8n webhook URL for red-flag doctor alerts |

## Daily check-in call

| Setting | Default | What it does |
| --- | --- | --- |
| `CALL_PROVIDER` | unset | simulator (default); a real adapter is added once a provider is chosen |
| `PUBLIC_API_URL` | unset | this API's public URL, for the provider's callback (webhook) address |
| `PHONE_ENCRYPTION_KEY` (secret) | unset | Fernet key (python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())") |
| `AZURE_SPEECH_KEY` (secret) | unset | optional: generate the call prompts with Azure bn-BD voices (backend/scripts/make_call_audio.py) |
| `AZURE_SPEECH_REGION` | unset | e.g. southeastasia |

## Daily WhatsApp check-in

| Setting | Default | What it does |
| --- | --- | --- |
| `WHATSAPP_TOKEN` (secret) | unset | system-user access token (WhatsApp Cloud API) |
| `WHATSAPP_PHONE_NUMBER_ID` | unset | the business phone number ID that sends the messages |
| `WHATSAPP_APP_SECRET` (secret) | unset | app secret, to check X-Hub-Signature-256 on webhooks |
| `WHATSAPP_VERIFY_TOKEN` (secret) | unset | any long random string; enter the same in the app's webhook settings |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | unset | only for backend/scripts/create_whatsapp_template.py |
| `WHATSAPP_TEMPLATE` | unset | optional: approved template name (default oushodh_daily_checkin) |
| `WHATSAPP_API_VERSION` | unset | optional: Graph API version (default v27.0) |

## Sathi (in-app helper)

| Setting | Default | What it does |
| --- | --- | --- |
| `SATHI_INTENT_MODEL` | `off` | escalate-only intent classifier; turn on only after eval/run_intent_eval.py passes (200+ human held-out examples) |
| `EMBEDDINGS_DISABLED` | unset | 1 = never call the embeddings API (Sathi uses keyword search only) |
| `HELP_INDEX_ON_START` | unset | 1 = build Sathi's vector index at start-up if it is empty (needs NVIDIA_API_KEY) |
| `HELP_VECTOR_ACCEPT` | unset | blank = 0.50: cosine at which the vector side alone counts as "in the guide" |

## Web, database and rate limits

| Setting | Default | What it does |
| --- | --- | --- |
| `CORS_ORIGINS` | unset | comma-separated frontend URLs (defaults to localhost:3000) |
| `CORS_ORIGIN_REGEX` | unset | optional, e.g. preview deploy URLs |
| `OUSHODH_DB` | unset | optional SQLite path (default backend/oushodh.db) |
| `DATABASE_URL` | unset | Postgres instead of SQLite, e.g. the Supabase session pooler (see docs/DEPLOY.md) |
| `SCAN_LIMIT_PER_IP` | `10` | photo scans per IP per hour |
| `SCAN_LIMIT_GLOBAL` | `200` | photo scans per day, all visitors |
| `PATIENT_LIMIT_PER_IP` | `5` | new households per IP per hour |
| `WRITE_LIMIT_PER_IP` | `120` | item, check and BP writes per IP per hour |
| `SATHI_LIMIT_PER_IP` | `60` | questions to Sathi per IP per hour |

## Other

| Setting | Default | What it does |
| --- | --- | --- |
| `WEB_LOOKUP` | `tavily` | unknown-brand web lookups, in order; add ",perplexity" for its fallback (paid credits) |

The frontend reads `NEXT_PUBLIC_API_URL` (the API's address; required for a production build), `NEXT_PUBLIC_SITE_URL` and `NEXT_PUBLIC_DEMO_SITE_URL` from `frontend/.env.local` or the Vercel project.
