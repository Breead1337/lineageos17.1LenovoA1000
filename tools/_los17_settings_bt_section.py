# -*- coding: utf-8 -*-
u"""A1000 / Android 10: Bluetooth — самостоятельный пункт главной настроек (как в девятке).

В десятке Bluetooth спрятан: переключатель — в «Подключённые устройства →
Настройки подключения → Bluetooth», списки устройств — в «Подключённых
устройствах». Переносим как в _los16_settings_bt_section.py, но под десятку:

1. top_level_settings.xml — главная в десятке уже XML, а не манифест: пункт
   «Bluetooth» (order -115, между «Сетью» и «Подключёнными устройствами»),
   открывает BluetoothDashboardFragment (там переключатель в switchbar).
2. bluetooth_screen.xml — сюда уезжают группы устройств из
   connected_devices.xml. Ключи НЕ менять: контроллеры ищут Preference по ним.
3. BluetoothDashboardFragment.onAttach — use(...).init(this) для них, иначе не
   подпишутся на события. onAttach в классе уже есть — дописываем в него.
4. ConnectedDeviceDashboardFragment.onAttach — убрать use() унесённых:
   use() вернёт null, и .init() упадёт NPE.
5. Манифест: android.settings.BLUETOOTH_SETTINGS (долгое нажатие на плитку BT)
   теперь ведёт в Bluetooth, а не в «Подключённые устройства»; фрагмент
   разрешён в SettingsGateway (иначе «Invalid fragment for this activity»).
6. PrintSettingPreferenceController — печать вырезана из сборки,
   PrintManager == null, Lifecycle зовёт onStart и у недоступных контроллеров:
   «Настройки подключения» роняли весь процесс настроек (_los16_settings_print_npe.py).
"""
import io

S = '/home/ard/los17/packages/apps/Settings/'


def edit(path, pairs, marker):
    p = S + path
    s = io.open(p, encoding='utf-8').read()
    if marker in s:
        print(path + ': уже'); return
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:80])
        s = s.replace(old, new)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print(path + ': правлен')


# ---------- 1. пункт главной ----------
edit('res/xml/top_level_settings.xml', [(
    u'    <Preference\n        android:key="top_level_connected_devices"',
    u'    <!-- A1000: Bluetooth отдельным разделом, как в девятке -->\n'
    u'    <Preference\n'
    u'        android:key="top_level_bluetooth"\n'
    u'        android:title="@string/bluetooth_settings_title"\n'
    u'        android:icon="@drawable/ic_homepage_bluetooth"\n'
    u'        android:order="-115"\n'
    u'        android:fragment="com.android.settings.connecteddevice.BluetoothDashboardFragment"/>\n'
    u'\n'
    u'    <Preference\n        android:key="top_level_connected_devices"')], 'top_level_bluetooth')

p = S + 'res/drawable/ic_homepage_bluetooth.xml'
io.open(p, 'w', encoding='utf-8', newline='\n').write(u'''<?xml version="1.0" encoding="utf-8"?>
<!-- A1000: иконка пункта Bluetooth на главной, в стиле соседних ic_homepage_* -->
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <com.android.settingslib.widget.AdaptiveIconShapeDrawable
            android:width="@dimen/dashboard_tile_image_size"
            android:height="@dimen/dashboard_tile_image_size"
            android:color="@color/homepage_generic_icon_background" />
    </item>
    <item
        android:width="@dimen/dashboard_tile_foreground_image_size"
        android:height="@dimen/dashboard_tile_foreground_image_size"
        android:start="@dimen/dashboard_tile_foreground_image_inset"
        android:top="@dimen/dashboard_tile_foreground_image_inset">
        <vector android:width="24dp" android:height="24dp"
            android:viewportWidth="24" android:viewportHeight="24">
            <path android:fillColor="@android:color/white"
                android:pathData="M17.71,7.71L12,2h-1v7.59L6.41,5 5,6.41 10.59,12 5,17.59 6.41,19 11,14.41L11,22h1l5.71,-5.71 -4.3,-4.29 4.3,-4.29zM13,5.83l1.88,1.88L13,9.59L13,5.83zM14.88,16.29L13,18.17v-3.76l1.88,1.88z"/>
        </vector>
    </item>
</layer-list>
''')
print('res/drawable/ic_homepage_bluetooth.xml: создан')

# ---------- 2. группы устройств: connected_devices.xml -> bluetooth_screen.xml ----------
GROUPS = u'''    <PreferenceCategory
        android:key="available_device_list"
        android:title="@string/connected_device_available_media_title"
        settings:controller="com.android.settings.connecteddevice.AvailableMediaDeviceGroupController"/>

    <PreferenceCategory
        android:key="connected_device_list"
        android:title="@string/connected_device_connected_title"
        settings:controller="com.android.settings.connecteddevice.ConnectedDeviceGroupController"/>

    <PreferenceCategory
        android:key="saved_tws_device_list"
        android:title="@string/connected_tws_device_saved_title"
        settings:controller="com.android.settings.connecteddevice.SavedTwsDeviceGroupController"/>

'''
PREV = u'''    <PreferenceCategory
        android:key="previously_connected_devices"
        android:title="@string/connected_device_previously_connected_title"
        settings:controller="com.android.settings.connecteddevice.PreviouslyConnectedDevicePreferenceController">

        <Preference
            android:key="previously_connected_devices_see_all"
            android:title="@string/previous_connected_see_all"
            android:icon="@drawable/ic_chevron_right_24dp"
            android:order="10"
            android:fragment="com.android.settings.connecteddevice.PreviouslyConnectedDeviceDashboardFragment"/>
    </PreferenceCategory>

'''
ADD = u'''    <com.android.settingslib.RestrictedPreference
        android:key="add_bt_devices"
        android:title="@string/bluetooth_pairing_pref_title"
        android:icon="@drawable/ic_add_24dp"
        android:summary="@string/connected_device_add_device_summary"
        android:fragment="com.android.settings.bluetooth.BluetoothPairingDetail"
        settings:allowDividerAbove="true"
        settings:userRestriction="no_config_bluetooth"
        settings:useAdminDisabledSummary="true"
        settings:controller="com.android.settings.connecteddevice.AddDevicePreferenceController"/>

'''
edit('res/xml/connected_devices.xml', [
    (GROUPS, u''), (PREV, u''),
    (ADD, u'    <!-- A1000: всё про Bluetooth переехало в свой раздел (bluetooth_screen.xml) -->\n\n'),
], 'A1000')

edit('res/xml/bluetooth_screen.xml', [
    (u'    <com.android.settingslib.RestrictedPreference\n        android:key="bluetooth_screen_add_bt_devices"',
     u'    <!-- A1000: списки устройств перенесены из connected_devices.xml.\n'
     u'         Ключи менять нельзя: контроллеры ищут Preference по ним. -->\n' + GROUPS +
     u'    <com.android.settingslib.RestrictedPreference\n        android:key="bluetooth_screen_add_bt_devices"'),
    (u'AddDevicePreferenceController"/>\n\n</PreferenceScreen>',
     u'AddDevicePreferenceController"/>\n\n' + PREV.replace(u'    <PreferenceCategory\n',
     u'    <PreferenceCategory\n        settings:allowDividerAbove="true"\n', 1) + u'</PreferenceScreen>'),
], 'A1000')

# ---------- 3, 4. фрагменты ----------
CD = 'src/com/android/settings/connecteddevice/'
edit(CD + 'BluetoothDashboardFragment.java', [(
    u'        use(BluetoothDeviceRenamePreferenceController.class).setFragment(this);\n',
    u'        use(BluetoothDeviceRenamePreferenceController.class).setFragment(this);\n'
    u'        // A1000: списки устройств переехали сюда из «Подключённых устройств».\n'
    u'        use(AvailableMediaDeviceGroupController.class).init(this);\n'
    u'        use(ConnectedDeviceGroupController.class).init(this);\n'
    u'        use(SavedTwsDeviceGroupController.class).init(this);\n'
    u'        use(PreviouslyConnectedDevicePreferenceController.class).init(this);\n')],
    'A1000')
edit(CD + 'ConnectedDeviceDashboardFragment.java', [(
    u'        use(AvailableMediaDeviceGroupController.class).init(this);\n'
    u'        use(ConnectedDeviceGroupController.class).init(this);\n'
    u'        use(SavedTwsDeviceGroupController.class).init(this);\n'
    u'        use(PreviouslyConnectedDevicePreferenceController.class).init(this);\n',
    u'        // A1000: группы устройств уехали в раздел Bluetooth; use() вернул бы null.\n')],
    'A1000')

# ---------- 5. BLUETOOTH_SETTINGS -> раздел Bluetooth ----------
BT_FILTER = (u'            <intent-filter android:priority="1">\n'
             u'                <action android:name="android.settings.BLUETOOTH_SETTINGS" />\n'
             u'                <category android:name="android.intent.category.DEFAULT" />\n'
             u'            </intent-filter>\n')
edit('AndroidManifest.xml', [
    (u'            android:parentActivityName="Settings">\n' + BT_FILTER +
     u'            <meta-data android:name="com.android.settings.FRAGMENT_CLASS"\n'
     u'                android:value="com.android.settings.connecteddevice.ConnectedDeviceDashboardFragment"/>',
     u'            android:parentActivityName="Settings">\n'
     u'            <!-- A1000: BLUETOOTH_SETTINGS отдан псевдониму Settings$BluetoothSettingsActivity -->\n'
     u'            <meta-data android:name="com.android.settings.FRAGMENT_CLASS"\n'
     u'                android:value="com.android.settings.connecteddevice.ConnectedDeviceDashboardFragment"/>'),
    (u'''            android:name="Settings$BluetoothSettingsActivity"
            android:label="@string/devices_title"
            android:targetActivity=".Settings$ConnectedDeviceDashboardActivity"
            android:exported="true">
            <intent-filter android:priority="10">
                <action android:name="android.intent.action.MAIN" />
                <category android:name="com.android.settings.SHORTCUT" />
            </intent-filter>
            <meta-data android:name="com.android.settings.FRAGMENT_CLASS"
                android:value="com.android.settings.connecteddevice.ConnectedDeviceDashboardFragment" />''',
     u'''            android:name="Settings$BluetoothSettingsActivity"
            android:label="@string/bluetooth_settings_title"
            android:targetActivity=".Settings$ConnectedDeviceDashboardActivity"
            android:exported="true">
            <intent-filter android:priority="10">
                <action android:name="android.intent.action.MAIN" />
                <category android:name="com.android.settings.SHORTCUT" />
            </intent-filter>
''' + BT_FILTER + u'''            <!-- A1000: Bluetooth - самостоятельный раздел -->
            <meta-data android:name="com.android.settings.FRAGMENT_CLASS"
                android:value="com.android.settings.connecteddevice.BluetoothDashboardFragment" />'''),
    (u'''                        android:targetActivity="Settings$BluetoothSettingsActivity"
                        android:exported="true"
                        android:clearTaskOnLaunch="true">
            <meta-data android:name="com.android.settings.FRAGMENT_CLASS"
                       android:value="com.android.settings.connecteddevice.ConnectedDeviceDashboardFragment" />''',
     u'''                        android:targetActivity="Settings$BluetoothSettingsActivity"
                        android:exported="true"
                        android:clearTaskOnLaunch="true">
            <meta-data android:name="com.android.settings.FRAGMENT_CLASS"
                       android:value="com.android.settings.connecteddevice.BluetoothDashboardFragment" />'''),
], 'BLUETOOTH_SETTINGS отдан')

edit('src/com/android/settings/core/gateway/SettingsGateway.java', [
    (u'import com.android.settings.connecteddevice.ConnectedDeviceDashboardFragment;\n',
     u'import com.android.settings.connecteddevice.BluetoothDashboardFragment;\n'
     u'import com.android.settings.connecteddevice.ConnectedDeviceDashboardFragment;\n'),
    (u'            ConnectedDeviceDashboardFragment.class.getName(),\n',
     u'            // A1000: isValidFragment() пускает только фрагменты из этого списка\n'
     u'            BluetoothDashboardFragment.class.getName(),\n'
     u'            ConnectedDeviceDashboardFragment.class.getName(),\n'),
], 'BluetoothDashboardFragment')

# ---------- 6. печать вырезана -> PrintManager == null ----------
edit('src/com/android/settings/print/PrintSettingPreferenceController.java', [
    (u'        mPrintManager.addPrintJobStateChangeListener(this);\n',
     u'        // A1000: печать вырезана из сборки, PrintManager == null, а Lifecycle\n'
     u'        // зовёт onStart и у недоступных контроллеров.\n'
     u'        if (mPrintManager != null) mPrintManager.addPrintJobStateChangeListener(this);\n'),
    (u'        mPrintManager.removePrintJobStateChangeListener(this);\n',
     u'        if (mPrintManager != null) mPrintManager.removePrintJobStateChangeListener(this);\n'),
    (u'        final List<PrintJob> printJobs = mPrintManager.getPrintJobs();\n',
     u'        if (mPrintManager == null) return null;\n'
     u'        final List<PrintJob> printJobs = mPrintManager.getPrintJobs();\n'),
], 'mPrintManager != null')
