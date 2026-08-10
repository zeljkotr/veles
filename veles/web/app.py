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
import socket
from pathlib import Path
from veles.modules.monitoring import monitoring

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

sys.path.insert(0, BASE_DIR)


from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
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

from veles.modules.registry import get_modules

from veles.modules.infrastructure.service import infrastructure

from veles.modules.infrastructure.discovery import (
    discover_network_targets
)


app = Flask(__name__)

app.secret_key = "veles-dev-secret-change-me"


TAILSCALE_IP = "0.0.0.0"

CERT_FILE = "certs/meshcorers.taild94372.ts.net.crt"

KEY_FILE = "certs/meshcorers.taild94372.ts.net.key"


AUDIO_DIR = (
    Path(__file__).parent /
    "static" /
    "audio"
)

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

    return markdown.render(text)



def _generate_answer_audio(text: str):

    try:

        wav_path = synthesize_to_file(text)

        filename = (
            f"{uuid.uuid4().hex}.wav"
        )

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



# ==========================================
# INFRASTRUCTURE
# ==========================================


@app.route("/infrastructure")
def infrastructure_page():

    data = infrastructure.get_status()

    servers = data.get(
        "servers",
        []
    )

    server = None

    if servers:
        server = servers[0]


    return render_template(
        "infrastructure.html",
        data=data,
        server=server
    )



# ==========================================
# DISCOVERY CENTER
# ==========================================


@app.route("/discovery")
def discovery_page():

    targets = discover_network_targets()


    return render_template(
        "discovery.html",
        targets=targets,
        discovered=session.get(
            "discovery_results",
            []
        )
    )



@app.route(
    "/discovery/scan",
    methods=["POST"]
)
def discovery_scan():

    from veles.modules.infrastructure.discovery import (
        discover_network_hosts
    )


    networks = request.form.getlist(
        "network"
    )


    discovered = []


    for network in networks:

        result = discover_network_hosts(
            network
        )

        discovered.extend(
            result
        )


    session["discovery_results"] = discovered


    return render_template(
        "discovery.html",
        targets=discover_network_targets(),
        discovered=discovered
    )



@app.route("/discovery/status")
def discovery_status():

    return render_template(
        "discovery_status.html"
    )



@app.route("/infrastructure/discover")
def discover_infrastructure():

    result = infrastructure.discover()


    return render_template(
        "infrastructure.html",
        data=infrastructure.get_status(),
        server=result.get("local"),
        discovered=result.get("discovered")
    )



@app.route(
    "/discovery/add",
    methods=["POST"]
)
def add_discovered_resource():

    item = request.form.get(
        "resource"
    )

    if not item:
        return redirect(
            url_for(
                "discovery_page"
            )
        )


    data = json.loads(item)


    resource = {

        "id": f"res-{uuid.uuid4().hex[:6]}",

        "type": data.get(
            "type",
            "server"
        ),

        "name": data.get(
            "name"
        ),

        "host": data.get(
            "host"
        ),

        "port": data.get(
            "port",
            0
        ),

        "services": data.get(
            "services",
            []
        ),

        "group": "network",

        "status": "registered"

    }


    infrastructure.add_resource(
        resource
    )


    results = session.get(
        "discovery_results",
        []
    )


    session["discovery_results"] = [
        item for item in results
        if item.get("host") != resource["host"]
    ]


    flash(
        "RESOURCE ADDED",
        "success"
    )


    return redirect(
        url_for(
            "discovery_page"
        )
    )

@app.route(
    "/discovery/import",
    methods=["POST"]
)
def import_discovered_resources():

    resources = request.form.getlist(
        "resource"
    )

    added = 0


    for item in resources:

        data = json.loads(item)


        resource = {

            "id": f"res-{uuid.uuid4().hex[:6]}",

            "type": data.get(
                "type",
                "server"
            ),

            "name": data.get(
                "name"
            ),

            "host": data.get(
                "host"
            ),

            "port": data.get(
                "port",
                0
            ),

            "services": data.get(
                "services",
                []
            ),

            "group": "network",

            "status": "registered"

        }


        infrastructure.add_resource(
            resource
        )


        added += 1


    print(
        "DISCOVERY IMPORT:",
        added
    )


    flash(
        "RESOURCE ADDED",
        "success"
    )


    return render_template(
        "discovery.html",
        targets=discover_network_targets(),
        discovered=session.get(
            "discovery_results",
            []
        )
    )



@app.route(
    "/infrastructure/<group>"
)
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



@app.route(
    "/infrastructure/resource/<resource_id>"
)
def resource_detail(resource_id):

    resource = infrastructure.resource_registry.get_resource(
        resource_id
    )


    return render_template(
        "resource_detail.html",
        resource=resource
    )



@app.route(
    "/infrastructure/resource/<resource_id>/verify"
)
def verify_resource(resource_id):

    resource = infrastructure.resource_registry.get_resource(
        resource_id
    )


    if not resource:

        return redirect(
            url_for(
                "infrastructure_page"
            )
        )


    infrastructure.resource_registry.update_verification(
        resource_id,
        {
            "status": "checking"
        }
    )


    host = resource.get(
        "host"
    )

    port = resource.get(
        "port",
        22
    )


    try:

        socket.create_connection(
            (
                host,
                int(port)
            ),
            timeout=3
        ).close()


        infrastructure.resource_registry.update_verification(
            resource_id,
            {
                "status": "verified"
            }
        )


    except Exception as e:

        print(
            "VERIFY ERROR:",
            e
        )


        infrastructure.resource_registry.update_verification(
            resource_id,
            {
                "status": "failed"
            }
        )


    return redirect(
        url_for(
            "resource_detail",
            resource_id=resource_id
        )
    )



@app.route(
    "/infrastructure/resource/<resource_id>/verify/<state>"
)
def set_verify_state(
    resource_id,
    state
):

    infrastructure.resource_registry.update_verification(
        resource_id,
        {
            "status": state
        }
    )


    return redirect(
        url_for(
            "resource_detail",
            resource_id=resource_id
        )
    )



# ==========================================
# MONITOR
# ==========================================


@app.route(
    "/infrastructure/resource/<resource_id>/monitor"
)
def monitor_resource(resource_id):

    resource = infrastructure.resource_registry.get_resource(
        resource_id
    )


    if not resource:

        return redirect(
            url_for(
                "infrastructure_page"
            )
        )


    # RUN CHECK ONLY FOR THIS RESOURCE

    if request.args.get("check") == "1":

        monitoring.check_resource(
            resource
        )


    # GET CURRENT HEALTH

    health = monitoring.get_health(
        resource_id
    )


    # HANDLE ID TYPE DIFFERENCES

    if health is None:

        for key, item in monitoring.get_all_health().items():

            if str(key) == str(resource_id):

                health = item

                break


    return render_template(
        "resource_monitor.html",
        resource=resource,
        health=health
    )







@app.route(
    "/infrastructure/resource/<resource_id>/delete",
    methods=["GET", "POST"]
)
def delete_resource(resource_id):

    resource = infrastructure.resource_registry.get_resource(
        resource_id
    )


    if not resource:

        return redirect(
            url_for(
                "infrastructure_page"
            )
        )


    if request.method == "POST":

        infrastructure.resource_registry.delete_resource(
            resource_id
        )


        return redirect(
            url_for(
                "infrastructure_page"
            )
        )


    return render_template(
        "delete_resource.html",
        resource=resource
    )





@app.route(
    "/infrastructure/add",
    methods=["GET", "POST"]
)
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



# ==========================================
# DASHBOARD
# ==========================================


@app.route("/")
@app.route("/dashboard")
def dashboard_view():

    modules = get_modules()


    return render_template(
        "dashboard.html",
        modules=modules
    )



# ==========================================
# CHAT
# ==========================================


@app.route(
    "/chat",
    methods=["GET"]
)
def chat():

    if request.args.get(
        "new"
    ) == "1":

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



@app.route(
    "/ask",
    methods=["POST"]
)
def ask():

    question = request.form.get(
        "question",
        ""
    ).strip()


    if not question:

        return redirect(
            url_for(
                "chat"
            )
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



@app.route(
    "/new_chat",
    methods=["POST"]
)
def new_chat():

    session["history"] = []


    return redirect(
        url_for(
            "chat"
        )
    )



@app.route(
    "/confirm_memory",
    methods=["POST"]
)
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
        url_for(
            "chat"
        )
    )



# ==========================================
# MEMORY
# ==========================================


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
        url_for(
            "memory_view"
        )
    )



# ==========================================
# LOGS
# ==========================================

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



# ==========================================
# MONITORING
# ==========================================


@app.route("/monitoring")
def monitoring_view():

    resources = infrastructure.get_resources()

    health = monitoring.get_all_health()

    return render_template(
        "monitoring.html",
        resources=resources,
        health=health,
        data=monitoring.get_status()
    )


@app.route("/monitoring/check")
def monitoring_check():

    resources = infrastructure.get_resources()

    monitoring.check_resources(
        resources
    )

    return redirect(
        url_for(
            "monitoring_view"
        )
    )





# ==========================================
# SYSTEM
# ==========================================

@app.route("/system")
def system_view():

    system = get_system_info()


    return render_template(
        "system.html",
        system=system
    )


# ==========================================
# SERVICES
# ==========================================

@app.route("/services")
def services_view():

    services = list_common_services()


    return render_template(
        "services.html",
        services=services
    )



# ==========================================
# START
# ==========================================


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
