cmake_minimum_required(VERSION 3.22.1)
project(wasi_host)

set(CMAKE_C_STANDARD 99)

# Configure WAMR build options & target Android platform explicitly
set(WAMR_BUILD_PLATFORM android)
set(WAMR_BUILD_INTERP 1)
set(WAMR_BUILD_AOT 0)
set(WAMR_BUILD_JIT 0)
set(WAMR_BUILD_SIMD 0)

# Include WAMR subdirectory
add_subdirectory(wamr)

# Build your host runner shared library
add_library(wasi_host SHARED wamr_host.c)

# Tell the compiler where to find WAMR headers
target_include_directories(wasi_host PRIVATE
    wamr/core/iwasm/include
    wamr/core/shared/utils
)

# Link against WAMR's core vmlib target and Android's log library
target_link_libraries(wasi_host PRIVATE vmlib log)

# Enforce 16 KB page-size memory alignment for Android 16
target_link_options(wasi_host PRIVATE "-Wl,-z,max-page-size=16384")
