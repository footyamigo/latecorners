# Late Corner Bet Monitoring Dashboard

This web dashboard provides a real-time view of live football matches, specifically designed to identify potential late-stage corner betting opportunities. It uses data from the SportMonks API to track live scores, match statistics, and game time.

## Features

- **Live Match Tracking:** See all currently live football matches in one place.
- **Key Statistics:** View essential stats like scores, minute, and league information.
- **Simple Deployment:** Single-process app that runs on any platform that supports Python/Flask.

## How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/footyamigo/latecorners.git
    cd latecorners
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file and add your API keys:
    ```
    SPORTMONKS_API_KEY=your_sportmonks_api_key_here
    ```

4.  **Run the application:**
    ```bash
    flask run
    ```
    The dashboard will be available at `http://127.0.0.1:5000`.

## Deployment

This application is designed for simple, single-process deployment on platforms like Railway, DigitalOcean App Platform, Heroku, etc.

- The `Procfile` is configured to run a Gunicorn web server.
- The app fetches and caches data in memory for 60 seconds.
- No background workers, volumes, or complex setup is required.
- Just push to your provider, and it will work. 