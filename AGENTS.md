# Rasa Maestro project — Poly voice insurance

This directory is a **Rasa Maestro** agent (Skills / calm_v2) that teaches
building a **voice** insurance assistant with **Deepgram** ASR + TTS.

## Layout

- `agent.yml` — identity, persona (Poly), voice flags, rules
- `integrations.yml` — OpenAI LLM + Inspector channel with Deepgram ASR/TTS
- `memory.yml` — project-wide memory (`session.project.*`)
- `responses.yml` — project-wide verbatim responses (greeting override)
- `skills/<name>/` — one skill per folder (`skill.md`, optional `tools/`,
  `memory.yml`, `responses.yml`, `references/`)
- `tools/` — shared `@tool` functions (imported via `import_tools`)
- `lib/` — shared Python helpers (SQLite demo insurance DB)
- `data/source/` — JSON seed data for the demo customer
- `scripts/` — `verify_setup.py` (pre-flight) and `show_demo_data.py`
- `tutorial/` — live-session script and paste-ready snippets

## Build loop

```bash
make install   # uv sync --prerelease=allow
make env       # copy .env.example -> .env, then fill in the keys
make verify    # pre-flight diagnostics (scripts/verify_setup.py)
make train
make inspect   # voice + text Inspector
```

Run `make` alone for the grouped help screen.

## Ground rules

- Reference secrets only as env vars / `.env` — never commit keys
- Do **not** add CALM v1 files (`domain.yml`, `config.yml`, flow YAMLs)
- Keep each skill focused; compose with `@skill.<name>` when needed
- Prefer progressive control: prose → tool constraints → scoped `if:` →
  verbatim `utter:` → ordered blocks only when order is the requirement
- Boolean expressions in skill `if:` use Python `True`/`False`, not YAML
- Only put `description:` on llm_settable (or collect-owned) memory fields
- Makefile may `-include .env` for presence checks — never blanket-`export` it
- Voice instructions must be short sentences suitable for TTS

Docs for authors: see `tutorial/TUTORIAL.md` and `.cursor/rules/rasa-skills.mdc`
