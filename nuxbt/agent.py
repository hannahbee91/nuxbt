import collections.abc
import collections
import logging

# Monkey patch collections.Sequence for dbus-python compatibility (Python 3.10+)
if not hasattr(collections, 'Sequence'):
    collections.Sequence = collections.abc.Sequence

import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

AGENT_INTERFACE = "org.bluez.Agent1"
AGENT_MANAGER_INTERFACE = "org.bluez.AgentManager1"
SERVICE_NAME = "org.bluez"
BLUEZ_OBJECT_PATH = "/org/bluez"

class BlueZAgent(dbus.service.Object):
    """A BlueZ Agent that automatically accepts all pairing requests.
    This suppresses the system popup for pairing confirmation.
    """

    def __init__(self, bus, path):
        self.logger = logging.getLogger('nuxbt')
        dbus.service.Object.__init__(self, bus, path)

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Release(self):
        pass

    @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        self.logger.debug(f"AuthorizeService ({device}, {uuid})")
        return

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        self.logger.debug(f"RequestPinCode ({device})")
        return "0000"

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        self.logger.debug(f"RequestPasskey ({device})")
        return dbus.UInt32("000000")

    @dbus.service.method(AGENT_INTERFACE, in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        self.logger.debug(f"DisplayPasskey ({device}, {passkey} reached {entered})")

    @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        self.logger.debug(f"DisplayPinCode ({device}, {pincode})")

    @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        self.logger.debug(f"RequestConfirmation ({device}, {passkey})")
        return

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        self.logger.debug(f"RequestAuthorization ({device})")
        return

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Cancel(self):
        self.logger.debug("Cancel")

def run_agent_loop(agent_path="/org/bluez/nuxbt_agent"):
    """Runs the BlueZ Agent in a GLib MainLoop.
    This function blocks and should be run in a separate process.
    """
    
    # Configure DBus to use GLib MainLoop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    bus = dbus.SystemBus()
    agent = BlueZAgent(bus, agent_path)
    
    obj = bus.get_object(SERVICE_NAME, BLUEZ_OBJECT_PATH)
    manager = dbus.Interface(obj, AGENT_MANAGER_INTERFACE)
    
    capability = "DisplayYesNo"
    
    try:
        manager.RegisterAgent(agent_path, capability)
    except dbus.exceptions.DBusException as e:
        if "AlreadyExists" in str(e):
             # If agent is already registered, unregister it and re-register
             try:
                manager.UnregisterAgent(agent_path)
                manager.RegisterAgent(agent_path, capability)
             except Exception:
                 pass
        else:
            print(f"Failed to register agent: {e}")

    try:
        manager.RequestDefaultAgent(agent_path)
    except Exception as e:
        print(f"Failed to set default agent: {e}")

    mainloop = GLib.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass
