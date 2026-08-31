"""
Veles Operations Center Module Registry

Central registry for all Veles operational domains.
"""

MODULES = {

    "intelligence": {
        "name": "Intelligence",
        "icon": "🧠",
        "status": "online",
        "description": "AI reasoning, planning and decision engine",
        "entry": "/chat",
    },

    "infrastructure": {
        "name": "Infrastructure",
        "icon": "🖥",
        "status": "online",
        "description": "Servers, devices and inventory",
        "entry": "/infrastructure",
    },

    "delivery": {
        "name": "Delivery",
        "icon": "📦",
        "status": "planned",
        "description": "CI/CD and deployment",
        "entry": "/module/delivery",
    },

    "cloud": {
        "name": "Cloud",
        "icon": "☁",
        "status": "planned",
        "description": "Cloud platforms",
        "entry": "/module/cloud",
    },

    "security": {
        "name": "Security",
        "icon": "🔐",
        "status": "online",
        "description": "Security operations",
        "entry": "/security",
    },

    "automation": {
        "name": "Automation",
        "icon": "⚙",
        "status": "planned",
        "description": "Automation workflows",
        "entry": "/module/automation",
    },

    "observability": {
        "name": "Monitoring",
        "icon": "📊",
        "status": "online",
        "description": "Monitoring, health checks and alerts",
        "entry": "/monitoring",
    },

    "network": {
        "name": "Network",
        "icon": "🌐",
        "status": "online",
        "description": "Network discovery and topology",
        "entry": "/network",
    },

    "platform": {
        "name": "Platform",
        "icon": "🏗",
        "status": "planned",
        "description": "Platform engineering",
        "entry": "/module/platform",
    },

    "data": {
        "name": "Data",
        "icon": "🗄",
        "status": "planned",
        "description": "Databases and storage",
        "entry": "/module/data",
    },

    "testing": {
        "name": "Testing",
        "icon": "🧪",
        "status": "planned",
        "description": "Testing environments",
        "entry": "/module/testing",
    },

    "access": {
        "name": "Access",
        "icon": "🔐",
        "status": "planned",
        "description": "Identity and access",
        "entry": "/module/access",
    },
}


def get_modules():
    return MODULES


def get_module(name):
    return MODULES.get(name)