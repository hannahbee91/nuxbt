import pytest
import json
import os
from unittest.mock import patch
from nuxbt.web import app

@pytest.fixture
def client():
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client

@pytest.fixture
def temp_config_dir(tmp_path):
    with patch('nuxbt.web.app.get_config_dir') as mock_dir:
        mock_dir.return_value = str(tmp_path)
        yield tmp_path

def test_keybinds_persistence(client, temp_config_dir):
    # Initial get - should be empty object
    res = client.get('/api/keybinds')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data == {}

    # Save keybinds
    payload = {
        "keyboard": {"A": "KeyZ"},
        "gamepad": {"buttons": {"A": 0}, "axes": {}}
    }
    res = client.post('/api/keybinds', json=payload)
    assert res.status_code == 200

    # Verify file created
    assert os.path.exists(os.path.join(temp_config_dir, "keybinds.json"))

    # Get keybinds
    res = client.get('/api/keybinds')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["keyboard"]["A"] == "KeyZ"
