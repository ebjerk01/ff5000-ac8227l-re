# Song/media text on the VW cluster — what the head unit can and can't do

A capability finding + a workaround plan, for VW cars running this head unit via a VW-RZ
(Raise) CAN box. (Example car: a VW Passat CC with the colour MFD.)

## Confirmed: the head unit CANNOT send media text to the cluster
Everything the firmware's VW (`Golf`) CAN profile can **send** to the car is **numeric** —
`GolfSendCmd(int,int)`, `GolfWcDisplaySet(int,int)`, `GolfAmpSet(int,int)`, camera/AC/language/
driving-mode setters, etc. There is **no media/song-text send function** for VW anywhere in
`libcan50.so` / `com.lgb.canmodule.CanJni`. The media-text functions that exist
(`…GetMediaInfo`, `…GetCdTextInfo`, `…GetId3Info`) are all **receive** and only for brands where
the *factory* source feeds text to the head unit (Honda/Toyota/Lexus/Mazda…), not the reverse.

So on VW, **volume is the ceiling** of what the unit pushes to the cluster (volume is a number;
the box forwards it → the on-screen volume bar). A track title is text, and neither the firmware
nor the box builds that message. If your cluster shows a generic **"Other media"** line, that's
the box asserting an active audio source with no text — the display is awake, only the content
is missing.

## Workaround (UNVERIFIED PLAN): inject VW BAP yourself
> ⚠️ **Not tested.** Pieced together from VW PQ-platform community projects on analogous
> hardware. Every CAN ID / byte layout must be confirmed by sniffing your own bus. Injecting on
> a live vehicle bus is risky — stationary + dry-run first.

VW pushes radio/media text to the cluster with **BAP** (Bedien- und Anzeigeprotokoll) — a
stateful, **multi-frame** protocol on CAN, not a single frame:
- **Bus:** Infotainment/Comfort CAN at **100 kbps** (not 500). PQ platform.
- **Roles:** cluster = **ASG** (display); radio/head-unit = **FSG** (function controller). Text
  rides a `BAP_AUDIO` channel. From a Passat B6 toolkit (same PQ/BAP family): FSG = LSG `0x31`,
  CAN id `0x6C6` (confirm for your car).

**Approach:** add a **USB-CAN adapter** (driven by the rooted unit, or a standalone ESP32+MCP2515)
on the Infotainment CAN; run a **BAP engine** (`nor24o/bap_protocol` — a Passat B6 cluster
text injector with sniffer + dry-run; or `norly/revag-bap` — SocketCAN, Golf Mk6); bridge
Android now-playing metadata (MediaSession, via root) → the BAP audio-text message. The main
unknown is **coexistence with the box** (which already sends the "Other media"/source message) —
sniff what it sends and either match its FSG identity or send a complementary text frame.

## References
- `nor24o/bap_protocol` — https://github.com/nor24o/bap_protocol
- `norly/revag-bap` — https://github.com/norly/revag-bap
- dietmann.org — "BAP reverse engineering (Volkswagen PQ)" (BAP channel/ID table incl BAP_AUDIO)
