# OushodhSathi MCP server

A small [Model Context Protocol](https://modelcontextprotocol.io) server (stdio) that lets an
MCP client such as Claude Desktop use OushodhSathi's medicine logic directly. Built with the
official `mcp` Python SDK (v2, `MCPServer`).

| Tool | What it does | Writes anything? |
| --- | --- | --- |
| `match_brand(brand)` | Maps a Bangladeshi brand (e.g. "Napa 500 mg") to its generic and class: exact, then strict fuzzy. "Napa Extra" is never forced onto "Napa". | No |
| `lookup_unknown_brand(brand, strength)` | Searches medex.com.bd, arogga.com and medeasy.health (Tavily, then Perplexity). Must cite a source; always marked `web_unverified`. Needs a key in `backend/.env`. | No (caches successful lookups only) |
| `check_medicines(items, age, egfr?, kidney_test_date?)` | Runs the deterministic safety rules on a list and returns findings marked "pending clinician review". With `egfr` (and the test date, YYYY-MM-DD) it also checks kidney dosing and an overdue kidney test. | No — it never creates flags |
| `explain_flag_path(generics)` | Returns numbered facts from the medicine knowledge graph (`backend/app/medgraph.py`) around the given generics: class, triple-whammy group, interactions, Beers, kidney, anticholinergic and AWaRe links, each with the table row it came from. | No — it explains links and never creates findings |

All four tools are annotated read-only. Findings returned here are not for patients: in the
product, every finding is confirmed by a pharmacist or doctor first.

## Run

The server uses the backend's virtual environment (the `mcp` package is in `backend/requirements.txt`):

```bash
backend/.venv/Scripts/python mcp/server.py     # Windows
backend/.venv/bin/python mcp/server.py         # macOS / Linux
```

## Claude Desktop

Add this to `claude_desktop_config.json` (Settings → Developer → Edit config), with your own
absolute paths:

```json
{
  "mcpServers": {
    "oushodhsathi": {
      "command": "C:\\path\\to\\OushodhSathi\\backend\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\OushodhSathi\\mcp\\server.py"],
      "env": { "PYTHONIOENCODING": "utf-8" }
    }
  }
}
```

On macOS / Linux use `.../backend/.venv/bin/python` and `.../mcp/server.py`.

## Example (real output from a test run)

`check_medicines` with Napa (drug shop), Ace (village doctor), Rivotril and Tryptin (expiry
2026-09), age 68, returns a red `DUPLICATE_GENERIC` (Napa + Ace, both paracetamol), a red
`EXPIRED` (Tryptin), a red `INTERACTION` (Rivotril + Tryptin, major), amber `BEERS_65`
findings and an amber `ANTICHOLINERGIC_BURDEN` (Tryptin, score 3) — each with `"status": "pending clinician review — not for patients"`.
