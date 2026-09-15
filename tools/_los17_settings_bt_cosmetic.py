# -*- coding: utf-8 -*-
u"""A1000 / Android 10: косметика раздела Bluetooth (после _los17_settings_bt_section.py).

1. «Текущие подключения: USB» на экране Bluetooth: ConnectedDeviceGroupController
   сводит в одну группу BT + USB + док. Теперь по фрагменту: в Bluetooth — только
   BT, в «Подключённых устройствах» (группа возвращена) — только USB и док.
2. Подпись «Включите Bluetooth, чтобы…» висела и при включённом BT: в стоке Q
   это экран-переключатель, текст один на оба состояния. При включённом — прячем.
3. «Подключённые устройства» без Bluetooth (просьба владельца 14.09): пункт
   «Настройки подключения» (внутри только BT, а NFC/печати на A1000 нет — пустой
   экран), подвал «Название в списке устройств…» (имя для BT) и подпись
   «Bluetooth» на главной -> «USB».
"""
import io

S = '/home/ard/los17/packages/apps/Settings/'
CD = 'src/com/android/settings/connecteddevice/'


def edit(path, pairs, marker):
    p = S + path
    s = io.open(p, encoding='utf-8').read()
    if marker in s:
        print(path + u': уже'); return
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:80])
        s = s.replace(old, new)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print(path + u': правлен')


edit(CD + 'ConnectedDeviceGroupController.java', [
    (u'''        mBluetoothDeviceUpdater.registerCallback();
        mConnectedUsbDeviceUpdater.registerCallback();
        mConnectedDockUpdater.registerCallback();''',
     u'''        if (mBluetoothDeviceUpdater != null) mBluetoothDeviceUpdater.registerCallback();
        if (mConnectedUsbDeviceUpdater != null) mConnectedUsbDeviceUpdater.registerCallback();
        if (mConnectedDockUpdater != null) mConnectedDockUpdater.registerCallback();'''),
    (u'''        mConnectedUsbDeviceUpdater.unregisterCallback();
        mBluetoothDeviceUpdater.unregisterCallback();
        mConnectedDockUpdater.unregisterCallback();''',
     u'''        if (mConnectedUsbDeviceUpdater != null) mConnectedUsbDeviceUpdater.unregisterCallback();
        if (mBluetoothDeviceUpdater != null) mBluetoothDeviceUpdater.unregisterCallback();
        if (mConnectedDockUpdater != null) mConnectedDockUpdater.unregisterCallback();'''),
    (u'''            mBluetoothDeviceUpdater.setPrefContext(context);
            mBluetoothDeviceUpdater.forceUpdate();
            mConnectedUsbDeviceUpdater.initUsbPreference(context);
            mConnectedDockUpdater.setPreferenceContext(context);
            mConnectedDockUpdater.forceUpdate();''',
     u'''            if (mBluetoothDeviceUpdater != null) {
                mBluetoothDeviceUpdater.setPrefContext(context);
                mBluetoothDeviceUpdater.forceUpdate();
            }
            if (mConnectedUsbDeviceUpdater != null) {
                mConnectedUsbDeviceUpdater.initUsbPreference(context);
            }
            if (mConnectedDockUpdater != null) {
                mConnectedDockUpdater.setPreferenceContext(context);
                mConnectedDockUpdater.forceUpdate();
            }'''),
    (u'''        final DockUpdater connectedDockUpdater =
                dockUpdaterFeatureProvider.getConnectedDockUpdater(context, this);
        init(new ConnectedBluetoothDeviceUpdater(context, fragment, this),
                new ConnectedUsbDeviceUpdater(context, fragment, this),
                connectedDockUpdater);''',
     u'''        // A1000: Bluetooth — свой раздел: там только BT, в «Подключённых» — USB и док.
        final boolean btScreen = fragment instanceof BluetoothDashboardFragment;
        final DockUpdater connectedDockUpdater = btScreen ? null
                : dockUpdaterFeatureProvider.getConnectedDockUpdater(context, this);
        init(btScreen ? new ConnectedBluetoothDeviceUpdater(context, fragment, this) : null,
                btScreen ? null : new ConnectedUsbDeviceUpdater(context, fragment, this),
                connectedDockUpdater);'''),
], 'A1000')

edit('res/xml/connected_devices.xml', [(
    u'    <!-- A1000: всё про Bluetooth переехало в свой раздел (bluetooth_screen.xml) -->\n',
    u'    <!-- A1000: всё про Bluetooth переехало в свой раздел (bluetooth_screen.xml) -->\n\n'
    u'    <!-- A1000: USB и док (контроллер сам отсекает BT на этом экране) -->\n'
    u'    <PreferenceCategory\n'
    u'        android:key="connected_device_list"\n'
    u'        android:title="@string/connected_device_connected_title"\n'
    u'        settings:controller="com.android.settings.connecteddevice.ConnectedDeviceGroupController"/>\n')],
    u'USB и док')

edit(CD + 'ConnectedDeviceDashboardFragment.java', [(
    u'        // A1000: группы устройств уехали в раздел Bluetooth; use() вернул бы null.\n',
    u'        // A1000: группы устройств уехали в раздел Bluetooth; use() вернул бы null.\n'
    u'        // Кроме подключённых: здесь она показывает USB и док (без BT).\n'
    u'        use(ConnectedDeviceGroupController.class).init(this);\n')],
    u'USB и док (без BT)')

edit('src/com/android/settings/bluetooth/BluetoothSwitchPreferenceController.java', [(
    u'    @VisibleForTesting void updateText(boolean isChecked) {\n',
    u'    @VisibleForTesting void updateText(boolean isChecked) {\n'
    u'        // A1000: «Включите Bluetooth…» при включённом BT — лишнее.\n'
    u'        mFooterPreference.setVisible(!isChecked);\n')],
    u'A1000')

# ---------- 3. «Подключённые устройства» без Bluetooth ----------
edit('res/xml/connected_devices.xml', [(
    u'''    <Preference
        android:key="connection_preferences"
        android:title="@string/connected_device_connections_title"
        android:fragment="com.android.settings.connecteddevice.AdvancedConnectedDeviceDashboardFragment"
        settings:allowDividerAbove="true"
        settings:controller="com.android.settings.connecteddevice.AdvancedConnectedDeviceController"/>
''', u'''    <!-- A1000: «Настройки подключения» убраны — внутри был только Bluetooth -->
''')], u'«Настройки подключения» убраны')

edit(CD + 'ConnectedDeviceDashboardFragment.java', [
    (u'''        final DiscoverableFooterPreferenceController discoverableFooterPreferenceController =
                new DiscoverableFooterPreferenceController(context);
        controllers.add(discoverableFooterPreferenceController);

        if (lifecycle != null) {
            lifecycle.addObserver(discoverableFooterPreferenceController);
        }

''', u'''        // A1000: подвал «Название в списке устройств» (имя для Bluetooth) убран.
'''),
    (u'''        use(DiscoverableFooterPreferenceController.class).init(this);
''', u''),
    (u'''        use(DiscoverableFooterPreferenceController.class)
                .setAlwaysDiscoverable(isAlwaysDiscoverable(callingAppPackageName, action));
''', u''),
], u'подвал «Название в списке устройств»')

edit(CD + 'TopLevelConnectedDevicesPreferenceController.java', [(
    u'''        return mContext.getText(
                AdvancedConnectedDeviceController.getConnectedDevicesSummaryResourceId(mContext));
''', u'''        // A1000: Bluetooth — отдельный пункт главной, здесь остаётся только USB.
        return "USB";
''')], u'остаётся только USB')
