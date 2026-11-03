# CAN — Java model & built-in raw-CAN logger (FF-5000, AC8227L)

Reversed offline from the vendor UI app (`com.ts.MainUI`, `MainUI.apk`) with JADX.
Complements [can-protocol.md](can-protocol.md) (the MCU serial framing + the native
`libcan50.so` decoder) with the **Java side**: the JNI accessor surface, the decoded data
structs the UI reads, and the factory raw-CAN logger.

## Architecture (Java ↔ native)
```
MCU serial [0x23][CMD][LEN][payload][XOR]
  -> libts50xhw.so (UART)  -> libcan50.so  CCan<vehicle>::HandleCanCmd / Deal_*  (byte decode, C++)
  -> JNI -> com.lgb.canmodule.CanJni      (native-method bridge, ~1900 methods)
  -> fills com.lgb.canmodule.CanDataInfo$<Struct>  (plain int holders + Update/UpdateOnce dirty bits)
  -> com.lgb.canmodule.Can  (high-level API) -> UI activities / CarInfoService
```
Only three Java classes carry the model: **`Can`** (API), **`CanJni`** (native bridge),
**`CanDataInfo`** (hundreds of nested struct classes). The byte math lives in `libcan50.so`;
the Java structs name the decoded fields, so the two together document each signal.

## Vehicle profile
The CAN-box protocol is chosen by a profile index persisted at
`/storage/emulated/0/TsCarInfo/Can_Com_Para.bin`. `CanJni` ships decoders for ~120 vehicle
families; the method-name prefix is the family. Rough family sizes (of 1893 native methods):
`Golf 91`, `Ford 79`, `Gm 46`, `Honda 40`, `Toyota 35`, `Mzd 33`, `Psa 28`, `Hyundai 23`,
`Chrysler 23`, `Touareg 12`, `Cc 11`, … The `Rzc` infix denotes the "Raise" CAN-box protocol.

A VW car on the Raise VW box uses the **`Golf`/`Cc`** families (native `CCanGolfBase` /
`CCanGolfWc` / `CCanVwWc`).

## VW/Golf accessor surface (example of a full decode family)
Each `Golf*Get*` native call fills one or more `CanDataInfo$Golf*` structs:

| Accessor | Struct(s) | Signal group |
|---|---|---|
| `GolfGetMFD` | `GolfMFD` | instrument cluster / trip computer |
| `GolfGetACData`, `GolfWcGetAcData` | `GolfACData`, `GolfWcACData` | climate |
| `GolfGetTyres`, `GolfWcGetDirectTpmsData` | `GolfTyres`, `GolfWcDirectTpms` | TPMS |
| `GolfGetOpenClose` | `GolfOpeningAndClosing` | doors / locks / convenience |
| `GolfGetLight`, `GolfGetMirrorWiper` | `GolfLight(2)`, `GolfMirrorsAndWipers` | lights / mirrors / wipers |
| `GolfGetDrivingData*`, `GolfGetDrivingRange`, `GolfGetOilInfo` | `GolfRange`,`GolfDistance`,`GolfDrivingComm`,`GolfDrivingOil` | trip memories / range / oil |
| `GolfGetService` | `GolfVehicleNo`,`GolfDaysComm`,`GolfDistanceCommon` | service interval |
| `GolfGetReports`, `GolfGetCarTip` | `GolfCarReports`, `GolfCarTip` | warnings / tips |
| `GolfGetAmpData`, `GolfGetEleData` | `GolfAmpData`, `GolfEleData` | amplifier / electrical |
| `GolfGetSeatDriveProfile`, `GolfGetDriverAss` | `GolfSeatDriveProfile`, `GolfDriverAss(2)` | seats / driver assist |
| `GolfQuery`, `GolfSendCmd`, `GolfSetTime`, `GolfWc*Set` | — | **writes to the bus** — only with intent |

### Struct field layouts (observed; `fg…` = flag, `n…` = count)
- **`GolfMFD`** (dash/trip): `fgDigitalSpeedDisplay`, `fgCurConsumption`, `fgAvgConsumption`,
  `fgAvgSpeed`, `fgDistanceTravelled`, `fgTravellingTime`, `fgOilTemp`,
  `fgConvenienceConsumers`, `fgEcoTips`, `fgSpeedWarning`.
- **`GolfACData`** (climate): `Profile`, `SwHot`, `fgAutoRecircule`, `ClearAir`, `ClearAirPro`,
  `ChairSwSync`, `nLtChairWind`, `nRtChairWind`.
- **`GolfTyres`** (TPMS): `Data`, `Avalid`, `SpeedDW`, `fgSpeedWarning`, plus a reset flag.
- **`GolfOpeningAndClosing`** (doors): `DoorUnlocking`, `ConvOpening`, `InteriorMonitoring`,
  `fgAutoLocking`, `fgAcousticConfirm`, + several VW convenience flags.

All structs carry `Update`/`UpdateOnce` dirty bits set by the native decoder. Dump any class
with a decompiler: `com.lgb.canmodule.CanDataInfo$<Name>`.

## Built-in raw-CAN logger (factory monitor)
`com.ts.can.CanDataLogService` is a **floating-window** monitor of raw head-unit↔CAN-box
traffic (the factory-menu CAN log). Exported component + action:
`com.ts.MainUI/com.ts.can.CanDataLogService`, action `"com.ts.can.CanDataLogService"`.

- Buttons: **Receive** (start/stop capture into an in-memory list), **Pause**, **Send**
  (inject a frame from ID/data fields — a bus write), **Save**, **Min**, **Exit**.
- `saveData()` writes each captured line to **`/storage/emulated/0/TsCarInfo/CanData.txt`**
  (deleted+recreated, one frame per line, `\n`-separated).

### Capture recipe (with a root shell, car ACC on)
```
su -c 'am startservice -n com.ts.MainUI/com.ts.can.CanDataLogService'   # background svc, no UI disruption
# tap Receive on the floating window (or: input tap <x> <y>), exercise inputs, tap Save
adb pull /storage/emulated/0/TsCarInfo/CanData.txt
```
Pairs raw frames with the decode dictionary above. (Starting the service is harmless; binding
`CarInfoService` from a *foreground* app can crash the launcher, so prefer the service route.)

## Notes confirmed on a live unit
- The vendor DSP serial channel uses the `0x8A 0xA8` sync framing (seen on `/dev/ttyMT3`).
- `CarInfoService` is bindable by an unprivileged third-party app (exported, no permission).
- The MCU/CAN ttys are held exclusively by the UI process → you can't byte-steal raw frames
  off the tty; use the logger above.
