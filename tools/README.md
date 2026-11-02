# Tools

> ⚠️ **EXPERIMENTAL.** These are reverse-engineered from firmware and have **not been
> verified end-to-end on real hardware**. The flashing path can **permanently brick** your
> unit. Use at your own risk: confirm secure boot is off (`ro.boot.verifiedbootstate` =
> `orange`), always build and keep a **stock restore package** on a separate USB stick, and
> treat the A-to-A/BROM cable as your only guaranteed unbrick. See
> [../boot-and-package.md](../boot-and-package.md) and [../flash-magisk.md](../flash-magisk.md).

| Tool | What it does | Risk |
|---|---|---|
| `rc4_pkg.py` | Decrypt/re-encrypt the `su` package whitelist blob (`pkg.bin`, RC4 key `lbdzjzlzq`). | read-only |
| `pack88xj.py` | `info` / `unpack` / `pack` the `8227L-8.bin` update container. Round-trips the stock package byte-identical. | local files only |
| `pull_live_boot.sh` | Pull the live `boot`/`recovery` + verified-boot state over ADB (via the su backdoor). | read-only on device |
| `build_root_package.sh` | Wrap one boot image into a **boot-only** `8227L-8.bin` (flashes only the boot partition). | builds a flashable image |

None of these flash anything by themselves — flashing is a separate, deliberate step you
perform with the produced `8227L-8.bin` on a USB stick. Magisk itself is not included here;
get it from [the official releases](https://github.com/topjohnwu/Magisk/releases) (a build
that still ships `armeabi-v7a` binaries, e.g. v31.1).
