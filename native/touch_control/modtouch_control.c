#include <stdbool.h>
#include <stdint.h>

#include "driver/touch_sensor.h"
#include "py/obj.h"
#include "py/runtime.h"

#define TOUCH_CONTROL_TIMEOUT_THRESHOLD_MAX (0x3fffff)
#define TOUCH_CONTROL_TIMEOUT_THRESHOLD_DEFAULT TOUCH_CONTROL_TIMEOUT_THRESHOLD_MAX

static void touch_control_check_error(esp_err_t error) {
    if (error != ESP_OK) {
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("ESP-IDF touch error: %d"), error);
    }
}

static mp_int_t touch_control_get_int_in_range(
    mp_obj_t value,
    mp_int_t minimum,
    mp_int_t maximum,
    const char *name
) {
    mp_int_t integer = mp_obj_get_int(value);
    if (integer < minimum || integer > maximum) {
        mp_raise_msg_varg(
            &mp_type_ValueError,
            MP_ERROR_TEXT("%s must be between %d and %d"),
            name,
            (int)minimum,
            (int)maximum
        );
    }
    return integer;
}

static touch_pad_t touch_control_get_channel(mp_obj_t channel_obj) {
    return (touch_pad_t)touch_control_get_int_in_range(
        channel_obj,
        TOUCH_PAD_NUM1,
        TOUCH_PAD_MAX - 1,
        "channel"
    );
}

static mp_obj_t touch_control_set_timeout(mp_obj_t enabled_obj, mp_obj_t threshold_obj) {
    uint32_t threshold = (uint32_t)touch_control_get_int_in_range(
        threshold_obj,
        0,
        TOUCH_CONTROL_TIMEOUT_THRESHOLD_MAX,
        "threshold"
    );
    touch_control_check_error(touch_pad_timeout_set(mp_obj_is_true(enabled_obj), threshold));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(touch_control_set_timeout_obj, touch_control_set_timeout);

static mp_obj_t touch_control_resume(void) {
    touch_control_check_error(touch_pad_timeout_resume());
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(touch_control_resume_obj, touch_control_resume);

static mp_obj_t touch_control_set_charge_discharge_times(mp_obj_t cycles_obj) {
    uint16_t cycles = (uint16_t)touch_control_get_int_in_range(cycles_obj, 0, UINT16_MAX, "cycles");
    touch_control_check_error(touch_pad_set_charge_discharge_times(cycles));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(
    touch_control_set_charge_discharge_times_obj,
    touch_control_set_charge_discharge_times
);

static mp_obj_t touch_control_get_charge_discharge_times(void) {
    uint16_t cycles;
    touch_control_check_error(touch_pad_get_charge_discharge_times(&cycles));
    return MP_OBJ_NEW_SMALL_INT(cycles);
}
static MP_DEFINE_CONST_FUN_OBJ_0(
    touch_control_get_charge_discharge_times_obj,
    touch_control_get_charge_discharge_times
);

static mp_obj_t touch_control_set_measurement_interval(mp_obj_t interval_obj) {
    uint16_t interval = (uint16_t)touch_control_get_int_in_range(
        interval_obj,
        0,
        UINT16_MAX,
        "interval"
    );
    touch_control_check_error(touch_pad_set_measurement_interval(interval));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(
    touch_control_set_measurement_interval_obj,
    touch_control_set_measurement_interval
);

static mp_obj_t touch_control_get_measurement_interval(void) {
    uint16_t interval;
    touch_control_check_error(touch_pad_get_measurement_interval(&interval));
    return MP_OBJ_NEW_SMALL_INT(interval);
}
static MP_DEFINE_CONST_FUN_OBJ_0(
    touch_control_get_measurement_interval_obj,
    touch_control_get_measurement_interval
);

static mp_obj_t touch_control_set_count_mode(
    mp_obj_t channel_obj,
    mp_obj_t slope_obj,
    mp_obj_t initial_level_obj
) {
    touch_pad_t channel = touch_control_get_channel(channel_obj);
    touch_cnt_slope_t slope = (touch_cnt_slope_t)touch_control_get_int_in_range(
        slope_obj,
        TOUCH_PAD_SLOPE_0,
        TOUCH_PAD_SLOPE_7,
        "slope"
    );
    touch_tie_opt_t initial_level = (touch_tie_opt_t)touch_control_get_int_in_range(
        initial_level_obj,
        TOUCH_PAD_TIE_OPT_LOW,
        TOUCH_PAD_TIE_OPT_FLOAT,
        "initial_level"
    );
    touch_control_check_error(touch_pad_set_cnt_mode(channel, slope, initial_level));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(touch_control_set_count_mode_obj, touch_control_set_count_mode);

static mp_obj_t touch_control_get_count_mode(mp_obj_t channel_obj) {
    touch_pad_t channel = touch_control_get_channel(channel_obj);
    touch_cnt_slope_t slope;
    touch_tie_opt_t initial_level;
    touch_control_check_error(touch_pad_get_cnt_mode(channel, &slope, &initial_level));
    mp_obj_t result[] = {
        MP_OBJ_NEW_SMALL_INT(slope),
        MP_OBJ_NEW_SMALL_INT(initial_level),
    };
    return mp_obj_new_tuple(2, result);
}
static MP_DEFINE_CONST_FUN_OBJ_1(touch_control_get_count_mode_obj, touch_control_get_count_mode);

static mp_obj_t touch_control_set_voltage(
    mp_obj_t high_obj,
    mp_obj_t low_obj,
    mp_obj_t attenuation_obj
) {
    touch_high_volt_t high = (touch_high_volt_t)touch_control_get_int_in_range(
        high_obj,
        TOUCH_HVOLT_2V4,
        TOUCH_HVOLT_2V7,
        "high"
    );
    touch_low_volt_t low = (touch_low_volt_t)touch_control_get_int_in_range(
        low_obj,
        TOUCH_LVOLT_0V5,
        TOUCH_LVOLT_0V8,
        "low"
    );
    touch_volt_atten_t attenuation = (touch_volt_atten_t)touch_control_get_int_in_range(
        attenuation_obj,
        TOUCH_HVOLT_ATTEN_1V5,
        TOUCH_HVOLT_ATTEN_0V,
        "attenuation"
    );
    touch_control_check_error(touch_pad_set_voltage(high, low, attenuation));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(touch_control_set_voltage_obj, touch_control_set_voltage);

static mp_obj_t touch_control_get_voltage(void) {
    touch_high_volt_t high;
    touch_low_volt_t low;
    touch_volt_atten_t attenuation;
    touch_control_check_error(touch_pad_get_voltage(&high, &low, &attenuation));
    mp_obj_t result[] = {
        MP_OBJ_NEW_SMALL_INT(high),
        MP_OBJ_NEW_SMALL_INT(low),
        MP_OBJ_NEW_SMALL_INT(attenuation),
    };
    return mp_obj_new_tuple(3, result);
}
static MP_DEFINE_CONST_FUN_OBJ_0(touch_control_get_voltage_obj, touch_control_get_voltage);

static mp_obj_t touch_control_set_idle_connection(mp_obj_t connection_obj) {
    touch_pad_conn_type_t connection = (touch_pad_conn_type_t)touch_control_get_int_in_range(
        connection_obj,
        TOUCH_PAD_CONN_HIGHZ,
        TOUCH_PAD_CONN_GND,
        "connection"
    );
    touch_control_check_error(touch_pad_set_idle_channel_connect(connection));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(
    touch_control_set_idle_connection_obj,
    touch_control_set_idle_connection
);

static mp_obj_t touch_control_get_idle_connection(void) {
    touch_pad_conn_type_t connection;
    touch_control_check_error(touch_pad_get_idle_channel_connect(&connection));
    return MP_OBJ_NEW_SMALL_INT(connection);
}
static MP_DEFINE_CONST_FUN_OBJ_0(
    touch_control_get_idle_connection_obj,
    touch_control_get_idle_connection
);

static mp_obj_t touch_control_current_channel(void) {
    return MP_OBJ_NEW_SMALL_INT(touch_pad_get_current_meas_channel());
}
static MP_DEFINE_CONST_FUN_OBJ_0(touch_control_current_channel_obj, touch_control_current_channel);

static mp_obj_t touch_control_measurement_in_progress(void) {
    return mp_obj_new_bool(touch_pad_meas_is_done());
}
static MP_DEFINE_CONST_FUN_OBJ_0(
    touch_control_measurement_in_progress_obj,
    touch_control_measurement_in_progress
);

static mp_obj_t touch_control_interrupt_status(void) {
    return mp_obj_new_int_from_uint(touch_pad_read_intr_status_mask());
}
static MP_DEFINE_CONST_FUN_OBJ_0(touch_control_interrupt_status_obj, touch_control_interrupt_status);

static mp_obj_t touch_control_clear_interrupts(mp_obj_t mask_obj) {
    uint32_t mask = (uint32_t)touch_control_get_int_in_range(
        mask_obj,
        0,
        TOUCH_PAD_INTR_MASK_ALL,
        "mask"
    );
    touch_control_check_error(touch_pad_intr_clear(mask));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(touch_control_clear_interrupts_obj, touch_control_clear_interrupts);

static mp_obj_t touch_control_configure_filter(size_t n_args, const mp_obj_t *args) {
    touch_filter_config_t config = {
        .mode = (touch_filter_mode_t)touch_control_get_int_in_range(
            args[0],
            TOUCH_PAD_FILTER_IIR_4,
            TOUCH_PAD_FILTER_JITTER,
            "mode"
        ),
        .debounce_cnt = (uint32_t)touch_control_get_int_in_range(
            args[1],
            0,
            TOUCH_DEBOUNCE_CNT_MAX,
            "debounce_count"
        ),
        .noise_thr = (uint32_t)touch_control_get_int_in_range(
            args[2],
            0,
            TOUCH_NOISE_THR_MAX,
            "noise_threshold"
        ),
        .jitter_step = (uint32_t)touch_control_get_int_in_range(
            args[3],
            0,
            TOUCH_JITTER_STEP_MAX,
            "jitter_step"
        ),
        .smh_lvl = (touch_smooth_mode_t)touch_control_get_int_in_range(
            args[4],
            TOUCH_PAD_SMOOTH_OFF,
            TOUCH_PAD_SMOOTH_IIR_8,
            "smooth_level"
        ),
    };
    touch_control_check_error(touch_pad_filter_set_config(&config));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    touch_control_configure_filter_obj,
    5,
    5,
    touch_control_configure_filter
);

static mp_obj_t touch_control_get_filter_config(void) {
    touch_filter_config_t config;
    touch_control_check_error(touch_pad_filter_get_config(&config));
    mp_obj_t result[] = {
        MP_OBJ_NEW_SMALL_INT(config.mode),
        MP_OBJ_NEW_SMALL_INT(config.debounce_cnt),
        MP_OBJ_NEW_SMALL_INT(config.noise_thr),
        MP_OBJ_NEW_SMALL_INT(config.jitter_step),
        MP_OBJ_NEW_SMALL_INT(config.smh_lvl),
    };
    return mp_obj_new_tuple(5, result);
}
static MP_DEFINE_CONST_FUN_OBJ_0(
    touch_control_get_filter_config_obj,
    touch_control_get_filter_config
);

static mp_obj_t touch_control_enable_filter(void) {
    touch_control_check_error(touch_pad_filter_enable());
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(touch_control_enable_filter_obj, touch_control_enable_filter);

static mp_obj_t touch_control_disable_filter(void) {
    touch_control_check_error(touch_pad_filter_disable());
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(touch_control_disable_filter_obj, touch_control_disable_filter);

static mp_obj_t touch_control_read_smooth(mp_obj_t channel_obj) {
    touch_pad_t channel = touch_control_get_channel(channel_obj);
    uint32_t value;
    touch_control_check_error(touch_pad_filter_read_smooth(channel, &value));
    return mp_obj_new_int_from_uint(value);
}
static MP_DEFINE_CONST_FUN_OBJ_1(touch_control_read_smooth_obj, touch_control_read_smooth);

#define TOUCH_CONTROL_FUNCTION(name) \
    { MP_ROM_QSTR(MP_QSTR_##name), MP_ROM_PTR(&touch_control_##name##_obj) }

#define TOUCH_CONTROL_CONSTANT(name, value) \
    { MP_ROM_QSTR(MP_QSTR_##name), MP_ROM_INT(value) }

static const mp_rom_map_elem_t touch_control_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_touch_control) },

    TOUCH_CONTROL_FUNCTION(set_timeout),
    TOUCH_CONTROL_FUNCTION(resume),
    TOUCH_CONTROL_FUNCTION(set_charge_discharge_times),
    TOUCH_CONTROL_FUNCTION(get_charge_discharge_times),
    TOUCH_CONTROL_FUNCTION(set_measurement_interval),
    TOUCH_CONTROL_FUNCTION(get_measurement_interval),
    TOUCH_CONTROL_FUNCTION(set_count_mode),
    TOUCH_CONTROL_FUNCTION(get_count_mode),
    TOUCH_CONTROL_FUNCTION(set_voltage),
    TOUCH_CONTROL_FUNCTION(get_voltage),
    TOUCH_CONTROL_FUNCTION(set_idle_connection),
    TOUCH_CONTROL_FUNCTION(get_idle_connection),
    TOUCH_CONTROL_FUNCTION(current_channel),
    TOUCH_CONTROL_FUNCTION(measurement_in_progress),
    TOUCH_CONTROL_FUNCTION(interrupt_status),
    TOUCH_CONTROL_FUNCTION(clear_interrupts),
    TOUCH_CONTROL_FUNCTION(configure_filter),
    TOUCH_CONTROL_FUNCTION(get_filter_config),
    TOUCH_CONTROL_FUNCTION(enable_filter),
    TOUCH_CONTROL_FUNCTION(disable_filter),
    TOUCH_CONTROL_FUNCTION(read_smooth),

    TOUCH_CONTROL_CONSTANT(TIMEOUT_THRESHOLD_DEFAULT, TOUCH_CONTROL_TIMEOUT_THRESHOLD_DEFAULT),

    TOUCH_CONTROL_CONSTANT(COUNT_SLOPE_0, TOUCH_PAD_SLOPE_0),
    TOUCH_CONTROL_CONSTANT(COUNT_SLOPE_1, TOUCH_PAD_SLOPE_1),
    TOUCH_CONTROL_CONSTANT(COUNT_SLOPE_2, TOUCH_PAD_SLOPE_2),
    TOUCH_CONTROL_CONSTANT(COUNT_SLOPE_3, TOUCH_PAD_SLOPE_3),
    TOUCH_CONTROL_CONSTANT(COUNT_SLOPE_4, TOUCH_PAD_SLOPE_4),
    TOUCH_CONTROL_CONSTANT(COUNT_SLOPE_5, TOUCH_PAD_SLOPE_5),
    TOUCH_CONTROL_CONSTANT(COUNT_SLOPE_6, TOUCH_PAD_SLOPE_6),
    TOUCH_CONTROL_CONSTANT(COUNT_SLOPE_7, TOUCH_PAD_SLOPE_7),

    TOUCH_CONTROL_CONSTANT(INITIAL_LEVEL_LOW, TOUCH_PAD_TIE_OPT_LOW),
    TOUCH_CONTROL_CONSTANT(INITIAL_LEVEL_HIGH, TOUCH_PAD_TIE_OPT_HIGH),
    TOUCH_CONTROL_CONSTANT(INITIAL_LEVEL_FLOAT, TOUCH_PAD_TIE_OPT_FLOAT),

    TOUCH_CONTROL_CONSTANT(VOLTAGE_HIGH_2V4, TOUCH_HVOLT_2V4),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_HIGH_2V5, TOUCH_HVOLT_2V5),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_HIGH_2V6, TOUCH_HVOLT_2V6),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_HIGH_2V7, TOUCH_HVOLT_2V7),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_LOW_0V5, TOUCH_LVOLT_0V5),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_LOW_0V6, TOUCH_LVOLT_0V6),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_LOW_0V7, TOUCH_LVOLT_0V7),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_LOW_0V8, TOUCH_LVOLT_0V8),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_ATTENUATION_1V5, TOUCH_HVOLT_ATTEN_1V5),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_ATTENUATION_1V0, TOUCH_HVOLT_ATTEN_1V),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_ATTENUATION_0V5, TOUCH_HVOLT_ATTEN_0V5),
    TOUCH_CONTROL_CONSTANT(VOLTAGE_ATTENUATION_0V0, TOUCH_HVOLT_ATTEN_0V),

    TOUCH_CONTROL_CONSTANT(IDLE_HIGH_Z, TOUCH_PAD_CONN_HIGHZ),
    TOUCH_CONTROL_CONSTANT(IDLE_GROUND, TOUCH_PAD_CONN_GND),

    TOUCH_CONTROL_CONSTANT(INTERRUPT_DONE, TOUCH_PAD_INTR_MASK_DONE),
    TOUCH_CONTROL_CONSTANT(INTERRUPT_ACTIVE, TOUCH_PAD_INTR_MASK_ACTIVE),
    TOUCH_CONTROL_CONSTANT(INTERRUPT_INACTIVE, TOUCH_PAD_INTR_MASK_INACTIVE),
    TOUCH_CONTROL_CONSTANT(INTERRUPT_SCAN_DONE, TOUCH_PAD_INTR_MASK_SCAN_DONE),
    TOUCH_CONTROL_CONSTANT(INTERRUPT_TIMEOUT, TOUCH_PAD_INTR_MASK_TIMEOUT),

    TOUCH_CONTROL_CONSTANT(FILTER_IIR_4, TOUCH_PAD_FILTER_IIR_4),
    TOUCH_CONTROL_CONSTANT(FILTER_IIR_8, TOUCH_PAD_FILTER_IIR_8),
    TOUCH_CONTROL_CONSTANT(FILTER_IIR_16, TOUCH_PAD_FILTER_IIR_16),
    TOUCH_CONTROL_CONSTANT(FILTER_IIR_32, TOUCH_PAD_FILTER_IIR_32),
    TOUCH_CONTROL_CONSTANT(FILTER_IIR_64, TOUCH_PAD_FILTER_IIR_64),
    TOUCH_CONTROL_CONSTANT(FILTER_IIR_128, TOUCH_PAD_FILTER_IIR_128),
    TOUCH_CONTROL_CONSTANT(FILTER_IIR_256, TOUCH_PAD_FILTER_IIR_256),
    TOUCH_CONTROL_CONSTANT(FILTER_JITTER, TOUCH_PAD_FILTER_JITTER),
    TOUCH_CONTROL_CONSTANT(SMOOTH_OFF, TOUCH_PAD_SMOOTH_OFF),
    TOUCH_CONTROL_CONSTANT(SMOOTH_IIR_2, TOUCH_PAD_SMOOTH_IIR_2),
    TOUCH_CONTROL_CONSTANT(SMOOTH_IIR_4, TOUCH_PAD_SMOOTH_IIR_4),
    TOUCH_CONTROL_CONSTANT(SMOOTH_IIR_8, TOUCH_PAD_SMOOTH_IIR_8),
};
static MP_DEFINE_CONST_DICT(touch_control_module_globals, touch_control_module_globals_table);

const mp_obj_module_t touch_control_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&touch_control_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_touch_control, touch_control_user_cmodule);
