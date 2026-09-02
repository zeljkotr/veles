"""
VELES Mobile

Mobile security device integration for VELES.

The Mobile module provides the foundation for:
- device identity
- device pairing
- device authentication
- secret access
- approval workflows

Secrets are not implemented in this initial version.
"""

from veles.modules.mobile.service import MobileService


mobile = MobileService()
