"""Support ticket API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.tools import create_support_ticket, get_user_tickets
from app.auth.dependencies import get_current_admin, get_current_user
from app.database.mongodb import get_collection
from app.schemas.schemas import TicketCreate, TicketResponse, TicketStatus
from app.utils.helpers import utc_now

router = APIRouter(prefix="/tickets", tags=["Support Tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, current_user: dict = Depends(get_current_user)):
    ticket = create_support_ticket(
        user_email=current_user["email"],
        issue=payload.issue,
        category=payload.category or "General",
    )

    await get_collection("support_tickets").insert_one({
        **ticket,
        "user_id": current_user["_id"],
    })

    return TicketResponse(
        ticket_id=ticket["ticket_id"],
        issue=ticket["issue"],
        status=TicketStatus.OPEN,
        created_at=ticket["created_at"],
    )


@router.get("", response_model=List[TicketResponse])
async def list_tickets(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        cursor = get_collection("support_tickets").find().sort("created_at", -1)
        tickets = await cursor.to_list(length=200)
    else:
        tickets = await get_collection("support_tickets").find(
            {"user_id": current_user["_id"]}
        ).sort("created_at", -1).to_list(length=50)

    return [
        TicketResponse(
            ticket_id=t["ticket_id"],
            issue=t["issue"],
            status=TicketStatus(t.get("status", "open")),
            created_at=t["created_at"],
            resolution=t.get("resolution"),
        )
        for t in tickets
    ]
