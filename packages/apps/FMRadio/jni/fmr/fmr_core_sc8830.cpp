/*
 * A1000 (Spreadtrum sc8830 + sr2351): реализация FMR_* поверх драйвера
 * drivers/misc/fm_2351 (/dev/Trout_FM).
 *
 * Заменяет MediaTek'овские fmr_core.cpp + common.cpp. Интерфейс наружу —
 * тот же fmr.h, поэтому libfm_jni.cpp менять не пришлось.
 *
 * Частоты: драйвер работает в единицах 0.1 МГц (875 = 87.5 МГц), потому что
 * CONFIG_FM_SEEK_STEP_50KHZ выключен. FMR_seek по историческим причинам
 * получает и отдаёт 0.01 МГц — конвертируем на границе.
 */

#include "fmr.h"

#ifdef LOG_TAG
#undef LOG_TAG
#endif
#define LOG_TAG "FMLIB_SC8830"

/* ---- интерфейс драйвера, один в один с drivers/misc/fm_2351/sr2351_fm_ctrl.h ---- */
#define SC_FM_DEV_NAME       "/dev/Trout_FM"

#define SC_FM_IOCTL_BASE     'R'
#define SC_FM_ENABLE         _IOW(SC_FM_IOCTL_BASE, 0, int)
#define SC_FM_GET_ENABLE     _IOW(SC_FM_IOCTL_BASE, 1, int)
#define SC_FM_SET_TUNE       _IOW(SC_FM_IOCTL_BASE, 2, int)
#define SC_FM_GET_FREQ       _IOW(SC_FM_IOCTL_BASE, 3, int)
#define SC_FM_SEARCH         _IOW(SC_FM_IOCTL_BASE, 4, int[4])
#define SC_FM_STOP_SEARCH    _IOW(SC_FM_IOCTL_BASE, 5, int)
#define SC_FM_MUTE           _IOW(SC_FM_IOCTL_BASE, 6, int)
#define SC_FM_SET_VOLUME     _IOW(SC_FM_IOCTL_BASE, 7, int)
#define SC_FM_GET_VOLUME     _IOW(SC_FM_IOCTL_BASE, 8, int)
#define SC_FM_CONFIG         _IOW(SC_FM_IOCTL_BASE, 9, int)
#define SC_FM_GET_RSSI       _IOW(SC_FM_IOCTL_BASE, 10, int)

/* направление поиска у драйвера: 0 — вверх, 1 — вниз */
#define SC_SEEK_DIR_UP       0
#define SC_SEEK_DIR_DOWN     1
#define SC_SEEK_TIMEOUT      1

/* диапазон в единицах 0.1 МГц */
#define SC_BAND_LOW          875
#define SC_BAND_HIGH         1080
#define SC_BAND_STEP         1      /* 100 кГц */

#define SC_VOL_MAX           15

struct fmr_ds fmr_data;

static int sc_ioctl_set(int fd, unsigned int cmd, int val)
{
    if (fd < 0) return -ERR_INVALID_FD;
    if (ioctl(fd, cmd, &val) < 0) {
        LOGE("%s: ioctl 0x%x val=%d failed: %s", __func__, cmd, val, strerror(errno));
        return -1;
    }
    return 0;
}

static int sc_ioctl_get(int fd, unsigned int cmd, int *val)
{
    FMR_ASSERT(val);
    if (fd < 0) return -ERR_INVALID_FD;
    if (ioctl(fd, cmd, val) < 0) {
        LOGE("%s: ioctl 0x%x failed: %s", __func__, cmd, strerror(errno));
        return -1;
    }
    return 0;
}

static inline int sc_clamp_freq(int f10)
{
    if (f10 < SC_BAND_LOW)  return SC_BAND_LOW;
    if (f10 > SC_BAND_HIGH) return SC_BAND_HIGH;
    return f10;
}

/* ------------------------------------------------------------------ */

int FMR_init(void)
{
    memset(&fmr_data, 0, sizeof(fmr_data));
    fmr_data.fd = -1;
    fmr_data.cur_freq = SC_BAND_LOW;
    fmr_data.scan_stop = fm_false;
    /* Конфиг статический: у драйвера нет ни чтения региона, ни выбора шага. */
    fmr_data.cfg_data.chip = 0x2351;
    fmr_data.cfg_data.band = 1;
    fmr_data.cfg_data.low_band = SC_BAND_LOW;
    fmr_data.cfg_data.high_band = SC_BAND_HIGH;
    fmr_data.cfg_data.seek_space = SC_BAND_STEP;
    fmr_data.cfg_data.max_scan_num = 200;
    fmr_data.cfg_data.seek_lev = 0;
    fmr_data.cfg_data.scan_sort = 0;
    fmr_data.cfg_data.short_ana_sup = 0;   /* короткой антенны нет */
    LOGI("%s: sc8830/sr2351 FM backend", __func__);
    return 0;   /* единственный индекс */
}

int FMR_get_cfgs(int idx)
{
    (void)idx;
    return 0;
}

int FMR_open_dev(int idx)
{
    (void)idx;
    if (fmr_data.fd >= 0) return 0;

    fmr_data.fd = open(SC_FM_DEV_NAME, O_RDWR);
    if (fmr_data.fd < 0) {
        LOGE("%s: open %s failed: %s", __func__, SC_FM_DEV_NAME, strerror(errno));
        FMR_seterr(ERR_INVALID_FD);
        return -ERR_INVALID_FD;
    }
    LOGI("%s: %s opened, fd=%d", __func__, SC_FM_DEV_NAME, fmr_data.fd);
    return 0;
}

int FMR_close_dev(int idx)
{
    (void)idx;
    if (fmr_data.fd < 0) return 0;
    close(fmr_data.fd);
    fmr_data.fd = -1;
    return 0;
}

/* freq в 0.1 МГц */
int FMR_pwr_up(int idx, int freq)
{
    (void)idx;
    int ret;

    ret = sc_ioctl_set(fmr_data.fd, SC_FM_ENABLE, 1);
    if (ret) return ret;

    /* Драйвер после enable молчит до первой настройки — сразу тюнимся. */
    ret = FMR_tune(idx, freq);
    if (ret) return ret;

    sc_ioctl_set(fmr_data.fd, SC_FM_SET_VOLUME, SC_VOL_MAX);
    return 0;
}

int FMR_pwr_down(int idx, int type)
{
    (void)idx; (void)type;
    return sc_ioctl_set(fmr_data.fd, SC_FM_ENABLE, 0);
}

/* freq в 0.1 МГц */
int FMR_tune(int idx, int freq)
{
    (void)idx;
    int f = sc_clamp_freq(freq);
    int ret = sc_ioctl_set(fmr_data.fd, SC_FM_SET_TUNE, f);
    if (!ret) fmr_data.cur_freq = (uint16_t)f;
    return ret;
}

/* start_freq и *ret_freq — в 0.01 МГц, драйверу нужны 0.1 МГц */
int FMR_seek(int idx, int start_freq, int dir, int *ret_freq)
{
    (void)idx;
    FMR_ASSERT(ret_freq);
    int buf[4];

    if (fmr_data.fd < 0) return -ERR_INVALID_FD;

    buf[0] = sc_clamp_freq(start_freq / 10);
    buf[1] = dir ? SC_SEEK_DIR_UP : SC_SEEK_DIR_DOWN;
    buf[2] = SC_SEEK_TIMEOUT;
    buf[3] = 0;

    if (ioctl(fmr_data.fd, SC_FM_SEARCH, buf) < 0) {
        LOGE("%s: seek from %d failed: %s", __func__, buf[0], strerror(errno));
        *ret_freq = start_freq;
        return -1;
    }
    if (buf[3] < SC_BAND_LOW || buf[3] > SC_BAND_HIGH) {
        LOGW("%s: driver returned freq %d out of band", __func__, buf[3]);
        *ret_freq = start_freq;
        return -1;
    }

    fmr_data.cur_freq = (uint16_t)buf[3];
    *ret_freq = buf[3] * 10;
    LOGD("%s: found %d (0.1MHz)", __func__, buf[3]);
    return 0;
}

/*
 * Автопоиск. У драйвера нет пакетного сканирования — крутим seek по кругу,
 * пока частоты растут. Останов по stopScan обрабатывается флагом: ioctl
 * STOP_SEARCH прерывает текущий seek в ядре, а флаг не даёт начать следующий.
 */
int FMR_scan(int idx, uint16_t *tbl, int *num)
{
    FMR_ASSERT(tbl);
    FMR_ASSERT(num);

    int max = *num;
    int cnt = 0;
    int cur = SC_BAND_LOW;
    int prev = -1;

    if (fmr_data.fd < 0) return -ERR_INVALID_FD;
    if (max > fmr_data.cfg_data.max_scan_num) max = fmr_data.cfg_data.max_scan_num;

    fmr_data.scan_stop = fm_false;

    while (cnt < max) {
        int found = 0;
        if (fmr_data.scan_stop == fm_true) {
            LOGI("%s: stopped by user at %d", __func__, cur);
            break;
        }
        /* FMR_seek принимает 0.01 МГц */
        if (FMR_seek(idx, cur * 10, 1 /* вверх */, &found) != 0) break;

        found /= 10;
        /* дошли до конца диапазона и завернулись — выходим */
        if (prev >= 0 && found <= prev) break;
        if (found <= SC_BAND_LOW && cnt > 0) break;

        tbl[cnt++] = (uint16_t)found;
        prev = found;
        cur = found + SC_BAND_STEP;
        if (cur > SC_BAND_HIGH) break;
    }

    *num = cnt;
    LOGI("%s: %d stations", __func__, cnt);
    return (fmr_data.scan_stop == fm_true) ? -1 : 0;
}

int FMR_stop_scan(int idx)
{
    (void)idx;
    fmr_data.scan_stop = fm_true;
    return sc_ioctl_set(fmr_data.fd, SC_FM_STOP_SEARCH, 0);
}

/*
 * У драйвера ioctl MUTE — пустышка (case FM_IOCTL_MUTE: break;), реально
 * глушит установка громкости в 0: sr2351_fm_set_volume(0) зовёт sr2351_fm_mute().
 */
int FMR_set_mute(int idx, int mute)
{
    (void)idx;
    return sc_ioctl_set(fmr_data.fd, SC_FM_SET_VOLUME, mute ? 0 : SC_VOL_MAX);
}

int FMR_get_rssi(int idx, int *rssi)
{
    (void)idx;
    return sc_ioctl_get(fmr_data.fd, SC_FM_GET_RSSI, rssi);
}

int FMR_get_chip_id(int idx, int *chipid)
{
    (void)idx;
    FMR_ASSERT(chipid);
    *chipid = 0x2351;
    return 0;
}

/* ---- RDS: у sr2351 его нет, честно отвечаем "не поддерживается" ---- */

int FMR_is_rdsrx_support(int idx, int *supt)
{
    (void)idx;
    FMR_ASSERT(supt);
    *supt = 0;
    return 0;
}

int FMR_turn_on_off_rds(int idx, int onoff)
{
    (void)idx; (void)onoff;
    return 0;   /* приложение зовёт это безусловно, ошибкой отвечать незачем */
}

int FMR_read_rds_data(int idx, uint16_t *rds_status)
{
    (void)idx;
    FMR_ASSERT(rds_status);
    *rds_status = 0;
    return -ERR_RDS_NO_DATA;
}

int FMR_get_ps(int idx, uint8_t **ps, int *ps_len)
{
    (void)idx; (void)ps;
    if (ps_len) *ps_len = 0;
    return -ERR_RDS_NO_DATA;
}

int FMR_get_rt(int idx, uint8_t **rt, int *rt_len)
{
    (void)idx; (void)rt;
    if (rt_len) *rt_len = 0;
    return -ERR_RDS_NO_DATA;
}

int FMR_active_af(int idx, uint16_t *ret_freq)
{
    (void)idx;
    if (ret_freq) *ret_freq = fmr_data.cur_freq;
    return -ERR_RDS_NO_DATA;
}

/* ---- антенна ---- */

int FMR_ana_switch(int idx, int antenna)
{
    (void)idx;
    /* Антенна одна — провод гарнитуры. Короткой (встроенной) у sr2351 нет. */
    if (antenna == FM_SHORT_ANA) {
        LOGW("%s: short antenna is not supported by sr2351", __func__);
        FMR_seterr(ERR_UNSUPT_SHORTANA);
        return -ERR_UNSUPT_SHORTANA;
    }
    return 0;
}

/* ---- вокруг автопоиска приложение глушит звук ---- */

int FMR_Pre_Search(int idx)
{
    fmr_data.backup_freq = fmr_data.cur_freq;
    return FMR_set_mute(idx, 1);
}

int FMR_Restore_Search(int idx)
{
    return FMR_set_mute(idx, 0);
}
