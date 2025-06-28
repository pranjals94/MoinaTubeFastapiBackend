cd "$(dirname "$0")"
source venv/bin/activate
uvicorn test:app --host=0.0.0.0 --port=8001  --workers 2