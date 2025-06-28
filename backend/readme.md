// install fastapi and uvicorn
pip install fastapi uvicorn

//start the server for the private network
uvicorn main:app --host 192.168.1.10 --port 8000 --reload
