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
