import json
import os
from threading import RLock
import time
from socket import gethostname


from ..nuxbt import Nxbt, PRO_CONTROLLER
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import uvicorn
import socketio


app = Flask(__name__,
            static_url_path='',
            static_folder='static',)
nuxbt = Nxbt()

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

from a2wsgi import WSGIMiddleware
from socketio import WSGIApp

# async_mode='threading' to avoid eventlet auto-detection if installed
sio = SocketIO(app, async_mode='threading', cookie=False)

# Helper middleware to inject flask.app into environ for Flask-SocketIO
class FlaskAppInjector:
    def __init__(self, app, wsgi_app):
        self.app = app
        self.wsgi_app = wsgi_app
    def __call__(self, environ, start_response):
        environ['flask.app'] = self.app
        return self.wsgi_app(environ, start_response)

# Create a combined WSGI app (Socket.IO + Flask)
# This uses the synchronous Socket.IO server (threading mode) compatible with WSGI
combined_wsgi_app = WSGIApp(sio.server, app)

# Inject flask.app
injected_wsgi_app = FlaskAppInjector(app, combined_wsgi_app)

# Wrap the combined WSGI app with a2wsgi to run on uvicorn (ASGI)
app_asgi = WSGIMiddleware(injected_wsgi_app)

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



def start_web_app(ip='0.0.0.0', port=8000):
    # Run uvicorn server
    # note: app_asgi is not available in this scope easily if it's top level, 
    # but 'app.py' is the module. 
    # I should actually fix the variable access or just wrap it here?
    # The variable `app` in this file is the Flask app. 
    # I replaced the socketio init above to create `app_asgi`.
    # I need to make sure `app_asgi` is accessible or defined.
    
    # Actually, uvicorn.run expects an import string or an app instance.
    # Since I'm creating app_asgi at module level (in the previous chunk), I can use it.
    # But wait, the previous chunk target line 34.
    
    uvicorn.run(app_asgi, host=ip, port=port, ws='wsproto')


if __name__ == "__main__":
    start_web_app()
