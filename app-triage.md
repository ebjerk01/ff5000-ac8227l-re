# Remaining vendor apps — security triage

Offline triage (REA/JADX + manifest/string analysis) of the vendor apps not covered by their
own docs. Covers phone-home, privileged capabilities, and purpose. See [CARCLIENT.md](carclient.md)
and [JUNCAN-TXZ.md](juncan-txz.md) for the two main cloud agents.

## Summary table
| App (package) | Purpose | Phones home | Notable caps | Severity |
|---|---|---|---|---|
| **CarClient** `com.ts.car.client` | remote mgmt / telemetry | `carnet.forfan.cn` + MQTT `47.115.178.37` | INSTALL/DELETE_PKG, GPS, mic, cam | **high** (own doc) |
| **JunCan/TXZ** `com.txznet.trace` | voice/telematics | `wss://websocket.txzing.com` | boot, location, phone-state | **high** (own doc) |
| **xfapp** `com.forfan.xfapp` | forfan service client | `m.kaikaibao.com.cn`, `forfan.com/.net` | **INSTALL_PKG + MOUNT_UNMOUNT_FS**, boot, location, root-whitelisted | **high** |
| **EasyConnected** `WWEasyConnect` (Carbit) | phone projection | `*.carbit.com.cn` (`apiota`, `api/record`) + Tencent Bugly | RECORD_AUDIO, location, phone-state, REQUEST_INSTALL, boot | medium |
| **SpeedPlay** `com.suding.speedplay` | phone projection (CarPlay/AA) | none (native libs) | **Tencent StubShell packed** (anti-RE) | medium (opaque) |
| **tscanupdate** `com.ts.tscanupdate` | CAN-box (MCU) firmware updater | none | ShellUtils flash of CAN box from bundled fw | low (local) |
| **apkmanage** `com.ts.apk` | local APK installer/browser | none | InstallApk | low (local) |
| **SRV_Upgrade** `com.android.sunoddtool` | firmware upgrade tool | none | uses `libSUNODDTOOL.so` | low (local) |
| **Specision** | diagnostics (packed, non-`com.*` root) | none found | opaque | low |

## xfapp — root-whitelisted + install + mount + phone-home
`com.forfan.xfapp` is already known to be **on the `su` root whitelist** and to run the
`xfapp_check()` challenge/response over a local socket (see [ROOT.md](ROOT.md);
native `libecode.so`). Triage adds: it **starts on boot**, holds **`INSTALL_PACKAGES`** and
**`MOUNT_UNMOUNT_FILESYSTEMS`** (can remount `system` and install apps), `ACCESS_FINE_LOCATION`,
`READ_PHONE_STATE`, `SYSTEM_ALERT_WINDOW`, and **phones home** to `m.kaikaibao.com.cn` (开开宝,
a Chinese vehicle-service platform) and `forfan.com`/`forfan.net`. So it is a third privileged,
boot-launched, internet-connected vector — and uniquely it can legitimately obtain root via the
whitelist. Treat as high-risk; disable if not needed.

## EasyConnected (Carbit) — projection app with mic + telemetry cloud
`WWEasyConnect` (Carbit's phone-projection app, "TS05" build). User-facing (not hidden), but
holds `RECORD_AUDIO`, `ACCESS_FINE_LOCATION`, `READ_PHONE_STATE`, `REQUEST_INSTALL_PACKAGES`,
`RECEIVE_BOOT_COMPLETED`, `SYSTEM_ALERT_WINDOW`. Phones home to Carbit's cloud:
`apiota.carbit.com.cn`/`sapiota…` (OTA) and `apirecord.carbit.com.cn/api/record` /
`sapirecord…` (a "record"/telemetry endpoint), plus Tencent **Bugly** (`android.bugly.qq.com`,
`rqd.uu.qq.com`) crash/analytics. Lower severity than CarClient/JunCan (user-initiated
projection, not a silent agent), but still a mic-capable app with an OTA+telemetry cloud.

## SpeedPlay — packed, opaque
`com.suding.speedplay` (速迪 SuDing projection) is wrapped with the **Tencent StubShell / legu
packer** (`com.tencent.StubShell.TxAppEntry` + `com.wrapper.proxyapplication.*`): the real dex
is encrypted and unpacked at runtime, so static analysis sees only the loader. Its projection
logic lives in native libs (`libSdCarplay.so`, `libSdAuto.so`, `libAirPlay*.so`,
`libcustomiap.so`). No cleartext phone-home URL in the loader; a full assessment would need
runtime unpacking (Frida) or native-lib RE — deferred (not root-privileged, user-facing).

## Local-only utilities (no cloud, low risk)
- **tscanupdate** (`com.ts.tscanupdate`): flashes the CAN-box/MCU firmware from a bundled,
  unzipped payload via `ShellUtils` — relevant later for understanding/choosing CAN-box fw,
  not a privacy concern.
- **apkmanage** (`com.ts.apk`): a simple local APK browser/installer.
- **SRV_Upgrade** (`com.android.sunoddtool`): local firmware-upgrade helper (`libSUNODDTOOL.so`).
- **Specision**: diagnostics; dex not under `com.*` (packed/obfuscated), no phone-home observed.

## Media apps (not triaged in depth)
TsPlayer (VLC-based), TsGallery, IpodPlayer, DvdBox, MyCamera (reversing camera — safety,
never remove), MyTouch (steering-wheel buttons), the TS Launcher, SkinStore — standard
user-facing media/UI, no cloud behaviour of note.

## Bottom line
Three privileged internet-connected agents worth keeping disabled: **CarClient**, **JunCan/TXZ**,
and **xfapp**. Two of them (CarClient, JunCan) were already disabled in debloat; **xfapp should be
added to that list**. EasyConnected is a mic-capable projection app with a telemetry cloud; keep
it only if phone projection is actually used.
