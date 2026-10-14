cmake_minimum_required(VERSION 3.22.1)
project(wasi_host)

set(CMAKE_C_STANDARD 99)

# Configure WAMR build options
set(WAMR_BUILD_INTERP 1)
set(WAMR_BUILD_AOT 0)
set(WAMR_BUILD_JIT 0)
set(WAMR_BUILD_SIMD 0)
add_subdirectory(wamr)

# Build your host runner shared library
add_library(wasi_host SHARED wamr_host.c)

# CRITICAL: Tell the compiler where to find WAMR headers like wasm_export.h
target_include_directories(wasi_host PRIVATE
    wamr/core/iwasm/include
    wamr/core/shared/utils
)

# Link against WAMR's core iwasm library
target_link_libraries(wasi_host PRIVATE iwasm)

# CRITICAL for Android 16: Enforce 16 KB page-size memory alignment
target_link_options(wasi_host PRIVATE "-Wl,-z,max-page-size=16384")
target_shared_link_options(wasi_host PRIVATE "-Wl,-z,max-page-size=16384")
