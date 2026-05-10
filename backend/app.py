from flask import Flask, redirect
import os
import subprocess
import sys
from pathlib import Path

try:
    from flask_cors import CORS
except ImportError:
    def CORS(app):
        return app

from routes.ask_route import ask_bp
from routes.history_route import history_bp
from utils.seed import seed_prompt

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STREAMLIT_APP = PROJECT_ROOT / "backend" / "streamlit_app.py"
_streamlit_process = None

app.register_blueprint(ask_bp)
app.register_blueprint(history_bp)

try:
    seed_prompt()
except Exception:
    pass


def launch_streamlit() -> None:
    global _streamlit_process

    if _streamlit_process is not None:
        return

    if not STREAMLIT_APP.exists():
        return

    _streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(STREAMLIT_APP)],
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "CHATBOT_API_BASE_URL": "http://127.0.0.1:5000"},
    )


def should_launch_streamlit() -> bool:
    if os.environ.get("FLASK_RUN_FROM_CLI") == "true" and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return False

    return True


@app.route("/")
def home():
    return redirect("http://127.0.0.1:8501", code=302)

if __name__ == "__main__":
    if should_launch_streamlit():
        launch_streamlit()
    app.run(debug=True, port=5000, use_reloader=False)

elif should_launch_streamlit():
    launch_streamlit()