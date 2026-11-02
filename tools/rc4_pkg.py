#!/usr/bin/env python3
"""Decrypt (or re-encrypt) the FF-5000 / AC8227L su package whitelist blob.

/system/pkg.bin is a 256-byte RC4-encrypted, newline-separated list of package
names that /system/xbin/su grants root to. The RC4 key `lbdzjzlzq` is hardcoded in
the su binary. RC4 is symmetric, so the same routine encrypts and decrypts.

Usage:
    python3 rc4_pkg.py pkg.bin            # decrypt and print the package list
    python3 rc4_pkg.py pkg.bin out.bin    # decrypt pkg.bin -> write raw bytes to out.bin

Pull pkg.bin from your own device: `adb pull /system/pkg.bin`.
"""
import sys

KEY = b"lbdzjzlzq"


def rc4(key: bytes, data: bytes) -> bytes:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    out = bytearray()
    i = j = 0
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    data = open(sys.argv[1], "rb").read()
    dec = rc4(KEY, data)
    if len(sys.argv) >= 3:
        open(sys.argv[2], "wb").write(dec)
        return 0
    # Print the readable package list (blob is padded with random bytes after it).
    text = dec.split(b"\x00", 1)[0].decode("latin-1")
    for line in text.splitlines():
        line = line.strip()
        if line:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
