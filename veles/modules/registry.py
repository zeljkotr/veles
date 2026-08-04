"""
Veles Operations Center Module Registry

Central registry for all Veles operational domains.
"""


MODULES = {

    "intelligence": {
        "name": "Inteligencija",
        "icon": "🧠",
        "status": "online",
        "description": "AI reasoning, planning and decision engine"
    },


    "infrastructure": {
        "name": "Infrastruktura",
        "icon": "🖥",
        "status": "building",
        "description": "Servers, devices and inventory"
    },


    "delivery": {
        "name": "Isporuka",
        "icon": "📦",
        "status": "planned",
        "description": "CI/CD and deployment"
    },


    "cloud": {
        "name": "Oblak",
        "icon": "☁",
        "status": "planned",
        "description": "Cloud platforms"
    },


    "security": {
        "name": "Bezbednost",
        "icon": "🔐",
        "status": "planned",
        "description": "Security operations"
    },


    "automation": {
        "name": "Automatizacija",
        "icon": "⚙",
        "status": "planned",
        "description": "Automation workflows"
    },


    "observability": {
        "name": "Nadzor",
        "icon": "📊",
        "status": "planned",
        "description": "Monitoring and alerts"
    },


    "network": {
        "name": "Mreža",
        "icon": "🌐",
        "status": "planned",
        "description": "Network discovery and topology"
    },


    "platform": {
        "name": "Platforma",
        "icon": "🏗",
        "status": "planned",
        "description": "Platform engineering"
    },


    "data": {
        "name": "Podaci",
        "icon": "🗄",
        "status": "planned",
        "description": "Databases and storage"
    },


    "testing": {
        "name": "Testiranje",
        "icon": "🧪",
        "status": "planned",
        "description": "Testing environments"
    },


    "access": {
        "name": "Pristup",
        "icon": "🔐",
        "status": "planned",
        "description": "Identity and access"
    }

}



def get_modules():

    return MODULES



def get_module(name):

    return MODULES.get(name)