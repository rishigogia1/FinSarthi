"""
api/chat/routes.py — Router for chat conversations and multi-agent messages.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter(prefix="/chat", tags=["AI Conversations"])


# Pydantic Schemas
class ConversationResponse(BaseModel):
    id: str
    title: str | None
    workflow_id: str | None = None
    workflow_status: str | None = None
    primary_agent: str | None = None
    supporting_agents: list[str] | dict | None = None
    icon: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreateConversationRequest(BaseModel):
    title: str | None = None


class UpdateConversationRequest(BaseModel):
    title: str


class LaunchWorkflowRequest(BaseModel):
    workflow_type: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class LaunchWorkflowResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[MessageResponse]
    dynamic_chips: list[str]


class CreateMessageRequest(BaseModel):
    content: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[ConversationResponse]:
    """Retrieve all conversations for the authenticated user, ordered by created_at desc."""
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
    )
    result = await db.execute(stmt)
    convs = result.scalars().all()
    return [ConversationResponse.model_validate(c) for c in convs]


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationResponse:
    """Create a new conversation session."""
    conv = Conversation(
        user_id=current_user.id,
        title=payload.title or "New Conversation"
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationResponse.model_validate(conv)


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    payload: UpdateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ConversationResponse:
    """Rename an existing conversation title."""
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    conv.title = payload.title.strip() or "Untitled Conversation"
    await db.commit()
    await db.refresh(conv)
    return ConversationResponse.model_validate(conv)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Permanently delete a conversation session and all associated messages."""
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Delete related messages explicitly
    msg_stmt = delete(Message).where(Message.conversation_id == conversation_id)
    await db.execute(msg_stmt)

    await db.delete(conv)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/workflows/launch", response_model=LaunchWorkflowResponse, status_code=201)
async def launch_workflow(
    payload: LaunchWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> LaunchWorkflowResponse:
    """Launches a guided financial workflow, creating conversation, assembling context & executing initial AI turn."""
    from app.services.workflows.workflow_launcher import WorkflowLauncher
    try:
        conv, messages, dynamic_chips = await WorkflowLauncher.launch(
            db_session=db,
            user=current_user,
            workflow_id=payload.workflow_type
        )
        return LaunchWorkflowResponse(
            conversation=ConversationResponse.model_validate(conv),
            messages=[MessageResponse.model_validate(m) for m in messages],
            dynamic_chips=dynamic_chips
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[MessageResponse]:
    """Retrieve all messages for a specific conversation session."""
    # Verify ownership
    conv_stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    conv_result = await db.execute(conv_stmt)
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def send_message(
    conversation_id: str,
    payload: CreateMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[MessageResponse]:
    """Send a user message and trigger an automated agent response."""
    # Verify conversation ownership
    conv_stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    conv_result = await db.execute(conv_stmt)
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Delegate to the ChatService which handles memory, prompts, and LLM orchestration
    from app.services.chat_service import ChatService
    
    updated_messages = await ChatService.process_message(
        session=db,
        conversation=conv,
        user=current_user,
        content=payload.content
    )

    return [MessageResponse.model_validate(m) for m in updated_messages]

