# -*- coding: utf-8 -*-
# LOS 17.1 / A1000: перенос всех наших правок RIL (8.1 + девятка).
#
# Блоб libreference-ril_sp.so собран под Android 5, поэтому:
#   * не знает запрос 98 (DEVICE_IDENTITY) — IMEI берём старым 38 (GET_IMEI),
#     а он отдаёт ОДНУ строку цифр, а не массив из четырёх char*;
#   * присылает индексы приложений SIM вне диапазона — из-за строгих проверок
#     обе SIM объявлялись пустыми;
#   * присылает КОРОТКУЮ RIL_SignalStrength (v5/v6) — вся индикация уровня
#     сигнала отбрасывалась, в телефонии оставались 99/-1;
#   * пользуется устаревшими состояниями радио (2..9) — фреймворк падал с
#     «Unrecognized RadioState» и навсегда оставался с RADIO_OFF;
#   * AT+SFUN=4 отвечает через 15+ секунд, а HIDL-пул из одного потока делает
#     rild немым на это время -> ANR в com.android.phone (правка девятки);
#   * запускается ПО ПРОЦЕССУ НА СЛОТ, а имя сервиса клеилось как slot+clientId,
#     то есть оба демона регистрировались как slot1.
import io

R = '/home/ard/los17/hardware/ril/'

# ---------- ril_commands.h ----------
P = R + 'libril/ril_commands.h'
s = io.open(P, encoding='utf-8').read()
if 'A1000_IMEI' in s:
    print('ril_commands.h: uzhe pravlen')
else:
    old = "    {RIL_REQUEST_GET_IMEI, NULL},"
    new = "    {RIL_REQUEST_GET_IMEI, radio::getDeviceIdentityResponse},   // A1000_IMEI"
    assert old in s
    io.open(P, 'w', encoding='utf-8').write(s.replace(old, new, 1))
    print('ril_commands.h: GET_IMEI -> getDeviceIdentityResponse')

# ---------- ril_service.cpp ----------
P = R + 'libril/ril_service.cpp'
s = io.open(P, encoding='utf-8').read()
if 'A1000_IMEI' in s:
    print('ril_service.cpp: uzhe pravlen')
else:
    if '#include <cutils/properties.h>' not in s:
        s = s.replace('#include <inttypes.h>',
                      '#include <inttypes.h>\n#include <cutils/properties.h>', 1)

    # 1. запрос IMEI
    old = """    dispatchVoid(serial, mSlotId, RIL_REQUEST_DEVICE_IDENTITY);
    return Void();"""
    new = """    // A1000_IMEI: вендорная libreference-ril_sp.so не реализует запрос 98
    // (DEVICE_IDENTITY) — отбивает его GENERIC_FAILURE, не отправив ни одной
    // AT-команды. IMEI она отдаёт по старому 38 (GET_IMEI), которым и
    // пользовался фреймворк Android 5.
    dispatchVoid(serial, mSlotId, RIL_REQUEST_GET_IMEI);
    return Void();"""
    assert old in s, 'ne nayden dispatch DEVICE_IDENTITY'
    s = s.replace(old, new, 1)

    # 2. статус SIM: индексы приводим к -1 вместо выброса всего ответа
    old = """        if (response == NULL || responseLen != sizeof(RIL_CardStatus_v6)
                || p_cur->gsm_umts_subscription_app_index >= p_cur->num_applications
                || p_cur->cdma_subscription_app_index >= p_cur->num_applications
                || p_cur->ims_subscription_app_index >= p_cur->num_applications) {
            RLOGE("getIccCardStatusResponse: Invalid response");
            if (e == RIL_E_SUCCESS) responseInfo.error = RadioError::INVALID_RESPONSE;
        } else {
            cardStatus.cardState = (CardState) p_cur->card_state;
            cardStatus.universalPinState = (PinState) p_cur->universal_pin_state;
            cardStatus.gsmUmtsSubscriptionAppIndex = p_cur->gsm_umts_subscription_app_index;
            cardStatus.cdmaSubscriptionAppIndex = p_cur->cdma_subscription_app_index;
            cardStatus.imsSubscriptionAppIndex = p_cur->ims_subscription_app_index;

            RIL_AppStatus *rilAppStatus = p_cur->applications;
            cardStatus.applications.resize(p_cur->num_applications);
            AppStatus *appStatus = cardStatus.applications.data();
#if VDBG
            RLOGD("getIccCardStatusResponse: num_applications %d", p_cur->num_applications);
#endif
            for (int i = 0; i < p_cur->num_applications; i++) {"""
    new = """        /* A1000: индекс вне диапазона — это НЕ повод выбросить весь ответ.
         * Со вставленной картой блоб SPRD (сборка под Android 5) присылает в
         * одном из индексов своё значение, и Android объявлял оба слота
         * пустыми, хотя модем уже видел сеть. По стандарту RIL индекс -1
         * означает «такого приложения нет» — к нему и приводим. Чтения за
         * границей массива это не допускает ровно так же. */
        if (response == NULL || responseLen != sizeof(RIL_CardStatus_v6)) {
            RLOGE("getIccCardStatusResponse: Invalid response: responseLen %zu, ozhidalsya %zu",
                    responseLen, sizeof(RIL_CardStatus_v6));
            if (e == RIL_E_SUCCESS) responseInfo.error = RadioError::INVALID_RESPONSE;
        } else {
            int a1000_napp = p_cur->num_applications;
            if (a1000_napp < 0 || a1000_napp > RIL_CARD_MAX_APPS) {
                RLOGE("A1000: num_applications %d vne [0..%d], schitaem 0",
                        a1000_napp, RIL_CARD_MAX_APPS);
                a1000_napp = 0;
            }
            cardStatus.cardState = (CardState) p_cur->card_state;
            cardStatus.universalPinState = (PinState) p_cur->universal_pin_state;
            cardStatus.gsmUmtsSubscriptionAppIndex =
                    (p_cur->gsm_umts_subscription_app_index < a1000_napp)
                    ? p_cur->gsm_umts_subscription_app_index : -1;
            cardStatus.cdmaSubscriptionAppIndex =
                    (p_cur->cdma_subscription_app_index < a1000_napp)
                    ? p_cur->cdma_subscription_app_index : -1;
            cardStatus.imsSubscriptionAppIndex =
                    (p_cur->ims_subscription_app_index < a1000_napp)
                    ? p_cur->ims_subscription_app_index : -1;

            RIL_AppStatus *rilAppStatus = p_cur->applications;
            cardStatus.applications.resize(a1000_napp);
            AppStatus *appStatus = cardStatus.applications.data();
#if VDBG
            RLOGD("getIccCardStatusResponse: num_applications %d", p_cur->num_applications);
#endif
            for (int i = 0; i < a1000_napp; i++) {"""
    assert old in s, 'ne nayden getIccCardStatusResponse'
    s = s.replace(old, new, 1)

    # 3. длина ответа уровня сигнала (ответ на запрос)
    old = """        if (response == NULL || (responseLen != sizeof(RIL_SignalStrength_v10)
                && responseLen != sizeof(RIL_SignalStrength_v8))) {
            RLOGE("getSignalStrengthResponse: Invalid response");"""
    new = """        /* A1000: короткие структуры v5/v6 тоже годятся, см.
         * convertRilSignalStrengthToHal(). */
        if (response == NULL || responseLen < sizeof(RIL_SignalStrength_v5)) {
            RLOGE("getSignalStrengthResponse: Invalid response: responseLen %zu", responseLen);"""
    assert old in s, 'ne nayden getSignalStrengthResponse'
    s = s.replace(old, new, 1)

    # 4. IMEI приходит одной строкой
    old = """        int numStrings = responseLen / sizeof(char *);
        hidl_string emptyString;
        if (response == NULL || numStrings != 4) {
            RLOGE("getDeviceIdentityResponse Invalid response: NULL");"""
    new = """        int numStrings = responseLen / sizeof(char *);
        hidl_string emptyString;

        // A1000_IMEI: мы подменили запрос 98 на 38 (GET_IMEI), и блоб отвечает
        // ОДНОЙ строкой цифр, а не массивом из четырёх char*. По длине их не
        // различить: 15 цифр и завершающий ноль = 16 байт = ровно 4 указателя,
        // из-за чего rild уходил в ветку char** и падал в strlen по адресу,
        // собранному из самих цифр. Смотрим на содержимое: сплошные цифры
        // длиной 14..16, закрытые нулём.
        bool imeiPlainString = false;
        if (response != NULL && responseLen > 0) {
            const char *raw = (const char *) response;
            size_t n = 0;
            while (n < responseLen && raw[n] >= '0' && raw[n] <= '9') {
                n++;
            }
            imeiPlainString = (n >= 14 && n <= 16 && n < responseLen && raw[n] == 0);
        }

        if (imeiPlainString) {
            // SVN у блоба нет вообще — ни строки IMEISV, ни запроса 39.
            // Штатный reference-ril в такой ситуации отдаёт "01"; берём то же,
            // но через свойство, чтобы менять без пересборки.
            char svn[PROPERTY_VALUE_MAX];
            property_get("ro.ril.imeisv", svn, "01");
            Return<void> retStatus
                    = radioService[slotId]->mRadioResponse->getDeviceIdentityResponse(responseInfo,
                    convertCharPtrToHidlString((char *) response),
                    convertCharPtrToHidlString(svn),
                    emptyString, emptyString);
            radioService[slotId]->checkReturnStatus(retStatus);
        } else if (response == NULL || numStrings != 4) {
            RLOGE("getDeviceIdentityResponse Invalid response: NULL");"""
    assert old in s, 'ne nayden getDeviceIdentityResponse'
    s = s.replace(old, new, 1)

    # 5. устаревшие состояния радио
    old = """int radio::radioStateChangedInd(int slotId,
                                 int indicationType, int token, RIL_Errno e, void *response,
                                 size_t responseLen) {
    if (radioService[slotId] != NULL && radioService[slotId]->mRadioIndication != NULL) {
        RadioState radioState =
                (RadioState) CALL_ONSTATEREQUEST(slotId);"""
    new = """// A1000: вендорный блоб пользуется устаревшими состояниями радио.
// Он снят со стокового Android 5 (RIL version 10) и отдаёт 2 = SIM_NOT_READY,
// 3 = SIM_LOCKED_OR_ABSENT, 4 = SIM_READY, 5..9 = RUIM/NV. HIDL
// android.hardware.radio@1.0 знает только OFF(0), UNAVAILABLE(1) и ON(10);
// с чужим числом фреймворк падает с «Unrecognized RadioState» и навсегда
// остаётся с RADIO_OFF. Все устаревшие значения означают ВКЛЮЧЁННОЕ радио и
// различаются лишь готовностью SIM, о которой спрашивают отдельно.
static RadioState convertVendorRadioState(int vendorState) {
    switch (vendorState) {
        case RADIO_STATE_OFF:
        case RADIO_STATE_UNAVAILABLE:
        case RADIO_STATE_ON:
            return (RadioState) vendorState;
        default:
            RLOGD("convertVendorRadioState: ustarevshee sostoyanie %d -> ON", vendorState);
            return RadioState::ON;
    }
}

int radio::radioStateChangedInd(int slotId,
                                 int indicationType, int token, RIL_Errno e, void *response,
                                 size_t responseLen) {
    if (radioService[slotId] != NULL && radioService[slotId]->mRadioIndication != NULL) {
        RadioState radioState =
                convertVendorRadioState(CALL_ONSTATEREQUEST(slotId));"""
    assert old in s, 'ne nayden radioStateChangedInd'
    s = s.replace(old, new, 1)

    # 6. короткая структура уровня сигнала
    old = """    if (responseLen == sizeof(RIL_SignalStrength_v8)) {
        convertRilSignalStrengthToHalV8(response, responseLen, signalStrength);
    } else {
        convertRilSignalStrengthToHalV10(response, responseLen, signalStrength);
    }"""
    new = """    if (responseLen == sizeof(RIL_SignalStrength_v8)) {
        convertRilSignalStrengthToHalV8(response, responseLen, signalStrength);
    } else if (responseLen == sizeof(RIL_SignalStrength_v10)) {
        convertRilSignalStrengthToHalV10(response, responseLen, signalStrength);
    } else {
        /* A1000: блоб присылает КОРОТКУЮ структуру (v5 = 28 байт или v6 = 48),
         * а здесь ждут v8/v10. Из-за этого вся индикация уровня сигнала
         * отбрасывалась, и в телефонии оставались 99/-1. Короткие версии —
         * байтовые ПРЕФИКСЫ v10, поэтому копируем что пришло в обнулённую v10,
         * а недостающие поля заполняем «неизвестно». */
        RIL_SignalStrength_v10 v10;
        memset(&v10, 0, sizeof(v10));
        size_t n = (responseLen < sizeof(v10)) ? responseLen : sizeof(v10);
        memcpy(&v10, response, n);
        if (responseLen < sizeof(RIL_SignalStrength_v6)) {
            /* LTE не пришло вовсе */
            v10.LTE_SignalStrength.signalStrength = 99;
            v10.LTE_SignalStrength.rsrp = INT_MAX;
            v10.LTE_SignalStrength.rsrq = INT_MAX;
            v10.LTE_SignalStrength.rssnr = INT_MAX;
            v10.LTE_SignalStrength.cqi = INT_MAX;
        }
        v10.LTE_SignalStrength.timingAdvance = INT_MAX;
        v10.TD_SCDMA_SignalStrength.rscp = INT_MAX;
        convertRilSignalStrengthToHalV10(&v10, sizeof(v10), signalStrength);
    }"""
    assert old in s, 'ne nayden convertRilSignalStrengthToHal'
    s = s.replace(old, new, 1)

    # 7. длина в индикации уровня сигнала
    old = """        if (response == NULL || (responseLen != sizeof(RIL_SignalStrength_v10)
                && responseLen != sizeof(RIL_SignalStrength_v8))) {
            RLOGE("currentSignalStrengthInd: invalid response");"""
    new = """        /* A1000: короткие структуры v5/v6 тоже годятся. */
        if (response == NULL || responseLen < sizeof(RIL_SignalStrength_v5)) {
            RLOGE("currentSignalStrengthInd: invalid response: responseLen %zu", responseLen);"""
    assert old in s, 'ne nayden currentSignalStrengthInd'
    s = s.replace(old, new, 1)

    # 8. пул потоков HIDL (правка девятки)
    old = "    configureRpcThreadpool(1, true /* callerWillJoin */);"
    new = """    /* A1000: шесть потоков вместо одного. AT+SFUN=4 у этого модема отвечает
     * через 15+ секунд, и с одним потоком rild на это время немой: главный
     * поток com.android.phone виснет на interfaceChain() и процесс убивают по
     * ANR. Блоб к параллельным запросам готов — он сам разводит AT-каналы. */
    configureRpcThreadpool(6, true /* callerWillJoin */);"""
    assert old in s, 'ne nayden configureRpcThreadpool'
    s = s.replace(old, new, 1)

    io.open(P, 'w', encoding='utf-8').write(s)
    print('ril_service.cpp: IMEI, SIM, signal, radio state, threadpool')

# ---------- rild.c: номер слота ----------
P = R + 'rild/rild.c'
s = io.open(P, encoding='utf-8').read()
if 'A1000' in s:
    print('rild.c: uzhe pravlen')
else:
    old = """    if (strncmp(clientId, "0", MAX_CLIENT_ID_LENGTH)) {
        snprintf(ril_service_name, sizeof(ril_service_name), "%s%s", ril_service_name_base,
                 clientId);
    }"""
    new = """    // A1000: номер слота = clientId + 1, а не сам clientId. Spreadtrum
    // запускает по процессу rild на слот (-c 0 и -c 1), а имена HIDL-сервисов
    // — slot1 и slot2. Со старой склейкой второй демон регистрировался под
    // тем же именем slot1 и затирал первый, RILJ [SUB1] не находил slot2.
    snprintf(ril_service_name, sizeof(ril_service_name), "%s%d", ril_service_name_base,
             atoi(clientId) + 1);"""
    assert old in s, 'ne naydeno imya servisa'
    io.open(P, 'w', encoding='utf-8').write(s.replace(old, new, 1))
    print('rild.c: imya servisa = slot(clientId+1)')

# ---------- rild/Android.mk: свой init-скрипт ----------
P = R + 'rild/Android.mk'
s = io.open(P, encoding='utf-8').read()
if 'A1000' in s:
    print('rild/Android.mk: uzhe pravlen')
else:
    old = """ifeq ($(PRODUCT_COMPATIBLE_PROPERTY),true)
LOCAL_INIT_RC := rild.rc
LOCAL_CFLAGS += -DPRODUCT_COMPATIBLE_PROPERTY
else
LOCAL_INIT_RC := rild.legacy.rc
endif"""
    new = """# A1000: init-скрипт AOSP не ставим — модем поднимается из a1000_ril.rc
# (modemd -> wril-daemon с вендорной libreference-ril_sp.so), а rild.rc завёл
# бы второй, пустой экземпляр.
ifeq ($(PRODUCT_COMPATIBLE_PROPERTY),true)
LOCAL_CFLAGS += -DPRODUCT_COMPATIBLE_PROPERTY
endif"""
    assert old in s, 'ne nayden blok LOCAL_INIT_RC'
    io.open(P, 'w', encoding='utf-8').write(s.replace(old, new, 1))
    print('rild/Android.mk: bez rild.rc')
