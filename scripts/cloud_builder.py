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
    if not os.path.isfile(filepath) or os.path.islink(filepath):
        return

    termux_path = "/data/data/com.termux/files/usr"
    app_path = f"/data/data/{app_package_name}/files/bin"

    try:
        with open(filepath, "rb") as f:
            header = f.read(4)
        is_elf = (header == b"\x7fELF")
    except Exception:
        is_elf = False

    if is_elf:
        print(f"[ELF] Patching binary: {os.path.basename(filepath)}")
        subprocess.run(["patchelf", "--set-rpath", app_path, filepath], stderr=subprocess.DEVNULL)
        try:
            subprocess.run(["patchelf", "--set-interpreter", "/system/bin/linker64", filepath], stderr=subprocess.DEVNULL)
        except Exception:
            pass
    else:
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
    
    subprocess.run(["ar", "x", deb_name])
    data_tar = next((f for f in os.listdir(".") if f.startswith("data.tar")), None)
    
    extract_path = f"extracted_{tool_name}"
    if data_tar:
        os.makedirs(extract_path, exist_ok=True)
        subprocess.run(["tar", "-xf", data_tar, "-C", extract_path])
        
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                smart_patch_file(os.path.join(root, file))

    patched_tar_name = f"{tool_name}_{version}_patched.tar.gz"
    print(f"Repackaging patched files into {patched_tar_name}...")
    subprocess.run(["tar", "-czf", patched_tar_name, "-C", extract_path, "."])

    # Calculate SHA-256 hash of the patched archive
    sha256_hash = hashlib.sha256()
    with open(patched_tar_name, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    sha256 = sha256_hash.hexdigest()

    # Upload via GitHub Releases using the GitHub CLI (`gh`)
    tag_name = f"{tool_name}-v{version}"
    repo = os.environ.get("GITHUB_REPOSITORY", "jch0029987-glitch/Custom-terminal-backend")
    
    print(f"Publishing release asset to GitHub Releases under tag {tag_name}...")
    # Delete tag/release if it already exists to allow clean re-builds
    subprocess.run(["gh", "release", "delete", tag_name, "--yes"], stderr=subprocess.DEVNULL)
    subprocess.run(["git", "push", "origin", f":refs/tags/{tag_name}"], stderr=subprocess.DEVNULL)

    # Create new release and upload the patched tarball as an asset
    subprocess.run([
        "gh", "release", "create", tag_name, patched_tar_name,
        "--title", f"{tool_name} {version} (Android Patched)",
        "--notes", f"Automatically patched arm64-v8a build for {tool_name} version {version}."
    ], check=True)

    release_download_url = f"https://github.com/{repo}/releases/download/{tag_name}/{patched_tar_name}"

    # Load or initialize packages.json safely
    if os.path.exists(MANIFEST_PATH) and os.path.getsize(MANIFEST_PATH) > 0:
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError:
            manifest = {"repository": repo.split("/")[-1], "version": 1, "packages": []}
    else:
        manifest = {"repository": repo.split("/")[-1], "version": 1, "packages": []}

    new_entry = {
        "name": tool_name,
        "version": version,
        "arch": "arm64-v8a",
        "url": release_download_url,
        "sha256": sha256,
        "binaryName": tool_name
    }

    manifest["packages"] = [p for p in manifest["packages"] if p["name"] != tool_name]
    manifest["packages"].append(new_entry)

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    # Cleanup temp files
    for cleanup_file in [deb_name, data_tar, patched_tar_name, "control.tar.xz", "debian-binary"]:
        if cleanup_file and os.path.exists(cleanup_file):
            try:
                os.remove(cleanup_file)
            except Exception:
                pass
            
    print(f"Successfully published release asset and updated manifest for {tool_name} v{version}!")

if __name__ == "__main__":
    process_remote_tool()
