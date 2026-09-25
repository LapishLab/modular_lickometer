add_library(usermod_touch_control INTERFACE)

target_sources(usermod_touch_control INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/modtouch_control.c
)

target_include_directories(usermod_touch_control INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_touch_control)
