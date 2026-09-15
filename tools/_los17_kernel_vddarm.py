#!/usr/bin/env python3
# Ядро #115: зависания Android 10 «через время» = CPU недокормлен на 1.2/1.3 ГГц.
#
# Живой kmsg на ПК (14.09): оба зависания (09:13, 09:24) оборвались сразу после
# «cpufreq_scx35: 768000 --> 1200000» — без Oops/паники, аппарат висит (USB
# «offline»), потом владелец держит кнопку -> u-boot: rst_mode 0, power key.
#
# 1. u-boot калибрует DCDC по АЦП и пишет в регистр vddarm «1000 мВ» как 966,
#    потому что «намерил» +3.4% (все шины, LDO и DCDC, у него +3..5.7% — это
#    похоже на смещение самого АЦП). Ядро берёт это в uV_offset (-34..-44 мВ,
#    плавает от загрузки) и вычитает из КАЖДОЙ точки таблицы: 1.2 ГГц идёт на
#    995 мВ вместо 1030. Для vddarm отрицательный сдвиг не применяем.
# 2. Пауза на подъём DCDC — «50 мВ за 10 мкс» с FIXME (26 мкс на 768->1200).
#    Даём вдвое больше и +30 мкс запаса: переход раз в сотню мс, цена ноль.
p = "/home/ard/a1000-kernel/drivers/regulator/sc2713s-regulator_dt.c"
s = open(p).read()

pairs = [
("""		rdev->constraints->uV_offset = ctl_vol - to_vol;//uV
""",
"""		rdev->constraints->uV_offset = ctl_vol - to_vol;//uV
		/* A1000: калибровка u-boot срезает vddarm на 34..44 мВ ниже
		 * таблицы cpufreq -> зависания сразу после перехода на 1.2 ГГц */
		if (!strcmp(desc->desc.name, "vddarm") && rdev->constraints->uV_offset < 0)
			rdev->constraints->uV_offset = 0;
"""),
("""		int dly = (vol - old_vol) * 10 / (50 * 1000);
""",
"""		int dly = (vol - old_vol) * 10 / (50 * 1000) * 2 + 30; /* A1000: запас */
"""),
]
if "A1000: калибровка u-boot" in s:
    print("sc2713s-regulator_dt.c: already patched")
else:
    for old, new in pairs:
        assert s.count(old) == 1, old
        s = s.replace(old, new)
    open(p, "w").write(s)
    print("sc2713s-regulator_dt.c: patched")
