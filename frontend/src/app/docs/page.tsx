import { ExternalLink } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { Wordmark } from "@/components/BrandMark";
import { EvalPanel, LiveStatus, PilotPanel } from "@/components/docs/LivePanels";

export const metadata: Metadata = { title: "Docs — pitch, whitepaper, system status" };

const TOC = [
  ["problem", "Problem"], ["solution", "Solution"], ["architecture", "Architecture"], ["ai", "AI approach"],
  ["safety", "Safety & privacy"], ["evaluation", "Evaluation"], ["status", "Live system status"],
  ["roadmap", "Roadmap"], ["team", "Team"],
];

const AI_ROWS = [
  ["Read photos", "Free OpenRouter vision model (auto-picked: price 0, image input, largest context), then NARAROUTER → EXPLAB → AGENTROUTER", "Cut strips, glare and Bangla text need a vision model; free models keep it affordable", "Typed Pydantic output, one retry, then needs-review; confidence < 0.75 always shown for a human check"],
  ["Unknown brand → generic", "Tavily search on medex.com.bd, arogga.com, medeasy.health + text model; Perplexity Sonar fallback", "Bangladesh has tens of thousands of brands; the seed table cannot hold them all", "Model must cite a numbered result; stored as web_unverified with the source URL; failures never cached"],
  ["Bangla explanation", "Ollama qwen2.5:3b locally first, cloud fallback", "Private and free when run locally", "Only for confirmed flags; dose and stop-word filter; fixed template fallback; fixed safety sentence"],
  ["Safety findings", "No model. Deterministic rules in backend/app/rules.py", "Judgement must be repeatable and auditable", "Pure functions with tests; a clinician confirms every flag"],
];

export default function Docs() {
  return (
    <div lang="en" className="min-h-dvh">
      <nav className="mx-auto flex max-w-[1200px] items-center justify-between px-5 py-4 sm:px-8">
        <Link href="/" aria-label="OushodhSathi home"><Wordmark /></Link>
        <Link href="/p/1" className="inline-flex h-11 items-center rounded-chip border border-rule px-4 text-[15px] font-medium">Open the demo</Link>
      </nav>

      <div className="mx-auto grid max-w-[1200px] grid-cols-[minmax(0,1fr)] gap-10 px-5 pb-24 pt-6 sm:px-8 lg:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="hidden lg:block">
          <nav aria-label="On this page" className="sticky top-6">
            <ol className="grid gap-0.5 border-l border-rule text-[15px]">
              {TOC.map(([id, label]) => (
                <li key={id}><a href={`#${id}`} className="block py-1.5 pl-4 text-ink-soft hover:text-ink">{label}</a></li>
              ))}
            </ol>
          </nav>
        </aside>

        <article className="min-w-0 max-w-[72ch] text-[17px] leading-relaxed text-ink [&_h2]:mt-16 [&_h2]:scroll-mt-6 [&_h2]:font-display [&_h2]:text-[40px] [&_h2]:leading-none [&_h3]:mt-8 [&_h3]:text-lg [&_h3]:font-semibold [&_p]:mt-4">
          <h1 className="font-display text-[clamp(44px,6vw,72px)] leading-[1.0]">OushodhSathi, in depth</h1>
          <p lang="bn" className="!mt-3 font-bn-display text-[24px] text-ink-soft">ওষুধসাথী — পিচ, হোয়াইটপেপার ও সিস্টেম ড্যাশবোর্ড</p>
          <p className="text-lg text-ink-soft">
            The live pitch, technical whitepaper and system dashboard for the International AI Builders Congress 2026
            (HealthSphere AI → ChronicCare AI). Every number on this page is either cited, read live from the running
            system, or labelled as demo data.
          </p>

          <h2 id="problem">Problem</h2>
          <p>
            An elderly patient with high blood pressure or diabetes in Bangladesh often collects medicines from three
            places: a hospital outpatient doctor, a village doctor, and the local drug shop. Each sees only their own
            prescription. The same molecule is sold under many brand names, so a family cannot tell that{" "}
            <strong>Napa</strong> and <strong>Ace</strong> are both paracetamol, or that two doctors have each started
            amlodipine.
          </p>
          <ul className="mt-4 grid gap-3 pl-5 [list-style:disc]">
            <li>Hypertension is now the most common illness in Bangladesh, at 78.28 per 1,000 people (BBS Health and Morbidity Status Survey 2025, as reported by <a className="underline" href="https://www.bssnews.net/others/337437">BSS</a> and <a className="underline" href="https://www.thedailystar.net/health/disease/news/hypertension-most-common-illness-country-4047686">The Daily Star</a>).</li>
            <li>Only 11% of people with hypertension had their blood pressure controlled below 140/90, a background figure in the <a className="underline" href="https://heart.bmj.com/content/heartjnl/early/2024/07/16/heartjnl-2024-324253.full.pdf">WHO-HEARTS evaluation in Bangladesh (Heart, 2024)</a>.</li>
            <li>In a small 2011 study of 35 geriatric outpatients at a private hospital, 69% were prescribed five or more medicines (<a className="underline" href="https://www.academia.edu/111376182/Trends_of_prescribing_for_out_door_geriatric_patients_in_a_private_hospital_of_Bangladesh">Trends of prescribing for out-door geriatric patients</a>).</li>
          </ul>

          <h2 id="solution">Solution</h2>
          <p>
            A family member photographs every strip, box and prescription. A vision model reads the photos into a typed
            list; each brand is mapped to its generic; a deterministic rules engine flags duplicates, same-class pairs,
            interactions, drugs risky after 65 (AGS Beers Criteria) and expired strips; a pharmacist or doctor confirms
            every flag; and only then does the family see a plain-Bangla explanation, a weekly report and a printable
            medicine passport with a QR code.
          </p>

          <h2 id="architecture">Architecture</h2>
          <ArchitectureDiagram />

          <h2 id="ai">AI approach</h2>
          <p>
            One router (<code className="font-mono text-[15px]">backend/app/llm_router.py</code>) talks to every model through
            OpenAI-compatible APIs, falls through on 429, 5xx and timeouts, and caches every response in SQLite by a
            SHA-256 of task, model and messages. The shelf agent is built with Pydantic-AI and may call three tools:
            match_brand, lookup_unknown_brand and a read-only check_medicines. It cannot write flags.
          </p>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse text-left text-[15px] leading-snug">
              <thead>
                <tr className="border-b-2 border-ink">
                  {["Task", "Model / provider", "Why", "Guardrail"].map((h) => <th key={h} className="py-2 pr-4 font-semibold">{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {AI_ROWS.map((r) => (
                  <tr key={r[0]} className="border-b border-rule align-top">
                    {r.map((c, i) => <td key={i} className={i === 0 ? "py-3 pr-4 font-semibold" : "py-3 pr-4 text-ink-soft"}>{c}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>
            Prompts are versioned files in <code className="font-mono text-[15px]">backend/app/prompts/</code>{" "}
            (extract_strip.v1, brand_lookup.v1, explain_bn.v1). Changing a prompt means a new version file and a new eval run.
          </p>

          <h2 id="safety">Safety &amp; privacy</h2>
          <ol className="mt-4 grid gap-3 pl-5 [list-style:decimal]">
            <li>Safety flags come only from the deterministic rules engine. Models never create, remove or change the severity of a flag.</li>
            <li>Flags start as pending review. The family view of the API returns only confirmed flags, and a test enforces it.</li>
            <li>No text tells a patient to stop, start or change a medicine or a dose.</li>
            <li>Readings below 0.75 confidence and web-found brand matches are always marked for human confirmation.</li>
            <li>Patient names and phone numbers are never sent to a model, only medicine photos and medicine names.</li>
            <li>Photos are processed in memory and not stored after extraction.</li>
          </ol>
          <p>
            These follow the data-minimisation and purpose-limitation principles of Bangladesh&rsquo;s Personal Data
            Protection Ordinance 2025 (PDPO). OushodhSathi is a research prototype, not a medical device, and makes no
            compliance claim.
          </p>

          <h2 id="evaluation">Evaluation</h2>
          <p>Extraction accuracy on our own labelled photos of real Bangladeshi strips (cut strips, Bangla text, blur):</p>
          <div className="mt-5"><EvalPanel /></div>
          <p>The rules engine, API safety gate, router fallback and explanation guard are covered by the pytest suite; the live count is in the status table below.</p>
          <h3>Pilot</h3>
          <p>What we find in real homes, reported as proportions with 95% Wilson score intervals, which stay honest at small sample sizes:</p>
          <div className="mt-5"><PilotPanel /></div>

          <h2 id="status">Live system status</h2>
          <div className="mt-5"><LiveStatus /></div>

          <h2 id="roadmap">Roadmap</h2>
          <ol className="mt-4 grid gap-3 pl-5 [list-style:decimal]">
            <li>A pharmacist-verified brand table (replace the demo seed with a licensed Bangladeshi drug database).</li>
            <li>Full DDInter 2.0 interaction import, reviewed for medicines common in Bangladesh.</li>
            <li>Partner pharmacies as scan points for families without a smartphone.</li>
            <li>Bangla voice check-ins for blood pressure and doses.</li>
            <li>A pilot with families, with results published here only once they are real.</li>
          </ol>

          <h2 id="team">Team</h2>
          <p className="text-ink-soft">[Team names, roles and mentor to be added.]</p>
          <p className="!mt-10 border-t border-rule pt-6 text-[15px] text-ink-soft">
            OushodhSathi is a research prototype, not a medical device. It does not give medical advice. All findings must
            be confirmed by a registered pharmacist or doctor. Demo data is invented.{" "}
            <Link href="/" className="inline-flex items-center gap-1 underline">Back to the overview <ExternalLink aria-hidden size={13} /></Link>
          </p>
        </article>
      </div>
    </div>
  );
}

function Box({ title, sub, tone = "plain" }: { title: string; sub?: string; tone?: "plain" | "ink" | "teal" | "foil" }) {
  const cls = {
    plain: "border-rule-strong bg-paper-raised text-ink",
    ink: "border-ink bg-ink text-paper",
    teal: "border-teal bg-teal text-on-teal",
    foil: "foil border-foil-lo text-ink",
  }[tone];
  return (
    <div className={`rounded-card border px-3 py-2.5 text-center ${cls}`}>
      <p className="text-[15px] font-semibold leading-tight">{title}</p>
      {sub && <p className="mt-0.5 text-[13px] leading-snug opacity-80">{sub}</p>}
    </div>
  );
}

function Down({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-1.5 text-[13px] text-ink-faint" aria-hidden>
      <svg width="12" height="22" viewBox="0 0 12 22"><path d="M6 0v19M1 14l5 6 5-6" fill="none" stroke="var(--rule-strong)" strokeWidth="1.5" /></svg>
      {label}
    </div>
  );
}

function ArchitectureDiagram() {
  return (
    <figure className="mt-6 rounded-card border border-rule bg-paper-sunk/50 p-5">
      <div className="mx-auto grid max-w-[620px]">
        <Box title="Next.js frontend" sub="family app (Bangla) · reviewer dashboard · passport · /docs" />
        <Down label="HTTPS, JSON" />
        <Box title="FastAPI" sub="family view returns confirmed flags only" />
        <Down />
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="grid content-start">
            <Box tone="foil" title="Shelf agent" sub="Pydantic-AI, typed output" />
            <Down />
            <Box tone="foil" title="LLM router" sub="cache + fall-through" />
            <Down />
            <Box title="Providers" sub="OpenRouter → NARAROUTER → EXPLAB → AGENTROUTER → Ollama" />
          </div>
          <div className="grid content-start">
            <Box title="Brand matcher" sub="exact → fuzzy ≥ 88 → web lookup (Tavily / Perplexity, unverified)" />
            <Down label="confirmed items" />
            <Box tone="ink" title="Rules engine" sub="deterministic, no AI" />
          </div>
          <div className="grid content-start">
            <Box title="SQLite" sub="items, flags, reviews, cache" />
            <Down label="pending flags" />
            <Box tone="teal" title="Clinician review gate" sub="confirm / dismiss + note" />
            <Down label="confirmed only" />
            <Box title="Family view + passport" sub="Bangla explanation, QR" />
          </div>
        </div>
      </div>
      <figcaption className="mt-4 text-[13px] text-ink-faint">
        Silver: AI perception. Ink: deterministic judgement. Teal: human judgement. The MCP server and n8n automations call the same backend modules, read-only.
      </figcaption>
    </figure>
  );
}
