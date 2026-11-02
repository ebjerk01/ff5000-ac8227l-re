#!/usr/bin/env bash
# ⚠️  EXPERIMENTAL — reverse-engineered, NOT verified on real hardware. Read-only on the
#     device (it only dumps + pulls), but use at your own risk. See ../boot-and-package.md.
#
# Pull the unit's live boot + recovery and the verified-boot state over ADB, using the
# vendor su backdoor for the dd reads. Nothing is written to the device.
#
# Usage: pull_live_boot.sh <unit-ip> [outdir]
set -euo pipefail
IP="${1:?usage: pull_live_boot.sh <unit-ip> [outdir]}"
OUT="${2:-.}"
ADB="${ADB:-adb}"
MAGIC='@#zxcvbnmasdfghjklqwertyuiop1234567890,.'

"$ADB" connect "$IP:5555"

echo "=== verified-boot / secure-boot state (want: orange) ==="
"$ADB" shell "getprop ro.boot.verifiedbootstate; getprop ro.boot.flash.locked; cat /proc/cmdline"

echo "=== dumping boot + recovery to /sdcard (root via su backdoor) ==="
printf '%s\n' \
  'dd if=/dev/block/by-name/BOOTIMG of=/sdcard/boot-live.img' \
  'dd if=/dev/block/by-name/RECOVERY of=/sdcard/recovery-live.img' \
  'ls -l /dev/block/by-name/BOOTIMG /dev/block/by-name/RECOVERY' \
  'id' \
  | "$ADB" shell "/system/xbin/su '$MAGIC'"

echo "=== pulling to $OUT ==="
mkdir -p "$OUT"
"$ADB" pull /sdcard/boot-live.img "$OUT/boot-live.img"
"$ADB" pull /sdcard/recovery-live.img "$OUT/recovery-live.img"
( cd "$OUT" && sha256sum boot-live.img recovery-live.img )
