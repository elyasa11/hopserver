import os
import time
import subprocess
import json
import sys

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

# ================= FUNGSI ROOT (MODIFIKASI AMAN) =================

def run_as_root(cmd):
    """Menjalankan perintah sebagai Root"""
    full_cmd = f"su -c '{cmd}'"
    os.system(f"{full_cmd} > /dev/null 2>&1")

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

# [DINOAKTIFKAN] Fungsi ini penyebab kerusakan pada Cloud Phone kamu
# Kita biarkan kosong agar aman.
def force_close(pkg):
    pass 

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
    # Ambil setting
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    if not specific_place_id:
        return

    final_uri = ""
    
    # Logika Link
    if vip_link_input and ("http" in vip_link_input or "roblox.com" in vip_link_input):
        final_uri = vip_link_input.strip()
        print(f"    -> Target: 🔗 Private Server")
    elif vip_link_input and vip_link_input.strip() != "":
        final_uri = f"roblox://placeId={specific_place_id}&privateServerLinkCode={vip_link_input.strip()}"
        print(f"    -> Target: 🔒 Private Server Code")
    else:
        final_uri = f"roblox://placeId={specific_place_id}"
        print(f"    -> Target: 🎲 Public/Random Server")

    print(f"    -> 🚀 Meluncurkan/Refresh {clean}...")
    
    # KUNCI PERBAIKAN: --activity-clear-task
    # Ini akan merestart game di dalam aplikasi tanpa mematikan paksa aplikasinya
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" --activity-clear-task {clean}"
    run_as_root(cmd)

def jalankan_siklus_aman(pkg):
    """
    Siklus Launch Only (Tanpa Kill)
    """
    launch_game(pkg)
    print("    ⏳ Menunggu 20 detik untuk stabilisasi...")
    time.sleep(20)

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
    print("✅ Konfigurasi disimpan.")

def setup_configuration():
    global PACKAGE_SETTINGS
    saved_data = load_last_config()
    loaded_packages = False
    
    if saved_data:
        print(f"\n📂 Ditemukan data {len(saved_data.get('packages', {}))} akun.")
        pilih = input("Pakai data lama? (y/n): ").lower().strip()
        if pilih == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded_packages = True

    if not loaded_packages:
        print("\n--- SETUP BARU ---")
        pid = input("Masukkan Place ID: ").strip()
        vip = input("Link Private Server (Enter jika Public): ").strip()
        for pkg in BASE_PACKAGES:
            PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    print("\n" + "="*40)
    try:
        def_min = 0
        if saved_data: def_min = int(saved_data.get('restart_seconds', 0)/60)
        inp = input(f"Auto Restart tiap berapa menit? (Enter={def_min}): ").strip()
        restart_seconds = (int(inp) * 60) if inp else (def_min * 60)
    except:
        restart_seconds = 0
    
    save_current_config(restart_seconds)
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (SAFE MODE: NO KILL) ===")
    os.system("su -c 'echo ✅ Root Check OK' || echo '⚠️ Root Check'")

    RESTART_INTERVAL = setup_configuration()
    
    # FILTER PAKET
    for pkg in BASE_PACKAGES:
        if PACKAGE_SETTINGS.get(pkg, {}).get('place_id'):
            ACTIVE_PACKAGES.append(pkg)

    # 1. PELUNCURAN AWAL (PHASE 1)
    print(f"\n[PHASE 1] PELUNCURAN AWAL")
    for pkg in ACTIVE_PACKAGES:
        jalankan_siklus_aman(pkg)

    print("\n" + "="*50)
    print(f"✅ PHASE 1 SELESAI. {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")
    
    if RESTART_INTERVAL > 0:
        print(f"⏳ Auto-Restart: {int(RESTART_INTERVAL/60)} Menit")
    else:
        print("⏸️  Standby Mode")
    print("="*50)

    # 2. LOOP AUTO RESTART (PHASE 2)
    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10)
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n🔄 WAKTU RESTART! MENIMPA SESI LAMA...")
                    
                    # Kita tidak pakai Loop Kill lagi.
                    # Langsung Loop Launch satu per satu.
                    
                    for pkg in ACTIVE_PACKAGES:
                        print(f"   -> Refreshing {get_pkg_name(pkg)}...")
                        jalankan_siklus_aman(pkg)
                    
                    last_restart_time = time.time()
                    print(f"\n✅ Refresh Selesai. Menunggu siklus berikutnya.")
                    
        except KeyboardInterrupt:
            print("\n🛑 Stop.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
