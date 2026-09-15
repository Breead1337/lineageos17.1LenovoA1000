# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: занято/всего ОЗУ вверху «Недавних».
#
# Как и в девятке (_los16_recents_ram.py), «Недавние» рисует лаунчер
# (config_recentsComponentName = com.android.launcher3/...quickstep.RecentsActivity),
# модуль TrebuchetQuickStep. В десятке LauncherRecentsView переехал в
# quickstep/recents_ui_overrides и уже сам переопределяет
# setOverviewStateEnabled — пересчёт цифры добавляем в него, второй метод
# с той же сигнатурой не компилируется.
#
# Грабли те же: вьюха — PagedView, ребёнка не добавить (станет страницей),
# поэтому текст рисуется в draw(); координаты скроллены (getScrollX());
# прозрачность из getContentAlpha(), иначе надпись висит над рабочим столом.
import io

Q = '/home/ard/los17/packages/apps/Trebuchet'
P = Q + '/quickstep/recents_ui_overrides/src/com/android/quickstep/views/LauncherRecentsView.java'
S = Q + '/quickstep/res/values/strings.xml'


def sub(s, old, new):
    assert s.count(old) == 1, old[:70]
    return s.replace(old, new)


s = io.open(P, encoding='utf-8').read()
if 'mMemoryText' in s:
    print('LauncherRecentsView.java: уже правлен')
else:
    s = sub(s, 'import android.annotation.TargetApi;\n',
            'import android.annotation.TargetApi;\nimport android.app.ActivityManager;\n')
    s = sub(s, 'import android.graphics.Canvas;\n',
            'import android.graphics.Canvas;\nimport android.graphics.Color;\nimport android.graphics.Paint;\n')
    s = sub(s, 'import android.util.AttributeSet;\n',
            'import android.text.format.Formatter;\nimport android.util.AttributeSet;\n')
    s = sub(s, '    private final TransformParams mTransformParams = new TransformParams();\n',
            '    private final TransformParams mTransformParams = new TransformParams();\n\n'
            '    /** A1000: сколько ОЗУ занято — надпись вверху «Недавних». */\n'
            '    private final Paint mMemoryPaint = new Paint(Paint.ANTI_ALIAS_FLAG);\n'
            '    private String mMemoryText;\n')
    s = sub(s, """        setContentAlpha(0);
        mActivity.getStateManager().addStateListener(this);
    }""", """        setContentAlpha(0);
        mActivity.getStateManager().addStateListener(this);

        mMemoryPaint.setColor(Color.WHITE);
        mMemoryPaint.setTextAlign(Paint.Align.CENTER);
        mMemoryPaint.setTextSize(12f * getResources().getDisplayMetrics().scaledDensity);
        mMemoryPaint.setShadowLayer(3f, 0f, 1f, 0xA0000000);
    }""")
    s = sub(s, """        maybeDrawEmptyMessage(canvas);
        super.draw(canvas);
    }""", """        maybeDrawEmptyMessage(canvas);
        super.draw(canvas);
        drawMemoryInfo(canvas);
    }

    private String formatMemoryInfo() {
        ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
        getContext().getSystemService(ActivityManager.class).getMemoryInfo(mi);
        return getContext().getString(R.string.a1000_recents_memory,
                Formatter.formatShortFileSize(getContext(), mi.totalMem - mi.availMem),
                Formatter.formatShortFileSize(getContext(), mi.totalMem));
    }

    private void drawMemoryInfo(Canvas canvas) {
        final float alpha = getContentAlpha();
        if (mMemoryText == null || alpha <= 0.01f) {
            return;
        }
        mMemoryPaint.setAlpha(Math.round(255f * alpha));
        canvas.drawText(mMemoryText, getScrollX() + getWidth() / 2f,
                mInsets.top + mMemoryPaint.getTextSize() * 1.6f, mMemoryPaint);
    }""")
    s = sub(s, """        super.setOverviewStateEnabled(enabled);
        if (enabled) {""", """        super.setOverviewStateEnabled(enabled);
        // A1000: считаем ровно на входе в «Недавние» — ни таймера, ни подписок.
        mMemoryText = enabled ? formatMemoryInfo() : null;
        if (enabled) {""")
    io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
    print('LauncherRecentsView.java: надпись про ОЗУ добавлена')

t = io.open(S, encoding='utf-8').read()
if 'a1000_recents_memory' not in t:
    i = t.rfind('</resources>')
    t = (t[:i] + '    <!-- A1000: занято/всего ОЗУ вверху «Недавних» -->\n'
         '    <string name="a1000_recents_memory" translatable="false">RAM: %1$s / %2$s</string>\n' + t[i:])
    io.open(S, 'w', encoding='utf-8', newline='\n').write(t)
    print('quickstep strings.xml: строка добавлена')
