add_executable(test_edf_parser
    test_edf_parser.cpp
)

target_link_libraries(test_edf_parser PUBLIC limacore)

set_property(TARGET test_edf_parser PROPERTY CXX_STANDARD 17)

add_executable(test_simulator
    test_simulator.cpp
)

target_link_libraries(test_simulator PUBLIC limacore simulator)

add_test(
    NAME basic_test
    COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/test.py
)
