import pytest
from unittest.mock import MagicMock, patch
import sys
from click.testing import CliRunner

# Ensure dbus is mocked
if 'dbus' not in sys.modules:
    sys.modules['dbus'] = MagicMock()

from nuxbt.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_nxbt_cls():
    with patch('nuxbt.cli.Nxbt') as mock:
        yield mock

def test_cli_help(runner):
    """Test that the CLI shows help."""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "NUXBT: Control your Nintendo Switch via Bluetooth." in result.output

def test_cli_demo(runner, mock_nxbt_cls):
    """Test the demo command."""
    mock_instance = mock_nxbt_cls.return_value
    mock_instance.get_available_adapters.return_value = ['/org/bluez/hci0']
    mock_instance.create_controller.return_value = 0
    mock_instance.state = {0: {'state': 'connected', 'finished_macros': ['123']}}
    mock_instance.macro.return_value = '123'
    
    with patch('time.sleep', side_effect=[None, None, None]):
        result = runner.invoke(cli, ['demo'])
    
    assert result.exit_code == 0
    assert mock_instance.create_controller.called
    assert mock_instance.macro.called
    assert "Running Demo..." in result.output

def test_cli_macro_file(runner, mock_nxbt_cls, tmp_path):
    """Test macro command with file input."""
    # Create temp macro file
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "test.macro"
    p.write_text("A 0.1s")
    
    mock_instance = mock_nxbt_cls.return_value
    mock_instance.create_controller.return_value = 0
    mock_instance.state = {0: {'state': 'connected', 'finished_macros': ['123']}}
    mock_instance.macro.return_value = '123'
    
    with patch('time.sleep', side_effect=[None]):
        result = runner.invoke(cli, ['macro', '-c', str(p)])
        
    assert result.exit_code == 0
    assert mock_instance.macro.called
    call_args = mock_instance.macro.call_args
    assert call_args[0][1] == "A 0.1s"

def test_cli_macro_string(runner, mock_nxbt_cls):
    """Test macro command with string input."""
    mock_instance = mock_nxbt_cls.return_value
    mock_instance.create_controller.return_value = 0
    mock_instance.state = {0: {'state': 'connected', 'finished_macros': ['123']}}
    mock_instance.macro.return_value = '123'
    
    with patch('time.sleep', side_effect=[None]):
        result = runner.invoke(cli, ['macro', '-c', 'B 1s'])
        
    assert result.exit_code == 0
    assert mock_instance.macro.called
    call_args = mock_instance.macro.call_args
    assert call_args[0][1] == "B 1s"

def test_cli_webapp(runner):
    """Test the webapp command."""
    with patch('nuxbt.web.start_web_app') as mock_start:
        result = runner.invoke(cli, ['webapp'])
        assert result.exit_code == 0
        assert mock_start.called
