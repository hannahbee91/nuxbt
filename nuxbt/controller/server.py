import socket
import fcntl
import os
import time
import queue
import select
import logging
import traceback
import atexit
from threading import Thread

from .controller import Controller, ControllerTypes
from ..bluez import BlueZ, find_devices_by_alias
from .protocol import ControllerProtocol
from .input import InputParser
from .utils import format_msg_controller, format_msg_switch


class ControllerServer():

    def __init__(self, controller_type, adapter_path="/org/bluez/hci0",
                 state=None, task_queue=None, lock=None, colour_body=None,
                 colour_buttons=None):

        self.logger = logging.getLogger('nuxbt')
        # Cache logging level to increase performance on checks
        self.logger_level = self.logger.level

        atexit.register(self._on_exit)

        if state:
            self.state = state
        else:
            self.state = {
                "state": "",
                "finished_macros": [],
                "errors": None,
                "direct_input": None
            }

        self.task_queue = task_queue

        self.controller_type = controller_type
        self.colour_body = colour_body
        self.colour_buttons = colour_buttons

        if lock:
            self.lock = lock

        self.reconnect_counter = 0

        self._crw_running = False
        self._watchdog_connected_devices = []
        self._watchdog_connected_devices_count = {}

        # Intializing Bluetooth
        self.bt = BlueZ(adapter_path=adapter_path)

        self.controller = Controller(self.bt, self.controller_type)
        self.protocol = ControllerProtocol(
            self.controller_type,
            self.bt.address,
            colour_body=self.colour_body,
            colour_buttons=self.colour_buttons)

        self.input = InputParser(self.protocol)

        self.cached_msg = ''

    def run(self, reconnect_address=None):
        """Runs the mainloop of the controller server.

        :param reconnect_address: The Bluetooth MAC address of a
        previously connected to Nintendo Switch, defaults to None
        :type reconnect_address: string or list, optional
        """

        self.state["state"] = "initializing"

        try:
            # If we have a lock, prevent other controllers
            # from initializing at the same time and saturating the DBus,
            # potentially causing a kernel panic.
            if self.lock:
                self.lock.acquire()
            try:
                self.controller.setup()

                if reconnect_address:
                    try:
                        itr, ctrl = self.reconnect(reconnect_address)
                    except OSError:
                        itr, ctrl = self.connect()
                else:
                    itr, ctrl = self.connect()
            finally:
                if self.lock:
                    self.lock.release()

            self.switch_address = itr.getpeername()[0]
            self.state["last_connection"] = self.switch_address

            self.state["state"] = "connected"

            self.mainloop(itr, ctrl)

        except KeyboardInterrupt:
            pass
        except Exception:
            try:
                self.state["state"] = "crashed"
                self.state["errors"] = traceback.format_exc()
                return self.state
            except Exception as e:
                self.logger.debug("Error during graceful shutdown:")
                self.logger.debug(traceback.format_exc())
        finally:
            self._crw_running = False

    # While active input is held (button down/stick tilted/macro running)
    # we resend at the Bluetooth interval so a single lost packet doesn't
    # drop the input and so macro timing keeps advancing.
    ACTIVE_INTERVAL = 1 / 132
    # When idle, send a keepalive report every so often so the Switch
    # doesn't drop the controller (replaces the old tick >= 132 counter).
    KEEPALIVE_INTERVAL = 1.0

    def mainloop(self, itr, ctrl):

        # The interrupt socket plus the task queue's read end form the set of
        # event sources. select() blocks until the Switch sends something, an
        # input/macro event arrives, or the timeout fires, instead of polling
        # shared state on a fixed timer.
        if self.task_queue is not None:
            queue_reader = self.task_queue._reader
        else:
            queue_reader = None

        while True:
            # Hold/macro active -> wake at the BT interval to keep resending.
            # Idle -> wake at the keepalive interval.
            timeout = (self.ACTIVE_INTERVAL
                       if self.input.active_input_queued()
                       else self.KEEPALIVE_INTERVAL)

            read_set = [itr] if queue_reader is None else [itr, queue_reader]
            readable, _, _ = select.select(read_set, [], [], timeout)
            timed_out = not readable

            # Attempt to get output from Switch (itr stays non-blocking)
            try:
                reply = itr.recv(50)
                if self.logger_level <= logging.DEBUG and len(reply) > 40:
                    self.logger.debug(format_msg_switch(reply))
            except BlockingIOError:
                reply = None

            # Drain the task queue every loop. This is cheap when empty and
            # avoids missed wakeups from the Queue's internal buffer being out
            # of sync with the pipe that select() watches.
            if self.task_queue is not None:
                try:
                    while True:
                        msg = self.task_queue.get_nowait()
                        if msg and msg["type"] == "macro":
                            self.input.buffer_macro(
                                msg["macro"], msg["macro_id"])
                        elif msg and msg["type"] == "stop":
                            self.input.stop_macro(
                                msg["macro_id"], state=self.state)
                        elif msg and msg["type"] == "clear":
                            self.input.clear_macros()
                        elif msg and msg["type"] == "direct":
                            self.input.set_controller_input(msg["input"])
                except queue.Empty:
                    pass

            self.protocol.process_commands(reply)
            self.input.set_protocol_input(state=self.state)

            msg = self.protocol.get_report()

            if self.logger_level <= logging.DEBUG and reply and len(reply) > 45:
                self.logger.debug(format_msg_controller(msg))

            try:
                # When active input is queued (buttons held/macro running),
                # always send so the Switch sees continuous reports and
                # a single lost BT packet doesn't drop the input.
                if self.input.active_input_queued():
                    itr.sendall(msg)
                    self.cached_msg = msg[3:]
                # If the report changed (input change or a subcommand reply
                # from the Switch), send it once and cache it to avoid
                # flooding the Switch on the "Change Grip/Order" menu.
                elif msg[3:] != self.cached_msg:
                    itr.sendall(msg)
                    self.cached_msg = msg[3:]
                # The Switch sent us something that needs a reply.
                elif reply:
                    itr.sendall(msg)
                # Idle keepalive so the Switch doesn't drop the controller.
                elif timed_out:
                    itr.sendall(msg)
            except BlockingIOError:
                continue
            except OSError as e:
                # The interrupt socket died; close the stale sockets before
                # reconnecting so we don't leak them or hold PSM 17/19.
                for sock in (itr, ctrl):
                    try:
                        sock.close()
                    except OSError:
                        pass
                # Attempt to reconnect to the Switch
                itr, ctrl = self.save_connection(e)


    def save_connection(self, error, state=None):

        while self.reconnect_counter < 2:
            try:
                self.logger.debug("Attempting to reconnect")
                # Reinitialize the protocol
                self.protocol = ControllerProtocol(
                    self.controller_type,
                    self.bt.address,
                    colour_body=self.colour_body,
                    colour_buttons=self.colour_buttons)
                self.input.reassign_protocol(self.protocol)
                if self.lock:
                    self.lock.acquire()
                try:
                    itr, ctrl = self.reconnect(self.switch_address)

                    received_first_message = False
                    while True:
                        # Attempt to get output from Switch
                        try:
                            reply = itr.recv(50)
                            if self.logger_level <= logging.DEBUG and len(reply) > 40:
                                self.logger.debug(format_msg_switch(reply))
                        except BlockingIOError:
                            reply = None

                        if reply:
                            received_first_message = True

                        self.protocol.process_commands(reply)
                        msg = self.protocol.get_report()

                        if self.logger_level <= logging.DEBUG and reply:
                            self.logger.debug(format_msg_controller(msg))

                        try:
                            itr.sendall(msg)
                        except BlockingIOError:
                            continue

                        # Exit pairing loop when player lights have been set and
                        # vibration has been enabled
                        if (reply and len(reply) > 45 and
                                self.protocol.vibration_enabled and self.protocol.player_number):
                            break

                        # Switch responds to packets slower during pairing
                        # Pairing cycle responds optimally on a 15Hz loop
                        if not received_first_message:
                            time.sleep(0.05)
                        else:
                            time.sleep(1/15)

                    self.state["state"] = "connected"
                    return itr, ctrl
                finally:
                    if self.lock:
                        self.lock.release()
            except OSError:
                self.reconnect_counter += 1
                self.logger.debug(error)
                time.sleep(0.5)

        # If we can't reconnect, transition to attempting
        # to connect to any Switch.
        self.logger.debug("Connecting to any Switch")
        self.reconnect_counter = 0

        # Reinitialize the protocol
        self.protocol = ControllerProtocol(
            self.controller_type,
            self.bt.address,
            colour_body=self.colour_body,
            colour_buttons=self.colour_buttons)
        self.input.reassign_protocol(self.protocol)

        # Since we were forced to attempt a reconnection
        # we need to press the L/SL and R/SR buttons before
        # we can proceed with any input.
        if self.controller_type == ControllerTypes.PRO_CONTROLLER:
            self.input.current_macro_commands = "L R 0.0s".strip(" ").split(" ")
        elif self.controller_type == ControllerTypes.JOYCON_L:
            self.input.current_macro_commands = "JCL_SL JCL_SR 0.0s".strip(" ").split(" ")
        elif self.controller_type == ControllerTypes.JOYCON_R:
            self.input.current_macro_commands = "JCR_SL JCR_SR 0.0s".strip(" ").split(" ")

        if self.lock:
            self.lock.acquire()
        try:
            itr, ctrl = self.connect()
        finally:
            if self.lock:
                self.lock.release()

        self.state["state"] = "connected"

        # Store the Switch's address (the remote peer), not our own adapter,
        # so a later reconnect() targets the Switch instead of looping back.
        self.switch_address = itr.getpeername()[0]

        return itr, ctrl

    def connection_reset_watchdog(self):

        while self._crw_running:
            paths = self.bt.find_connected_devices(alias_filter="Nintendo Switch")
            if len(paths) > 0:
                self._watchdog_connected_devices = list(
                    set(self._watchdog_connected_devices + paths))

            disconnected = list(
                set(self._watchdog_connected_devices) - set(paths))
            if len(disconnected) > 0:
                for path in disconnected:
                    self._watchdog_connected_devices_count[path] = (
                        self._watchdog_connected_devices_count.get(path, 0) + 1
                    )
                self._watchdog_connected_devices = list(
                    set(self._watchdog_connected_devices) - set(disconnected))

            for key, count in list(self._watchdog_connected_devices_count.items()):
                if count >= 2:
                    self.logger.debug(
                        "A Nintendo Switch disconnected. Resetting Connection...")
                    self.logger.debug(f"Removing {str(key)}")
                    self.bt.remove_device(key)
                    self._watchdog_connected_devices_count[key] = 0

            time.sleep(0.1)

    def connect(self):
        """Configures as a specified controller, pairs with a Nintendo Switch,
        and creates/accepts sockets for communication with the Switch.
        """

        # The controller server will continue attempting to connect
        # to any Nintendo Switch until the connection procedure fully
        # succeeds. This prevents situations where the Switch will
        # disconnect during a connection.
        while True:
            s_ctrl = s_itr = None
            try:
                self.state["state"] = "connecting"

                # Creating control and interrupt sockets
                s_ctrl = socket.socket(
                    family=socket.AF_BLUETOOTH,
                    type=socket.SOCK_SEQPACKET,
                    proto=socket.BTPROTO_L2CAP)
                s_itr = socket.socket(
                    family=socket.AF_BLUETOOTH,
                    type=socket.SOCK_SEQPACKET,
                    proto=socket.BTPROTO_L2CAP)

                s_ctrl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s_itr.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                # Setting up HID interrupt/control sockets
                try:
                    s_ctrl.bind((self.bt.address, 17))
                    s_itr.bind((self.bt.address, 19))
                except OSError:
                    s_ctrl.bind((socket.BDADDR_ANY, 17))
                    s_itr.bind((socket.BDADDR_ANY, 19))

                s_itr.listen(1)
                s_ctrl.listen(1)

                self.bt.set_discoverable(True)

                # WARNING:
                # A device's class must be set **AFTER** discoverability
                # is set. If it is set before or in a similar timeframe,
                # the class will be reset to the default value.
                self.bt.set_class("0x02508")

                self._crw_running = True
                crw = Thread(target = self.connection_reset_watchdog, daemon=True)
                crw.start()

                itr, itr_address = s_itr.accept()
                ctrl, ctrl_address = s_ctrl.accept()

                # Send an empty input report to the Switch to prompt a reply
                self.protocol.process_commands(None)
                msg = self.protocol.get_report()
                itr.sendall(msg)

                # Setting interrupt connection as non-blocking.
                # In this case, non-blocking means it throws a "BlockingIOError"
                # for sending and receiving, instead of blocking.
                fcntl.fcntl(itr, fcntl.F_SETFL, os.O_NONBLOCK)

                # Mainloop
                received_first_message = False
                while True:
                    # Attempt to get output from Switch
                    try:
                        reply = itr.recv(50)
                        if self.logger_level <= logging.DEBUG and len(reply) > 40:
                            self.logger.debug(format_msg_switch(reply))
                    except BlockingIOError:
                        reply = None

                    if reply:
                        received_first_message = True

                    self.protocol.process_commands(reply)
                    msg = self.protocol.get_report()

                    if self.logger_level <= logging.DEBUG and reply:
                        self.logger.debug(format_msg_controller(msg))

                    try:
                        itr.sendall(msg)
                    except BlockingIOError:
                        continue

                    # Exit pairing loop when player lights have been set and
                    # vibration has been enabled
                    if (reply and len(reply) > 45 and
                            self.protocol.vibration_enabled and self.protocol.player_number):
                        break

                    # Switch responds to packets slower during pairing
                    # Pairing cycle responds optimally on a 15Hz loop
                    time.sleep(1/15)
                
                break
            except OSError as e:
                self.logger.debug(e)
                for sock in (s_ctrl, s_itr):
                    try:
                        sock.close()
                    except Exception:
                        pass

        self.input.exited_grip_order_menu = False

        return itr, ctrl

    def reconnect(self, reconnect_address):
        """Attempts to reconnect with a Switch at the given address.

        :param reconnect_address: The Bluetooth MAC address of the Switch
        :type reconnect_address: string or list
        """

        def recreate_sockets():
            # Creating control and interrupt sockets
            ctrl = socket.socket(
                family=socket.AF_BLUETOOTH,
                type=socket.SOCK_SEQPACKET,
                proto=socket.BTPROTO_L2CAP)
            itr = socket.socket(
                family=socket.AF_BLUETOOTH,
                type=socket.SOCK_SEQPACKET,
                proto=socket.BTPROTO_L2CAP)

            return itr, ctrl

        self.state["state"] = "reconnecting"

        itr = None
        ctrl = None
        if type(reconnect_address) == list:
            for address in reconnect_address:
                test_itr, test_ctrl = recreate_sockets()
                try:
                    # Setting up HID interrupt/control sockets
                    test_ctrl.connect((address, 17))
                    test_itr.connect((address, 19))

                    itr = test_itr
                    ctrl = test_ctrl
                except OSError:
                    test_itr.close()
                    test_ctrl.close()
                    pass
                else:
                    break
        elif type(reconnect_address) == str:
            test_itr, test_ctrl = recreate_sockets()

            # Setting up HID interrupt/control sockets
            test_ctrl.connect((reconnect_address, 17))
            test_itr.connect((reconnect_address, 19))

            itr = test_itr
            ctrl = test_ctrl

        if not itr and not ctrl:
            raise OSError("Unable to reconnect to sockets at the given address(es)",
                          reconnect_address)

        fcntl.fcntl(itr, fcntl.F_SETFL, os.O_NONBLOCK)

        # Send an empty input report to the Switch to prompt a reply
        self.protocol.process_commands(None)
        msg = self.protocol.get_report()
        itr.sendall(msg)

        return itr, ctrl

    def _on_exit(self):
        self._crw_running = False
        self._watchdog_connected_devices = []
        self._watchdog_connected_devices_count = {}
        self.bt.reset_adapter()
