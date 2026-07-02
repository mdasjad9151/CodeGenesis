sudo kill -9 $(sudo lsof -t -i:3000)
uvicorn main:app --host 0.0.0.0 --port 3000 --reload