from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

app = FastAPI()
origins = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    
    allow_headers=["*"],  
)

DB_URL = f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
engine = create_engine(DB_URL)
Base = declarative_base()
# Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(255))
    timestamp = Column(DateTime)

@app.post("/submit")
async def submit(request: Request):
    data = await request.json()
    content = data.get("content", "")
    db = SessionLocal()
    msg = Message(content=content, timestamp=datetime.now())
    db.add(msg)
    db.commit()
    db.close()
    return {"status": "saved"}
