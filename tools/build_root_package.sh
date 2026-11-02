#!/usr/bin/env bash
# ⚠️  EXPERIMENTAL — reverse-engineered from firmware, NOT verified on real hardware.
#     Flashing can PERMANENTLY BRICK your unit. Use at your own risk, confirm secure boot
#     is off first, and always build + keep a stock restore package. See ../boot-and-package.md.
#
# Wrap a single boot image into a BOOT-ONLY 8227L-8.bin for the lk USB-stick flasher.
#
# The 88xj package only flashes the partition slots it contains, so a boot-only package
# writes ONLY the boot partition and leaves system/vendor/lk/tee/recovery/seccfg untouched.
# Use for BOTH the install package (input = Magisk-patched boot) and the restore package
# (input = stock boot, pulled before patching).
#
# Usage: build_root_package.sh <boot.img> <out-8227L-8.bin>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BOOT="${1:?usage: build_root_package.sh <boot.img> <out.bin>}"
OUT="${2:?usage: build_root_package.sh <boot.img> <out.bin>}"

magic="$(dd if="$BOOT" bs=1 count=8 2>/dev/null || true)"
if [ "$magic" != "ANDROID!" ]; then
  echo "ERROR: '$BOOT' is not an Android boot image (magic='$magic'). Refusing." >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp "$BOOT" "$tmp/02-boot.img"          # slot 2 = boot; no other slots -> boot-only
python3 -I "$HERE/pack88xj.py" pack "$tmp" "$OUT"
echo "--- package contents ---"
python3 -I "$HERE/pack88xj.py" info "$OUT"
echo
echo "OK. Copy '$OUT' to a FAT-formatted USB stick as 8227L-8.bin."
echo "When lk flashes it, ONLY the boot partition is written."
