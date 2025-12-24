from unittest.mock import MagicMock
import pytest
import sys
import os

# Adjust path to find nuxbt module
sys.path.append(os.getcwd())

from nuxbt.controller.input import InputParser

class TestMacroHold:

    def test_hold_parsing(self):
        protocol = MagicMock()
        parser = InputParser(protocol)
        
        macro_string = "HOLD DPAD_DOWN\n  A 0.1s\n  0.1s"
        
        # We need to manually drive the parsing because set_protocol_input logic 
        # is complex to simulate perfectly without full mocking. 
        # However, we can use the parser to parse the macro string and inspect the result.
        
        parsed_commands = parser.parse_macro(macro_string)
        
        # Expected:
        # 1. "A 0.1s DPAD_DOWN" (or "DPAD_DOWN A 0.1s")
        # 2. "0.1s DPAD_DOWN" (or "DPAD_DOWN 0.1s")
        
        print(f"Parsed commands: {parsed_commands}")
        
        assert len(parsed_commands) == 2
        assert "DPAD_DOWN" in parsed_commands[0]
        assert "A" in parsed_commands[0]
        assert "0.1s" in parsed_commands[0]
        
        assert "DPAD_DOWN" in parsed_commands[1]
        assert "0.1s" in parsed_commands[1]
        tokens = parsed_commands[1].split()
        assert "A" not in tokens

    def test_nested_hold(self):
        protocol = MagicMock()
        parser = InputParser(protocol)
        
        macro_string = "HOLD ZL\n  HOLD ZR\n    A 0.1s"
        
        parsed_commands = parser.parse_macro(macro_string)
        
        assert len(parsed_commands) == 1
        assert "ZL" in parsed_commands[0]
        assert "ZR" in parsed_commands[0]
        assert "A" in parsed_commands[0]

    def test_hold_with_loop(self):
        protocol = MagicMock()
        parser = InputParser(protocol)
        
        macro_string = "HOLD B\n  LOOP 2\n    A 0.1s"
        
        parsed_commands = parser.parse_macro(macro_string)
        
        assert len(parsed_commands) == 2
        for cmd in parsed_commands:
            assert "B" in cmd
            assert "A" in cmd
