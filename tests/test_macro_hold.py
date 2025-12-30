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
        
        print(f"Parsed commands: {parsed_commands}")
        
        # New behavior: "DPAD_DOWN 0.05s" inserted at start
        assert len(parsed_commands) == 4
        
        # Frame 0: Setup
        cmd0_tokens = parsed_commands[0].split()
        assert "DPAD_DOWN" in cmd0_tokens
        assert "0.05s" in cmd0_tokens
        assert "A" not in cmd0_tokens
        
        # Frame 1: Action
        cmd1_tokens = parsed_commands[1].split()
        assert "DPAD_DOWN" in cmd1_tokens
        assert "A" in cmd1_tokens
        
        # Frame 2: Post-action wait (if any)? 
        # Orig: "0.1s" -> "DPAD_DOWN 0.1s"
        cmd2_tokens = parsed_commands[2].split()
        assert "DPAD_DOWN" in cmd2_tokens
        assert "0.1s" in cmd2_tokens
        assert "A" not in cmd2_tokens
        
        # Frame 3: Cooldown
        assert len(parsed_commands) == 4
        cmd3_tokens = parsed_commands[3].split()
        assert "DPAD_DOWN" in cmd3_tokens
        assert "0.05s" in cmd3_tokens
        assert "A" not in cmd3_tokens

    def test_nested_hold(self):
        protocol = MagicMock()
        parser = InputParser(protocol)
        
        macro_string = "HOLD ZL\n  HOLD ZR\n    A 0.1s"
        
        parsed_commands = parser.parse_macro(macro_string)
        
        parsed_commands = parser.parse_macro(macro_string)
        
        # Setup ZL (0.05s), Setup ZL+ZR (0.05s), Action ZL+ZR+A (0.1s), Cooldown ZL+ZR (0.05s), Cooldown ZL (0.05s)
        # Wait, nested holds:
        # HOLD ZL
        #  HOLD ZR
        #   A
        
        # Expands to:
        # 1. ZL Setup
        # 2. [ZR Block]
        #    - ZR Setup (ZL+ZR)
        #    - A (ZL+ZR+A)
        #    - ZR Cooldown (ZL+ZR)
        # 3. ZL Cooldown
        
        assert len(parsed_commands) == 5
        # Frame 1: ZL setup
        assert "ZL" in parsed_commands[0]
        # Frame 2: ZR setup (ZL held)
        assert "ZL" in parsed_commands[1]
        assert "ZR" in parsed_commands[1]
        # Frame 3: Action
        assert "ZL" in parsed_commands[2]
        assert "ZR" in parsed_commands[2]
        assert "A" in parsed_commands[2]
        # Frame 4: ZR Cooldown
        assert "ZL" in parsed_commands[3]
        assert "ZR" in parsed_commands[3]
        assert "0.05s" in parsed_commands[3]
        # Frame 5: ZL Cooldown
        assert "ZL" in parsed_commands[4]
        assert "0.05s" in parsed_commands[4]

    def test_hold_with_loop(self):
        protocol = MagicMock()
        parser = InputParser(protocol)
        
        macro_string = "HOLD B\n  LOOP 2\n    A 0.1s"
        
        parsed_commands = parser.parse_macro(macro_string)
        
        parsed_commands = parser.parse_macro(macro_string)
        
        # Setup B (0.05s), Loop 1, Loop 2, Cooldown B (0.05s)
        assert len(parsed_commands) == 4
        assert "B" in parsed_commands[0]
        assert "0.05s" in parsed_commands[0]
        assert "A" not in parsed_commands[0]
        
        # Check looped commands (indices 1 and 2)
        for i in range(1, 3):
             cmd = parsed_commands[i]
             assert "B" in cmd
             assert "A" in cmd
             
        # Cooldown
        assert "B" in parsed_commands[3]
        assert "0.05s" in parsed_commands[3]
