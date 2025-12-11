import click
from random import randint
from time import sleep
import os
import traceback
import sys

from .nuxbt import Nxbt, PRO_CONTROLLER
from .bluez import find_devices_by_alias
from .tui import InputTUI

MACRO = """
B 0.1s
0.5s
B 0.1s
0.5s
B 0.1s
0.5s
B 0.1s
1.5s
DPAD_RIGHT 0.075s
0.075s
A 0.1s
1.5s
LOOP 12
    DPAD_DOWN 0.075s
    0.075s
A 0.1s
0.25s
DPAD_DOWN 0.93s
A 0.1s
0.25s
L_STICK_PRESS 0.1s
1.0s
L_STICK@-100+000 0.75s
L_STICK@+000+100 0.75s
L_STICK@+100+000 0.75s
L_STICK@+000-100 0.75s
B 0.1s
0.25s
R_STICK_PRESS 0.1s
1.0s
R_STICK@-100+000 0.75s
R_STICK@+000+100 0.75s
R_STICK@+100+000 0.75s
R_STICK@+000-100 0.75s
B 0.1s
0.1s
B 0.1s
0.1s
B 0.1s
0.1s
B 0.1s
0.4s
DPAD_LEFT 0.1s
0.1s
A 0.1s
1.5s
A 0.1s
5.0s
"""

def random_colour():
    return [
        randint(0, 255),
        randint(0, 255),
        randint(0, 255),
    ]

def check_bluetooth_address(address):
    """Check the validity of a given Bluetooth MAC address"""
    address_bytes = len(address.split(":"))
    if address_bytes != 6:
        raise ValueError("Invalid Bluetooth address")

def get_reconnect_target(reconnect, address):
    if reconnect:
        reconnect_target = find_devices_by_alias("Nintendo Switch")
    elif address:
        check_bluetooth_address(address)
        reconnect_target = address
    else:
        reconnect_target = None
    return reconnect_target

@click.group()
@click.option('--debug/--no-debug', default=False, help="Enables debug mode in nuxbt.")
@click.option('--logfile/--no-logfile', default=False, help="Enables logging to a file in the current working directory.")
@click.pass_context
def cli(ctx, debug, logfile):
    """NUXBT: Control your Nintendo Switch via Bluetooth."""
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    ctx.obj['LOGFILE'] = logfile

@cli.command()
@click.option('--ip', default="0.0.0.0", help="Specifies the IP to run the webapp at. Defaults to 0.0.0.0")
@click.option('--port', default=8000, help="Specifies the port to run the webapp at. Defaults to 8000")
@click.option('--usessl/--no-usessl', default=False, help="Enables or disables SSL use in the webapp")
@click.option('--certpath', default=None, help="Specifies the folder location for SSL certificates.")
def webapp(ip, port, usessl, certpath):
    """Runs web server and allows for controller/macro input from a web browser."""
    from .web import start_web_app
    start_web_app(ip=ip, port=port, usessl=usessl, cert_path=certpath)

@cli.command()
@click.pass_context
def demo(ctx):
    """Runs a demo macro (ensure Switch is on 'Change Grip/Order' menu)."""
    nx = Nxbt(debug=ctx.obj['DEBUG'], log_to_file=ctx.obj['LOGFILE'])
    adapters = nx.get_available_adapters()
    if len(adapters) < 1:
        raise OSError("Unable to detect any Bluetooth adapters.")

    controller_idxs = []
    for i in range(0, len(adapters)):
        index = nx.create_controller(
            PRO_CONTROLLER,
            adapters[i],
            colour_body=random_colour(),
            colour_buttons=random_colour())
        controller_idxs.append(index)

    print("Running Demo...")
    macro_id = nx.macro(controller_idxs[-1], MACRO, block=False)
    while macro_id not in nx.state[controller_idxs[-1]]["finished_macros"]:
        state = nx.state[controller_idxs[-1]]
        if state['state'] == 'crashed':
            print("An error occurred while running the demo:")
            print(state['errors'])
            exit(1)
        sleep(1.0)
    print("Finished!")

@cli.command()
@click.option('-c', '--commands', required=True, help="Specifies a macro string or a file location.")
@click.option('-r', '--reconnect', is_flag=True, help="Attempt to reconnect to any previously connected Switch.")
@click.option('-a', '--address', help="Attempt to reconnect to a specific Bluetooth MAC address.")
@click.pass_context
def macro(ctx, commands, reconnect, address):
    """Allows for input of a specified macro."""
    macro_content = None
    if os.path.isfile(commands):
        with open(commands, "r") as f:
            macro_content = f.read()
    else:
        macro_content = commands

    reconnect_target = get_reconnect_target(reconnect, address)
    nx = Nxbt(debug=ctx.obj['DEBUG'], log_to_file=ctx.obj['LOGFILE'])
    
    print("Creating controller...")
    index = nx.create_controller(
        PRO_CONTROLLER,
        colour_body=random_colour(),
        colour_buttons=random_colour(),
        reconnect_address=reconnect_target)
    
    print("Waiting for connection...")
    nx.wait_for_connection(index)
    print("Connected!")

    print("Running macro...")
    macro_id = nx.macro(index, macro_content, block=False)
    while True:
        if nx.state[index]["state"] == "crashed":
            print("Controller crashed while running macro")
            print(nx.state[index]["errors"])
            break
        if macro_id in nx.state[index]["finished_macros"]:
            print("Finished running macro. Exiting...")
            break
        sleep(1/30)

@cli.command()
@click.option('-r', '--reconnect', is_flag=True, help="Attempt to reconnect to any previously connected Switch.")
@click.option('-a', '--address', help="Attempt to reconnect to a specific Bluetooth MAC address.")
def tui(reconnect, address):
    """Opens a TUI for direct input."""
    reconnect_target = get_reconnect_target(reconnect, address)
    tui = InputTUI(reconnect_target=reconnect_target)
    tui.start()

@cli.command()
@click.option('-r', '--reconnect', is_flag=True, help="Attempt to reconnect to any previously connected Switch.")
@click.option('-a', '--address', help="Attempt to reconnect to a specific Bluetooth MAC address.")
def remote_tui(reconnect, address):
    """Opens a remote TUI for direct input."""
    reconnect_target = get_reconnect_target(reconnect, address)
    tui = InputTUI(reconnect_target=reconnect_target, force_remote=True)
    tui.start()

@cli.command()
def addresses():
    """Lists Bluetooth MAC addresses for previously connected Switches."""
    addresses = find_devices_by_alias("Nintendo Switch")
    if not addresses or len(addresses) < 1:
        print("No Switches have previously connected to this device.")
        return

    print("---------------------------")
    print("| Num | Address           |")
    print("---------------------------")
    for i in range(0, len(addresses)):
        address = addresses[i]
        print(f"| {i+1}   | {address} |")
    print("---------------------------")

@cli.command()
@click.pass_context
def test(ctx):
    """Runs a series of tests to ensure NUXBT is working."""
    print("[1] Attempting to initialize NUXBT...")
    try:
        nx = Nxbt(debug=ctx.obj['DEBUG'], log_to_file=ctx.obj['LOGFILE'])
    except Exception as e:
        print("Failed to initialize:")
        print(traceback.format_exc())
        exit(1)
    print("Successfully initialized NUXBT.\n")

    print("[2] Checking for Bluetooth adapter availability...")
    try:
        adapters = nx.get_available_adapters()
    except Exception as e:
        print("Failed to check for adapters:")
        print(traceback.format_exc())
        exit(1)
    if len(adapters) < 1:
        print("Unable to detect any Bluetooth adapters.")
        print("Please ensure you system has Bluetooth capability.")
        exit(1)
    print(f"{len(adapters)} Bluetooth adapter(s) available.")
    print("Adapters:", adapters, "\n")

    print("[3] Please turn on your Switch and navigate to the 'Change Grip/Order menu.'")
    input("Press Enter to continue...")

    print("Creating a controller with the first Bluetooth adapter...")
    try:
        cindex = nx.create_controller(
                 PRO_CONTROLLER,
                 adapters[0],
                 colour_body=random_colour(),
                 colour_buttons=random_colour())
    except Exception as e:
        print("Failed to create a controller:")
        print(traceback.format_exc())
        exit(1)
    print("Successfully created a controller.\n")

    print("[4] Waiting for controller to connect with the Switch...")
    timeout = 120
    print(f"Connection timeout is {timeout} seconds for this test script.")
    elapsed = 0
    while nx.state[cindex]['state'] != 'connected':
        if elapsed >= timeout:
            print("Timeout reached, exiting...")
            exit(1)
        elif nx.state[cindex]['state'] == 'crashed':
            print("An error occurred while connecting:")
            print(nx.state[cindex]['errors'])
            exit(1)
        elapsed += 1
        sleep(1)
    print("Successfully connected.\n")

    print("[5] Attempting to exit the 'Change Grip/Order Menu'...")
    nx.macro(cindex, "B 0.1s\n0.1s")
    sleep(5)
    if nx.state[cindex]['state'] != 'connected':
        print("Controller disconnected after leaving the menu.")
        print("Exiting...")
        exit(1)
    print("Controller successfully exited the menu.\n")
    print("All tests passed.")

def main():
    cli(obj={})

if __name__ == "__main__":
    main()
