import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from nuxbt.cli import main
from nuxbt import __version__

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_nuxbt():
    with patch('nuxbt.cli.Nuxbt') as mock:
        yield mock

@pytest.fixture
def mock_find_devices():
    with patch('nuxbt.cli.find_devices_by_alias') as mock:
        yield mock

@pytest.fixture
def mock_input_tui():
    with patch('nuxbt.cli.InputTUI') as mock:
        yield mock

@pytest.fixture
def mock_start_web_app():
    with patch('nuxbt.web.start_web_app') as mock:
        yield mock

def test_version_flag(runner):
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert __version__ in result.output

def test_help(runner):
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert "Control your Nintendo Switch" in result.output

def test_webapp_command(runner, mock_start_web_app):
    result = runner.invoke(main, ['webapp', '-i', '127.0.0.1', '-p', '5000', '--usessl'])
    assert result.exit_code == 0
    mock_start_web_app.assert_called_once_with(ip='127.0.0.1', port=5000, usessl=True, cert_path=None, debug=False)

def test_demo_command(runner, mock_nuxbt):
    # Mocking behavior for demo
    instance = mock_nuxbt.return_value
    instance.get_available_adapters.return_value = ['/org/bluez/hci0']
    instance.create_controller.return_value = 0
    instance.macro.return_value = "macro_id"
    # Need to simulate state to allow loop to exit
    instance.state = {0: {"state": "connected", "finished_macros": ["macro_id", "other"]}}
    
    result = runner.invoke(main, ['demo'])
    assert result.exit_code == 0
    assert "Running Demo..." in result.output
    assert "Finished!" in result.output

def test_macro_command_no_args_fails(runner):
    result = runner.invoke(main, ['macro'])
    # In original code it just printed and returned, so exit code 0 but prints error
    assert result.exit_code == 0
    assert "No macro commands were specified" in result.output

def test_macro_command_string(runner, mock_nuxbt):
    instance = mock_nuxbt.return_value
    instance.create_controller.return_value = 0
    instance.wait_for_connection.return_value = None
    instance.macro.return_value = "mid"
    instance.state = {0: {"state": "connected", "finished_macros": ["mid"], "errors": []}}

    result = runner.invoke(main, ['macro', '-c', 'A 0.1s'])
    assert result.exit_code == 0
    assert "Running macro..." in result.output
    instance.macro.assert_called()

def test_addresses_command(runner, mock_find_devices):
    mock_find_devices.return_value = ["XX:XX:XX:XX:XX:XX"]
    result = runner.invoke(main, ['addresses'])
    assert result.exit_code == 0
    assert "num" in result.output.lower()
    assert "XX:XX:XX:XX:XX:XX" in result.output

def test_tui_command(runner, mock_input_tui):
    result = runner.invoke(main, ['tui'])
    assert result.exit_code == 0
    mock_input_tui.assert_called_once()
    mock_input_tui.return_value.start.assert_called_once()

def test_test_command_timeout(runner, mock_nuxbt):
    # This is tricky because the test command has sleeps and loops.
    # We want to verify that the timeout argument is respected.
    # We can probably infer it by mocking time to jump forward?
    # Or just mock the args passed if we could, but here we can check the print output maybe?
    # Wait, the code prints "Connection timeout is {timeout} seconds for this test script."
    
    # We need to ensure we don't actually hang or fail early in the mocks
    instance = mock_nuxbt.return_value
    instance.get_available_adapters.return_value = ['hci0']
    instance.create_controller.return_value = 0
    # Make state connected immediately so we don't wait
    instance.state = {0: {"state": "connected"}}

    with patch('nuxbt.cli.sleep'), \
         patch('nuxbt.cli.input', return_value=""):
        result = runner.invoke(main, ['test', '--timeout', '50'])
    
    assert result.exit_code == 0
    assert "Connection timeout is 50 seconds" in result.output

def test_logging_flags_default(runner, mock_nuxbt):
    # Test -l flag
    with patch('nuxbt.cli.Nuxbt') as mock_nx:
         # Need to invoke a command that instantiates Nuxbt, e.g., demo
         # And we need to mock other things so demo doesn't fail before Nuxbt init
         instance = mock_nx.return_value
         instance.get_available_adapters.return_value = ['hci0']
         instance.create_controller.return_value = 0
         # Prevent loop
         instance.state = {0: {"state": "connected", "finished_macros": ["mid"], "errors": []}}
         instance.macro.return_value = "mid"

         result = runner.invoke(main, ['-l', 'demo'])
         assert result.exit_code == 0
         # Check if log_file_path was passed as True to Nuxbt
         call_kwargs = mock_nx.call_args[1]
         assert call_kwargs['log_file_path'] is True

def test_logging_flags_custom(runner, mock_nuxbt):
    # Test --logfile custom.log
    with patch('nuxbt.cli.Nuxbt') as mock_nx:
         instance = mock_nx.return_value
         instance.get_available_adapters.return_value = ['hci0']
         instance.create_controller.return_value = 0
         instance.state = {0: {"state": "connected", "finished_macros": ["mid"], "errors": []}}
         instance.macro.return_value = "mid"
         
         result = runner.invoke(main, ['--logfile', 'custom.log', 'demo'])
         assert result.exit_code == 0
         call_kwargs = mock_nx.call_args[1]
         assert call_kwargs['log_file_path'] == 'custom.log'
