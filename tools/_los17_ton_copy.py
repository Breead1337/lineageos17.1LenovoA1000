# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: нажатие на «Номер сборки» кладёт адрес TON в буфер обмена.
#
# В дереве десятки правки не было вовсе (свойство ro.baton4iks.usdt.ton в
# build.prop есть, а Settings его не читает). Переносим из 8.1
# (build_settings_ton_copy.sh) сразу в правильное место — ВЫШЕ проверки
# isAdminUser(): на девятке вызов попал внутрь ветки не-администратора и у
# владельца не срабатывал никогда (_los16_ton_copy_fix.py). Счётчик семи
# тапов режима разработчика не трогаем.
import io

T = '/home/ard/los17/packages/apps/Settings/'
P = T + 'src/com/android/settings/deviceinfo/BuildNumberPreferenceController.java'


def sub(s, old, new):
    assert s.count(old) == 1, old[:70]
    return s.replace(old, new)


s = io.open(P, encoding='utf-8').read()
if 'copyDonateAddress' in s:
    print('BuildNumberPreferenceController.java: уже правлен')
else:
    s = sub(s, 'import android.app.settings.SettingsEnums;\n',
            'import android.app.settings.SettingsEnums;\n'
            'import android.content.ClipData;\nimport android.content.ClipboardManager;\n')
    s = sub(s, 'import android.os.Build;\n', 'import android.os.Build;\nimport android.os.SystemProperties;\n')
    s = sub(s, """        if (Utils.isMonkeyRunning()) {
            return false;
        }
        // Don't enable developer options for secondary non-demo users.""",
            """        if (Utils.isMonkeyRunning()) {
            return false;
        }
        // A1000: адрес для донатов — в буфер. ДО отсечки не-администраторов и
        // до счётчика тапов: режим разработчика включается как прежде.
        copyDonateAddress();

        // Don't enable developer options for secondary non-demo users.""")
    i = s.rstrip().rfind('\n}')
    s = s[:i] + '''

    /** A1000: адрес USDT (TON) из ro.baton4iks.usdt.ton в буфер обмена. */
    private void copyDonateAddress() {
        final String address = SystemProperties.get("ro.baton4iks.usdt.ton", "");
        final ClipboardManager cb = mContext.getSystemService(ClipboardManager.class);
        if (TextUtils.isEmpty(address) || cb == null) {
            return;
        }
        cb.setPrimaryClip(ClipData.newPlainText("USDT TON", address));
        Toast.makeText(mContext, R.string.baton4iks_ton_copied, Toast.LENGTH_SHORT).show();
    }
}
'''
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print('BuildNumberPreferenceController.java: копирование TON добавлено')

for path, line in (
        ('res/values/strings.xml',
         '    <string name="baton4iks_ton_copied">TON address copied to clipboard</string>\n'),
        ('res/values-ru/strings.xml',
         '    <string name="baton4iks_ton_copied">Адрес TON скопирован</string>\n')):
    p = T + path
    t = io.open(p, encoding='utf-8').read()
    if 'baton4iks_ton_copied' in t:
        continue
    i = t.rfind('</resources>')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t[:i] + line + t[i:])
    print(path + ': строка добавлена')
