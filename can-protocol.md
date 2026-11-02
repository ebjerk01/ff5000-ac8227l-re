# MCU / CAN serial protocol (FF-5000 / AC8227L)

How Android talks to the MCU / CAN box over the internal serial link, reversed from the
`com.ts.MainUI` native libraries (read-only, from a firmware image).

## The two native libraries
- **`libts50xhw.so`** (~330 KB) — the **MCU/serial hardware layer**. JNI backing for the
  Java class `com.yyw.ts70xhw.Mcu`. Opens `/dev/ttyMT*`, owns the UART, and builds/sends
  MCU frames. Named functions include `c_uartopen/uartread/uartsend/uartsetspeed`,
  `c_SendCanMsg`, `c_SendCan360Msg`, `c_SendCanMsgConfig`, `c_SendBeep`, `c_SendClock`,
  `c_SendDisp`, `c_McuModuleInit`, `GetMcuId/Type/Ver`. Log tag `_YYW_`.
- **`libcan50.so`** (~2 MB, ~11,200 exported C++ symbols — not name-stripped) — the **CAN
  decoder**: per-vehicle/box tables that turn MCU CAN payloads into the car-data values the
  UI shows. (Per-field decode mapping is in progress.)

## MCU frame format (transmit) — confirmed
`c_SendCanMsg(buf, len)` (len ≤ 0x50) stages `[0x43][len][payload]`, and the transmitter
finalises and writes the full frame:

```
+------+------+------+-----------------+----------+
| 0x23 | CMD  | LEN  | PAYLOAD (LEN B) | CHECKSUM |
+------+------+------+-----------------+----------+
```
- **`0x23`** (`'#'`) — start/sync byte.
- **`CMD`** — command/type byte. `0x43` (`'C'`) is a CAN message for the box. Other
  senders (beep, clock, display, 360, CAN-config) use their own CMD bytes.
- **`LEN`** — payload length, max 0x50 (80).
- **`PAYLOAD`** — `LEN` bytes.
- **`CHECKSUM`** — XOR of `CMD`, `LEN`, and every payload byte (the `0x23` header is **not**
  included), stored right after the payload.
- Total bytes written = `LEN + 4`.

That is the framing to reproduce to talk to the MCU/box from your own code, or to emulate
the box for offline testing.

## A separate DSP channel
A second serial channel carries DSP / peripheral commands, read in 0x20-byte chunks into an
accumulator and framed by a **2-byte sync header `0x8A 0xA8`**, with its own per-command
checksum (`dsp cmd checksum error! cmd=0x%x`). This is the on-board DSP/beep/clock/display
path, distinct from the MCU/CAN channel.

## Decoded data model (`libcan50.so`)
`libcan50.so` exposes a large family of **`GolfGet*` JNI accessors** (1200+ symbols) over a
global decoded state struct — a far richer VW model than the `int[72]` summary: AC, seats,
driver-assist, ESC, lights, MFD, tyres, amplifier, electric consumption, driving data
(long-term / since-refuel / since-start), range, driving mode, mirror/wiper, language,
meter settings, and more.

Each item is a small record read by its accessor, e.g. `GolfGetDrivingRange` reads
`[Update:u8][UpdateOnce:u8][Value:u16][DW:u16]` and marshals it into a Java object
(`Update`/`UpdateOnce`/`Value`/`DW`) via a `CJNIHandler` helper, then clears the `Update`
dirty-bit. `Update`/`UpdateOnce` are set by the CAN decoder when new data arrives.

## Still being mapped
- The **CAN-payload → struct decoder** (the inverse of the `GolfGet*` accessors) — the real
  per-field decode, keyed by CAN id / box sub-command.
- The **receive framing** confirmation (expected to mirror the TX `0x23`/CMD/LEN/XOR).
- The full **CMD byte** list, and a cross-check against a live serial capture.

## Why it matters
With the frame format known, a custom app or OS can speak to the MCU/box directly — build
`[0x23][CMD][LEN][payload][XOR]` and write it to the MCU tty — and, once the receive path
is mapped, read car data without the vendor UI and without an OBD dongle, for whatever the
box forwards. (Transmitting onto a live vehicle bus is obviously something to do only
deliberately and at your own risk.)
