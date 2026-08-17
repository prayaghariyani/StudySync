"""
Convenience launcher: `python run.py`

Equivalent to running:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
but as a plain script so it also works from IDEs that just hit "Run".
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
