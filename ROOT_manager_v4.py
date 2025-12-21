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
        # Kita hanya pakai force-stop agar lebih aman dan spesifik
        run_as_root(f"am force-stop {clean}")
        # killall dihapus karena berpotensi membunuh package lain yg mirip namanya
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

    print(f"    -> 🚀 Meluncurkan {clean} (ROOT)...")
    
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" --activity-clear-task {clean}"
    run_as_root(cmd)

# === FUNGSI SIKLUS (Hanya dipakai untuk peluncuran, bukan mematikan) ===
def jalankan_peluncuran_saja(pkg):
    """
    Fungsi ini HANYA menyalakan game. 
    Proses mematikan dipisah agar tidak saling tabrak.
    """
    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    
    # Langsung Launch (Karena sudah dimatikan massal sebelumnya)
    launch_game(pkg)
    
    # Jeda Wajib
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
        print(f"\n📂 Ditemukan data {len(saved_data.get('packages', {}))} akun tersimpan.")
        pilih = input("Gunakan ID/Link game yang tersimpan? (y/n): ").lower().strip()
        if pilih == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded_packages = True

    if not loaded_packages:
        print("\n--- PENGATURAN MODE GAME BARU ---")
        print("1. SATU GAME untuk SEMUA AKUN")
        print("2. BEDA GAME setiap AKUN")
        mode = input("Pilih Mode (1/2): ").strip()

        if mode == "1":
            print("\n[MODE SERAGAM]")
            pid = input("Masukkan Place ID: ").strip()
            print("Masukkan Link Private Server (Share Link / Code):")
            vip = input("(Kosongkan jika Public): ").strip()
            
            for pkg in BASE_PACKAGES:
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
                
        else:
            print("\n[MODE INDIVIDUAL]")
            for pkg in BASE_PACKAGES:
                clean = get_pkg_name(pkg)
                print(f"\nSetting untuk {clean}:")
                pid = input(f"  - Place ID: ").strip()
                vip = ""
                if pid:
                    print(f"  - Link Private Server (Enter jika Public):")
                    vip = input(f"    > ").strip()
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    print("\n" + "="*40)
    print("🕒 PENGATURAN WAKTU AUTO-RESTART")
    print("="*40)
    
    try:
        default_menit = 0
        if saved_data and 'restart_seconds' in saved_data:
            default_menit = int(saved_data['restart_seconds'] / 60)
            
        inp = input(f"Restart tiap berapa menit? (Enter={default_menit} mnt): ").strip()
        
        if inp == "":
            restart_seconds = default_menit * 60
        else:
            restart_seconds = int(inp) * 60
            
    except:
        restart_seconds = 0
    
    save_current_config(restart_seconds)
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (BATCH RESTART FIX) ===")
    
    # Cek Root Info
    os.system("su -c 'echo ✅ Akses Root OK' || echo '⚠️ Cek izin Root...'")

    RESTART_INTERVAL = setup_configuration()
    
    # 1. PELUNCURAN AWAL (PHASE 1)
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    
    # Filter Paket Aktif
    for pkg in BASE_PACKAGES:
        settings = PACKAGE_SETTINGS.get(pkg)
        if settings and settings['place_id']:
            ACTIVE_PACKAGES.append(pkg)
    
    if len(ACTIVE_PACKAGES) == 0:
        print("❌ Tidak ada akun yang di-setting.")
        return

    # Jalankan Awal (Satu persatu tidak masalah karena belum ada yang jalan)
    for pkg in ACTIVE_PACKAGES:
        # Matikan dulu biar fresh
        force_close(pkg)
        time.sleep(1)
        # Jalankan
        jalankan_peluncuran_saja(pkg)

    print("\n" + "="*50)
    print(f"✅ SELESAI. {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")

    if RESTART_INTERVAL > 0:
        print(f"⏳ Jadwal Restart Aktif: Setiap {int(RESTART_INTERVAL/60)} Menit")
    else:
        print("⏸️  Mode Standby (Tanpa Auto-Restart)")
    print("="*50)

    # 2. LOOP AUTO RESTART (PHASE 2)
    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10)
            
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ WAKTU HABIS! MEMULAI SIKLUS RESTART MASSAL...")
                    print("="*40)
                    
                    # === LANGKAH 1: MATIKAN SEMUA DULU (BATCH KILL) ===
                    print("🛑 TAHAP 1: Mematikan SEMUA akun serentak...")
                    for pkg in ACTIVE_PACKAGES:
                        print(f"   -> Kill {get_pkg_name(pkg)}")
                        force_close(pkg)
                    
                    print("   (Menunggu 5 detik agar semua proses benar-benar bersih...)")
                    time.sleep(5)
                    
                    # === LANGKAH 2: NYALAKAN SATU PER SATU ===
                    print("\n🚀 TAHAP 2: Meluncurkan ulang satu per satu...")
                    for pkg in ACTIVE_PACKAGES:
                        # Fungsi ini hanya menyalakan, tidak mematikan lagi
                        jalankan_peluncuran_saja(pkg)
                    
                    last_restart_time = time.time()
                    print(f"\n✅ Restart Massal Selesai. Menunggu {int(RESTART_INTERVAL/60)} menit lagi.")
                    
        except KeyboardInterrupt:
            print("\n🛑 Script Dihentikan.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
