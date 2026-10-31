[app]
title = Цветные нонограммы
package.name = picsudoku
package.domain = org.picsudoku
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json
version = 0.1

# Сборка по образцу рабочего FlowDo. ОДНА строка requirements: дубли и пустая строка ломают сборку.
# Pillow не нужен: игра грузит картинки через Kivy (SDL2_image).
requirements = python3==3.14.2,kivy==2.3.1,kivymd==1.2.0

android.api = 34
android.minapi = 23
p4a.extra_args = --allow-minsdk-ndkapi-mismatch
android.ndk = 27.3.13750724
android.ndk_api = 21
android.archs = arm64-v8a
android.build_tools_version = 34.0.0
android.sdk_path = /usr/local/lib/android/sdk
android.ndk_path = /usr/local/lib/android/sdk/ndk/27.3.13750724
android.accept_sdk_license = True
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
