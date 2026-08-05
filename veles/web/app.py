"""
veles/web/app.py

Flask web interface for Veles.

Dashboard + Chat + Memory + Logs + System + Services.
Voice output is generated server-side using Piper TTS.
"""


import sys
import os
import json
import shutil
import uuid

from veles.modules.registry import get_modules
from veles.modules.infrastructure.service import infrastructure

from pathlib import Path


sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            ".."
        )
    )
)


from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)


from markdown_it import MarkdownIt


from veles.core.brain import ask_veles


from veles.memory.memory import (
    remember,
    recall_with_ids,
    delete_memory
)


from veles.tts.piper_tts import synthesize_to_file


from veles.logs.logger import LOG_FILE


from veles.system.system_info import get_system_info


from veles.system.services import list_common_services





app = Flask(__name__)


app.secret_key = "veles-dev-secret-change-me"





TAILSCALE_IP = "0.0.0.0"


CERT_FILE = "certs/meshcorers.taild94372.ts.net.crt"

KEY_FILE = "certs/meshcorers.taild94372.ts.net.key"






AUDIO_DIR = Path(__file__).parent / "static" / "audio"


AUDIO_DIR.mkdir(
    parents=True,
    exist_ok=True
)





markdown = MarkdownIt(
    "commonmark",
    {
        "html": False,
        "breaks": True
    }
)



@app.template_filter("markdown")
def markdown_filter(text):

    if not text:
        return ""

    return markdown.render(
        text
    )









def _generate_answer_audio(text: str):

    """
    Generate Serbian speech using Piper.
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










@app.route("/infrastructure")
def infrastructure_page():


    server = infrastructure.discover()

    data = infrastructure.get_status()


    return render_template(
        "infrastructure.html",
        data=data,
        server=server
    )






@app.route("/infrastructure/<group>")
def resource_group(group):


    allowed_groups = [
        "servers",
        "containers",
        "agents",
        "devices",
        "cloud"
    ]


    if group not in allowed_groups:

        return redirect(
            url_for(
                "infrastructure_page"
            )
        )


    resources = infrastructure.get_resources(
        group
    )


    return render_template(
        "resources.html",
        title=group.capitalize(),
        resources=resources
    )





@app.route("/infrastructure/resource/<resource_id>")
def resource_detail(resource_id):


    resources = infrastructure.get_resources()


    resource = None


    for group in resources.values():

        for item in group:

            if item.get("id") == resource_id:

                resource = item
                break


        if resource:
            break



    return render_template(
        "resource_detail.html",
        resource=resource
    )






@app.route("/infrastructure/server/<server_id>")
def server_details(server_id):


    server = infrastructure.get_registered_server(
        server_id
    )


    return render_template(
        "server.html",
        server=server
    )






@app.route("/infrastructure/add", methods=["GET", "POST"])
def add_resource():


    if request.method == "POST":


        resource = {


            "id": f"res-{uuid.uuid4().hex[:6]}",


            "type": request.form.get(
                "type",
                "server"
            ),


            "name": request.form.get(
                "name",
                "Unnamed Resource"
            ),


            "host": request.form.get(
                "host",
                ""
            ),


            "port": request.form.get(
                "port",
                "22"
            ),


            "username": request.form.get(
                "username",
                ""
            ),


            "group": request.form.get(
                "group",
                "default"
            ),


            "status": "registered"

        }



        infrastructure.add_resource(
            resource
        )



        return redirect(
            url_for(
                "infrastructure_page"
            )
        )



    return render_template(
        "add_resource.html"
    )

@app.route("/")
@app.route("/dashboard")
def dashboard_view():

    modules = get_modules()

    return render_template(
        "dashboard.html",
        modules=modules
    )











@app.route("/chat", methods=["GET"])
def chat():


    if request.args.get("new") == "1":

        session["history"] = []



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











@app.route(
    "/memory/<int:memory_id>/delete",
    methods=["POST"]
)
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
        ) as file:


            lines = file.readlines()[-100:]



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











@app.route("/system")
def system_view():


    system = get_system_info()



    return render_template(
        "system.html",
        system=system
    )











@app.route("/services")
def services_view():


    services = list_common_services()



    return render_template(
        "services.html",
        services=services
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