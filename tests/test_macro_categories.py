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
def temp_macro_dir(tmp_path):
    # Patch get_macro_dir in nuxbt.web.app to return tmp_path
    with patch('nuxbt.web.app.get_macro_dir') as mock_dir:
        mock_dir.return_value = str(tmp_path)
        yield tmp_path

def test_save_and_list_macros(client, temp_macro_dir):
    # Save uncategorized macro
    res = client.post('/api/macros', json={
        "name": "Macro1",
        "category": "Uncategorized",
        "macro": "A 1s"
    })
    assert res.status_code == 200
    
    # Save categorized macro
    res = client.post('/api/macros', json={
        "name": "Macro2",
        "category": "Speedrun",
        "macro": "B 1s"
    })
    assert res.status_code == 200
    
    # List macros
    res = client.get('/api/macros')
    data = json.loads(res.data)
    
    # Check structure
    assert "Uncategorized" in data
    assert "Macro1" in data["Uncategorized"]
    assert "Speedrun" in data
    assert "Macro2" in data["Speedrun"]

def test_get_macro(client, temp_macro_dir):
    # Save macro
    client.post('/api/macros', json={
        "name": "Macro3",
        "category": "Bosses",
        "macro": "X 1s"
    })
    
    # Get macro with category
    res = client.get('/api/macros/Bosses/Macro3')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["macro"] == "X 1s"
    
    # Test 404
    res = client.get('/api/macros/Bosses/NonExistent')
    assert res.status_code == 404

def test_delete_macro(client, temp_macro_dir):
    # Save macro
    client.post('/api/macros', json={
        "name": "Macro4",
        "category": "DeleteMe",
        "macro": "Y 1s"
    })
    
    # Verify file exists
    macro_path = os.path.join(temp_macro_dir, "DeleteMe", "Macro4.txt")
    assert os.path.exists(macro_path)
    
    # Delete macro
    res = client.delete('/api/macros/DeleteMe/Macro4')
    assert res.status_code == 200
    
    # Verify file is gone
    assert not os.path.exists(macro_path)
    
    # Verify empty category directory is removed
    cat_path = os.path.join(temp_macro_dir, "DeleteMe")
    assert not os.path.exists(cat_path)

def test_backward_compatibility_get(client, temp_macro_dir):
    # Create file in root manually (simulating old version)
    with open(os.path.join(temp_macro_dir, "OldMacro.txt"), "w") as f:
        f.write("OLD 1s")
    
    # Test get via old route (which now maps to Uncategorized check)
    res = client.get('/api/macros/OldMacro')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["macro"] == "OLD 1s"
    
    # Test get via new route with Uncategorized
    res = client.get('/api/macros/Uncategorized/OldMacro')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["macro"] == "OLD 1s"

