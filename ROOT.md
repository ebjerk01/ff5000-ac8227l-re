# Root on the FF-5000 / AC8227L

Two independent ways in: an **unauthenticated network ADB shell**, and a **hardcoded
backdoor in the vendor `su` binary** that turns that (unprivileged) shell into root.

> **No PC, no cable, no USB adapter, no flashing is required to get root.** It's done
> entirely over the network with `adb`. USB/BROM only enters the picture if you later
> want to flash Magisk — see [flash-magisk.md](flash-magisk.md) — and even that can be
> done without USB (at some risk). See
> [root without any hardware](#root-without-any-hardware) below.

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

<a name="root-without-any-hardware"></a>
## Root without any hardware
Because ADB needs no authentication and the `su` backdoor works from that shell, getting
a root shell requires **nothing but a network connection** to the unit — no PC-side
flashing, no BROM mode, no USB-A-to-A ("male-to-male") cable, no service connector.

```
adb connect <unit-ip>:5555
adb shell
/system/xbin/su "@#zxcvbnmasdfghjklqwertyuiop1234567890,."
id        # uid=0(root)
```

And root is **already persistent**: the backdoor lives in the read-only `system`
partition, so it is present on every boot with nothing installed. If all you want is
reliable root access, you are done here — you never need a cable or a flash.

The USB adapter / BROM path is only relevant if you specifically want **Magisk** (a root
manager, systemless modules, DenyList). Even that can be done without USB by patching and
flashing `boot` on-device with `dd` as root — but then you lose the BROM "unbrick" safety
net, so a bad `boot` flash could bootloop with only the stock recovery (if usable) as a
USB-free fallback. Details and the risk tradeoff are in
[flash-magisk.md](flash-magisk.md).

## Reproduction notes
Pull your own `/system/xbin/su` and `/system/pkg.bin` over ADB and analyse them; the
decompilation above is from a disassembler (Ghidra). Nothing here depends on binaries
shipped in this repo.
