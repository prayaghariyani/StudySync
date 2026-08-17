"""
Convenience launcher: `python run.py`

Equivalent to running:
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
but as a plain script so it also works from IDEs that just hit "Run".
"""
import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST") or ("0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
    reload = os.getenv("UVICORN_RELOAD", "false" if os.getenv("PORT") else "true").lower() == "true"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
