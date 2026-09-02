"""
VELES Mobile Service

Foundation service for VELES Mobile devices.

Current scope:
- device registration
- device identity
- device status
- pairing state
- revocation state

Secrets are intentionally not implemented yet.
"""

from datetime import datetime

from veles.modules.mobile.models import (
    MobileDevice,
    MobileResponse
)

from veles.modules.mobile.protocol import (
    PROTOCOL_VERSION
)


class MobileService:
    """
    Main VELES Mobile service.

    The service does not generate Mobile identities.
    The Mobile device is the authority for its own device_id.
    """

    def __init__(self):

        self.device = None

        self.paired = False

        self.revoked = False


    def register_device(
        self,
        device_id,
        name="",
        metadata=None
    ):
        """
        Register a Mobile device identity.

        device_id must be supplied by the Mobile device.
        """

        if not device_id:
            return MobileResponse(
                status="error",
                message="Mobile device_id is required."
            )

        if self.revoked:
            return MobileResponse(
                status="error",
                message="Mobile device is revoked."
            )

        self.device = MobileDevice(
            device_id=device_id,
            name=name,
            protocol_version=PROTOCOL_VERSION,
            status="registered",
            metadata=dict(
                metadata or {}
            )
        )

        return MobileResponse(
            status="ok",
            message="Mobile device registered.",
            data=self._device_data()
        )


    def get_status(self):
        """
        Return current Mobile connection state.
        """

        if self.device is None:

            return MobileResponse(
                status="not_connected",
                message="No Mobile device registered."
            )

        return MobileResponse(
            status=self.device.status,
            data={
                "device": self._device_data(),
                "paired": self.paired,
                "revoked": self.revoked
            }
        )


    def get_identity(self):
        """
        Return the registered Mobile identity.
        """

        if self.device is None:

            return MobileResponse(
                status="not_connected",
                message="No Mobile device registered."
            )

        return MobileResponse(
            status="ok",
            data=self._device_data()
        )


    def pair(self):
        """
        Mark the registered Mobile device as paired.

        Cryptographic authentication will be implemented later.
        """

        if self.device is None:

            return MobileResponse(
                status="error",
                message="No Mobile device registered."
            )

        if self.revoked:

            return MobileResponse(
                status="error",
                message="Mobile device is revoked."
            )

        self.paired = True
        self.device.status = "paired"
        self.device.last_seen = (
            datetime.now().isoformat()
        )

        return MobileResponse(
            status="ok",
            message="Mobile device paired.",
            data=self._device_data()
        )


    def revoke(self):
        """
        Revoke the registered Mobile device.
        """

        if self.device is None:

            return MobileResponse(
                status="error",
                message="No Mobile device registered."
            )

        self.revoked = True
        self.paired = False
        self.device.status = "revoked"

        return MobileResponse(
            status="ok",
            message="Mobile device revoked.",
            data=self._device_data()
        )


    def _device_data(self):

        if self.device is None:
            return {}

        return {
            "device_id": self.device.device_id,
            "name": self.device.name,
            "protocol_version": (
                self.device.protocol_version
            ),
            "status": self.device.status,
            "metadata": dict(
                self.device.metadata
            ),
            "created_at": self.device.created_at,
            "last_seen": self.device.last_seen
        }


mobile = MobileService()
