"""
Veles Operations Center Module Registry

Central registry for all Veles operational domains.
"""

MODULES = {

    "intelligence": {
        "name": "Intelligence",
        "icon": "🧠",
        "status": "online",
        "description": "AI reasoning, planning and decision engine"
    },

    "infrastructure": {
        "name": "Infrastructure",
        "icon": "🖥",
        "status": "online",
        "description": "Servers, devices and inventory"
    },

    "delivery": {
        "name": "Delivery",
        "icon": "📦",
        "status": "planned",
        "description": "CI/CD and deployment"
    },

    "cloud": {
        "name": "Cloud",
        "icon": "☁",
        "status": "planned",
        "description": "Cloud platforms"
    },

    "security": {
        "name": "Security",
        "icon": "🔐",
        "status": "planned",
        "description": "Security operations"
    },

    "automation": {
        "name": "Automation",
        "icon": "⚙",
        "status": "planned",
        "description": "Automation workflows"
    },

    "observability": {
        "name": "Monitoring",
        "icon": "📊",
        "status": "online",
        "description": "Monitoring, health checks and alerts"
    },

    "network": {
        "name": "Network",
        "icon": "🌐",
        "status": "online",
        "description": "Network discovery and topology"
    },

    "platform": {
        "name": "Platform",
        "icon": "🏗",
        "status": "planned",
        "description": "Platform engineering"
    },

    "data": {
        "name": "Data",
        "icon": "🗄",
        "status": "planned",
        "description": "Databases and storage"
    },

    "testing": {
        "name": "Testing",
        "icon": "🧪",
        "status": "planned",
        "description": "Testing environments"
    },

    "access": {
        "name": "Access",
        "icon": "🔐",
        "status": "planned",
        "description": "Identity and access"
    }
}


def get_modules():
    return MODULES


def get_module(name):
    return MODULES.get(name)