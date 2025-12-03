import os
from sqlalchemy import create_engine, Column, Integer, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Message(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Text)
    role = Column(Text)
    content = Column(Text)
    created_at = Column(TIMESTAMP)

Base.metadata.create_all(bind=engine)

def add_message(session_id: str, role: str, content: str):
    db = SessionLocal()
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.close()

def get_history(session_id: str, limit=6):
    db = SessionLocal()
    msgs = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    db.close()
    return list(reversed(
        [{"role": m.role, "content": m.content} for m in msgs]
    ))
