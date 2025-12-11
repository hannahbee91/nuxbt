import pytest
from unittest.mock import MagicMock, patch
import sys

# Ensure dbus is mocked if not already by conftest
if 'dbus' not in sys.modules:
    sys.modules['dbus'] = MagicMock()

from nuxbt import Nxbt, PRO_CONTROLLER
from nuxbt.nuxbt import NxbtCommands

class TestNxbt:
    @pytest.fixture
    def nxbt_instance(self):
        with patch('nuxbt.nuxbt.Process') as mock_process, \
             patch('nuxbt.nuxbt.Manager') as mock_manager, \
             patch('nuxbt.nuxbt.toggle_clean_bluez') as mock_toggle, \
             patch('nuxbt.nuxbt.find_objects', return_value=['/org/bluez/hci0']):
            
            # Setup mock manager dict
            mock_manager_instance = mock_manager.return_value
            mock_manager_instance.dict.return_value = {}
            
            nx = Nxbt(debug=True, disable_logging=True)
            yield nx
            
            # Cleanup
            # We don't need to call _on_exit explicitly as it is registered with atexit,
            # but we can call it to test partial cleanup if we wanted.

    def test_init(self, nxbt_instance):
        """Test that Nxbt initializes correctly."""
        assert nxbt_instance.debug is True
        assert nxbt_instance.task_queue is not None
        # Check if process was started
        assert nxbt_instance.controllers.start.called

    def test_create_controller_no_adapters(self):
        """Test create_controller raises error when no adapters available."""
        with patch('nuxbt.nuxbt.Process'), \
             patch('nuxbt.nuxbt.Manager'), \
             patch('nuxbt.nuxbt.toggle_clean_bluez'), \
             patch('nuxbt.nuxbt.find_objects', return_value=[]): # No adapters
             
            nx = Nxbt(disable_logging=True)
            with pytest.raises(ValueError, match="No adapters available"):
                nx.create_controller(PRO_CONTROLLER)

    def test_create_controller_success(self, nxbt_instance):
        """Test creating a controller successfully."""
        # We need to simulate the controller manager updating the state
        # effectively unblocking the wait in create_controller
        
        # Since create_controller blocks waiting for state update, we need to mock the wait logic
        # OR we can mock task_queue.put and avoid the blocking loop by mocking `time.sleep` into a side_effect
        # that updates the state.
        
        # However, it's easier to mock the _controller_lock and the loop condition if possible?
        # Actually, let's just test that it puts the command in the queue.
        # But create_controller blocks. We must mock the blocking behavior.
        
        # We can patch 'time.sleep' to update the state so the loop exits
        def side_effect_sleep(*args):
             # Update state to simulate controller creation
             nxbt_instance.manager_state[0] = {"state": "connecting"}
             
        with patch('time.sleep', side_effect=side_effect_sleep):
            idx = nxbt_instance.create_controller(PRO_CONTROLLER)
            assert idx == 0
            # Retrieve item from queue to verify
            msg = nxbt_instance.task_queue.get(timeout=1)
            assert msg['command'] == NxbtCommands.CREATE_CONTROLLER

    def test_macro(self, nxbt_instance):
        """Test inputting a macro."""
        # Mock manager state to include the controller
        nxbt_instance.manager_state[0] = {"state": "connected", "finished_macros": []}
        
        macro_string = "B 0.1s\n0.1s"
        macro_id = nxbt_instance.macro(0, macro_string, block=False)
        
        assert isinstance(macro_id, str)
        # Check queue
        # Queue.queue is the underlying deque in standard python Queue
        # Using mocks, task_queue is a real Queue unless we mocked it, 
        # but in Nxbt init it creates a real Queue.
        
        # Because Nxbt uses multiprocessing.Queue, accessing .queue might not be straightforward 
        # or safe if it was shared. But here it's local.
        # Wait, multiprocessing.Queue doesn't have .queue attribute directly accessible easily like standard queue?
        # Actually, we should probably mock Queue in __init__ if we want to inspect it easily,
        # OR just use .get() since we are the consumer in this test.
        
        msg = nxbt_instance.task_queue.get()
        assert msg['command'] == NxbtCommands.INPUT_MACRO
        assert msg['arguments']['macro'] == macro_string
        assert msg['arguments']['controller_index'] == 0

    def test_macro_blocking(self, nxbt_instance):
        """Test blocking macro wait."""
        nxbt_instance.manager_state[0] = {"state": "connected", "finished_macros": []}
        
        # We need to simulate the macro finishing
        macro_id_holder = []
        
        original_put = nxbt_instance.task_queue.put
        
        def side_effect_put(item, *args, **kwargs):
            if item['command'] == NxbtCommands.INPUT_MACRO:
                macro_id_holder.append(item['arguments']['macro_id'])
            original_put(item, *args, **kwargs)
            
        def side_effect_sleep(*args):
            # Simulate macro finishing
            if macro_id_holder:
                mid = macro_id_holder[0]
                nxbt_instance.manager_state[0] = {"state": "connected", "finished_macros": [mid]}

        # Patch put to capture ID, patch sleep to update state
        with patch.object(nxbt_instance.task_queue, 'put', side_effect=side_effect_put), \
             patch('time.sleep', side_effect=side_effect_sleep):
             
            macro_string = "A 0.1s"
            result_id = nxbt_instance.macro(0, macro_string, block=True)
            assert result_id == macro_id_holder[0]
