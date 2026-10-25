import os
import sys
import json
import hashlib
import urllib.request
import gzip
import subprocess

MANIFEST_PATH = "packages.json"
APP_PACKAGE_NAME = "com.jeremy.app"

def smart_patch_file(filepath, app_package_name=APP_PACKAGE_NAME):
    """
    Intelligently checks file type and applies the correct patching strategy:
    - ELF binaries: Uses patchelf to update RPATH / interpreter.
    - Scripts / Text files: Performs string replacement for Termux hardcoded paths.
    """
    if not os.path.isfile(filepath) or os.path.islink(filepath):
        return

    termux_path = "/data/data/com.termux/files/usr"
    app_path = f"/data/data/{app_package_name}/files/bin"

    # Check if it's an ELF file
    try:
        with open(filepath, "rb") as f:
            header = f.read(4)
        is_elf = (header == b"\x7fELF")
    except Exception:
        is_elf = False

    if is_elf:
        print(f"[ELF] Patching binary: {os.path.basename(filepath)}")
        
        # 1. Set RPATH to look inside your app's internal bin directory
        subprocess.run([
            "patchelf", "--set-rpath", app_path, filepath
        ], stderr=subprocess.DEVNULL)
        
        # 2. Set dynamic interpreter to standard Android linker
        try:
            subprocess.run([
                "patchelf", "--set-interpreter", "/system/bin/linker64", filepath
            ], stderr=subprocess.DEVNULL)
        except Exception:
            pass
    else:
        # Check for text scripts / shebangs containing Termux paths
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            if termux_path in content:
                print(f"[Script/Text] Rewriting Termux paths in: {os.path.basename(filepath)}")
                new_content = content.replace(termux_path, f"/data/data/{app_package_name}/files")
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
        except Exception:
            pass

    # Ensure file is executable
    os.chmod(filepath, 0o755)

def process_remote_tool():
    tool_name = os.environ.get("TOOL_NAME")
    if not tool_name:
        print("Error: No TOOL_NAME environment variable provided.")
        sys.exit(1)

    TERMUX_REPO_BASE = "https://packages.termux.dev/apt/termux-main"
    index_url = f"{TERMUX_REPO_BASE}/dists/stable/main/binary-aarch64/Packages.gz"
    
    print(f"Fetching Termux upstream index for '{tool_name}'...")
    req = urllib.request.Request(index_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        content = gzip.decompress(response.read()).decode('utf-8')
    
    # Locate tool in Termux index
    current_pkg = {}
    found = False
    for line in content.splitlines():
        if not line.strip():
            if current_pkg.get("Package") == tool_name:
                found = True
                break
            current_pkg = {}
            continue
        parts = line.split(": ", 1)
        if len(parts) == 2:
            current_pkg[parts[0]] = parts[1]

    if not found and current_pkg.get("Package") != tool_name:
        print(f"Error: Tool '{tool_name}' not found in Termux repository.")
        sys.exit(1)

    version = current_pkg["Version"]
    download_url = f"{TERMUX_REPO_BASE}/{current_pkg['Filename']}"
    deb_name = download_url.split("/")[-1]
    
    print(f"Downloading package asset: {deb_name}")
    urllib.request.urlretrieve(download_url, deb_name)
    
    # Extract .deb archive
    subprocess.run(["ar", "x", deb_name])
    data_tar = next((f for f in os.listdir(".") if f.startswith("data.tar")), None)
    
    if data_tar:
        extract_path = f"extracted_{tool_name}"
        os.makedirs(extract_path, exist_ok=True)
        subprocess.run(["tar", "-xf", data_tar, "-C", extract_path])
        
        # Walk and smart-patch every file inside the package
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                smart_patch_file(os.path.join(root, file))

    # Calculate SHA-256 hash of the original package for verification
    sha256_hash = hashlib.sha256()
    with open(deb_name, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    sha256 = sha256_hash.hexdigest()

    # Update packages.json manifest
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
    else:
        manifest = {"repository": "CustomCliRepo", "version": 1, "packages": []}

    new_entry = {
        "name": tool_name,
        "version": version,
        "arch": "arm64-v8a",
        "url": download_url,
        "sha256": sha256,
        "binaryName": tool_name
    }

    manifest["packages"] = [p for p in manifest["packages"] if p["name"] != tool_name]
    manifest["packages"].append(new_entry)

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=4)
        
    # Cleanup local temp files
    os.remove(deb_name)
    if data_tar and os.path.exists(data_tar):
        os.remove(data_tar)
    if os.path.exists("control.tar.xz"):
        os.remove("control.tar.xz")
    if os.path.exists("debian-binary"):
        os.remove("debian-binary")

    print(f"Successfully processed, smart-patched, and indexed {tool_name} v{version}!")

if __name__ == "__main__":
    process_remote_tool()
