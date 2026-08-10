---
name: Schedule Inspection
description: >
  Schedule an inspection appointment for a claim that is ready for inspection.
  Activate when the customer wants to book or propose inspection times.
import_tools:
  - load_customer_profile
  - schedule_inspection
tool_constraints:
  - schedule_inspection:
      requires: session.schedule_inspection.claim_number
      requires_confirmation:
        enabled: true
        utter_for_confirmation: utter_confirm_inspection
        utter_on_user_denial: utter_inspection_cancelled
      on_success: utter_inspection_scheduled
---

Help the customer schedule a claim inspection. Do not invent claim numbers.

If customer_id is missing, call `@tool.load_customer_profile`.

if: not session.schedule_inspection.claim_number
Ask which claim to schedule. Prefer the claim number already discussed.
Set `claim_number`.

Ask which date and time they prefer. Set `inspection_date`.

When ready, call `@tool.schedule_inspection` with claim_number and
inspection_date. Confirm in one short spoken sentence.
