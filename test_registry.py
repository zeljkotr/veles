from veles.modules.infrastructure.server_registry import ServerRegistry


registry = ServerRegistry()


registry.add_server(
    {
        "id": "srv-001",
        "name": "Test Server",
        "host": "192.168.1.10",
        "port": 22,
        "username": "test",
        "group": "test"
    }
)


print(registry.list_servers())
