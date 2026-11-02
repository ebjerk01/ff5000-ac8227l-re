# Car data on the FF-5000 / AC8227L (TS platform)

How vehicle data reaches Android on this unit, and the (wide-open) interface any app can
use to read it or to transmit onto the car's CAN box. Derived from decompiling the
`com.ts.MainUI` firmware.

## Data path
```
car bus  ->  CAN box (VW-RZ, decodes the bus)  ->  serial (/dev/ttyMT0, /dev/ttyMT3)
         ->  libcan50.so (native, inside com.ts.MainUI)  ->  screens & services
```
The head unit never sees raw CAN. It sees whatever the box forwards, in the box's own
protocol. `libcan50.so` contains decoders for hundreds of vehicles/boxes. On this build
the MCU/serial link is `/dev/ttyMT0` and `/dev/ttyMT3` (both world-readable/writable).

## `CarInfoService` — exported and unprotected
`com.ts.can.carinfo.CarInfoService` (descriptor `com.ts.can.carinfo.ICarInfoService`) in
`com.ts.MainUI` is **exported with no permission**, so **any installed app can bind to it
without root**.

Read transactions:

| Code | Method | Returns |
|---|---|---|
| 6 | `requestCarBaseInfo()` | `int[72]`: speed, rpm, water temp, tyres, consumption, range, distance, battery V, lights, brakes, gear, belts, VIN (idx 42–58), doors (61–66), outside temp (67), oil temp (68), locks, warnings |
| 4 | `requestCarDoorInfo()` | Doors, boot, bonnet |
| 1 | `requestCarAirInfo(String)` | One climate value by name (PWR, fgAC, nLeftTemp, nWindValue, ~60 more) |
| 2, 3 | `requestCarAirLtTemp/RtTemp()` | Climate temperatures as text |
| 5 | `requestCarIllInfo()` | Lights on |

Write/transmit transactions — **equally unprotected**, and these put bytes on the car side:

- `UartCanSend` (24): queues bytes for the CAN box. No check.
- `SendCmd` (19): queues a command for the CAN code.
- `UartOpen/Close/Read/Send` (20–23): Read/Send gated only on the serial containing `FSHW`.

**Security impact:** any app — including a sideloaded APK — can read the VIN and send to
the CAN box through this service, with no permission and no user interaction. Removing that
exposure requires modifying `MainUI`.

`TsCarService` (`com.ts.tsspeechlib.car.TsCarService`) is also exported but is mostly empty
stubs (its "speed" is GPS speed; only steering angle is real).

The richer per-brand data (`CanJni` / `GolfGet*`: driving data, consumers, service
interval, tyres, vehicle number for VW) is only reachable inside `MainUI`'s own process —
so reading it needs root, a modified `MainUI`, or the raw log below.

## Built-in factory CAN log
`CanDataLogService` is a floating window showing RX/TX bytes between the head unit and the
CAN box, with a filter and "save" to a file under internal storage (`TsCarInfo/CanData.txt`).
It is opened from the factory menu (Settings → the equipment/factory screen → factory-code
entry handled by `MainSet.DealFactorySec`) with a specific code. This dumps the box's
protocol (not raw CAN) and is the way to map what the box forwards that the `int[72]`
summary omits.

Note: the same factory-code handler dispatches many codes that do very different things —
enumerate them from the decompiled handler before entering any.

## Steering-wheel keys
Steering-wheel buttons do **not** arrive as Linux input events — only the touchscreen and
the volume/power keypad are kernel input devices. The wheel keys come in over the MCU
serial link into `MainUI`, i.e. through `libcan50.so`, and are not visible in logcat.

## ELM327 vs. the CAN box
They overlap but differ. The box forwards body/comfort data (doors, lights, climate,
outside temp, trip data) with no extra hardware; an ELM327 on the OBD port answers engine
PIDs and fault codes on request. Whether live engine values (speed, rpm, coolant) actually
come through `CarInfoService` depends on the specific car/box pairing — on some it does,
on others those fields stay zero and you need the OBD dongle.
