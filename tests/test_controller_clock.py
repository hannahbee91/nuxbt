import logging
import socket

import pytest

from nuxbt.controller.server import (
    CONTROLLER_LOOP_HZ,
    NANOSECONDS_PER_SECOND,
    ControllerServer,
    _ControllerLoopClock,
)


class _FakeTime:
    def __init__(self, now_ns=10 * NANOSECONDS_PER_SECOND):
        self.now_ns = now_ns

    def monotonic_ns(self):
        return self.now_ns

    def sleep(self, seconds):
        self.now_ns += round(seconds * NANOSECONDS_PER_SECOND)

    def advance(self, nanoseconds):
        self.now_ns += nanoseconds


class _StopMainloop(RuntimeError):
    pass


class _RecordingClock:
    def __init__(self, clock, cycles):
        self.clock = clock
        self.cycles = cycles
        self.starts_ns = []

    def wait_next_cycle(self):
        if len(self.starts_ns) == self.cycles:
            raise _StopMainloop
        started_ns = self.clock.wait_next_cycle()
        self.starts_ns.append(started_ns)
        return started_ns


class _InputDependency:
    def set_controller_input(self, packet):
        pass

    def set_protocol_input(self, *, state):
        pass

    def active_input_queued(self):
        return True


class _ProtocolDependency:
    report = bytes(50)

    def __init__(self, fake_time, workload_ns):
        self.fake_time = fake_time
        self.workload_ns = workload_ns
        self.iteration = 0

    def process_commands(self, reply):
        workload = self.workload_ns[self.iteration % len(self.workload_ns)]
        self.fake_time.advance(workload)
        self.iteration += 1

    def get_report(self):
        return self.report


def _new_server(fake_time, workload_ns):
    server = object.__new__(ControllerServer)
    server.logger = logging.getLogger("nuxbt-controller-clock-test")
    server.logger_level = logging.INFO
    server.task_queue = None
    server.state = {"direct_input": None}
    server.input = _InputDependency()
    server.protocol = _ProtocolDependency(fake_time, workload_ns)
    server.cached_msg = b""
    server.tick = 1
    server.times = []
    return server


def test_clock_advances_exactly_one_second_after_132_intervals():
    fake_time = _FakeTime()
    clock = _ControllerLoopClock(
        monotonic_ns=fake_time.monotonic_ns,
        sleeper=fake_time.sleep,
    )

    starts_ns = [clock.wait_next_cycle() for _ in range(133)]

    assert starts_ns == [
        starts_ns[0]
        + index * NANOSECONDS_PER_SECOND // CONTROLLER_LOOP_HZ
        for index in range(133)
    ]
    assert starts_ns[-1] - starts_ns[0] == NANOSECONDS_PER_SECOND


def test_clock_rebases_after_a_full_period_overrun():
    fake_time = _FakeTime()
    clock = _ControllerLoopClock(
        monotonic_ns=fake_time.monotonic_ns,
        sleeper=fake_time.sleep,
    )
    first_start = clock.wait_next_cycle()
    fake_time.advance(3 * clock.period_ceiling_ns)

    rebased_start = clock.wait_next_cycle()
    next_start = clock.wait_next_cycle()

    assert rebased_start == first_start + 3 * clock.period_ceiling_ns
    assert next_start == (
        rebased_start + NANOSECONDS_PER_SECOND // CONTROLLER_LOOP_HZ
    )


@pytest.mark.parametrize("run_index", range(8))
def test_mainloop_stays_phase_locked_without_bluetooth(run_index):
    """Run the real mainloop repeatedly over a local socket and fake clock."""
    cycles = 67
    fake_time = _FakeTime(now_ns=(run_index + 1) * NANOSECONDS_PER_SECOND)
    workload_ns = [
        250_000 + ((run_index * 7_919 + index * 104_729) % 4_000_000)
        for index in range(cycles)
    ]
    clock = _RecordingClock(
        _ControllerLoopClock(
            monotonic_ns=fake_time.monotonic_ns,
            sleeper=fake_time.sleep,
        ),
        cycles,
    )
    server = _new_server(fake_time, workload_ns)
    controller_socket, peer_socket = socket.socketpair()
    controller_socket.setblocking(False)

    try:
        with pytest.raises(_StopMainloop):
            server.mainloop(controller_socket, None, clock=clock)

        peer_socket.setblocking(False)
        received = bytearray()
        while True:
            try:
                received.extend(peer_socket.recv(64 * 1024))
            except BlockingIOError:
                break
    finally:
        controller_socket.close()
        peer_socket.close()

    assert len(received) == cycles * len(_ProtocolDependency.report)
    assert clock.starts_ns == [
        clock.starts_ns[0]
        + index * NANOSECONDS_PER_SECOND // CONTROLLER_LOOP_HZ
        for index in range(cycles)
    ]
    assert clock.starts_ns[-1] - clock.starts_ns[0] == 500_000_000
