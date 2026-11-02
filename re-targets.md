# Reverse-engineering backlog (FF-5000 / AC8227L)

Firmware components worth decompiling, beyond the vendor `su` (covered in
[ROOT.md](ROOT.md)). Pull each from a device or a firmware image, and open the native
`.so` files in a disassembler (e.g. Ghidra) and the APK/DEX in an Android decompiler
(e.g. JADX/JEB). All read-only analysis.

## Tier 1 — core of the platform
1. **`com.ts.MainUI`** (priv-app) and its native **`libcan50.so`**. The heart of the
   firmware (~4800 classes): CAN decode, radio/BT, settings, factory menu, all car
   screens.
   - `libcan50.so` holds the MCU/CAN serial protocol over `ttyMT0`/`ttyMT3` and the
     per-vehicle/box decoders — the key to reading or emulating the CAN box.
   - DEX side: `CarInfoService`, `CanDataLogService`, `CanJni`/`GolfGet*`, and the
     factory-code handler (`MainSet.DealFactorySec`) — enumerate every factory code and
     what it does.
2. **`com.forfan.xfapp`** (priv-app). A `su`-whitelisted caller; implements the
   `127.0.0.1` + `md5sum` challenge that `su` runs for it. Reveals the vendor's intended
   "root helper" flow.
3. **`com.ts.car.client`** (priv-app). Vendor cloud client; `su`-whitelisted; can install
   packages and reach camera/mic. The main "what can the vendor do to this unit remotely"
   surface — what it phones home, remote-install path, any authentication.

## Tier 2 — install / update / CAN-box control
4. **`apkmanage`** (priv-app) — silent package manager; how apps get pushed/updated.
5. **`com.ts.tscanupdate`** — updates the CAN box firmware; `su`-whitelisted. Decompile to
   learn the box update/flash protocol over the serial link (the deepest CAN-box control
   path). Do not exercise any transmit path against a live bus without care.
6. **`com.txznet.aipal.sync`** ("JunCan") — Junsun/TXZ tracing + sync; telemetry that
   leaves the unit.

## Tier 3 — UI / media / customisation
7. **Launcher** (`8227LTsLauncher2_*`) + skins under `/vendor/tsoem/launcher` — basis for
   a custom home screen.
8. **`com.forfan.skinstore`** — `su`-whitelisted theme delivery.
9. **TsPlayer / TsGallery / IpodPlayer / 360Camera** — TS media + camera apps; audio
   routing.

## Tier 4 — platform / security context
10. **EngineerMode.apk** — MTK engineer menu; may expose serial/CAN test modes without
    root.
11. **`/vendor/bin/hw/vendor.autochips.hardware.*`** (backcar, dvr, metalogo) —
    AutoChips-specific HAL services; relevant for a custom OS/HAL layer.
