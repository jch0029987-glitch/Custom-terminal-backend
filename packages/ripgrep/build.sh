#!/bin/bash
set -e
OUTPUT_DIR=$(realpath "$1")
mkdir -p "$OUTPUT_DIR/wasm"

echo "Building ripgrep target for WASI (wasm32-wasip1)..."
rustup target add wasm32-wasip1

if [ ! -d "ripgrep" ]; then
    git clone --depth 1 https://github.com/BurntSushi/ripgrep.git
fi

cd ripgrep
cargo build --target wasm32-wasip1 --release

# Copy the compiled WASM binary to the output directory
cp target/wasm32-wasip1/release/rg.wasm "$OUTPUT_DIR/wasm/ripgrep.wasm"

echo "Ripgrep .wasm binary successfully built and packaged!"
