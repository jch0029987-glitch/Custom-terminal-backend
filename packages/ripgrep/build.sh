#!/bin/bash
set -e
OUTPUT_DIR=$1
mkdir -p "$OUTPUT_DIR"

echo "Building ripgrep target for WASI..."
rustup target add wasm32-wasip1

if [ ! -d "ripgrep" ]; then
    git clone --depth 1 https://github.com/BurntSushi/ripgrep.git
fi

cd ripgrep
cargo build --target wasm32-wasip1 --release

cp target/wasm32-wasip1/release/rg.wasm "$OUTPUT_DIR/ripgrep.wasm"
echo "Ripgrep .wasm package successfully built!"
