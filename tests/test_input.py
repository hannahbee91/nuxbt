import copy
import sys
from unittest.mock import MagicMock

# nuxbt's package __init__ pulls in dbus; mock it for headless tests.
if 'dbus' not in sys.modules:
    sys.modules['dbus'] = MagicMock()

from nuxbt.controller.protocol import ControllerProtocol
from nuxbt.controller.controller import ControllerTypes
from nuxbt.controller.input import InputParser, DIRECT_INPUT_IDLE_PACKET


def _make_parser():
    proto = ControllerProtocol(ControllerTypes.PRO_CONTROLLER, "00:11:22:33:44:55")
    return proto, InputParser(proto)


def _press(button):
    pkt = copy.deepcopy(DIRECT_INPUT_IDLE_PACKET)
    pkt[button] = True
    proto, parser = _make_parser()
    parser.parse_controller_input(pkt)
    # report[5] is the "shared" middle button byte of the standard input report.
    return proto.report[5]


def test_direct_input_plus_minus_bits():
    """Direct input must pack Plus/Minus per the Switch HID spec:
    shared byte bit 0 = Minus, bit 1 = Plus (regression test for the swap)."""
    # Minus -> bit 0 only
    assert _press("MINUS") & 0x01
    assert not _press("MINUS") & 0x02
    # Plus -> bit 1 only
    assert _press("PLUS") & 0x02
    assert not _press("PLUS") & 0x01


def test_direct_input_matches_macro_path():
    """The direct path and the macro path must pack Plus/Minus identically."""
    proto_m, parser_m = _make_parser()
    parser_m.set_macro_input(["PLUS", "0.1s"])
    plus_macro = proto_m.report[5]

    proto_m, parser_m = _make_parser()
    parser_m.set_macro_input(["MINUS", "0.1s"])
    minus_macro = proto_m.report[5]

    assert _press("PLUS") == plus_macro
    assert _press("MINUS") == minus_macro


def test_held_input_reapplied_across_cycles():
    """A held direct input must be re-applied on every loop cycle, not consumed
    after the first parse.

    The protocol report is ephemeral: get_report() clears it and
    process_commands() rebuilds a neutral baseline each cycle. The controller
    mainloop only receives a SET_INPUT event when the input *changes*, then
    resends the report at the Bluetooth interval in between. If set_protocol_input
    consumed the input (controller_input -> None) those resends would carry a
    neutral report and the input would stutter (regression test)."""
    proto, parser = _make_parser()
    proto.device_info_queried = True  # required for buttons to reach the report

    pkt = copy.deepcopy(DIRECT_INPUT_IDLE_PACKET)
    pkt["A"] = True
    parser.set_controller_input(pkt)  # single "A pressed" event

    # Simulate several mainloop cycles with no further input events.
    for _ in range(5):
        proto.process_commands(None)      # rebuild neutral baseline
        parser.set_protocol_input()
        report = proto.get_report()       # send + clear
        # A is bit 3 (0x08) of the upper button byte, report[4].
        assert report[4] & 0x08, "held A must persist on resends"


def test_release_clears_held_input():
    """Releasing to an idle packet must drop the held input from the report."""
    proto, parser = _make_parser()
    proto.device_info_queried = True

    pressed = copy.deepcopy(DIRECT_INPUT_IDLE_PACKET)
    pressed["A"] = True
    parser.set_controller_input(pressed)
    proto.process_commands(None)
    parser.set_protocol_input()
    assert proto.get_report()[4] & 0x08
    assert parser.active_input_queued()

    # Release: idle packet event.
    parser.set_controller_input(copy.deepcopy(DIRECT_INPUT_IDLE_PACKET))
    assert not parser.active_input_queued()
    proto.process_commands(None)
    parser.set_protocol_input()
    assert not proto.get_report()[4] & 0x08
