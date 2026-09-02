"""
VELES Mobile Protocol

Protocol definitions for communication between VELES and
VELES Mobile.

This layer contains protocol names and validation only.

No credentials or secrets are stored here.
"""


PROTOCOL_VERSION = "1"


REQUEST_STATUS = "device.status"
REQUEST_IDENTITY = "device.identity"
REQUEST_PAIR = "device.pair"
REQUEST_REVOKE = "device.revoke"


SUPPORTED_REQUESTS = {
    REQUEST_STATUS,
    REQUEST_IDENTITY,
    REQUEST_PAIR,
    REQUEST_REVOKE
}


def is_supported_request(request_type):
    """
    Check whether a Mobile protocol request is supported.
    """

    return request_type in SUPPORTED_REQUESTS


def create_request(
    request_type,
    payload=None
):
    """
    Create a standard Mobile protocol request.
    """

    if not is_supported_request(
        request_type
    ):
        raise ValueError(
            f"Unsupported Mobile request: {request_type}"
        )

    return {
        "protocol_version": PROTOCOL_VERSION,
        "type": request_type,
        "payload": dict(
            payload or {}
        )
    }


def create_response(
    status="unknown",
    message="",
    data=None
):
    """
    Create a standard Mobile protocol response.
    """

    return {
        "protocol_version": PROTOCOL_VERSION,
        "status": status,
        "message": message,
        "data": dict(
            data or {}
        )
    }
