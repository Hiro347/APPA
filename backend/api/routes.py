from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from core.agent import handle_chat
from core.profile_manager import get_profile
from data.seed.seed_qdrant import seed as seed_qdrant_db

router = APIRouter()

# --- Request & Response Pydantic Models ---

class ChatHistoryItem(BaseModel):
    role: str = Field(..., description="Role of the sender: 'user' or 'assistant'")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    message: str = Field(..., description="The user's input text message")
    chat_history: Optional[List[ChatHistoryItem]] = Field(default=[], description="Sliding window of the last 10 messages")

class UIComponent(BaseModel):
    ui_type: str = Field(..., description="Type of visual component to render: 'text', 'checklist', 'pricing', 'chart'")
    content: Optional[str] = None
    items: Optional[List[dict]] = None
    hpp: Optional[int] = None
    market_avg: Optional[int] = None
    recommendation: Optional[int] = None
    xAxis: Optional[List[str]] = None
    yAxis: Optional[List[int]] = None
    sources: List[str] = Field(default=[])

class ChatResponse(BaseModel):
    components: List[UIComponent] = Field(..., description="Array of components for Generative UI rendering")
    profile_updated: bool = Field(default=True)

class UserProfileResponse(BaseModel):
    business_type: Optional[str] = None
    product_category: Optional[str] = None
    target_location: Optional[str] = None
    key_facts: dict = Field(default={})
    compliance_status: List[dict] = Field(default=[])


# --- API Routes ---

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Core chat endpoint. Evaluates input, updates SQLite profile, fetches Qdrant RAG + Web Search,
    and returns a structured Generative UI JSON.
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not request.message:
        raise HTTPException(status_code=400, detail="message is required")
        
    try:
        response_data = await handle_chat(request.user_id, request.message)
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def profile_endpoint(user_id: str):
    """
    Read-only profile endpoint for the sidebar status.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    try:
        profile_data = get_profile(user_id)
        # Map DB model fields to response schema
        return {
            "business_type": profile_data.get("business_type"),
            "product_category": profile_data.get("product_category"),
            "target_location": profile_data.get("target_location"),
            "key_facts": profile_data.get("key_facts", {}),
            "compliance_status": profile_data.get("compliance_status", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile retrieval error: {str(e)}")

@router.post("/seed")
async def seed_endpoint(background_tasks: BackgroundTasks):
    """
    Seeding endpoint. Can be triggered via API to load regulatory_rules.json into Qdrant in the background.
    """
    try:
        # Run seeding in background tasks so it does not block the HTTP thread
        background_tasks.add_task(seed_qdrant_db)
        return {"status": "success", "message": "Qdrant seeding has been started in the background."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start seeding: {str(e)}")
