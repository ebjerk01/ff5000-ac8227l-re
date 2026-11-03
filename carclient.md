# CarClient — vendor cloud telemetry & remote-management agent

`com.ts.car.client` (`CarClient_v22_1.0.16.v22`), decompiled with JADX. ~1336 classes,
min SDK 23 / target 28. A preinstalled, **hidden** agent on this firmware.

## What it is
- `MainActivity` in category **`NOLAUNCHER`** — no launcher icon, invisible to the user.
- An **exported, unprotected** service `com.ts.car.client.CarClientService`
  (action `com.ts.car.client.CarClientService`, no `android:permission`).
- An embedded MQTT client (Eclipse Paho).

## Privileged permissions
`INSTALL_PACKAGES`, `DELETE_PACKAGES` (silent, system-privileged app install/remove),
`CAMERA`, `RECORD_AUDIO`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`,
`SYSTEM_ALERT_WINDOW`, `INTERNET`, `READ/WRITE_EXTERNAL_STORAGE`.

## Phone-home infrastructure (hardcoded)
Vendor cloud **`carnet.forfan.cn`** over plain HTTP:
- `GET /api/v1/getMqttServiceAddr` — dynamic MQTT broker discovery.
- `GET /api/v1/checkUpdate`, `/api/v1/checkMainUIUpdate` — OTA for CarClient + the main UI.
- `POST /uploadAndDownload/uploadFile`, `/uploadFiles` — file upload to the vendor.

Hardcoded fallback MQTT broker **`tcp://47.115.178.37:1883`** (plaintext MQTT, no TLS).
MQTT auth via a `userToken`; a `WhiteUser` bean gates access; an AES `SecretKeySpec` is
present. Device identity = a deviceID read from `License.ini`.

## Data collected and uploaded (`MqttUploadData` beans)
- `CanDataList$CanData{speed=…}` — live vehicle CAN data (speed, etc.).
- `CarDataList$CarData{longitude=…, latitude=…}` — **GPS position**, plus navigation route
  POIs (`FromPoi*`/`ToPoi*` lat/long), via `LocationManager`.
- `AppDataList$AppData` / `DeviceAppData` (`uploadDeviceAppData`) — the installed-app inventory.
- Arbitrary files (`CarClient/UploadFile`).

With the unit online this can continuously report **location, driving data, and installed
apps** to the vendor cloud.

## Remote commands accepted (MQTT)
CarClient-specific handlers (ignoring the Android MediaSession `MSG_*` framework constants):
`MSG_COMMAND`, `MSG_CUSTOM_ACTION`, `MSG_CHECK_MQTT_ADDRESS`, `MSG_CHECK_UPGRADE_APK`,
`MSG_CHECK_UPGRADE_MAINUI_APK`, `MSG_REBIND_MAINUI`, `MSG_ADJUST_VOLUME`. With
`INSTALL_PACKAGES`/`DELETE_PACKAGES` and an `uninstallApk` path, the broker can **push or
remove arbitrary APKs** and replace the main UI remotely.

## Risk & mitigation
A silent, iconless, system-privileged agent that exfiltrates location/driving/app data over
plaintext MQTT and accepts remote install/uninstall/update commands. The broker address is
fetched over plain HTTP, so it is also redirectable by a network attacker.

Mitigation: disable it per-user (`pm disable-user --user 0 com.ts.car.client`); it is in
`/system/priv-app` so it cannot be fully uninstalled without a `system` rw remount. Blocking
`carnet.forfan.cn` and `47.115.178.37` at the network is a further layer.

## Confidence
Static analysis (manifest + decompiled strings/class structure). Exact upload cadence, the
full `MSG_COMMAND` sub-dispatch, and key derivation were not traced to the byte; capabilities
above are inferred from permissions, endpoints, bean names, and method names.
