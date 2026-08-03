"""
veles/web/app.py

Flask web interface for Veles.

Chat interface + memory + logs.
Voice output is generated server-side using Piper TTS.
"""

import sys
import os
import json
import shutil
import uuid
from pathlib import Path

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
)

from flask import Flask, render_template, request, redirect, url_for, session

from veles.core.brain import ask_veles
from veles.memory.memory import (
    remember,
    recall_with_ids,
    delete_memory
)

from veles.tts.piper_tts import synthesize_to_file
from veles.logs.logger import LOG_FILE


app = Flask(__name__)

app.secret_key = "veles-dev-secret-change-me"


TAILSCALE_IP = "100.90.76.41"

CERT_FILE = "certs/meshcorers.taild94372.ts.net.crt"
KEY_FILE = "certs/meshcorers.taild94372.ts.net.key"


AUDIO_DIR = Path(__file__).parent / "static" / "audio"

AUDIO_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def _generate_answer_audio(text: str):
    """
    Generate Serbian speech using Piper.

    Returns URL for browser playback.
    """

    try:
        wav_path = synthesize_to_file(text)

        filename = f"{uuid.uuid4().hex}.wav"

        destination = AUDIO_DIR / filename

        shutil.move(
            wav_path,
            destination
        )

        return url_for(
            "static",
            filename=f"audio/{filename}"
        )

    except Exception as e:
        print(
            f"[VELES TTS ERROR] {e}"
        )

        return None



@app.route("/", methods=["GET"])
def chat():

    history = session.get(
        "history",
        []
    )

    return render_template(
        "chat.html",
        history=history,
        suggestion=None,
        latest_answer=None,
        audio_url=None
    )



@app.route("/ask", methods=["POST"])
def ask():

    question = request.form.get(
        "question",
        ""
    ).strip()


    if not question:
        return redirect(
            url_for("chat")
        )


    result = ask_veles(
        question
    )


    answer = result["answer"]


    history = session.get(
        "history",
        []
    )


    history.append(
        {
            "role": "user",
            "text": question
        }
    )


    history.append(
        {
            "role": "assistant",
            "text": answer
        }
    )


    session["history"] = history


    audio_url = _generate_answer_audio(
        answer
    )


    return render_template(
        "chat.html",
        history=history,
        latest_answer=answer,
        suggestion=result.get(
            "suggested_memory"
        ),
        audio_url=audio_url
    )



@app.route("/new_chat", methods=["POST"])
def new_chat():

    session["history"] = []

    return redirect(
        url_for("chat")
    )



@app.route("/confirm_memory", methods=["POST"])
def confirm_memory():

    key = request.form.get(
        "key",
        ""
    ).strip()


    value = request.form.get(
        "value",
        ""
    ).strip()


    if key and value:

        remember(
            key,
            value
        )


    return redirect(
        url_for("chat")
    )



@app.route("/memory")
def memory_view():

    memories = recall_with_ids()

    return render_template(
        "memory.html",
        memories=memories
    )



@app.route("/memory/<int:memory_id>/delete", methods=["POST"])
def memory_delete(memory_id):

    delete_memory(
        memory_id
    )

    return redirect(
        url_for("memory_view")
    )



@app.route("/logs")
def logs_view():

    entries = []


    if os.path.exists(LOG_FILE):

        with open(
            LOG_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            lines = f.readlines()[-100:]


        for line in reversed(lines):

            try:

                entries.append(
                    json.loads(line)
                )

            except json.JSONDecodeError:

                pass


    return render_template(
        "logs.html",
        entries=entries
    )



if __name__ == "__main__":

    app.run(
        host=TAILSCALE_IP,
        port=5001,
        debug=False,
        ssl_context=(
            CERT_FILE,
            KEY_FILE
        )
    )