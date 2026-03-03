[app]
title = Velvet
package.name = velvet
package.domain = org.velvet

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt

version = 0.2.0

requirements = python3,kivy==2.3.0,plyer

orientation = portrait
fullscreen = 1

presplash.filename = splash.png
presplash.color = #0a0a0a

android.permissions = INTERNET,ACCESS_NETWORK_STATE,RECORD_AUDIO
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
