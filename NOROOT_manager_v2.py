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

    print(f"    -> Meluncurkan {clean}...")
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" {clean}"
    os.system(f"{cmd} > /dev/null 2>&1")

# === FUNGSI UTAMA: METODE DOUBLE LAUNCH ===
def jalankan_siklus_login(pkg):
    """
    Fungsi ini menjalankan logika:
    Force Close -> Launch 1 -> Tunggu 5 Detik -> Launch 2 -> Tunggu Stabil
    """
    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    
    # 1. Matikan dulu
    force_close(pkg)
    time.sleep(1)
    
    # 2. Peluncuran PERTAMA
    print("    🚀 (1/2) Mencoba membuka game...")
    launch_game(pkg)
    
    # 3. Jeda 5 Detik (Sesuai Request)
    print("    ⏳ Jeda 5 detik sebelum pemicu ulang...")
    time.sleep(5)
    
    # 4. Peluncuran KEDUA (Pemicu Paksa)
    print("    🚀 (2/2) Memicu ulang agar tidak stuck...")
    launch_game(pkg)
    
    # 5. Jeda Wajib Stabilisasi
    print("⏳ Menunggu 25 detik agar stabil...")
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
    print("✅ Konfigurasi berhasil disimpan/diupdate.")

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
    print("Berapa lama kamu ingin berada di dalam game sebelum restart?")
    print("Input '0' untuk mematikan fitur restart.")
    
    try:
        default_menit = 0
        if saved_data and 'restart_seconds' in saved_data:
            default_menit = int(saved_data['restart_seconds'] / 60)
            
        inp = input(f"Masukkan Menit (Enter untuk default {default_menit} mnt): ").strip()
        
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
    print("=== ROBLOX MANAGER (DOUBLE LAUNCH) ===")
    
    RESTART_INTERVAL = setup_configuration()
    
    # 1. PELUNCURAN AWAL (PHASE 1)
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    
    for pkg in BASE_PACKAGES:
        settings = PACKAGE_SETTINGS.get(pkg)
        
        # Filter akun kosong
        if not settings or not settings['place_id']:
            continue 
        
        ACTIVE_PACKAGES.append(pkg)
        
        # >>> MENJALANKAN METODE DOUBLE LAUNCH <<<
        jalankan_siklus_login(pkg)
        
    print("\n" + "="*50)
    print(f"✅ SELESAI. {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")
    
    if len(ACTIVE_PACKAGES) == 0:
        return

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
                    print("\n\n⏰ WAKTU HABIS! MEMULAI SIKLUS ULANG...")
                    print("   (Menjalankan metode Double Launch)")
                    
                    for pkg in ACTIVE_PACKAGES:
                        # >>> MENJALANKAN METODE DOUBLE LAUNCH <<<
                        jalankan_siklus_login(pkg)
                    
                    last_restart_time = time.time()
                    print(f"\n✅ Restart Selesai. Menunggu {int(RESTART_INTERVAL/60)} menit lagi.")
                    
        except KeyboardInterrupt:
            print("\n🛑 Script Dihentikan.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
