#!/bin/sh
# The API and the worker share one container.
python3 worker.py &
exec uvicorn app:app --host 0.0.0.0 --port 8000
