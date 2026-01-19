web: gunicorn backend:app --bind 0.0.0.0:$PORT --timeout 300 --workers 2 --threads 4
worker: python sync_worker.py
