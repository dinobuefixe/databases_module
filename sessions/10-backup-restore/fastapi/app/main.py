from fastapi import FastAPI, HTTPException

from app.db import DB_NAME, row_counts
from scripts.common import BACKUP_DIR, PREFIX, RESTORE_DB

app = FastAPI(title="Session 10: backup and restore")


def own_database(name: str) -> None:
    # The API only reads this project's databases, never the others on the server.
    if not name.startswith(PREFIX):
        raise HTTPException(400, f"only {PREFIX}* databases")


@app.get("/counts")
def counts(db: str = DB_NAME):
    """Row counts of every table, the same numbers scripts.verify compares."""
    own_database(db)
    return {"database": db, "tables": row_counts(db)}


@app.get("/backups")
def backups():
    """The dumps in backups/, newest first."""
    files = sorted(BACKUP_DIR.glob("*.dump"), reverse=True) if BACKUP_DIR.exists() else []
    return [{"file": f.name, "mb": round(f.stat().st_size / 1e6, 1)} for f in files]


@app.get("/compare")
def compare(first: str = DB_NAME, second: str = RESTORE_DB):
    """The tables whose row counts differ between two databases."""
    own_database(first)
    own_database(second)
    a, b = row_counts(first), row_counts(second)
    diff = {t: {first: a.get(t), second: b.get(t)} for t in sorted(a.keys() | b.keys()) if a.get(t) != b.get(t)}
    return {"match": not diff, "differences": diff}
