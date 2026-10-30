# TRD — Utsav AI

| Area | Decision | Why |
|---|---|---|
| UI | Streamlit 1.66 | Fast to build, free hosting, required live URL |
| AI | Google Gemini via `google-genai`, model configurable (`GEMINI_MODEL`), fallback list | GenAI mandatory; model IDs change, so not hard-coded to one |
| Logic | Pure-Python package `utsav/`, frozen dataclasses | Testable without UI, no extra deps |
| PDF | fpdf2 (lazy import) | Small, pure Python |
| Storage | None (session state + 1 h in-memory cache) | Privacy, simplicity |
| Auth | None | No personal data collected |
| Secrets | Streamlit secrets / env var | Never in code or browser |
| Hosting | Streamlit Community Cloud (app) + GitHub Pages (PWA shell) | Free |
| Windows app | PWA shell → PWABuilder → MSIX → Microsoft Store | Same codebase, no Python bundling, key stays server-side |
| CI | GitHub Actions: ruff + pytest | Quality gate on every push |

## Security
Input normalisation & HTML stripping, injection-phrase removal, user data fenced in prompt, JSON output validated and re-cleaned, `unsafe_allow_html` only for constant markup, XSRF on, CSP on the PWA shell, usage stats off.

## Performance
Single AI call with 900-token cap and 20 s timeout; `cache_resource` for client; `cache_data` (1 h, 128 entries) for plans; lazy imports for SDK and PDF; 3 runtime dependencies.

## Trade-offs
Ideas from Gemini can vary between runs (by design); numbers never do. PWA needs internet (offline page shown).

## Worst-case plan
Gemini down → offline ideas. Streamlit app asleep → shell shows wake-up notice. Model retired → set `GEMINI_MODEL` in secrets, no redeploy of code.
