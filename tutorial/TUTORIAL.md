# Build with me: Voice insurance agent (Rasa Skills + Deepgram)

**Audience:** beginners and teams new to Rasa Skills  
**Length:** ~75–90 minutes  
**End state:** a speaking insurance agent (Poly) with full starter-pack parity

This guide is paste-first. Every step points at a complete file under
[`tutorial/snippets/`](snippets/). Prefer copying files over typing.

> The repo already contains the **finished agent**. If anything breaks during
> the live session, stay calm: run `make inspect` on the finished tree,
> or recover with the tags documented in [`PRESENTER.md`](PRESENTER.md) and
> [`TAGS.md`](TAGS.md).

---

## Before you start (5 min)

1. Install [uv](https://docs.astral.sh/uv/)
2. Install dependencies and create your env file:

```bash
make install
make env
```

3. Open `.env` and fill in three keys:

| Variable | Purpose |
|---|---|
| `RASA_LICENSE` | Rasa Pro Developer Edition license |
| `OPENAI_API_KEY` | LLM for routing + conversation |
| `DEEPGRAM_API_KEY` | Speech-to-text **and** text-to-speech |

4. Gate the whole session on one command:

```bash
make verify
```

Do not move on until this prints **all checks passed**. It validates your keys
(including license expiry), the project structure, the demo insurance data, and
live connectivity to OpenAI and Deepgram — and names the exact fix for anything
it finds. Any time something misbehaves later, `make verify` is the first thing
to run.

---

## Step 0 — Scaffold a voice Skills project (8 min)

**Teach:** Maestro projects are files, not flowcharts. Voice is configured once.

Key files:

- [`agent.yml`](../agent.yml) — persona (Poly) + voice flags
- [`integrations.yml`](../integrations.yml) — OpenAI + Inspector with Deepgram ASR/TTS
- [`.env`](../.env.example) — secrets

Paste set: [`snippets/step-00-scaffold/`](snippets/step-00-scaffold/)

```bash
make train
make inspect
```

**Verify:** Inspector opens. Toggle the mic (or type) and say hello. Poly should greet you.

**Talking point:** Inspector defaults to Deepgram for both listening and speaking when `DEEPGRAM_API_KEY` is set.

---

## Step 1 — First skill: FAQ in plain language (8 min)

**Teach:** A skill can be a single `skill.md` + optional `references/`.

Paste set: [`snippets/step-01-faq/`](snippets/step-01-faq/)

Copy into:

- `skills/insurance_faq/skill.md`
- `skills/insurance_faq/references/universal_insurance_faq.md`

```bash
make train
make inspect
```

Try: “Does my homeowners policy cover flood damage?”

**Verify:** Answer comes from FAQ references, short enough to speak aloud.

---

## Step 2 — First tool: view policies (10 min)

**Teach:** Tools are Python functions with `@tool`. They are auto-discovered from
`tools/` (shared) or `skills/<name>/tools.py`.

Paste set: [`snippets/step-02-view-policies/`](snippets/step-02-view-policies/)

Copy:

- `skill.md` → `skills/view_policies/skill.md`
- `insurance.tools.py` → `tools/insurance.py`
- `database.py` → `lib/database.py`
- also ensure `data/source/*.json` seed files are present

Try: “What policies do I have?”

**Verify:** Agent lists Serena’s Car and Homeowner policies with premium and limit.

Demo customer: **Serena Williams** (id `123`)  
Useful policy: Car `009738813`, Homeowner `009738812`

Run `make show-demo-data` any time for policies, claims, and ready-made phrases.

---

## Step 3 — First hard guarantee: tool constraints (8 min)

**Teach:** Progressive control. Soft instructions become runtime guarantees.

In `skills/check_claim_status/skill.md`, `check_claim_status` is invisible until
`session.check_claim_status.claim_number` exists:

```yaml
tool_constraints:
  - check_claim_status:
      requires: session.check_claim_status.claim_number
```

Paste set: [`snippets/step-03-tool-constraints/`](snippets/step-03-tool-constraints/)

**Verify:** Without a claim number, the model cannot call the lookup tool
(it is removed from the schema).

Try: “Check claim CLAIM1236”

---

## Step 4 — File claim showcase (15 min)

**Teach:** Combine levers on one high-stakes skill:

1. `tool_constraints` + `requires_confirmation`
2. Scoped `if:` paragraphs (Car vs Homeowner)
3. Verbatim `utter:` + `responses.yml`
4. One `:::ordered_block` for strict collection order

Paste set: [`snippets/step-04-file-claim/`](snippets/step-04-file-claim/)

Try (voice if possible): “I need to file a claim on my car.”

**Verify:** Recording notice plays, auto-only fields are collected, confirmation
is required before submit, claim number `12345` is returned.

---

## Step 5 — Composition: status + inspection (12 min)

**Teach:** Small skills compose with `@skill.schedule_inspection`.

Paste set: [`snippets/step-05-composition/`](snippets/step-05-composition/)

Try: “What’s the status of CLAIM1236?” then agree to schedule an inspection.

**Verify:** Status skill delegates to `schedule_inspection` when status is `2`.

---

## Step 6 — Remaining insurance skills (fast-forward) (8 min)

For live timing, copy the finished folders rather than rebuilding:

- `skills/human_handoff`
- `skills/goodbye`
- `skills/leave_feedback`
- `skills/intro`
- `skills/view_policies` (if not already pasted)

Or reset to the finished tree:

```bash
git checkout main -- skills tools lib
make train
```

**Verify:** “I want a human”, “Goodbye”, “What can you help with?”

---

## Step 7 — Voice pass with Deepgram (10 min)

Keep Inspector open with the mic enabled.

Suggested spoken script:

1. “Hi Poly”
2. “What policies do I have?”
3. “Check claim CLAIM1234”
4. “I need to file a claim”
5. “Thanks, that’s all”

---

## Step 8 — Flywheel close (5 min)

1. Deliberately break a happy path (skip confirmation wording, change claim details mid-flow)
2. Add one tighter constraint or confirmation utterance
3. Retrain + re-inspect

**Teach:** Conversation-driven development beats guessing at instructions alone.

---

## What you built

| Capability | Skill |
|---|---|
| Greeting / orientation | `intro` + session greeting |
| Policy lookup | `view_policies` |
| Claim status | `check_claim_status` |
| Inspection scheduling | `schedule_inspection` (+ composition) |
| File a claim | `file_claim` |
| FAQ | `insurance_faq` |
| Human handoff | `human_handoff` |
| Goodbye + feedback | `goodbye`, `leave_feedback` |
| Voice | Deepgram ASR + TTS via Inspector |