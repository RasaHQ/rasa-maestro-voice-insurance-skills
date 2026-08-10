# Poly — Voice Insurance with Rasa Maestro

A production-style **voice insurance agent** built with the new Rasa **Skills / Maestro** architecture and **Deepgram** for speech-to-text and text-to-speech.

Poly can file auto and homeowners claims, check claim status, view policies, answer insurance questions, schedule inspections, and hand conversations off to a human — all through voice or text.

This repository is designed to be useful in two ways:

1. **Run the finished agent immediately**
2. **Build it yourself step by step** using the live-session tutorial in [`tutorial/TUTORIAL.md`](tutorial/TUTORIAL.md)

> **Demo customer:** Serena Williams (id `123`)  
> A seeded SQLite insurance environment is included under `data/source/`, so you can explore the complete agent without connecting to a real policy system.

---

## What Poly can do

| Skill | Capability |
| --- | --- |
| `view_policies` | List policies with premium and coverage limit |
| `check_claim_status` | Look up claim progress by claim number |
| `schedule_inspection` | Request an inspection appointment |
| `file_claim` | File an auto or homeowners claim (progressive-control showcase) |
| `insurance_faq` | Answer common insurance questions from reference material |
| `human_handoff` | Create a ticket for a live insurance agent |
| `intro` | Introduce Poly and orient the customer |
| `goodbye` | Close the conversation gracefully |
| `leave_feedback` | Collect a quick thumbs-up / thumbs-down rating |

`check_claim_status` also demonstrates **skill composition**: when a claim is ready for inspection, Poly can invoke `schedule_inspection` as part of the journey.

---

## Quick start

```bash
make install
make env          # creates .env from .env.example — then fill in the three keys
make verify       # pre-flight: keys, project, demo data, connectivity
make train
make inspect      # voice + text via Rasa Inspector (Deepgram)
```

Required secrets in `.env` (never commit this file):

| Variable | Purpose |
| --- | --- |
| `RASA_LICENSE` | Rasa Pro Developer Edition license |
| `OPENAI_API_KEY` | LLM for routing + conversation |
| `DEEPGRAM_API_KEY` | Speech-to-text **and** text-to-speech |

Run `make` alone for the full grouped help screen.

---

## Architecture

```text
                         ┌─────────────────────┐
                         │       Customer      │
                         │   voice or text     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Rasa Inspector     │
                         │                     │
                         │ Deepgram ASR / TTS  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Rasa Maestro     │
                         │                     │
                         │ skill selection     │
                         │ memory + control    │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
             ┌────────────┐  ┌────────────┐  ┌─────────────┐
             │   Skills   │  │   Tools    │  │ Insurance   │
             │            │  │ insurance  │  │ FAQ refs    │
             └────────────┘  └─────┬──────┘  └─────────────┘
                                   │
                                   ▼
                            ┌────────────┐
                            │ SQLite demo│
                            │ data/source│
                            └────────────┘
```

---

## Progressive control

Instead of one giant prompt, Poly uses focused skills with explicit control over:

* which tools are available
* when tools become available (`tool_constraints.requires`)
* when user confirmation is mandatory
* which instructions enter the model context (`if:`)
* which steps must happen in a strict order (`:::ordered_block`)
* which responses must use exact wording (`utter:` / `responses.yml`)

The **file claim** skill is the showcase that combines all of those levers.

---

## Project layout

| Path | Purpose |
| --- | --- |
| `agent.yml` | Identity, persona (Poly), voice flags, rules |
| `integrations.yml` | OpenAI LLM + Inspector Deepgram ASR/TTS |
| `memory.yml` | Project-wide session memory |
| `responses.yml` | Project-wide verbatim responses |
| `skills/` | One folder per skill |
| `tools/insurance.py` | Shared `@tool` functions |
| `lib/database.py` | SQLite demo backend |
| `data/source/` | JSON seed data for Serena’s policies and claims |
| `scripts/verify_setup.py` | Pre-flight diagnostics |
| `scripts/show_demo_data.py` | Presenter cheat sheet |
| `tutorial/` | Live-session guide + paste-ready snippets |

This is a **Maestro / Skills (`calm_v2`)** project. Do **not** add CALM v1 files
(`config.yml`, `domain.yml`, flow YAMLs under `data/`).

---

## Demo data

```bash
make show-demo-data
```

Useful utterances:

- “What policies do I have?”
- “Check the status of claim CLAIM1236”
- “I need to file a claim on my car”
- “Does my homeowners policy cover flood damage?”

Reset the SQLite demo DB with `make reset-db`.

---

## Build-with-me tutorial

See [`tutorial/TUTORIAL.md`](tutorial/TUTORIAL.md) for the 75–90 minute paste-first
walkthrough and [`tutorial/TAGS.md`](tutorial/TAGS.md).

Chapter list:

```bash
make tutorial
```

---

## Make targets

| Target | Purpose |
| --- | --- |
| `make install` | `uv sync --prerelease=allow` |
| `make env` | Create `.env` from `.env.example` (never overwrites) |
| `make verify` | Full pre-flight diagnostics |
| `make validate` | Fast skill/memory/tool validation |
| `make train` | Package the agent model |
| `make inspect` | Voice + text Inspector |
| `make run` | API server on port 5005 |
| `make show-demo-data` | Print Serena’s policies and claims |
| `make reset-db` | Reseed `data/insurance.db` |
| `make tutorial` | Print chapter / snippet paths |
| `make clean` | Remove models, caches, demo db |
| `make clean-all` | Also remove `.venv` |

---

## Coding agents

See [`AGENTS.md`](AGENTS.md) and [`.cursor/rules/rasa-skills.mdc`](.cursor/rules/rasa-skills.mdc).

Always start with `make verify` before changing skills or tools.
