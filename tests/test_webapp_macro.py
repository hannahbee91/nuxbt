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
                "errors": []
            }
        }
        
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
    
    server_thread = threading.Thread(target=lambda: uvicorn.run(app.app_asgi, host="127.0.0.1", port=port, log_level="critical", ws='wsproto'))
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
    
    # Click Pro Controller to start
    # The UI shows "Pro Controller" image.
    # Looking at index.html (implied by main.js finding #controller-selection)
    # createProController() is called.
    
    # We need to simulate the click. 
    # Since I don't have the HTML content, I assume there's an element triggering createProController
    # main.js: HTML_CONTROLLER_SELECTION = document.getElementById("controller-selection");
    
    # Let's inspect the page content first or make a best guess.
    # Assuming there's an img with onclick or a div.
    # I'll rely on text "Pro Controller" or id logic.
    
    # Click on the element that calls createProController. 
    # Based on main.js: "To create and start a Pro Controller, click the Pro controller graphic."
    # The graphic likely has an alt or is inside a clickable div.
    
    # Let's wait for selector.
    # Better: page.click("text=Pro Controller") might work if alt text is there.
    # Or by ID if I knew it. main.js refers to "joystick-selection" maybe?
    # Let's assume there is something clickable. I will verify HTML if this fails.
    
    # Wait: README says "click the Pro controller graphic".
    # I'll try to click `img[alt="Pro Controller"]` or similar if I can guessed it,
    # OR just evaluate js:
    page.evaluate("createProController()")
    
    # Wait for loader
    # main.js: HTML_LOADER.classList.remove('hidden')
    page.wait_for_selector("#loader:not(.hidden)")
    
    # The backend (mock) should emit create_pro_controller
    # The frontend waits for that event, then polls checkForLoad
    # checkForLoad checks STATE.
    # Our mock backend state has "connected".
    
    # Wait for connected UI
    # HTML_CONTROLLER_CONFIG.classList.remove('hidden')
    page.wait_for_selector("#controller-config:not(.hidden)", timeout=5000)
    
    # Test Recording
    # Click "Record Input" button.
    # main.js: toggleRecording()
    # Button id="record-macro-btn"
    page.click("#record-macro-btn")
    
    # Status should show
    # id="recording-status" not hidden
    assert page.is_visible("#recording-status")
    
    # Simulate button press
    # Using keyboard k: 'A' button -> keyCode 76 (from KEYMAP)
    page.keyboard.down('L')  # 'L' key is mapped to 'A' button in main.js (76: "A")?
    # Wait, KEYMAP: 76: "A" -> this is 'L' key code? 'L' char code is 76.
    # Let's check: 'l'.charCodeAt(0) might be 108. 'L' is 76?
    # 'L' keycode is 76.
    
    # Press 'L' (A Button)
    page.keyboard.down('L')
    time.sleep(0.1)
    page.keyboard.up('L')
    
    # Wait a bit
    time.sleep(0.5)
    
    # Stop Recording
    page.click("#record-macro-btn")
    
    # Check Macro Text Area
    # id="macro-text"
    macro_text = page.input_value("#macro-text")
    
    # Verify content
    # Should contain "A" and timings
    assert "A" in macro_text
    assert "s" in macro_text
    
    # Test Playback
    # Click "Run Macro" button (implied exits) or sendMacro()
    # Need to find the button.
    # Assuming there's a button calling sendMacro()
    page.evaluate("sendMacro()")
    
    # Backend mock.macro should be called
    # Wait a bit for socket emission
    time.sleep(0.5)
    
    mock_backend.macro.assert_called()
    call_args = mock_backend.macro.call_args
    assert call_args[0][0] == 0 # Index
    assert "A" in call_args[0][1] # Macro string
