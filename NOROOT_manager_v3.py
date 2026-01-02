import os
import time
import subprocess
import json

# ================= KONFIGURASI PAKET =================
BASE_PACKAGES = [
    "com.roblox.client",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

# Variabel Global
PACKAGE_SETTINGS = {}
ACTIVE_PACKAGES = []
CONFIG_FILE = "config_manager.json"

# ================= FUNGSI SISTEM =================

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def force_close(pkg):
    clean = get_pkg_name(pkg)
    try:
        os.system(f"am force-stop {clean} > /dev/null 2>&1")
    except:
        pass

# [BARU] Fungsi untuk membuka aplikasi ke Home Screen saja
def open_app_only(pkg):
    clean = get_pkg_name(pkg)
    # Perintah standar untuk membuka aplikasi layaknya mengetuk icon (Action Main + Category Launcher)
    cmd = f"am start --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER {clean}"
    os.system(f"{cmd} > /dev/null 2>&1")

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
    # Ambil setting jika tidak dipassing langsung
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    if not specific_place_id:
        return

    final_uri = ""
    
    # Logika Link (Sesuai File Anda)
    if vip_link_input and ("http" in vip_link_input or "roblox.com" in vip_link_input):
        final_uri = vip_link_input.strip()
        print(f"    -> Target: 🔗 Private Server (Direct Link)")
    elif vip_link_input and vip_link_input.strip() != "":
        final_uri = f"roblox://placeId={specific_place_id}&privateServerLinkCode={vip_link_input.strip()}"
        print(f"    -> Target: 🔒 Private Server (Code Injection)")
    else:
        final_uri = f"roblox://placeId={specific_place_id}"
        print(f"    -> Target: 🎲 Public/Random Server")

    print(f"    -> Meluncurkan {clean} (Inject Link)...")
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" {clean}"
    os.system(f"{cmd} > /dev/null 2>&1")

# === FUNGSI SIKLUS (DIMODIFIKASI: 2-STEP LAUNCH) ===
def jalankan_siklus_login(pkg):
    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    
    # 1. Matikan (Sesuai script asli)
    force_close(pkg)
    time.sleep(1)
    
    # [MODIFIKASI DIMULAI DARI SINI]
    
    # 2. LANGKAH PERTAMA: Buka APK Roblox saja (Tanpa Link)
    print("    📂 Langkah 1: Membuka Menu Utama Roblox...")
    open_app_only(pkg)
    
    # 3. JEDA 5 DETIK (Sesuai permintaan)
    print("       (Menunggu 5 detik loading awal...)")
    time.sleep(5)
    
    # 4. LANGKAH KEDUA: Masuk Game (Inject Link)
    print("    🚀 Langkah 2: Masuk ke dalam Game...")
    launch_game(pkg)
    
    # [MODIFIKASI SELESAI]
    
    # 5. Jeda Wajib (Sama seperti awal)
    print("    ⏳ Menunggu 25 detik agar stabil...")
    time.sleep(25) 

# ================= INPUT & SAVE MENU =================

def load_last_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_current_config(restart_time):
    data = {
        "restart_seconds": restart_time,
        "packages": PACKAGE_SETTINGS
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print("✅
