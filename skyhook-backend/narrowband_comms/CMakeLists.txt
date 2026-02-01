cmake_minimum_required(VERSION 3.18)

# create the project
project(rpi-llcc68)

# when using debuggers such as gdb, the following line can be used
#set(CMAKE_BUILD_TYPE Debug)

# if you did not build RadioLib as shared library (see wiki),
# you will have to add it as source directory
# the following is just an example, yours will likely be different
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/components/radiolib" "${CMAKE_CURRENT_BINARY_DIR}/radiolib")

# add socket io c++ client as static lib
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/components/sioclient" "${CMAKE_CURRENT_BINARY_DIR}/sioclient")

# add the executable
add_executable(${PROJECT_NAME} main.cpp)

# link libraries
target_link_libraries(${PROJECT_NAME} RadioLib lgpio sioclient)

# you can also specify RadioLib compile-time flags here
#target_compile_definitions(RadioLib PUBLIC RADIOLIB_DEBUG_BASIC RADIOLIB_DEBUG_SPI)
#target_compile_definitions(RadioLib PUBLIC RADIOLIB_DEBUG_PORT=stdout)
