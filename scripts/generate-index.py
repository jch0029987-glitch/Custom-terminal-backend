import os
import json
import sys

wasm_dir = sys.argv[1]
output_json = sys.argv[2]

packages = []
for filename in os.listdir(wasm_dir):
    if filename.endswith(".wasm"):
        name = filename.replace(".wasm", "")
        packages.append({
            "name": name,
            "type": "wasm",
            "version": "1.0.0",
            "architecture": "wasm32-wasi",
            "url": f"https://github.com/jch0029987-glitch/Custom-terminal-backend/releases/latest/download/{filename}"
        })

index = {"packages": packages}
with open(output_json, "w") as f:
    json.dump(index, f, indent=2)

print(f"Generated registry index containing {len(packages)} packages for jch0029987-glitch/Custom-terminal-backend.")
