# Nintendo Switch 2 notes

NUXBT was written for the original Nintendo Switch. This page documents the
Switch 2 behaviour observed while testing, and the workarounds used to get a
stable connection.

## Symptoms

- The web UI stays on `connecting` (or `reconnecting`).
- `btmon` shows the console repeatedly connecting and immediately failing:

```
> HCI Event: Connect Request            Address: <switch>
< HCI Command: Accept Connection Request
> HCI Event: Connect Complete
> HCI Event: Remote Name Req Complete   Status: Authentication Failure (0x05)
> HCI Event: Disconnect Complete        Reason: Authentication Failure (0x05)
```

- `bluetoothctl info <switch>` after pairing shows:

```
Paired: yes
Bonded: no
Connected: yes
```

## Why it happens

The Switch 2 negotiates a link key with `Authentication: No Bonding` and sends
`Store hint: No` to BlueZ. BlueZ therefore does **not** persist the key on the
Pi, while the console keeps its side of the pairing.

On the next connection the console tries to authenticate with the stored key,
but the Pi has no matching key, so the link fails with
`Authentication Failure (0x05)`. Restarting the console does not remove its
stored key.

## Workaround: use a fresh adapter MAC

The most reliable workaround is to present the adapter as a **new controller**
before pairing. The console then performs a full pairing instead of trying the
stale key.

The following example sets the adapter address with the Broadcom vendor
command (used by the Pi's onboard Bluetooth). The bytes are the MAC address in
reverse order:

```bash
# Example: 7C:BB:8A:53:32:11
sudo hciconfig hci0 up
sudo hcitool -i hci0 cmd 0x3f 0x001 0x11 0x32 0x53 0x8a 0xbb 0x7c
sudo hciconfig hci0 down
sudo hciconfig hci0 up
sudo systemctl restart bluetooth
```

On adapters that support the BlueZ management API, `btmgmt public-addr` can be
used instead.

Then start NUXBT/webapp and pair again from **Controllers → Change Grip/Order**.
Using a Nintendo OUI (`7C:BB:8A`) makes the adapter look like a normal Pro
Controller to the console.

A small companion project with ready-made scripts for this workflow is at
<https://github.com/lilong7676/switch2RemoteCtl>. Its `switchctl.sh` command
`enable` rotates the MAC automatically on boot and `newmac` rotates it manually.

## Changes in this PR

- Do not attempt a link-key reconnect for devices that BlueZ reports as
  unbonded (`Bonded: no`). This is the Switch 2 case.
- Keep the adapter discoverable until a console connects (the previous 180
  second timeout is too short for the Switch 2 pairing screen).
- Use Socket.IO polling in the web UI: the webapp is served by
  `uvicorn + a2wsgi`, which does not support WebSocket, so the browser's
  upgrade attempt receives HTTP 403 and the UI loops on "reconnecting".
- Fix the CLI `-a/--address` option, which was parsed as a boolean flag.

## Tested configuration

- Raspberry Pi 5, Debian 13, kernel 6.18.50
- Onboard Broadcom Bluetooth (BCM4345)
- NUXBT 3.3.7 with the changes in this PR
- Nintendo Switch 2

Validated: initial pairing, web UI input, and reconnection after the console
was put to sleep and woken up.

This is still a workaround, not official Switch 2 support. A complete fix would
need a bonding flow that lets BlueZ persist the link key (or a way to make the
console re-pair without changing the adapter address).
