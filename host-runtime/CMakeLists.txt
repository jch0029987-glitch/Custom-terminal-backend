cmake_minimum_required(VERSION 3.22.1)
project(wasi_host)

set(CMAKE_C_STANDARD 99)

# Include your WAMR (WebAssembly Micro Runtime) library target here
# add_subdirectory(wamr)

add_library(wasi_host SHARED wamr_host.c)

# CRITICAL for Android 16: Enforce 16 KB page-size memory alignment
target_link_options(wasi_host PRIVATE "-Wl,-z,max-page-size=16384")
