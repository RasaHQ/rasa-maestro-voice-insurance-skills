"""Shared insurance tools available via import_tools."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

from lib.database import (
    CLAIM_STATUS_LABELS,
    Database,
    adjustor_date_from_claim,
    get_customer,
    normalize_incident_date,
    resolve_customer_id,
)


def _customer_id(context: Optional[ToolContext]) -> str:
    if context is None:
        return resolve_customer_id()
    return resolve_customer_id(context.memory.get("customer_id"))


@tool(description="Load the demo customer profile into project memory.")
async def load_customer_profile(context: ToolContext = None) -> ToolResult:
    """Ensure customer_id / name fields are available."""
    customer_id = _customer_id(context)
    db = Database()
    row = get_customer(db, customer_id)
    if not row:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "customer_not_found",
                "customer_id": customer_id,
            }
        )

    cid, first_name, last_name = row
    if context is not None:
        context.memory.set("customer_id", cid)
        context.memory.set("customer_first_name", first_name)
        context.memory.set("customer_last_name", last_name)

    return ToolResult(
        llm_response={
            "ok": True,
            "customer_id": cid,
            "customer_first_name": first_name,
            "customer_last_name": last_name,
            "display_name": f"{first_name} {last_name}",
        }
    )


@tool(description="List the customer's insurance policies with premium and coverage limit.")
async def list_policies(context: ToolContext = None) -> ToolResult:
    customer_id = _customer_id(context)
    db = Database()
    rows = db.run_query(
        """
        SELECT policy_type, policy_num, expiration_date, premium, coverage_limit
        FROM policies WHERE customer_id = ?
        ORDER BY policy_type
        """,
        (customer_id,),
        one_record=False,
    )
    policies = [
        {
            "policy_type": policy_type,
            "policy_num": policy_num,
            "expiration_date": expiration_date,
            "premium": float(premium),
            "coverage_limit": float(coverage_limit),
        }
        for policy_type, policy_num, expiration_date, premium, coverage_limit in rows
        or []
    ]
    return ToolResult(
        llm_response={
            "ok": True,
            "policies": policies,
            "policy_count": len(policies),
            "customer_id": customer_id,
        }
    )


@tool(description="Look up an existing claim by claim number for the current customer.")
async def check_claim_status(claim_number: str, context: ToolContext = None) -> ToolResult:
    """Look up claim status by claim number.

    Args:
        claim_number: The claim id to look up (for example CLAIM1236).
    """
    customer_id = _customer_id(context)
    db = Database()
    normalized = claim_number.strip().upper()
    row = db.run_query(
        """
        SELECT claim_id, policy_num, claim_date, claim_status, inspection_date
        FROM claims
        WHERE customer_id = ? AND upper(claim_id) = ?
        """,
        (customer_id, normalized),
        one_record=True,
    )
    if not row:
        if context is not None:
            context.memory.set("claim_status", "5")
            context.memory.set("claim_status_label", CLAIM_STATUS_LABELS[5])
            context.memory.set("claim_number", normalized)
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "claim_not_found",
                "claim_number": normalized,
                "claim_status": 5,
                "claim_status_label": CLAIM_STATUS_LABELS[5],
                "hint": "Ask the customer to confirm the claim number.",
            }
        )

    claim_id, policy_num, claim_date, claim_status, inspection_date = row
    status_int = int(claim_status)
    adjustor_date = adjustor_date_from_claim(claim_date or "")
    label = CLAIM_STATUS_LABELS.get(status_int, "unknown")

    if context is not None:
        context.memory.set("claim_number", claim_id)
        context.memory.set("claim_status", str(status_int))
        context.memory.set("claim_status_label", label)
        context.memory.set("adjustor_date", adjustor_date)
        context.memory.set("policy_num", policy_num)
        if inspection_date:
            context.memory.set("inspection_date", inspection_date)

    return ToolResult(
        llm_response={
            "ok": True,
            "claim_number": claim_id,
            "policy_num": policy_num,
            "claim_date": claim_date,
            "claim_status": status_int,
            "claim_status_label": label,
            "adjustor_date": adjustor_date,
            "inspection_date": inspection_date,
            "adjustor_contact": {
                "name": "John Doe",
                "phone": "+1 222 333 4567",
            }
            if status_int == 1
            else None,
        }
    )


@tool(description="Normalize an incident date string to MM/DD/YYYY.")
async def normalize_incident_date_tool(
    incident_date: str, context: ToolContext = None
) -> ToolResult:
    """Normalize an incident date.

    Args:
        incident_date: Date as spoken or typed (relative phrases allowed).
    """
    normalized = normalize_incident_date(incident_date)
    if normalized is None:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "invalid_date",
                "hint": "Ask for mm/dd/yyyy, for example 03/25/2026.",
            }
        )
    if context is not None:
        context.memory.set("incident_date", normalized)
    return ToolResult(
        llm_response={"ok": True, "incident_date": normalized}
    )


@tool(description="Submit a new insurance claim for the current customer.")
async def submit_claim(
    policy_num: str,
    policy_name: str,
    claim_description: str,
    incident_date: str,
    additional_claim_info: str,
    incident_time: str = "",
    incident_location: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Submit a claim.

    Args:
        policy_num: Policy number selected for the claim.
        policy_name: Policy type (Car or Homeowner).
        claim_description: What happened.
        incident_date: Incident date in MM/DD/YYYY.
        additional_claim_info: Witnesses, police report, or other notes.
        incident_time: Time of incident (auto claims).
        incident_location: Location of incident (auto claims).
    """
    customer_id = _customer_id(context)
    db = Database()

    policy = db.run_query(
        """
        SELECT policy_num, policy_type FROM policies
        WHERE customer_id = ? AND policy_num = ?
        """,
        (customer_id, policy_num),
        one_record=True,
    )
    if not policy:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "policy_not_found",
                "policy_num": policy_num,
            }
        )

    normalized_date = normalize_incident_date(incident_date) or incident_date
    # Demo parity with the source starter: always return claim number 12345.
    claim_id = "12345"
    today = datetime.now().strftime("%m/%d/%Y")

    db.cursor.execute(
        """
        INSERT OR REPLACE INTO claims
        (customer_id, claim_id, policy_num, claim_date, claim_status, inspection_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (customer_id, f"CLAIM{claim_id}", policy_num, today, 0, None),
    )
    db.commit()

    if context is not None:
        context.memory.set("claim_submitted", True)
        context.memory.set("submitted_claim_number", claim_id)
        context.memory.set("incident_date", normalized_date)

    return ToolResult(
        llm_response={
            "ok": True,
            "claim_number": claim_id,
            "policy_num": policy_num,
            "policy_name": policy_name,
            "claim_description": claim_description,
            "incident_date": normalized_date,
            "incident_time": incident_time,
            "incident_location": incident_location,
            "additional_claim_info": additional_claim_info,
            "message": "An adjuster will be assigned to your claim.",
        }
    )


@tool(description="Schedule an inspection appointment for a claim in inspection status.")
async def schedule_inspection(
    claim_number: str,
    inspection_date: str,
    context: ToolContext = None,
) -> ToolResult:
    """Schedule an inspection.

    Args:
        claim_number: Claim id to update.
        inspection_date: Preferred date and time for the inspection.
    """
    customer_id = _customer_id(context)
    db = Database()
    normalized = claim_number.strip().upper()
    row = db.run_query(
        """
        SELECT claim_id, claim_status FROM claims
        WHERE customer_id = ? AND upper(claim_id) = ?
        """,
        (customer_id, normalized),
        one_record=True,
    )
    if not row:
        return ToolResult(
            llm_response={"ok": False, "error": "claim_not_found", "claim_number": normalized}
        )

    claim_id, claim_status = row
    if int(claim_status) != 2:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "inspection_not_available",
                "claim_number": claim_id,
                "claim_status": int(claim_status),
                "hint": "Inspection scheduling is only available when status is 2.",
            }
        )

    db.cursor.execute(
        "UPDATE claims SET inspection_date = ? WHERE claim_id = ? AND customer_id = ?",
        (inspection_date, claim_id, customer_id),
    )
    db.commit()

    if context is not None:
        context.memory.set("inspection_scheduled", True)
        context.memory.set("inspection_date", inspection_date)
        context.memory.set("claim_number", claim_id)

    return ToolResult(
        llm_response={
            "ok": True,
            "claim_number": claim_id,
            "inspection_date": inspection_date,
        }
    )


@tool(description="Create a human handoff ticket for a live insurance agent.")
async def create_handoff_ticket(reason: str, context: ToolContext = None) -> ToolResult:
    """Create a handoff ticket.

    Args:
        reason: Why the customer wants a human agent.
    """
    ticket_id = f"HO-{datetime.utcnow().strftime('%H%M%S')}"
    if context is not None:
        context.memory.set("handoff_created", True)
        context.memory.set("handoff_ticket_id", ticket_id)
    return ToolResult(
        llm_response={
            "ok": True,
            "ticket_id": ticket_id,
            "reason": reason,
            "eta_minutes": 5,
        }
    )
