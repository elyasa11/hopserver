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

# ================= FUNGSI BANTUAN (FIX TERMUX) =================

def input_wajib(prompt):
    """
    Fungsi ini memaksa user mengisi input.
    Jika Termux nge-skip (input kosong), dia akan tanya lagi.
    """
    while True:
        try:
            data = input(prompt).strip()
            if data: # Jika ada isinya, baru return
                return data
            # Jika kosong (kena skip), loop lagi
        except EOFError:
            pass

def input_opsional(prompt):
    """Untuk input yang boleh kosong (seperti Private Link)"""
    try:
        return input(prompt).strip()
    except:
        return ""

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

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

# === FUNGSI SIKLUS (SAMA PERSIS AWAL & RESTART) ===
def jalankan_siklus_login(pkg):
    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    
    # 1. Matikan
    force_close(pkg)
    time.sleep(1)
    
    # 2. Masuk Game
    launch_game(pkg)
    
    # 3. Jeda Wajib
    print("⏳ Menunggu 25 detik agar stabil...")
    time.sleep(25) 

# ================= INPUT & SAVE MENU =================

def load_last_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            print("⚠️ File config rusak, membuat baru...")
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
    
    # === FIX: HAPUS BUFFER SEBELUM INPUT ===
    try:
        sys.stdin.flush()
    except:
        pass

    if saved_data:
        print(f"\n📂 Ditemukan data {len(saved_data.get('packages', {}))} akun tersimpan.")
        # Pakai input_opsional agar kalau terskip dianggap 'n' (tidak)
        pilih = input_opsional("Gunakan ID/Link game yang tersimpan? (y/n): ").lower()
        if pilih == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded_packages = True
        else:
            print("   -> Membuat pengaturan baru.")

    if not loaded_packages:
        print("\n--- PENGATURAN MODE GAME BARU ---")
        print("1. SATU GAME untuk SEMUA AKUN")
        print("2. BEDA GAME setiap AKUN")
        
        # Pakai input_wajib agar tidak bisa diskip
        mode = input_wajib("Pilih Mode (1/2): ")

        if mode == "1":
            print("\n[MODE SERAGAM]")
            pid = input_wajib("Masukkan Place ID: ") # Wajib isi
            print("Masukkan Link Private Server (Share Link / Code):")
            vip = input_opsional("(Kosongkan jika Public): ") # Boleh kosong
            
            for pkg in BASE_PACKAGES:
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
                
        else:
            print("\n[MODE INDIVIDUAL]")
            for pkg in BASE_PACKAGES:
                clean = get_pkg_name(pkg)
                print(f"\nSetting untuk {clean}:")
                pid = input_wajib(f"  - Place ID: ") # Wajib isi
                vip = ""
                if pid:
                    print(f"  - Link Private Server (Enter jika Public):")
                    vip = input_opsional(f"    > ") # Boleh kosong
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
            
        inp = input_opsional(f"Masukkan Menit (Enter untuk default {default_menit} mnt): ")
        
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
    clear_screen()
    print("=== ROBLOX MANAGER (ANTI-SKIP / TERMUX FIX) ===")
    
    RESTART_INTERVAL = setup_configuration()
    
    # 1. PELUNCURAN AWAL (PHASE 1)
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    
    for pkg in BASE_PACKAGES:
        settings = PACKAGE_SETTINGS.get(pkg)
        
        if not settings or not settings['place_id']:
            continue 
        
        ACTIVE_PACKAGES.append(pkg)
        
        # JALANKAN SIKLUS
        jalankan_siklus_login(pkg)
        
    print("\n" + "="*50)
    print(f"✅ SELESAI. {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")
    
    if len(ACTIVE_PACKAGES) == 0:
        print("⚠️  Tidak ada akun yang di-setting. Coba hapus config_manager.json")
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
                    print("   (Menjalankan metode yang sama persis dengan awal)")
                    
                    for pkg in ACTIVE_PACKAGES:
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
