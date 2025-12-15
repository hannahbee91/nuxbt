import json
import os
from threading import RLock
import time
from socket import gethostname

from .cert import generate_cert
from ..nuxbt import Nxbt, PRO_CONTROLLER
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from a2wsgi import WSGIMiddleware
import uvicorn
import socketio
import pathlib
import pwd


app = Flask(__name__,
            static_url_path='',
            static_folder='static',)
nuxbt = Nxbt()


def get_macro_dir():
    """
    Get the directory where macros are stored.
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
    
    macro_dir = os.path.join(home, ".config", "nuxbt", "macros")
    os.makedirs(macro_dir, exist_ok=True)
    return macro_dir


@app.route('/api/macros', methods=['GET'])
def list_macros():
    macro_dir = get_macro_dir()
    macros = []
    if os.path.exists(macro_dir):
        for f in os.listdir(macro_dir):
            if f.endswith(".txt"):
                macros.append(f[:-4])  # Remove .txt extension
    return json.dumps(macros)


@app.route('/api/macros', methods=['POST'])
def save_macro():
    data = request.json
    name = data.get("name")
    content = data.get("macro")
    
    if not name or not content:
        return "Missing name or content", 400
    
    # Sanitize name to prevent directory traversal
    name = "".join(x for x in name if x.isalnum() or x in " -_")
    
    macro_dir = get_macro_dir()
    file_path = os.path.join(macro_dir, f"{name}.txt")
    
    with open(file_path, "w") as f:
        f.write(content)
        
    return "Saved", 200


@app.route('/api/macros/<name>', methods=['GET'])
def get_macro(name):
    # Sanitize name
    name = "".join(x for x in name if x.isalnum() or x in " -_")
    
    macro_dir = get_macro_dir()
    file_path = os.path.join(macro_dir, f"{name}.txt")
    
    if not os.path.exists(file_path):
        return "Macro not found", 404
        
    with open(file_path, "r") as f:
        content = f.read()
        
    return json.dumps({"macro": content})


@app.route('/api/macros/<name>', methods=['DELETE'])
def delete_macro(name):
    # Sanitize name
    name = "".join(x for x in name if x.isalnum() or x in " -_")
    
    macro_dir = get_macro_dir()
    file_path = os.path.join(macro_dir, f"{name}.txt")
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return "Deleted", 200
    else:
        return "Macro not found", 404


# Configuring/retrieving secret key
secrets_path = os.path.join(
    os.path.dirname(__file__), "secrets.txt"
)
if not os.path.isfile(secrets_path):
    secret_key = os.urandom(24).hex()
    with open(secrets_path, "w") as f:
        f.write(secret_key)
else:
    secret_key = None
    with open(secrets_path, "r") as f:
        secret_key = f.read()
app.config['SECRET_KEY'] = secret_key

# Starting socket server with Flask app
# Ensure async_mode is threading for uvicorn/standard WSGI compatibility without eventlet
# Note: This limits SocketIO to long-polling when running under uvicorn + a2wsgi/WSGIMiddleware
# unless a2wsgi handles websocket translation (which it does for uWSGI but maybe not generic).
sio = SocketIO(app, cookie=False, async_mode='threading')

# Wrap Flask app with WSGIMiddleware to allow running with uvicorn (ASGI)
# This middleware bridges ASGI -> WSGI
flask_asgi = WSGIMiddleware(app)
app_asgi = flask_asgi

user_info_lock = RLock()
USER_INFO = {}


@app.route('/')
def index():
    return render_template('index.html')


@sio.on('connect')
def on_connect():
    with user_info_lock:
        USER_INFO[request.sid] = {}


@sio.on('state')
def on_state():
    state_proxy = nuxbt.state.copy()
    state = {}
    for controller in state_proxy.keys():
        state[controller] = state_proxy[controller].copy()
    emit('state', state)


@sio.on('disconnect')
def on_disconnect():
    print("Disconnected")
    with user_info_lock:
        try:
            index = USER_INFO[request.sid]["controller_index"]
            nuxbt.remove_controller(index)
        except KeyError:
            pass


@sio.on('shutdown')
def on_shutdown(index):
    nuxbt.remove_controller(index)


@sio.on('web_create_pro_controller')
def on_create_controller():
    print("Create Controller")

    try:
        reconnect_addresses = nuxbt.get_switch_addresses()
        index = nuxbt.create_controller(PRO_CONTROLLER, reconnect_address=reconnect_addresses)

        with user_info_lock:
            USER_INFO[request.sid]["controller_index"] = index

        emit('create_pro_controller', index)
    except Exception as e:
        emit('error', str(e))


@sio.on('input')
def handle_input(message):
    # print("Webapp Input", time.perf_counter())
    message = json.loads(message)
    index = message[0]
    input_packet = message[1]
    nuxbt.set_controller_input(index, input_packet)


@sio.on('macro')
def handle_macro(message):
    message = json.loads(message)
    index = message[0]
    macro = message[1]
    macro_id = nuxbt.macro(index, macro, block=False)
    return macro_id



@sio.on('stop_all_macros')
def handle_stop_all_macros():
    nuxbt.clear_all_macros()



def start_web_app(ip='0.0.0.0', port=8000, usessl=False, cert_path=None):
    if usessl:
        if cert_path is None:
            # Store certs in the package directory
            cert_path = os.path.join(
                os.path.dirname(__file__), "cert.pem"
            )
            key_path = os.path.join(
                os.path.dirname(__file__), "key.pem"
            )
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
