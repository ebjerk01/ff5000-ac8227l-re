# FF-5000 (AutoChips AC8227L) head unit — reverse engineering notes

Reverse-engineering notes for a cheap Android car head unit: the **FF-5000**, built on
the **AutoChips AC8227L** SoC (a rebadged **MediaTek MT8127**), running a Junsun/"TS"
build of Android 8.1. The unit in question is installed in a VW Passat CC with a
`VW-RZ-08-0027-B1` (Raise/RZ) CAN box. This is independent research on hardware I own.

These are the same chipsets and firmware family shipped under many brand names (Junsun,
and other "TS platform" aftermarket units), so most findings should generalise across
that class of device.

## TL;DR
- The firmware ships a **hardcoded root backdoor** in `/system/xbin/su`: one magic
  argument gives an unrestricted root shell to *any* caller, no app whitelist needed.
  See [ROOT.md](ROOT.md).
- ADB is reachable over the network with **no authentication** — anyone on the same
  network gets a shell. See [ROOT.md](ROOT.md#adb).
- Any installed app can read the VIN and send frames to the car's CAN box through an
  **exported, unprotected service** (`CarInfoService`). See [car-data.md](car-data.md).
- The USB-stick firmware update package (`8227L-8.bin`) is an **unsigned** container, and
  the bootloader flashes it straight from a FAT USB stick — so a modified firmware can be
  installed with no PC, no BROM, and no special cable. See
  [boot-and-package.md](boot-and-package.md).
- Making root persistent with Magisk is straightforward on this boot layout. See
  [flash-magisk.md](flash-magisk.md).

## Contents
| File | What |
|---|---|
| [ROOT.md](ROOT.md) | The `su` backdoor + the full whitelist scheme, from decompilation. The headline finding. |
| [boot-and-package.md](boot-and-package.md) | The `8227L-8.bin` package format and the bootloader's USB-stick flasher (no-cable flashing). |
| [car-data.md](car-data.md) | How car data reaches Android, the `CarInfoService` surface, the factory CAN log. |
| [can-protocol.md](can-protocol.md) | The MCU serial frame format (sync/CMD/LEN/payload/XOR) and the two native libs behind it. |
| [flash-magisk.md](flash-magisk.md) | Making root permanent / adding Magisk on this boot layout. |
| [re-targets.md](re-targets.md) | Backlog of firmware components worth decompiling next. |
| [tools/rc4_pkg.py](tools/rc4_pkg.py) | Decryptor for the `su` package-whitelist blob (`pkg.bin`). |

## Device facts
- **Model** FF-5000. **SoC** AutoChips AC8227L = MediaTek MT8127 (4× Cortex-A7, 32-bit
  armeabi-v7a). mtkclient hardware code `0x8127`.
- **OS** Android **8.1** (API 27), marketed as "Android 11". Kernel **3.18.79**
  (`alps-mp-o1.mp5`, `full_8227L_demo` lineage). Screen 1024×600, density 240.
- **Security posture** SELinux **permissive**, userdebug / test-keys build,
  `ro.debuggable=1`, OEM unlocking enabled.
- **Firmware** `com.ts.MainUI` — a Junsun build of the "TS" platform.
- **RAM** 2 GB.

## Partition map (eMMC `mmcblk0`)
`BOOTIMG`=p10, `RECOVERY`=p11, `LK`=p6, `TEE1/2`=p7/p8, `SECCFG`=p5, `system`=p24 (ro),
`vendor`=p19 (ro), `userdata`=p26, `MISC`=p13. `boot.img` is Android header **v0**
(legacy, ramdisk-in-boot), 2 KB pages, single-slot. No `vbmeta` partition.

## What is deliberately not in this repo
- **No vendor binaries or firmware images.** Redistributing the proprietary `su`,
  `pkg.bin`, or system/vendor images is a copyright matter; the decompilation writeup
  conveys the findings without shipping the bytes. Anyone with the same unit can pull
  these from their own device.
- **No raw device dumps** (`getprop`, settings, etc.) — those carry a specific device's
  serials and identifiers.

## Disclaimer
Research on a device the author owns, published so other owners of the same hardware
understand what their unit does (unauthenticated remote root, an open CAN-box path, a
vendor backdoor). Rooting/flashing your unit can brick it and is at your own risk. Do not
use any of this against hardware you do not own.
