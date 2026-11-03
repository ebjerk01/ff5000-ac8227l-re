# JunCan / TXZ "Trace" — second cloud agent (voice-assistant telematics)

`com.txznet.trace` (`TXZTraceCore-junsun-tengshi-_junsun-release.apk`, sha256 f693b825…),
in `/system/priv-app/JunCan` with native `libTXZTrace.so`. Decompiled offline (REA/JADX).
The TXZ (txzing / txznet) voice-assistant + telematics SDK, Junsun-branded. Companion to the
[CarClient](carclient.md) agent — a **second** independent phone-home channel.

## Profile
- Package `com.txznet.trace`, version 1.0.0, **min/target SDK 19** (Android 4.4) → runs under
  the legacy permission model (all perms granted at install, no runtime prompts).
- Visible `MainActivity` (LAUNCHER), plus exported, unguarded:
  - service `com.txznet.sdk.service.TXZService` (action `com.txznet.trace.service.TXZService`)
  - AIDL service `com.txznet.trace.aidl.TXZAIDLService` (action `com.txznet.smartadapter.action.AidlService`)
  - receiver `ActivationInfoReceiver` — actions `com.txznet.aipal.sync` + **`BOOT_COMPLETED`**
    → **auto-starts on boot**; drives a device **activation** flow (`TYPE_ACTIVATION`,
    `mActivationDelay`/`DEFAULT_ACTIVATION_DELAY`).
  - receivers `WifiReceiver`, `LocaleChangeReceiver`.

## Permissions
`ACCESS_FINE_LOCATION` + `ACCESS_COARSE_LOCATION`, `CAMERA`, **`READ_PHONE_STATE`** (IMEI/
subscriber), `INTERNET`, `ACCESS_WIFI_STATE`+`CHANGE_WIFI_STATE`, `BLUETOOTH`+`BLUETOOTH_ADMIN`,
`SYSTEM_ALERT_WINDOW`, `DISABLE_KEYGUARD`, `RECEIVE_BOOT_COMPLETED`, `WAKE_LOCK`,
`READ/WRITE_EXTERNAL_STORAGE`, `VIBRATE`. (No `RECORD_AUDIO` in this "Trace" core — the mic/ASR
side lives elsewhere in the TXZ voice stack; this component is the telematics/activation/trace part.)

## Phone-home
Persistent **WebSocket** to the TXZ cloud:
- `wss://websocket.txzing.com/junsun/index` (production)
- `wss://websockettest.txzing.com/junsun/index` (test)

Also references `com.txznet.com`. Identity/payload keys seen: `HTTP_BODY_JSON_KEY_ANDROID_ID`
(**android_id**), location (`longitude`/`getLongitude`), plus the boot-time activation report.
So it ties the unit's android_id + location to a cloud account on the `junsun` channel.

## Risk
A second always-on, boot-launched agent with location + phone-identity + an exported AIDL
surface, holding a live WebSocket to a Chinese voice-cloud. Target SDK 19 means no runtime
permission gating. Between this and [CarClient](carclient.md), the stock firmware has **two
independent cloud channels** (`txzing.com` WS and `carnet.forfan.cn`/MQTT `47.115.178.37`).

## Mitigation (already applied)
`txznet.trace` was **disabled** in debloat (see the debloat notes). It is in
`/system/priv-app` (per-user disable, not uninstallable without `system` rw). Keep disabled;
block `*.txzing.com` + `txznet.com` at the network as a further layer.

## Confidence / limits
Static manifest + decompiled strings/class names. The exact WebSocket message schema and the
native `libTXZTrace.so` internals were not fully traced; capabilities inferred from
components, permissions, endpoints, and JSON key constants.
