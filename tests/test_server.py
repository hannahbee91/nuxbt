import copy
import multiprocessing
import queue
import sys
from unittest.mock import MagicMock

# nuxbt's package __init__ pulls in dbus; mock it for headless tests.
if 'dbus' not in sys.modules:
    sys.modules['dbus'] = MagicMock()

# nuxbt.controller.server imports fcntl, which is not available on Windows.
if 'fcntl' not in sys.modules:
    sys.modules['fcntl'] = MagicMock()

# nuxbt.nuxbt forces 'fork' start method, which is unavailable on Windows.
multiprocessing.set_start_method = MagicMock()

# nuxbt.agent imports PyGObject's GLib, which may not be installed on Windows.
if 'gi' not in sys.modules:
    sys.modules['gi'] = MagicMock()
    sys.modules['gi.repository'] = MagicMock()
    sys.modules['gi.repository.GLib'] = MagicMock()

from nuxbt.controller.server import ControllerServer
from nuxbt.controller.controller import ControllerTypes
from nuxbt.controller.input import InputParser, DIRECT_INPUT_IDLE_PACKET
from nuxbt.controller.protocol import ControllerProtocol


class DummyServer:
    """Minimal stand-in for ControllerServer so _sync_controller_input can be
    unit-tested without spinning up Bluetooth/BlueZ."""
    pass


def _make_server():
    proto = ControllerProtocol(ControllerTypes.PRO_CONTROLLER, "00:11:22:33:44:55")
    server = DummyServer()
    server.input = InputParser(proto)
    server.task_queue = queue.Queue()
    server.state = {}
    return server


def test_sync_controller_input_drains_direct_event():
    """A direct input event on the queue updates controller_input."""
    server = _make_server()
    pressed = copy.deepcopy(DIRECT_INPUT_IDLE_PACKET)
    pressed["A"] = True
    server.task_queue.put({"type": "direct", "input": pressed})

    ControllerServer._sync_controller_input(server)

    assert server.input.active_input_queued()
    assert server.task_queue.empty()


def test_sync_controller_input_fallback_to_shared_state_on_dropped_release():
    """If the neutral queue event was lost upstream, shared state still has the
    latest idle packet; re-sync from it so we don't stay stuck on a held input."""
    server = _make_server()

    # Simulate a stale held input (the release event never reached us).
    pressed = copy.deepcopy(DIRECT_INPUT_IDLE_PACKET)
    pressed["A"] = True
    server.input.set_controller_input(pressed)
    assert server.input.active_input_queued()

    # Meanwhile the main process already updated shared state to idle.
    server.state["direct_input"] = copy.deepcopy(DIRECT_INPUT_IDLE_PACKET)

    ControllerServer._sync_controller_input(server)

    assert not server.input.active_input_queued()
    assert server.task_queue.empty()


def test_sync_controller_input_does_not_read_shared_state_when_idle():
    """When controller_input is already idle, the fallback should not read the
    Manager dict; this keeps idle cycles cheap and avoids touching stale state."""
    server = _make_server()
    server.input.set_controller_input(copy.deepcopy(DIRECT_INPUT_IDLE_PACKET))
    # Intentionally invalid shared state; if it were read it would corrupt
    # controller_input. Because we are idle, it must be ignored.
    server.state["direct_input"] = {"should_not_be_read": True}

    ControllerServer._sync_controller_input(server)

    assert not server.input.active_input_queued()
    assert server.input.controller_input == DIRECT_INPUT_IDLE_PACKET


def test_sync_controller_input_queue_event_wins_over_shared_state():
    """When both a queue event and shared state are available, the queue event
    (the explicit edge) takes precedence over the fallback poll."""
    server = _make_server()

    # Shared state says A is still pressed.
    pressed = copy.deepcopy(DIRECT_INPUT_IDLE_PACKET)
    pressed["A"] = True
    server.state["direct_input"] = pressed

    # But a queue event says it was released.
    server.task_queue.put({"type": "direct", "input": copy.deepcopy(DIRECT_INPUT_IDLE_PACKET)})

    ControllerServer._sync_controller_input(server)

    assert not server.input.active_input_queued()


def test_sync_controller_input_macro_event_still_processed():
    """Macro events on the queue are still drained alongside direct input."""
    server = _make_server()
    server.task_queue.put({"type": "macro", "macro": "A 0.1s", "macro_id": "abc123"})

    ControllerServer._sync_controller_input(server)

    assert server.input.macro_buffer
    assert server.task_queue.empty()
