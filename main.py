from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME")
    )

class Project(BaseModel):
    id: str
    name: str
    prefix: str
    createdAt: str
    walls: List[dict] = []
    wallCount: int = 0

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

@app.put("/projects/{project_id}")
def update_project(project_id: str, project: Project):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE projects SET name=%s, walls=%s, wallCount=%s WHERE id=%s",
        (project.name, json.dumps(project.walls), project.wallCount, project_id)
    )
    db.commit()
    cursor.close()
    db.close()
    return {"success": True}

@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM projects WHERE id=%s", (project_id,))
    db.commit()
    cursor.close()
    db.close()
    return {"success": True}
