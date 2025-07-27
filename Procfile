web: gunicorn --bind 0.0.0.0:$PORT web_dashboard:app --timeout 120 --workers 1
updater: python live_data_updater.py 