include(boards/mpconfigboard_esp32s3_common.cmake)

list(APPEND SDKCONFIG_DEFAULTS
    boards/sdkconfig.flash_qio_80m
    boards/sdkconfig.csi
    ${MICROPY_BOARD_DIR}/sdkconfig.board
)

list(APPEND MICROPY_DEF_BOARD
    MICROPY_HW_BOARD_NAME="Modular Lickometer"
)
