from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
import os
import json
from datetime import datetime
import hashlib

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE"),
        port=int(os.environ.get("MYSQLPORT", 3306))
    )


# Add to your Project model area — new models
class User(BaseModel):
    id: str
    name: str
    email: str
    password: str
    role: str  # admin, salesperson, client

class LoginRequest(BaseModel):
    email: str
    password: str

class PricingItem(BaseModel):
    id: str
    name: str
    size: str
    price: float
    type: str  # wall, roof, end, kit, spline

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

# User endpoints
@app.post("/users")
def create_user(user: User):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)",
        (user.id, user.name, user.email, hash_password(user.password), user.role)
    )
    db.commit()
    cursor.close()
    db.close()
    return {"success": True}

@app.post("/login")
def login(req: LoginRequest):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (req.email, hash_password(req.password))
    )
    user = cursor.fetchone()
    cursor.close()
    db.close()
    if not user:
        return {"error": "Invalid email or password"}
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }

@app.get("/users")
def get_users():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, role FROM users")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows

@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
    db.commit()
    cursor.close()
    db.close()
    return {"success": True}

# Pricing endpoints
@app.get("/pricing")
def get_pricing():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pricing")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows

@app.put("/pricing/{item_id}")
def update_pricing(item_id: str, item: PricingItem):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pricing SET price=%s WHERE id=%s",
        (item.price, item_id)
    )
    db.commit()
    cursor.close()
    db.close()
    return {"success": True}
    
class Project(BaseModel):
    id: str
    name: Optional[str] = None
    prefix: Optional[str] = None
    createdAt: Optional[str] = None
    walls: List[dict] = []
    wallCount: int = 0
    scale: Optional[float] = None
    backgroundImage: Optional[str] = None

@app.put("/projects/{project_id}")
def update_project(project_id: str, project: Project):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE projects SET walls=%s, wallCount=%s WHERE id=%s",
        (json.dumps(project.walls), project.wallCount, project_id)
    )
    db.commit()
    cursor.close()
    db.close()
    return {"success": True}

@app.get("/")
def root():
    return {"status": "SIP Backend Running"}

@app.get("/projects")
def get_projects():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects ORDER BY createdAt DESC")
    rows = cursor.fetchall()
    for row in rows:
        row["walls"] = json.loads(row["walls"])
    cursor.close()
    db.close()
    return rows

@app.post("/projects")
def save_project(project: Project):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO projects (id, name, prefix, createdAt, walls, wallCount) VALUES (%s, %s, %s, %s, %s, %s)",
        (project.id, project.name, project.prefix, project.createdAt, json.dumps(project.walls), project.wallCount)
    )
    db.commit()
    cursor.close()
    db.close()
    return {"success": True}
    
@app.get("/projects/{project_id}")
def get_project(project_id: str):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects WHERE id=%s", (project_id,))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    if not row:
        return {"error": "Not found"}
    row['walls'] = json.loads(row['walls'])
    return row

@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM projects WHERE id=%s", (project_id,))
    db.commit()
    cursor.close()
    db.close()
    return {"success": True}

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str

@app.post("/signup")
def signup(req: SignupRequest):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email=%s", (req.email,))
    existing = cursor.fetchone()
    if existing:
        cursor.close()
        db.close()
        return {"error": "Email already in use"}
    import uuid
    user_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO users (id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)",
        (user_id, req.name, req.email, hash_password(req.password), req.role)
    )
    db.commit()
    cursor.close()
    db.close()
    return {"id": user_id, "name": req.name, "email": req.email, "role": "salesperson"}
