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

# ================= FUNGSI ROOT =================

def run_as_root(cmd):
    """Menjalankan perintah sebagai Root (su)"""
    full_cmd = f"su -c '{cmd}'"
    os.system(f"{full_cmd} > /dev/null 2>&1")

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def force_close(pkg):
    clean = get_pkg_name(pkg)
    try:
        run_as_root(f"am force-stop {clean}")
    except:
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
        print(f"    -> Target: 🔗 Private Server (Direct Link)")
    elif vip_link_input and vip_link_input.strip() != "":
        final_uri = f"roblox://placeId={specific_place_id}&privateServerLinkCode={vip_link_input.strip()}"
        print(f"    -> Target: 🔒 Private Server (Code Injection)")
    else:
        final_uri = f"roblox://placeId={specific_place_id}"
        print(f"    -> Target: 🎲 Public/Random Server")

    print(f"    -> 🚀 Meluncurkan {clean} (MODE FLOATING ID:5)...")
    
    # Flag --windowingMode 5 untuk Freeform/Floating
    cmd = (
        f"am start --user 0 "
        f"--windowingMode 5 " 
        f"-a android.intent.action.VIEW "
        f"-d \"{final_uri}\" "
        f"--activity-clear-task {clean}"
    )
    
    run_as_root(cmd)

# === FUNGSI SIKLUS ===
def jalankan_peluncuran_saja(pkg):
    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    launch_game(pkg)
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
    print("✅ Konfigurasi berhasil disimpan.")

def setup_configuration():
    global PACKAGE_SETTINGS
    
    saved_data = load_last_config()
    loaded_packages = False
    
    if saved_data:
        print(f"\n📂 Ditemukan data lama.")
        pilih = input("Gunakan settingan lama? (y/n): ").lower().strip()
        if pilih == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded_packages = True

    if not loaded_packages:
        print("\n--- PENGATURAN BARU ---")
        mode = input("1. Satu Game / 2. Beda Game: ").strip()

        if mode == "1":
            print("\n[MODE SERAGAM]")
            pid = input("Masukkan Place ID: ").strip()
            vip = input("Link Private (Enter jika Public): ").strip()
            for pkg in BASE_PACKAGES:
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
        else:
            print("\n[MODE INDIVIDUAL]")
            for pkg in BASE_PACKAGES:
                clean = get_pkg_name(pkg)
                print(f"\nSetting untuk {clean}:")
                pid = input(f"  - Place ID: ").strip()
                vip = ""
                if pid: vip = input(f"  - Link Private: ").strip()
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    print("\n" + "="*40)
    print("🕒 PENGATURAN WAKTU AUTO-RESTART")
    print("="*40)
    
    # === PERBAIKAN VARIABEL DI SINI ===
    try:
        default_menit = 0  # Nama variabel diperbaiki
        if saved_data and 'restart_seconds' in saved_data:
            default_menit = int(saved_data['restart_seconds'] / 60)
            
        inp = input(f"Restart tiap berapa menit? (Enter={default_menit} mnt): ").strip()
        
        if inp == "":
            restart_seconds = default_menit * 60
        else:
            restart_seconds = int(inp) * 60
            
    except Exception as e:
        print(f"⚠️ Error Input Waktu: {e}")
        restart_seconds = 0
    
    save_current_config(restart_seconds)
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (FLOATING + BATCH KILL + FIX INPUT) ===")
    os.system("su -c 'echo ✅ Akses Root OK' || echo '⚠️ Cek izin Root...'")

    RESTART_INTERVAL = setup_configuration()
    
    # 1. PELUNCURAN AWAL
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    
    for pkg in BASE_PACKAGES:
        settings = PACKAGE_SETTINGS.get(pkg)
        if settings and settings['place_id']:
            ACTIVE_PACKAGES.append(pkg)
    
    if len(ACTIVE_PACKAGES) == 0:
        print("❌ Tidak ada akun aktif.")
        return

    # Launch Awal
    for pkg in ACTIVE_PACKAGES:
        force_close(pkg)
        time.sleep(1)
        jalankan_peluncuran_saja(pkg)

    print(f"\n✅ {len(ACTIVE_PACKAGES)} AKUN BERJALAN (MODE FLOATING).")

    if RESTART_INTERVAL > 0:
        print(f"⏳ Auto-Restart: {int(RESTART_INTERVAL/60)} Menit")
    else:
        print("⏸️  Tanpa Auto-Restart")
    print("="*50)

    # 2. LOOP AUTO RESTART
    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10)
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ WAKTU HABIS! RESTARTING...")
                    print("="*40)
                    
                    # BATCH KILL (Mematikan Semua Dulu)
                    print("🛑 TAHAP 1: Kill All (Agar tidak bentrok)...")
                    for pkg in ACTIVE_PACKAGES:
                        force_close(pkg)
                    time.sleep(5)
                    
                    # RELAUNCH (Menyalakan Satu per Satu)
                    print("\n🚀 TAHAP 2: Relaunch Floating...")
                    for pkg in ACTIVE_PACKAGES:
                        jalankan_peluncuran_saja(pkg)
                    
                    last_restart_time = time.time()
                    print(f"\n✅ Selesai. Tunggu {int(RESTART_INTERVAL/60)} menit.")
                    
        except KeyboardInterrupt:
            print("\n🛑 Stop.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
