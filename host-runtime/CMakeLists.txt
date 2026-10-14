cmake_minimum_required(VERSION 3.22.1)
project(wasi_host)

set(CMAKE_C_STANDARD 99)

# Configure WAMR build options
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

# WAMR registers its core engine target as 'vmlib' when added via add_subdirectory
target_link_libraries(wasi_host PRIVATE vmlib)

# Enforce 16 KB page-size memory alignment for Android 16
target_link_options(wasi_host PRIVATE "-Wl,-z,max-page-size=16384")
