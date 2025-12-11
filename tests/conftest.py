import pytest
import sys
from unittest.mock import MagicMock

# Mock dbus dependencies before they are imported by nuxbt
sys.modules["dbus"] = MagicMock()
sys.modules["dbus.mainloop.glib"] = MagicMock()
sys.modules["dbus.service"] = MagicMock()

@pytest.fixture
def mock_bluetooth_adapters():
    """Mock the Bluetooth adapter discovery."""
    with pytest.MonkeyPatch.context() as m:
        # Mocking the internal method or class that finds adapters
        # This depends on the actual implementation of nuxbt
        pass
