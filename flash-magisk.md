# Making root permanent / adding Magisk (FF-5000, AC8227L)

The `su` backdoor already survives reboots (it lives in the read-only `system`
partition), so you *have* persistent root access already. Magisk adds what the backdoor
doesn't: a real root manager (per-app grant/deny), **systemless** modules (no `system`
rw edits), a DenyList, and `/data`-backed state you control. This is the clean base for
customising the unit.

> You do **not** need any of this for root — see [ROOT.md](ROOT.md). Magisk is optional,
> and it is the only part that involves USB/BROM.

## Do you need the USB-A-to-A cable?
Two routes to flash the patched `boot`:

- **BROM / mtkclient over USB (needs the cable, recommended):** gives a guaranteed
  "unbrick" path — a bad `boot` can always be rewritten from the backup, because BROM
  talks to the chip below Android.
- **`dd` on-device as root (no cable, riskier):** since you already have root, you can
  back up and flash `boot` entirely over ADB with no USB at all (see Phase 1/2 below). The
  cost is that there is **no BROM safety net**: if the patched `boot` bootloops, your only
  USB-free fallback is the stock `recovery` partition (p11, left untouched) — *if* it is
  reachable (`adb reboot recovery` before boot dies, or a key combo) and *if* its
  ADB/sideload works, which varies by unit.

Bottom line: for root alone, no cable. For Magisk, the ~€3 A-to-A cable (or a micro-USB
service port if present) is cheap insurance for the one step — writing `boot` — where a
mistake without a safety net can brick the unit.

> Flashing can brick the device. Take a full backup first and keep a verified recovery
> path. **Never write `LK` (p6), `TEE1/2` (p7/p8), or `SECCFG` (p5).** Everything here is
> at your own risk.

## Why this is the easy case
- SoC AC8227L = MT8127, mtkclient hardware code `0x8127`, **single-slot** (no A/B).
- `boot.img` is **Android header v0** (legacy), 2 KB pages, **with a ramdisk** → Magisk
  patches the boot ramdisk and you flash `boot` only. No system-as-root, no A/B slots.
- **No `vbmeta` partition** → AVB/dm-verity is not enforced (matches a userdebug build
  with SELinux permissive and `ro.debuggable=1`). Nothing to "disable" or zero.

## Phase 0 — full backup via mtkclient (BROM), before any write
Put the unit in BROM mode (power off; short the test point / hold the relevant pad while
plugging USB) and read everything out with [mtkclient](https://github.com/bkerler/mtkclient):

```
mtk printgpt
mtk r boot      boot.img
mtk r recovery  recovery.img
mtk r system    system.img
mtk r vendor    vendor.img
mtk r nvram     nvram.img
mtk r nvdata    nvdata.img
mtk r protect_f protect_f.img
mtk r protect_s protect_s.img
mtk r seccfg    seccfg.img     # read only — NEVER written back
```

Checksum the dumps and store them somewhere safe. This is your recovery baseline. Confirm
`boot.img` parses (`ANDROID!` magic, sane kernel/ramdisk sizes).

## Phase 1 — recon with a root shell (no flashing yet)
```
id                                    # expect uid=0
getprop ro.boot.verifiedbootstate
cat /proc/cmdline                     # check for verity/avb flags
ls -l /dev/block/by-name              # confirm names -> pNN
dd if=/dev/block/by-name/BOOTIMG  of=/sdcard/boot-live.img   # pull & keep
```
Patch the **live** boot (your unit's exact build), not a boot pulled from a generic image.

## Phase 2 — patch & flash boot
Produce a patched boot image:
- Install the Magisk app (32-bit armeabi-v7a; use a build that still supports API 27 /
  armeabi-v7a, or patch headlessly with `magiskboot`), "Patch a File" → `boot-live.img`,
  then pull `magisk_patched-*.img`.

Flash it — prefer the recoverable route:
- **mtkclient / BROM (safe):** `mtk w boot magisk_patched.img`. BROM can always re-flash,
  so a bad patch is undone by re-writing the Phase-0 `boot.img`.
- **`dd` on-device as root (convenient, riskier):**
  `dd if=/sdcard/magisk_patched.img of=/dev/block/by-name/BOOTIMG` — only once you have the
  BROM recovery path above in hand.

Reboot, open the Magisk app to finish setup. Root is now Magisk-managed.

## Recovery if a flash goes bad
Re-enter BROM and `mtk w boot boot.img` from the Phase-0 backup; re-flash
recovery/system/vendor from the dumps if needed. Since LK/TEE/SECCFG were never written,
the bootloader and TEE chain are untouched.

## Things to verify on-device first (cheap, read-only)
- Exact `verifiedbootstate` / cmdline verity flags (confirm AVB really is off).
- That a current Magisk build still installs on API 27 / armeabi-v7a (else use an older
  version or `magiskboot` by hand).
- Any watchdog/daemon that might rewrite `boot` (uncommon on these units, but check).
