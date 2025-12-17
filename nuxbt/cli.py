import click
import os
import traceback
import sys
import subprocess
from time import sleep, time
from random import randint

from .nuxbt import Nuxbt, PRO_CONTROLLER
from .bluez import find_devices_by_alias, is_nuxbt_plugin_enabled, get_toggle_commands
from .tui import InputTUI
from . import __version__


class GlobalContext:
    def __init__(self):
        self.logfile = None
        self.debug = False

pass_context = click.make_pass_decorator(GlobalContext, ensure=True)


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
    """Check the validity of a given Bluetooth MAC address

    :param address: A Bluetooth MAC address
    :type address: str
    :raises ValueError: If the Bluetooth address is invalid
    """

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


def ensure_plugin_enabled():
    """Checks if the NUXBT plugin is enabled. If not, exits with an error."""
    if not is_nuxbt_plugin_enabled():
        print("Error: NUXBT BlueZ plugin is not enabled.")
        print("Please run 'nuxbt toggle' to enable the plugin.")
        sys.exit(1)


@click.group()
@click.option('-l', 'enable_logging', is_flag=True, default=False,
              help="Enables logging to a file in the current working directory instead of stderr.")
@click.option('--logfile', required=False, default=None, type=str,
              help="Specifies a custom file path for logging.")
@click.option('-d', '--debug', is_flag=True, default=False,
              help="Enables debug mode in nuxbt.")
@click.version_option(__version__)
@pass_context
def main(ctx, enable_logging, logfile, debug):
    """
    Control your Nintendo Switch through a website, terminal, or macro.
    """
    if logfile:
        ctx.logfile = logfile
    elif enable_logging:
        ctx.logfile = True
    else:
        ctx.logfile = None
        
    ctx.debug = debug


@main.command()
@pass_context
def check(ctx):
    """Checks if the NUXBT BlueZ plugin override is enabled."""
    if is_nuxbt_plugin_enabled():
        print("NUXBT Plugin Enabled")
    else:
        print("NUXBT Plugin Disabled")


@main.command()
@pass_context
def toggle(ctx):
    """Toggles the NUXBT BlueZ plugin override."""
    
    enabled = is_nuxbt_plugin_enabled()
    action = "Disable" if enabled else "Enable"
    
    print(f"You are about to {action.upper()} the NUXBT BlueZ plugin.")
    print("This will require running the following commands with sudo:")
    print("")
    
    commands = get_toggle_commands(not enabled)
    for cmd in commands:
        print(f"  sudo {cmd}")
    
    print("")
    if click.confirm(f"Do you want to proceed to {action.lower()} the plugin?"):
        print(f"{action}d plugin...")
        for cmd in commands:
             # Using os.system or subprocess to run with sudo
             # If we just run it, it might prompt for password multiple times.
             # Better to run 'sudo sh -c "cmd"' or just let the user see what happens.
             # Since interactively, sudo will prompt if needed.
             subprocess.run(["sudo", "sh", "-c", cmd], check=True)
        
        print("Done.")
        # Verify
        if is_nuxbt_plugin_enabled() != enabled:
            # Should have flipped
            pass
        else:
             print("Warning: State did not seem to change. Check if previous commands succeeded.")


@main.command()
@click.option('-i', '--ip', default="0.0.0.0", type=str,
              help="Specifies the IP to run the webapp at. Defaults to 0.0.0.0")
@click.option('-p', '--port', default=8000, type=int,
              help="Specifies the port to run the webapp at. Defaults to 8000")
@click.option('--usessl', is_flag=True, default=False,
              help="Enables or disables SSL use in the webapp")
@click.option('--certpath', default=None, type=str,
              help="""Specifies the folder location for SSL certificates used
                    in the webapp. Certificates in this folder should be in the form of
                    a 'cert.pem' and 'key.pem' pair.""")
@pass_context
def webapp(ctx, ip, port, usessl, certpath):
    """Runs web server and allows for controller/macro input from a web browser."""
    ensure_plugin_enabled()
    # We need to set up logging here if we want it for the webapp process
    # But usually webapp might have its own or share logic.
    # The existing code imported and ran start_web_app.
    from .web import start_web_app
    # Note: start_web_app might need to be aware of logging, but for now we keep api same
    # or pass it if it accepts arguments. Checking app.py would be good if we can,
    # but based on previous cli, it didn't pass logging to start_web_app directly
    # except maybe via global config? No, it just called start_web_app.
    start_web_app(ip=ip, port=port, usessl=usessl, cert_path=certpath, debug=ctx.debug)


@main.command()
@pass_context
def demo(ctx):
    """Runs a demo macro (please ensure that your Switch is on the main menu's Change Grip/Order menu before running)."""
    ensure_plugin_enabled()
    nx = Nuxbt(debug=ctx.debug, log_file_path=ctx.logfile)
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

    # Run a macro on the last controller
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


@main.command()
@click.option('-c', '--commands', required=False, default=None, type=str,
              help="Specifies a macro string or a file location to load a macro string from.")
@click.option('-r', '--reconnect', is_flag=True, default=False,
              help="nuxbt will attempt to reconnect to any previously connected Nintendo Switch.")
@click.option('-a', '--address', required=False, default=False,
              help="nuxbt will attempt to reconnect to a specific Bluetooth MAC address of a Nintendo Switch.")
@pass_context
def macro(ctx, commands, reconnect, address):
    """Allows for input of a specified macro from the command line (with the argument -c) or from a file."""
    ensure_plugin_enabled()
    
    macro_content = None
    if commands:
        if os.path.isfile(commands):
            with open(commands, "r") as f:
                macro_content = f.read()
        else:
            macro_content = commands
    else:
        print("No macro commands were specified.")
        print("Please use the -c argument to specify a macro string or a file location")
        print("to load a macro string from.")
        return

    reconnect_target = get_reconnect_target(reconnect, address)

    nx = Nuxbt(debug=ctx.debug, log_file_path=ctx.logfile)
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
    while (True):
        if nx.state[index]["state"] == "crashed":
            print("Controller crashed while running macro")
            print(nx.state[index]["errors"])
            break
        if macro_id in nx.state[index]["finished_macros"]:
            print("Finished running macro. Exiting...")
            break
        sleep(1/30)


@main.command()
@click.option('-r', '--reconnect', is_flag=True, default=False,
              help="nuxbt will attempt to reconnect to any previously connected Nintendo Switch.")
@click.option('-a', '--address', required=False, default=False,
              help="nuxbt will attempt to reconnect to a specific Bluetooth MAC address of a Nintendo Switch.")
@pass_context
def tui(ctx, reconnect, address):
    """Opens a TUI that allows for direct input from the keyboard to the Switch."""
    ensure_plugin_enabled()
    reconnect_target = get_reconnect_target(reconnect, address)
    tui_instance = InputTUI(reconnect_target=reconnect_target)
    tui_instance.start()


@main.command()
@click.option('-r', '--reconnect', is_flag=True, default=False,
              help="nuxbt will attempt to reconnect to any previously connected Nintendo Switch.")
@click.option('-a', '--address', required=False, default=False,
              help="nuxbt will attempt to reconnect to a specific Bluetooth MAC address of a Nintendo Switch.")
@pass_context
def remote_tui(ctx, reconnect, address):
    """Opens a TUI that allows for direct input from the keyboard to the Switch (Remote Mode)."""
    ensure_plugin_enabled()
    reconnect_target = get_reconnect_target(reconnect, address)
    tui_instance = InputTUI(reconnect_target=reconnect_target, force_remote=True)
    tui_instance.start()


@main.command()
@pass_context
def addresses(ctx):
    """Lists the Bluetooth MAC addresses for all previously connected Nintendo Switches."""
    addresses_list = find_devices_by_alias("Nintendo Switch")

    if not addresses_list or len(addresses_list) < 1:
        print("No Switches have previously connected to this device.")
        return

    print("---------------------------")
    print("| Num | Address           |")
    print("---------------------------")
    for i in range(0, len(addresses_list)):
        address = addresses_list[i]
        print(f"| {i+1}   | {address} |")
    print("---------------------------")


@main.command()
@click.option('--timeout', default=120, type=int, help="Timeout in seconds to wait for connection. Defaults to 120.")
@pass_context
def test(ctx, timeout):
    """Runs through a series of tests to ensure NUXBT is working and compatible with your system."""
    ensure_plugin_enabled()
    # Init
    print("[1] Attempting to initialize NUXBT...")
    nx = None
    try:
        nx = Nuxbt(debug=ctx.debug, log_file_path=ctx.logfile)
    except Exception as e:
        print("Failed to initialize:")
        print(traceback.format_exc())
        exit(1)
    print("Successfully initialized NUXBT.\n")

    # Adapter Check
    print("[2] Checking for Bluetooth adapter availability...")
    adapters = None
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

    # Creating a controller
    print("[3] Please turn on your Switch and navigate to the 'Change Grip/Order menu.'")
    input("Press Enter to continue...")

    print("Creating a controller with the first Bluetooth adapter...")
    cindex = None
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

    # Controller connection check
    print("[4] Waiting for controller to connect with the Switch...")
    print(f"Connection timeout is {timeout} seconds for this test script.")
    elapsed = 0
    start_time = time()
    while nx.state[cindex]['state'] != 'connected':
        if time() - start_time >= timeout:
            print("Timeout reached, exiting...")
            exit(1)
        elif nx.state[cindex]['state'] == 'crashed':
            print("An error occurred while connecting:")
            print(nx.state[cindex]['errors'])
            exit(1)
        
        sleep(1)
    print("Successfully connected.\n")

    # Exit the Change Grip/Order Menu
    print("[5] Attempting to exit the 'Change Grip/Order Menu'...")
    nx.macro(cindex, "B 0.1s\n0.1s")
    sleep(5)
    if nx.state[cindex]['state'] != 'connected':
        print("Controller disconnected after leaving the menu.")
        print("Exiting...")
        exit(1)
    print("Controller successfully exited the menu.\n")

    print("All tests passed.")


@main.command()
@pass_context
def gui(ctx):
    """Launches the NUXBT GUI."""
    try:
        from .gui import start_gui
        start_gui()
    except ImportError as e:
        print("Failed to import GUI components. Please ensure PyQt6 is installed.")
        print(f"Error: {e}")
        sys.exit(1)



if __name__ == '__main__':
    main()
