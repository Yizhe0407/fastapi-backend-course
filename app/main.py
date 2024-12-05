from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

app = FastAPI()

DATABASE_URL = "sqlite:///./todos.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define Model
class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    due_date= Column(Date, nullable=True)

# Initialize Database's Table
Base.metadata.create_all(bind=engine)

# Validation
class TodoBase(BaseModel):
    title: str
    description: str | None = None
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoResponse(TodoBase):
    id: int

    class Config:
        orm_mode = True

# Database Injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routing
@app.post("/todos/", response_model=TodoResponse)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = Todo(**todo.dict())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.get("/todos/", response_model=list[TodoResponse])
def read_todos(db: Session = Depends(get_db)):
    return db.query(Todo).all()

@app.get("/todos/{todo_id}", response_model=TodoResponse)
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    for key, value in todo.dict().items():
        setattr(db_todo, key, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(db_todo)
    db.commit()
    return {"message": "Todo deleted successfully"}
