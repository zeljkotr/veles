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
import ipaddress
import threading

from pathlib import Path


from veles.modules.monitoring import monitoring
from veles.modules.network.service import network
from veles.modules.delivery.service import delivery


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


# ==========================================
# DISCOVERY RUNTIME STATE
# ==========================================

discovery_jobs = {}

# Latest completed discovery results are kept
# server-side instead of inside Flask's cookie session.
discovery_results = []

discovery_results_lock = threading.Lock()


app.secret_key = os.getenv(
    "VELES_SECRET_KEY",
    "veles-dev-secret-change-me"
)


# ==========================================
# RUNTIME WEB CONFIGURATION
# ==========================================

VELES_HOST = os.getenv(
    "VELES_HOST",
    "0.0.0.0"
)


VELES_PORT = int(
    os.getenv(
        "VELES_PORT",
        "5001"
    )
)


VELES_TLS = os.getenv(
    "VELES_TLS",
    "false"
).lower() == "true"


VELES_CERT_FILE = os.getenv(
    "VELES_CERT_FILE",
    ""
)


VELES_KEY_FILE = os.getenv(
    "VELES_KEY_FILE",
    ""
)


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

    custom_networks = session.get(
        "discovery_custom_networks",
        []
    )

    targets = discover_network_targets(
        custom_networks=custom_networks
    )

    with discovery_results_lock:

        current_results = list(
            discovery_results
        )

    return render_template(
        "discovery.html",
        targets=targets,
        discovered=current_results
    )


@app.route(
    "/discovery/scan",
    methods=["POST"]
)
def discovery_scan():

    from veles.modules.infrastructure.discovery import (
        discover_network_hosts
    )

    custom_network = request.form.get(
        "custom_network",
        ""
    ).strip()

    remove_network = request.form.get(
        "remove_network",
        ""
    ).strip()

    custom_networks = session.get(
        "discovery_custom_networks",
        []
    )

    # ======================================
    # REMOVE CUSTOM NETWORK
    # ======================================

    if remove_network:

        custom_networks = [
            network
            for network in custom_networks
            if network != remove_network
        ]

        session[
            "discovery_custom_networks"
        ] = custom_networks

        flash(
            "NETWORK REMOVED",
            "success"
        )

        return redirect(
            url_for(
                "discovery_page"
            )
        )

    # ======================================
    # ADD CUSTOM NETWORK
    # ======================================

    if request.form.get("add_custom"):

        if custom_network:

            try:

                network = ipaddress.ip_network(
                    custom_network,
                    strict=False
                )

                network_string = str(network)

                if network_string not in custom_networks:

                    custom_networks.append(
                        network_string
                    )

                    session[
                        "discovery_custom_networks"
                    ] = custom_networks

                    flash(
                        "NETWORK ADDED",
                        "success"
                    )

            except ValueError:

                flash(
                    "INVALID NETWORK",
                    "error"
                )

        return redirect(
            url_for(
                "discovery_page"
            )
        )

    # ======================================
    # START SCAN
    # ======================================

    networks = request.form.getlist(
        "network"
    )

    valid_networks = []

    seen_networks = set()

    for network in networks:

        network = network.strip()

        if not network:
            continue

        try:

            parsed = ipaddress.ip_network(
                network,
                strict=False
            )

        except ValueError:

            continue

        network_string = str(parsed)

        if network_string in seen_networks:
            continue

        seen_networks.add(
            network_string
        )

        valid_networks.append(
            network_string
        )

    print(
        "DISCOVERY SELECTED NETWORKS:",
        valid_networks
    )

    if not valid_networks:

        flash(
            "NO NETWORK SELECTED",
            "error"
        )

        return redirect(
            url_for(
                "discovery_page"
            )
        )

    scan_id = uuid.uuid4().hex

    discovery_jobs[scan_id] = {

        "running": True,

        "network": valid_networks[0],

        "networks": valid_networks,

        "current_network": valid_networks[0],

        "network_index": 0,

        "network_count": len(
            valid_networks
        ),

        "total": 0,

        "checked": 0,

        "found": 0,

        "results": [],

    }

    def run_scan():

        discovered = []

        discovered_hosts = set()

        try:

            total_all = 0
            checked_all = 0

            # ----------------------------------
            # CALCULATE TOTAL FOR ALL NETWORKS
            # ----------------------------------

            for network in valid_networks:

                parsed = ipaddress.ip_network(
                    network,
                    strict=False
                )

                total_all += len(
                    list(parsed.hosts())
                )

            discovery_jobs[scan_id].update({

                "total": total_all,

                "checked": 0,

                "found": 0,

                "current_network": valid_networks[0],

                "network_index": 0

            })

            # ----------------------------------
            # SCAN EACH SELECTED NETWORK
            # ----------------------------------

            for index, network in enumerate(
                valid_networks
            ):

                discovery_jobs[scan_id].update({

                    "running": True,

                    "network": network,

                    "current_network": network,

                    "network_index": index

                })

                network_checked_start = checked_all

                def progress_callback(
                    progress,
                    network=network,
                    network_checked_start=network_checked_start
                ):

                    local_checked = progress.get(
                        "checked",
                        0
                    )

                    local_total = progress.get(
                        "total",
                        0
                    )

                    local_found = progress.get(
                        "found",
                        0
                    )

                    current_checked = (
                        network_checked_start +
                        local_checked
                    )

                    discovery_jobs[scan_id].update({

                        "running": True,

                        "network": network,

                        "current_network": network,

                        "network_index": index,

                        "network_total": local_total,

                        "network_checked": local_checked,

                        "checked": current_checked,

                        "total": total_all,

                        "found": (
                            len(discovered) +
                            local_found
                        )

                    })

                print(
                    "DISCOVERY START:",
                    network
                )

                result = discover_network_hosts(
                    network,
                    progress_callback=progress_callback
                )

                print(
                    "DISCOVERY RESULT:",
                    network,
                    len(result)
                )

                # ----------------------------------
                # MERGE RESULTS
                # ----------------------------------

                for item in result:

                    host = item.get(
                        "host"
                    )

                    if not host:
                        continue

                    if host in discovered_hosts:
                        continue

                    discovered_hosts.add(
                        host
                    )

                    discovered.append(
                        item
                    )

                parsed = ipaddress.ip_network(
                    network,
                    strict=False
                )

                network_total = len(
                    list(parsed.hosts())
                )

                checked_all += network_total

                discovery_jobs[scan_id].update({

                    "checked": checked_all,

                    "total": total_all,

                    "found": len(discovered),

                    "results": list(discovered),

                    "network_index": index

                })

            # ----------------------------------
            # COMPLETE
            # ----------------------------------

            discovery_jobs[scan_id].update({

                "running": False,

                "network": valid_networks[-1],

                "current_network": None,

                "network_index": len(
                    valid_networks
                ),

                "checked": total_all,

                "total": total_all,

                "found": len(discovered),

                "results": list(discovered)

            })

            # ----------------------------------
            # SAVE RESULTS SERVER-SIDE
            # ----------------------------------

            with discovery_results_lock:

                discovery_results.clear()

                discovery_results.extend(
                    discovered
                )

            print(
                "DISCOVERY COMPLETE:",
                "networks=",
                valid_networks,
                "found=",
                len(discovered)
            )

        except Exception as e:

            print(
                "DISCOVERY SCAN ERROR:",
                e
            )

            discovery_jobs[scan_id].update({

                "running": False,

                "error": str(e),

                "results": list(discovered),

                "found": len(discovered)

            })

            with discovery_results_lock:

                discovery_results.clear()

                discovery_results.extend(
                    discovered
                )

    thread = threading.Thread(
        target=run_scan,
        daemon=True
    )

    thread.start()

    return redirect(
        url_for(
            "discovery_status",
            scan_id=scan_id
        )
    )


@app.route(
    "/discovery/status"
)
def discovery_status():

    scan_id = request.args.get(
        "scan_id"
    )

    job = discovery_jobs.get(
        scan_id
    )

    if not job:

        return redirect(
            url_for(
                "discovery_page"
            )
        )

    if not job.get("running"):

        with discovery_results_lock:

            discovery_results.clear()

            discovery_results.extend(
                job.get(
                    "results",
                    []
                )
            )

        return redirect(
            url_for(
                "discovery_page"
            )
        )

    return render_template(
        "discovery_status.html",
        scan_id=scan_id,
        scan=job
    )


@app.route(
    "/discovery/status/data"
)
def discovery_status_data():

    scan_id = request.args.get(
        "scan_id"
    )

    job = discovery_jobs.get(
        scan_id
    )

    if not job:

        return {
            "running": False,
            "error": "SCAN NOT FOUND"
        }, 404

    return job


@app.route(
    "/infrastructure/discover"
)
def discover_infrastructure():

    result = infrastructure.discover()

    return render_template(
        "infrastructure.html",
        data=infrastructure.get_status(),
        server=result.get("local"),
        discovered=result.get("discovered")
    )


# ==========================================
# ADD DISCOVERED RESOURCE
# ==========================================

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

    try:

        data = json.loads(item)

    except (TypeError, json.JSONDecodeError):

        flash(
            "INVALID RESOURCE",
            "error"
        )

        return redirect(
            url_for(
                "discovery_page"
            )
        )

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
            "port"
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

    # --------------------------------------
    # REMOVE ONLY THE ADDED HOST
    # FROM THE SERVER-SIDE DISCOVERY LIST
    # --------------------------------------

    resource_host = resource.get(
        "host"
    )

    with discovery_results_lock:

        remaining_results = [

            discovered

            for discovered in discovery_results

            if discovered.get("host")
            != resource_host

        ]

        discovery_results.clear()

        discovery_results.extend(
            remaining_results
        )

    flash(
        "RESOURCE ADDED",
        "success"
    )

    return redirect(
        url_for(
            "discovery_page"
        )
    )


# ==========================================
# IMPORT DISCOVERED RESOURCES
# ==========================================

@app.route(
    "/discovery/import",
    methods=["POST"]
)
def import_discovered_resources():

    resources = request.form.getlist(
        "resource"
    )

    added = 0

    added_hosts = set()

    for item in resources:

        try:

            data = json.loads(item)

        except (TypeError, json.JSONDecodeError):

            continue

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

        if resource.get("host"):

            added_hosts.add(
                resource.get("host")
            )

        added += 1

    print(
        "DISCOVERY IMPORT:",
        added
    )

    # --------------------------------------
    # REMOVE ONLY IMPORTED RESOURCES
    # --------------------------------------

    with discovery_results_lock:

        remaining_results = [

            discovered

            for discovered in discovery_results

            if discovered.get("host")
            not in added_hosts

        ]

        discovery_results.clear()

        discovery_results.extend(
            remaining_results
        )

    flash(
        "RESOURCE ADDED",
        "success"
    )

    return redirect(
        url_for(
            "discovery_page"
        )
    )


# ==========================================
# INFRASTRUCTURE GROUP
# ==========================================

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

    if request.args.get("check") == "1":

        monitoring.check_resource(
            resource
        )

    health = monitoring.get_health(
        resource_id
    )

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
# NETWORK
# ==========================================

@app.route("/network")
def network_view():

    data = network.get_status()

    return render_template(
        "network.html",
        data=data
    )


# ==========================================
# DELIVERY
# ==========================================

@app.route("/delivery")
def delivery_view():

    data = delivery.get_status()

    return render_template(
        "delivery.html",
        data=data
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

    if VELES_TLS:

        if not VELES_CERT_FILE or not VELES_KEY_FILE:

            raise RuntimeError(
                "VELES_TLS=true requires "
                "VELES_CERT_FILE and VELES_KEY_FILE"
            )

        ssl_context = (
            VELES_CERT_FILE,
            VELES_KEY_FILE
        )

    else:

        ssl_context = None

    app.run(
        host=VELES_HOST,
        port=VELES_PORT,
        debug=False,
        ssl_context=ssl_context
    )