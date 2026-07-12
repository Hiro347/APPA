import json
import datetime
from sqlalchemy.orm import Session
from db.models import UserProfile, SessionLocal, init_db

# Ensure the database is initialized
init_db()

def get_or_create_profile(db: Session, user_id: str) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(
            user_id=user_id,
            business_type=None,
            product_category=None,
            target_location=None,
            key_facts="{}",
            compliance_status="[]",
            last_updated=datetime.datetime.utcnow()
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def get_profile(user_id: str) -> dict:
    db = SessionLocal()
    try:
        profile = get_or_create_profile(db, user_id)
        return profile.to_dict()
    finally:
        db.close()

def update_profile(user_id: str, entities: dict) -> dict:
    db = SessionLocal()
    try:
        profile = get_or_create_profile(db, user_id)
        
        # Update core fields if present in entities
        if "business_type" in entities and entities["business_type"]:
            profile.business_type = entities["business_type"]
        if "product_category" in entities and entities["product_category"]:
            profile.product_category = entities["product_category"]
        if "target_location" in entities and entities["target_location"]:
            profile.target_location = entities["target_location"]
            
        # Update key_facts dictionary
        current_facts = json.loads(profile.key_facts) if profile.key_facts else {}
        for key in ["capital", "hpp", "competitors", "pricing", "target_market"]:
            if key in entities and entities[key] is not None:
                current_facts[key] = entities[key]
        profile.key_facts = json.dumps(current_facts)
        
        # Update compliance status if specified
        if "compliance_status" in entities and entities["compliance_status"]:
            # entities["compliance_status"] could be: [{"item": "NIB", "status": "done"}]
            # We merge the updates with the existing checklist
            current_status = json.loads(profile.compliance_status) if profile.compliance_status else []
            status_map = {item["item"]: item for item in current_status}
            
            for update in entities["compliance_status"]:
                item_name = update.get("item")
                if item_name:
                    status_map[item_name] = {
                        "item": item_name,
                        "status": update.get("status", "pending"),
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    }
            profile.compliance_status = json.dumps(list(status_map.values()))
            
        profile.last_updated = datetime.datetime.utcnow()
        db.commit()
        db.refresh(profile)
        return profile.to_dict()
    finally:
        db.close()
