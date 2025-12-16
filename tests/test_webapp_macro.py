import pytest
import threading
import time
from unittest.mock import MagicMock, patch
import sys

# Ensure dbus is mocked
if 'dbus' not in sys.modules:
    sys.modules['dbus'] = MagicMock()

from nuxbt.web import app
from nuxbt import Nxbt, PRO_CONTROLLER

# Flag to signal server to shutdown
shutdown_flag = threading.Event()

@pytest.fixture(scope="module")
def mock_backend():
    """Mock the Nxbt backend in the webapp."""
    with patch('nuxbt.web.app.nuxbt') as mock_nuxbt:
        # Configuration for mocks
        mock_nuxbt.get_switch_addresses.return_value = []
        mock_nuxbt.create_controller.return_value = 0
        mock_nuxbt.macro.return_value = "macro_id_123"
        
        # Mock state
        # The webapp accesses nuxbt.state.copy()
        mock_nuxbt.state = {
            0: {
                "state": "connected",
                "finished_macros": [],
                "errors": [],
                "direct_input": {
                    "L_STICK": {"PRESSED": False, "X_VALUE": 0, "Y_VALUE": 0},
                    "R_STICK": {"PRESSED": False, "X_VALUE": 0, "Y_VALUE": 0},
                    "DPAD_UP": False, "DPAD_LEFT": False, "DPAD_RIGHT": False, "DPAD_DOWN": False,
                    "L": False, "ZL": False, "R": False, "ZR": False,
                    "JCL_SR": False, "JCL_SL": False, "JCR_SR": False, "JCR_SL": False,
                    "PLUS": False, "MINUS": False, "HOME": False, "CAPTURE": False,
                    "Y": False, "X": False, "B": False, "A": False
                }
            }
        }
        
        def update_input(index, packet):
            if index in mock_nuxbt.state:
                mock_nuxbt.state[index]['direct_input'] = packet
        
        mock_nuxbt.set_controller_input.side_effect = update_input
        
        yield mock_nuxbt

@pytest.fixture(scope="module")
def web_server(mock_backend):
    """Start the Flask server in a separate thread."""
    # Run on a different port to avoid conflicts
    port = 5001
    
    # We need to use socketio.run or eventlet.wsgi.server
    # nuxbt uses eventlet.wsgi.server in start_web_app
    # We'll just call app.start_web_app but simplified or just run socketio
    
    # Actually app.py has start_web_app function.
    # We can patch eventlet.listen to bind to 5001
    
    # Run uvicorn in a separated thread
    import uvicorn
    # Redirect stderr/stdout to avoid cluttering test output if desired, or keep it.
    # uvicorn.run blocks, so we run it in a thread.
    
    def run_server():
        try:
            uvicorn.run(app.app_asgi, host="127.0.0.1", port=port, log_level="critical", ws='wsproto')
        except Exception as e:
            import traceback
            traceback.print_exc()
            
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    yield f"http://127.0.0.1:{port}"
    
    # No clean shutdown for daemon thread, but that's fine for tests usually

def test_macro_recording(page, web_server, mock_backend):
    """Test macro recording flow in the webapp."""
    page.goto(web_server)
    
    # Check if we are on the page
    assert page.title() == "NUXBT WebUI"
    
    # Click "Create Pro Controller" button
    # The new UI has a button with text "Create Pro Controller"
    page.click("text=Create Pro Controller")
    
    # Wait for the controller to show as connected
    # In App.tsx, hitting "connected" state shows "Pro Controller {index + 1}"
    # and the status badge connected.
    # We can wait for the header "Pro Controller 1"
    page.wait_for_selector("text=Pro Controller 1")
    
    # Switch to Macros Tab
    # App.tsx: <button>Macros</button>
    page.click("button:has-text('Macros')")
    
    # Wait for MacroControls to be visible (e.g. "Macro Editor" header)
    page.wait_for_selector("text=Macro Editor")
    
    # Test Recording
    # Click "Record" button.
    # MacroControls.tsx: button with text "Record"
    page.click("button:has-text('Record')")
    
    # Status should show REC indicator
    # MacroControls.tsx: span with text "REC"
    page.wait_for_selector("text=REC")
    
    # Simulate button press
    # Using keyboard 'L' -> 'A' button as per previous understanding 
    # (assuming mapping is preserved or standard keyboard mapping is used)
    # ControllerVisual.tsx: keys.has('L') -> packet.A = true
    page.keyboard.down('L')
    time.sleep(0.1)
    page.keyboard.up('L')
    
    # Wait a bit
    time.sleep(0.5)
    
    # Stop Recording
    # Button text changes to "Stop Rec"
    page.click("button:has-text('Stop Rec')")
    
    # Check Macro Text Area
    # textarea in MacroControls
    macro_text = page.input_value("textarea")
    
    # Verify content
    # Should contain "A" and timings
    assert "A" in macro_text
    assert "s" in macro_text
    
    # Test Playback
    # Click "Run" button
    page.click("button:has-text('Run')")
    
    # Backend mock.macro should be called
    # Wait a bit for socket emission
    time.sleep(0.5)
    
    mock_backend.macro.assert_called()
    call_args = mock_backend.macro.call_args
    assert call_args[0][0] == 0 # Index
    assert "A" in call_args[0][1] # Macro string
