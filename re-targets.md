# Reverse-engineering backlog (FF-5000 / AC8227L)

What's been reversed, and what's worth doing next — revised with the bootchain/package
findings (see [boot-and-package.md](boot-and-package.md)) in mind. Pull targets from a
device or firmware image and analyse: native `.so`/bootloader in a disassembler (e.g.
Ghidra), APK/DEX in an Android decompiler (e.g. JADX/JEB). All read-only.

## Done
- **`/system/xbin/su`** — magic-string root backdoor + the package-whitelist scheme
  (RC4 key `lbdzjzlzq`). See [ROOT.md](ROOT.md).
- **`8227L-8.bin` package format** + **`lk` as the USB/SD flasher** — unsigned container,
  no-cable flashing path. See [boot-and-package.md](boot-and-package.md).
- **`CarInfoService`** surface (exported VIN read + CAN-box transmit). See
  [car-data.md](car-data.md).

## Tier 1 — unlocks a modified unit without special hardware
1. **`forfan_sdcard_update` inside `lk`** (raw ARM; find the MTK load base). Confirm
   whether image signature verification (`img_auth`) is called unconditionally or only
   under SBC. This is now the single most load-bearing question: it decides whether a
   repacked `8227L-8.bin` flashes from a USB stick. Pair with the on-device
   `ro.boot.verifiedbootstate` check.
2. **A `88xj` unpacker/repacker tool.** The format is known; a small tool that splits the
   package and rebuilds it (swap one image, fix the size table, re-concatenate, recompute
   the MTK header CRCs) is what turns the findings into an actual modding workflow.
3. **`libcan50.so`** (native, inside `com.ts.MainUI`). The MCU/CAN serial protocol over
   `/dev/ttyMT0`/`ttyMT3` and the per-vehicle/box decoders — the key to reading or
   emulating the CAN box. With root now freely available, capture the live serial bytes
   too and reverse the wire protocol directly, cross-checking the static decode.

## Tier 2 — vendor / cloud / security surface
4. **`com.ts.car.client`** → the vendor cloud. Root makes it practical to capture its live
   TLS traffic and reverse the actual cloud API (remote install, camera/mic), not just the
   client. The main "what can the vendor do to this unit remotely" question.
5. **`/system/bin/forfan`** (statically-linked native) and the **`/system/psw.bin`** blob
   it reads — a second password/whitelist blob alongside `pkg.bin`; worth decrypting and
   understanding.
6. **`com.forfan.xfapp`** — the `su`-whitelisted caller that implements the `127.0.0.1` +
   `md5sum` challenge; reverse the challenge/response.
7. **`com.ts.tscanupdate`** — updates the CAN box firmware over the serial link; reversing
   it exposes the box's own update/flash protocol (the deepest CAN-box control path).

## Tier 3 — platform internals (for a custom OS)
8. **The `AND_AC_REGION` ("and-ac") blob** and the `metazone`/`preloader` images referenced
   by `lk` — AutoChips-specific config/calibration regions; understanding them matters for
   building a valid custom package.
9. **Recovery image internals** — whether stock recovery offers ADB sideload (a secondary
   USB-free unbrick), and its updater-script handling.
10. **AutoChips vendor HALs** in `/vendor/bin/hw/vendor.autochips.hardware.*` (backcar,
    dvr, metalogo) — for a custom OS/HAL layer.

## Tier 4 — peripherals & UI
11. **FM/AM tuner + DAB dongle** control paths — drive the radio from a custom app.
12. **Audio routing / DSP tuning** — ties into the external DSP work.
13. **`CarplayService` + `libcarplay_*.so`** — the wired/wireless phone-projection protocol.
14. **Launcher skin format** under `/vendor/tsoem/launcher` — theme or replace the home
    screen.
