import json
import os
from threading import RLock
import time
from socket import gethostname

from .cert import generate_cert
from ..nuxbt import Nuxbt, PRO_CONTROLLER
from flask import Flask, render_template, request, jsonify
from a2wsgi import WSGIMiddleware
import uvicorn
import pathlib
import pwd
import asyncio
import threading
from aiortc import RTCPeerConnection, RTCSessionDescription


app = Flask(__name__,
            static_folder='static',)
nuxbt = None


def get_config_dir():
    """
    Get the directory where nuxbt configuration is stored.
    Tries to store in the real user's home if running as root via sudo.
    """
    try:
        # If running as root via sudo, try to get the original user's home
        sudo_user = os.environ.get('SUDO_USER')
        if sudo_user:
            home = pwd.getpwnam(sudo_user).pw_dir
        else:
            home = str(pathlib.Path.home())
    except Exception:
        # Fallback to current user's home
        home = str(pathlib.Path.home())
    
    config_dir = os.path.join(home, ".config", "nuxbt")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_macro_dir():
    """
    Get the directory where macros are stored.
    """
    config_dir = get_config_dir()
    macro_dir = os.path.join(config_dir, "macros")
    os.makedirs(macro_dir, exist_ok=True)
    return macro_dir


@app.route('/api/macros', methods=['GET'])
def list_macros():
    macro_dir = get_macro_dir()
    macros = {}
    
    if os.path.exists(macro_dir):
        # Check root for uncategorized macros
        root_macros = []
        for f in os.listdir(macro_dir):
            full_path = os.path.join(macro_dir, f)
            if os.path.isfile(full_path) and f.endswith(".txt"):
                root_macros.append(f[:-4])
            elif os.path.isdir(full_path):
                # This is a category
                cat_name = f
                cat_macros = []
                for subf in os.listdir(full_path):
                    if subf.endswith(".txt"):
                        cat_macros.append(subf[:-4])
                if cat_macros:
                    macros[cat_name] = sorted(cat_macros)
        
        if root_macros:
            macros["Uncategorized"] = sorted(root_macros)
            
    return json.dumps(macros)


@app.route('/api/macros', methods=['POST'])
def save_macro():
    data = request.json
    name = data.get("name")
    category = data.get("category", "Uncategorized")
    content = data.get("macro")
    
    if not name or not content:
        return "Missing name or content", 400
    
    # Sanitize
    name = "".join(x for x in name if x.isalnum() or x in " -_")
    category = "".join(x for x in category if x.isalnum() or x in " -_")
    
    if not name or not category:
        return "Invalid name or category", 400

    macro_dir = get_macro_dir()
    
    # Check if category directory exists, create if not
    # Treat "Uncategorized" as the root directory? 
    # Or actually make a folder "Uncategorized"?
    # Decision: treating "Uncategorized" as root for backward compat might be confusing if we mix files.
    # Let's explicitly create an "Uncategorized" folder if they save there, 
    # BUT previously saved files are in root.
    # Migration: simpler to just use root for "Uncategorized"?
    # If I use root for "Uncategorized", I need to handle that logic.
    
    target_dir = macro_dir
    if category != "Uncategorized":
        target_dir = os.path.join(macro_dir, category)
    
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, f"{name}.txt")
    
    with open(file_path, "w") as f:
        f.write(content)
        
    return "Saved", 200


@app.route('/api/macros/<name>', methods=['GET'])
def get_macro_root(name):
    # Backward compatibility: look in root (Uncategorized concept)
    return get_macro("Uncategorized", name)

@app.route('/api/macros/<category>/<name>', methods=['GET'])
def get_macro(category, name):
    name = "".join(x for x in name if x.isalnum() or x in " -_")
    category = "".join(x for x in category if x.isalnum() or x in " -_")
    
    macro_dir = get_macro_dir()
    if category == "Uncategorized":
        # Check root first for backward compat, then explicit folder
        file_path = os.path.join(macro_dir, f"{name}.txt")
        if not os.path.exists(file_path):
             file_path = os.path.join(macro_dir, category, f"{name}.txt")
    else:
        file_path = os.path.join(macro_dir, category, f"{name}.txt")
    
    if not os.path.exists(file_path):
        return "Macro not found", 404
        
    with open(file_path, "r") as f:
        content = f.read()
        
    return json.dumps({"macro": content})


@app.route('/api/macros/<name>', methods=['DELETE'])
def delete_macro_root(name):
    return delete_macro("Uncategorized", name)

@app.route('/api/macros/<category>/<name>', methods=['DELETE'])
def delete_macro(category, name):
    name = "".join(x for x in name if x.isalnum() or x in " -_")
    category = "".join(x for x in category if x.isalnum() or x in " -_")
    
    macro_dir = get_macro_dir()
    
    # Helper to delete
    did_delete = False
    
    if category == "Uncategorized":
        # Check root
        p1 = os.path.join(macro_dir, f"{name}.txt")
        if os.path.exists(p1):
            os.remove(p1)
            did_delete = True
        
        # Check folder
        p2 = os.path.join(macro_dir, category, f"{name}.txt")
        if os.path.exists(p2):
            os.remove(p2)
            did_delete = True
    else:
        p = os.path.join(macro_dir, category, f"{name}.txt")
        if os.path.exists(p):
            os.remove(p)
            did_delete = True
            
        # Clean up empty category directory
        cat_dir = os.path.join(macro_dir, category)
        if os.path.exists(cat_dir) and not os.listdir(cat_dir):
            os.rmdir(cat_dir)

    if did_delete:
        return "Deleted", 200
    else:
        return "Macro not found", 404


@app.route('/api/keybinds', methods=['GET'])
def get_keybinds():
    config_dir = get_config_dir()
    path = os.path.join(config_dir, "keybinds.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return f.read(), 200, {'Content-Type': 'application/json'}
            except:
                pass
    return json.dumps({}), 200

@app.route('/api/keybinds', methods=['POST'])
def save_keybinds():
    config_dir = get_config_dir()
    path = os.path.join(config_dir, "keybinds.json")
    try:
        data = request.json
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return "Saved", 200
    except Exception as e:
        return str(e), 500

# Configuring/retrieving secret key
config_dir = get_config_dir()
secrets_path = os.path.join(config_dir, "secrets.txt")

if not os.path.isfile(secrets_path):
    secret_key = os.urandom(24).hex()
    with open(secrets_path, "w") as f:
        f.write(secret_key)
else:
    secret_key = None
    with open(secrets_path, "r") as f:
        secret_key = f.read()
app.config['SECRET_KEY'] = secret_key

# WebRTC Management
pcs = set()
data_channels = set()

def run_async(coro):
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    return asyncio.run_coroutine_threadsafe(coro, loop)

# We need a shared loop for aiortc to manage connections
webrtc_loop = asyncio.new_event_loop()
def start_webrtc_loop():
    asyncio.set_event_loop(webrtc_loop)
    webrtc_loop.run_forever()
threading.Thread(target=start_webrtc_loop, daemon=True).start()

async def broadcast_state():
    while True:
        if nuxbt:
            state_proxy = nuxbt.state.copy()
            state = {}
            for controller in state_proxy.keys():
                state[controller] = state_proxy[controller].copy()
            
            message = json.dumps({"type": "state", "data": state})
            for channel in list(data_channels):
                if channel.readyState == "open":
                    channel.send(message)
        await asyncio.sleep(0.1)

asyncio.run_coroutine_threadsafe(broadcast_state(), webrtc_loop)

@app.route('/offer', methods=['POST'])
def offer():
    params = request.json
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        data_channels.add(channel)
        
        @channel.on("message")
        def on_message(message):
            # print(f"Received message: {message[:100]}...")
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                except Exception as e:
                    print(f"Error parsing message: {e}")
                    return

                msg_type = data.get("type")
                msg_data = data.get("data")
                msg_id = data.get("id")

                # Robustness: sometimes data might be double-stringified from frontend
                if isinstance(msg_data, str) and (msg_data.startswith("[") or msg_data.startswith("{")):
                    try:
                        msg_data = json.loads(msg_data)
                    except:
                        pass

                if msg_type == "input":
                    packet = msg_data
                    if isinstance(packet, list) and len(packet) == 2:
                        index = packet[0]
                        input_packet = packet[1]
                        nuxbt.set_controller_input(index, input_packet)
                
                elif msg_type == "macro":
                    if isinstance(msg_data, list) and len(msg_data) == 2:
                        index = msg_data[0]
                        macro = msg_data[1]
                        macro_id = nuxbt.macro(index, macro, block=False)
                        # Send response back
                        channel.send(json.dumps({
                            "type": "response",
                            "id": msg_id,
                            "data": macro_id
                        }))
                
                elif msg_type == "stop_all_macros":
                    if nuxbt:
                        nuxbt.clear_all_macros()
                
                elif msg_type == "shutdown":
                    nuxbt.remove_controller(msg_data)
                
                elif msg_type == "create_pro_controller":
                    try:
                        reconnect_addresses = nuxbt.get_switch_addresses()
                        index = nuxbt.create_controller(PRO_CONTROLLER, reconnect_address=reconnect_addresses)
                        channel.send(json.dumps({
                            "type": "create_pro_controller",
                            "data": index
                        }))
                    except Exception as e:
                        channel.send(json.dumps({
                            "type": "error",
                            "data": str(e)
                        }))

        @channel.on("close")
        def on_close():
            data_channels.discard(channel)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState == "failed" or pc.connectionState == "closed":
            await pc.close()
            pcs.discard(pc)

    async def setup_offer():
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }

    future = asyncio.run_coroutine_threadsafe(setup_offer(), webrtc_loop)
    return jsonify(future.result())

# Starting socket server with Flask app
# Wrap Flask app with WSGIMiddleware to allow running with uvicorn (ASGI)
# This middleware bridges ASGI -> WSGI
flask_asgi = WSGIMiddleware(app)
app_asgi = flask_asgi

user_info_lock = RLock()
USER_INFO = {}


@app.route('/')
def index():
    return render_template('index.html')


# Removed SocketIO handlers as they are replaced by WebRTC DataChannel handlers



def start_web_app(ip='0.0.0.0', port=8000, usessl=False, cert_path=None, debug=False):
    global nuxbt
    if nuxbt is None:
        nuxbt = Nuxbt(debug=debug)

    if usessl:
        if cert_path is None:
            # Store certs in the user's config directory
            config_dir = get_config_dir()
            cert_path = os.path.join(config_dir, "cert.pem")
            key_path = os.path.join(config_dir, "key.pem")
        else:
            # If specified, store certs at the user's preferred location
            cert_path = os.path.join(
                cert_path, "cert.pem"
            )
            key_path = os.path.join(
                cert_path, "key.pem"
            )
        if not os.path.isfile(cert_path) or not os.path.isfile(key_path):
            print(
                "\n"
                "-----------------------------------------\n"
                "---------------->WARNING<----------------\n"
                "The NUXBT webapp is being run with self-\n"
                "signed SSL certificates for use on your\n"
                "local network.\n"
                "\n"
                "These certificates ARE NOT safe for\n"
                "production use. Please generate valid\n"
                "SSL certificates if you plan on using the\n"
                "NUXBT webapp anywhere other than your own\n"
                "network.\n"
                "-----------------------------------------\n"
                "\n"
                "The above warning will only be shown once\n"
                "on certificate generation."
                "\n"
            )
            print("Generating certificates...")
            cert, key = generate_cert(gethostname())
            with open(cert_path, "wb") as f:
                f.write(cert)
            with open(key_path, "wb") as f:
                f.write(key)

        # Run with uvicorn
        # Note: uvicorn.run blocks.
        uvicorn.run(app_asgi, host=ip, port=port, ssl_keyfile=key_path, ssl_certfile=cert_path)
    else:
        uvicorn.run(app_asgi, host=ip, port=port)


if __name__ == "__main__":
    start_web_app()
