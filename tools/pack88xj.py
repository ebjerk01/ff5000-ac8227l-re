#!/usr/bin/env python3
"""Unpack / repack the FF-5000 / AC8227L "88xj" firmware update package (8227L-8.bin).

Container format (reverse-engineered):
    0x00  char[4]  magic "88xj"
    0x04  u32      reserved (0)
    0x08  u32[14]  image-size table, little-endian, indexed by partition slot
    0x40  ...      image blobs concatenated in ascending slot order (zero-size slots skipped)
No trailer, no container signature/checksum: file size == 0x40 + sum(sizes).

Slot names (positional, for convenience only; packing is name-agnostic):
    0 lk  1 arm2  2 boot  3 recovery  4 -  5 tee  6 -  7 and-ac  8 dtbo  9 system  10 vendor

Usage:
    pack88xj.py unpack <8227L-8.bin> <outdir>     # writes NN-name.img per non-empty slot
    pack88xj.py pack   <indir> <out.bin>          # rebuilds from NN-*.img files in <indir>
    pack88xj.py info   <8227L-8.bin>              # print the size table
"""
import os
import struct
import sys

MAGIC = b"88xj"
HDR = 0x40
NSLOTS = 14
NAMES = {0: "lk", 1: "arm2", 2: "boot", 3: "recovery", 5: "tee",
         7: "and-ac", 8: "dtbo", 9: "system", 10: "vendor"}


def read_table(f):
    head = f.read(HDR)
    if head[:4] != MAGIC:
        sys.exit("not an 88xj package (bad magic %r)" % head[:4])
    return list(struct.unpack("<14I", head[8:8 + NSLOTS * 4]))


def cmd_info(path):
    with open(path, "rb") as f:
        sizes = read_table(f)
    total = HDR
    for i, s in enumerate(sizes):
        if s:
            print("slot %2d  %-10s %12d bytes" % (i, NAMES.get(i, "?"), s))
            total += s
    print("expected file size = %d, actual = %d" % (total, os.path.getsize(path)))


def cmd_unpack(path, outdir):
    os.makedirs(outdir, exist_ok=True)
    with open(path, "rb") as f:
        sizes = read_table(f)
        f.seek(HDR)
        for i, s in enumerate(sizes):
            if not s:
                continue
            name = "%02d-%s.img" % (i, NAMES.get(i, "slot%d" % i))
            with open(os.path.join(outdir, name), "wb") as o:
                remaining = s
                while remaining:
                    chunk = f.read(min(1 << 20, remaining))
                    if not chunk:
                        sys.exit("unexpected EOF in slot %d" % i)
                    o.write(chunk)
                    remaining -= len(chunk)
            print("slot %2d -> %s (%d bytes)" % (i, name, s))


def cmd_pack(indir, outpath):
    # Map slot index -> file by the NN- prefix of each NN-*.img
    slot_file = {}
    for fn in os.listdir(indir):
        if fn.endswith(".img") and len(fn) >= 3 and fn[:2].isdigit() and fn[2] == "-":
            slot_file[int(fn[:2])] = os.path.join(indir, fn)
    sizes = [0] * NSLOTS
    for i, p in slot_file.items():
        sizes[i] = os.path.getsize(p)
    with open(outpath, "wb") as o:
        o.write(MAGIC + b"\x00\x00\x00\x00" + struct.pack("<14I", *sizes))
        assert o.tell() == HDR, o.tell()
        for i in range(NSLOTS):
            if sizes[i]:
                with open(slot_file[i], "rb") as f:
                    while True:
                        chunk = f.read(1 << 20)
                        if not chunk:
                            break
                        o.write(chunk)
    print("wrote %s (%d bytes)" % (outpath, os.path.getsize(outpath)))


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "info":
        cmd_info(argv[2])
    elif cmd == "unpack" and len(argv) == 4:
        cmd_unpack(argv[2], argv[3])
    elif cmd == "pack" and len(argv) == 4:
        cmd_pack(argv[2], argv[3])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
