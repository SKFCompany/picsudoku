[app]
title = Судоку-Галерея
package.name = picsudoku
package.domain = org.farhad
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json
version = 0.1

# ВАЖНО: скопируй строки requirements / osx / hostpython3 / p4a из рабочего спека FlowDo или UmBala
# (python3 и hostpython3 должны быть одной версии, kivymd==1.2.0).
requirements = python3,kivy,kivymd==1.2.0,pillow

requirements = python3==3.14.2,kivy==2.3.1,kivymd==1.2.0,plyer,fpdf2,fonttools,defusedxml,openpyxl,et_xmlfile
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
android.api = 33
android.minapi = 24
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
