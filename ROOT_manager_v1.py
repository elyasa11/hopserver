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

# ================= FUNGSI BANTUAN & ROOT =================

def run_root_cmd(cmd):
    """Menjalankan perintah Root"""
    full_cmd = f"su -c '{cmd}'"
    os.system(f"{full_cmd} > /dev/null 2>&1")

def input_aman(prompt):
    """
    METODE RAW INPUT (ANTI-STUCK)
    Kita tidak menggunakan input() biasa karena bisa macet di cloudphone tertentu.
    Kita print dulu prompt-nya, lalu baca baris mentah dari terminal.
    """
    try:
        # Print pertanyaan dan paksa tampil ke layar (flush=True)
        print(prompt, end=' ', flush=True)
        # Baca input secara manual dari system standard input
        data = sys.stdin.readline()
        return data.strip()
    except KeyboardInterrupt:
        print("\n\nScript dihentikan paksa.")
        sys.exit()
    except:
        return ""

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

# ================= FUNGSI LOGIKA UTAMA =================

def force_close(pkg):
    clean = get_pkg_name(pkg)
    try:
        run_root_cmd(f"am force-stop {clean}")
        run_root_cmd(f"killall {clean}")
    except:
        pass

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    if not specific_place_id:
        print(f"⚠️  {clean} di-skip (ID Game kosong).")
        return

    final_uri = ""
    
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
    run_root_cmd(cmd)

# === FUNGSI SIKLUS ===
def jalankan_siklus_login(pkg):
    settings = PACKAGE_SETTINGS.get(pkg)
    if not settings or not settings['place_id']:
        return 

    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    
    print(f"    🛑 Mematikan paksa aplikasi...")
    force_close(pkg)
    
    time.sleep(2)
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
    print("✅ Konfigurasi tersimpan.")

def setup_configuration():
    global PACKAGE_SETTINGS
    saved_data = load_last_config()
    loaded_packages = False
    
    # KITA HAPUS SEMUA FLUSH YANG BIKIN ERROR
    
    if saved_data:
        print(f"\n📂 Ditemukan data lama.")
        pilih = input_aman("Gunakan settingan lama? (y/n): ").lower()
        if pilih == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded_packages = True

    if not loaded_packages:
        print("\n--- PENGATURAN BARU ---")
        mode = input_aman("1. Satu Game Semua Akun / 2. Beda-beda (Ketik 1/2):")

        if mode == "1":
            print("\n[MODE SERAGAM]")
            pid = input_aman("Masukkan Place ID:")
            vip = ""
            if pid: vip = input_aman("Link Private (Enter jika Public):")
            for pkg in BASE_PACKAGES:
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
        else:
            print("\n[MODE INDIVIDUAL]")
            for pkg in BASE_PACKAGES:
                clean = get_pkg_name(pkg)
                print(f"\nSetting untuk {clean}:")
                pid = input_aman(f"  - Place ID (Enter utk Skip):")
                vip = ""
                if pid: vip = input_aman(f"  - Link Private:")
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    print("\n--- WAKTU RESTART ---")
    try:
        def_menit = 0
        if saved_data and 'restart_seconds' in saved_data:
            def_menit = int(saved_data['restart_seconds'] / 60)
        inp = input_aman(f"Restart tiap berapa menit? (Enter={def_menit}):")
        if inp == "": restart_seconds = def_menit * 60
        else: restart_seconds = int(inp) * 60
    except:
        restart_seconds = 0
    
    save_current_config(restart_seconds)
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (ROOT - RAW INPUT MODE) ===")
    
    # Cek Root Sederhana
    try:
        check = os.system("su -c 'echo root_ok' > /dev/null 2>&1")
        if check != 0:
            print("⚠️  ROOT TIDAK TERDETEKSI!")
            print("    Pastikan mengetik 'su' dulu di termux dan izinkan akses.")
            time.sleep(3)
        else:
            print("✅ Root OK.")
    except:
        pass

    RESTART_INTERVAL = setup_configuration()
    
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    
    for pkg in BASE_PACKAGES:
        settings = PACKAGE_SETTINGS.get(pkg)
        if not settings or not settings['place_id']:
            continue 
            
        ACTIVE_PACKAGES.append(pkg)
        jalankan_siklus_login(pkg)
        
    print(f"\n✅ SELESAI. {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")
    if len(ACTIVE_PACKAGES) == 0: return

    if RESTART_INTERVAL > 0:
        print(f"⏳ Auto-Restart: {int(RESTART_INTERVAL/60)} Menit")
    else:
        print("⏸️  Tanpa Auto-Restart")
    print("="*50)

    last_restart_time = time.time()
    while True:
        try:
            time.sleep(10)
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ RESTARTING SIKLUS (ROOT)...")
                    for pkg in ACTIVE_PACKAGES:
                        jalankan_siklus_login(pkg)
                    last_restart_time = time.time()
                    print(f"\n✅ Selesai. Menunggu {int(RESTART_INTERVAL/60)} menit.")
        except KeyboardInterrupt:
            print("\n🛑 Stop.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
