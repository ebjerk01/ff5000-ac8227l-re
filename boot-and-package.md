# Bootchain & firmware-package format (FF-5000 / AC8227L)

How the unit boots and how its firmware update package is laid out — reversed from a
firmware image, read-only. **Headline: firmware can be flashed from a plain FAT USB stick
by the bootloader itself — no PC, no BROM download mode, no USB-A-to-A cable — and the
update package is unsigned.**

## The `8227L-8.bin` update package ("88xj" container)
The USB-stick update file is a flat container. Verified exactly (file size equals the
header plus the sum of the image sizes, no remainder):

```
0x00  char[4]  magic "88xj"  (38 38 78 6a)
0x04  u32      0            (reserved/version)
0x08  u32[14]  image-size table, little-endian, indexed by partition slot:
               [0] lk    [1] arm2(tee1)  [2] boot    [3] recovery
               [4] 0     [5] tee         [6] 0       [7] and-ac
               [8] dtbo  [9] system      [10] vendor [11..13] 0
0x40  ...      image blobs concatenated in ascending slot order, skipping zero slots.
```

Each blob keeps its native header:
- `lk`, `arm2`, `tee`, `dtbo`: MTK image header — magic `0x58881688`, then `u32 size`,
  then a `char[32]` name.
- `boot`, `recovery`: Android boot image (`ANDROID!`, header v0).
- `system`, `vendor`: Android **sparse** image (magic `0xed26ff3a`).
- `and-ac`: an `AND_AC_REGION` AutoChips config blob.

There is **no trailer, no container signature, and no container checksum**. Unpacking is:
read the size table, slice from 0x40 onward. Repacking is: swap a blob, fix its size in
the table, re-concatenate.

## `lk` is the USB/SD-card flasher
The bootloader (`lk`, MediaTek Little Kernel) contains the update logic. Telltale strings:
- `forfan_sdcard_update`, `forfan_usb_update` — SD and USB update entry points.
- `=======mount %s fat start=====`, `fat32_open_file` — it mounts a FAT volume.
- `8227L-8.bin`, `8227L-8.upd` — the filenames it looks for.
- `forfan/AC8227L_Android_scatter.txt` — an MTK scatter maps images to partitions.
- Sparse-image flashing: `CHUNK_TYPE_FILL`, `CHUNK_TYPE_RAW`, `partition_write`, `[UPG]`.

So dropping a (rebuildable) `8227L-8.bin` on a FAT USB stick makes the bootloader flash
it. The same mechanism is a built-in **unbrick** path — reflash the stock package from a
stick — as long as `lk` itself is intact (so: never include `lk` in a repacked package).

## Does the USB/SD path verify images? — No (decompiled)
`lk` decompiles cleanly at base `0x81E00000` (code starts at file offset 0x200, after the
MTK mkimg wrapper). The update path:

- **`forfan_sdcard_update`**: mounts a FAT volume, reads a 4-byte **"cxj" already-applied
  marker** and only flashes if it is not yet set, draws a progress bar (green
  `0xff00ff00`), runs the flashing loop over the image table, hangs red (`0xffff0000`) if
  any image errors, else writes the `"cxj"` marker and reboots.
- **The per-image flasher**: looks up the partition by name, reads the image bytes from the
  package buffer, handles sparse images, and **writes straight to the partition**. There is
  **no hash, no signature, and no `img_auth` call anywhere in this path.**

The MTK Secure Boot routines (`img_auth`, `Verifying Image Buffer...`, `Verification
ok/fail`, `Search SECRO ... [VERIFIED]`) do exist in `lk`, but they are wired into the
*normal boot* path, not the USB/SD update path. The only checks on the update are **CRCs
on the MTK image headers** — integrity, not cryptographic, and recomputed when repacking.

So a correctly-repacked **unsigned** package flashes from a USB stick **regardless of the
secure-boot fuse state**. (On these units SBC is in any case almost always off: BROM is
reachable without a signed download agent, the build is userdebug/test-keys, SELinux is
permissive, `ro.debuggable=1`, OEM unlocking is on, no `vbmeta`.)

Operational note: the `"cxj"` done-marker means a given package applies once; to re-flash
a changed package you reset/avoid that marker.

## Tooling
A small Python `info`/`unpack`/`pack` tool for the `88xj` container is in
[tools/pack88xj.py](tools/pack88xj.py). It round-trips the stock `8227L-8.bin`
byte-for-byte (identical SHA-256), confirming the format. To build a modified package:
`unpack`, replace one `NN-*.img` (e.g. a Magisk-patched `02-boot.img`), `pack`. Never
include `00-lk`, `01-arm2`, `05-tee`, or an `seccfg` image.

## Recovery
`recovery` is a conventional Android recovery (header v0: `init`,
`init.recovery.ac8227l.rc`, `sbin/`, `sepolicy`, `res/`). A secondary fallback; the
bootloader's USB-stick reflash is the primary no-cable recovery.

## Why this matters
Combined with the root findings, you can modify this unit **without any special
hardware**: rebuild `8227L-8.bin` with (for example) a Magisk-patched `boot`, put it on a
USB stick, and let the bootloader flash it. The package is unsigned, its CRCs are
recomputable, and signature enforcement is almost certainly off.

> Keep the stock `8227L-8.bin` on a stick as your restore image. Never put `lk`, `tee`,
> or `seccfg` in a repacked package. Prove the round-trip first by repacking the
> *unchanged* stock images and confirming the unit still boots, before changing anything.
