import datetime
import json
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String, primary_key=True, index=True)
    business_type = Column(String, nullable=True)
    product_category = Column(String, nullable=True)
    target_location = Column(String, nullable=True)
    key_facts = Column(Text, default="{}")  # JSON string
    compliance_status = Column(Text, default="[]")  # JSON string: [{"item": "NIB", "status": "done"}, ...]
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        try:
            facts = json.loads(self.key_facts) if self.key_facts else {}
        except Exception:
            facts = {}

        try:
            compliance = json.loads(self.compliance_status) if self.compliance_status else []
        except Exception:
            compliance = []

        return {
            "user_id": self.user_id,
            "business_type": self.business_type,
            "product_category": self.product_category,
            "target_location": self.target_location,
            "key_facts": facts,
            "compliance_status": compliance,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

# Ensure database directory exists
import os
db_path = settings.DATABASE_URL.replace("sqlite:///", "")
# Handle relative path and absolute path
db_dir = os.path.dirname(db_path)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
