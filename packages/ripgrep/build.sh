#!/bin/bash
set -e
OUTPUT_DIR=$(realpath "$1")
mkdir -p "$OUTPUT_DIR/usr/bin"

echo "Building ripgrep native target for aarch64-linux-android..."
rustup target add aarch64-linux-android

if [ ! -d "ripgrep" ]; then
    git clone --depth 1 https://github.com/BurntSushi/ripgrep.git
fi

cd ripgrep

# Note: Ensure your Android NDK toolchain is configured in cargo config or environment 
# if linking native C dependencies, though ripgrep is pure Rust and compiles cleanly.
cargo build --target aarch64-linux-android --release

# Copy and name it 'rg' directly into usr/bin
cp target/aarch64-linux-android/release/rg "$OUTPUT_DIR/usr/bin/rg"
chmod +x "$OUTPUT_DIR/usr/bin/rg"

echo "Ripgrep native aarch64 'rg' binary successfully built!"
