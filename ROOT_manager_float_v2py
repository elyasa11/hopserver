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

# KITA NONAKTIFKAN FUNGSI FORCE CLOSE
# Agar jendela Floating Taskbar tidak hilang/reset
def force_close(pkg):
    pass 
    # Sengaja dikosongkan. 
    # Kita tidak mau mematikan process ID.

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
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

    print(f"    -> 🔄 Hot-Reloading {clean} (Keep Float)...")
    
    # === RAHASIA AGAR TIDAK PERLU FORCE STOP ===
    # Kita gunakan flag '--activity-clear-top' dan '--activity-single-top'
    # Ini memaksa game reload ke menu awal/join baru TANPA menutup jendela.
    
    cmd = (
        f"am start --user 0 "
        f"-a android.intent.action.VIEW "
        f"-d \"{final_uri}\" "
        f"--activity-clear-top "   # <--- Hapus aktivitas lama di dalam jendela
        f"--activity-single-top "  # <--- Pakai jendela yang sudah ada (jangan buat baru)
        f"{clean}"
    )
    
    os.system(f"{cmd} > /dev/null 2>&1")

# === FUNGSI SIKLUS ===
def jalankan_siklus_login(pkg):
    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    
    # 1. KITA HAPUS BAGIAN FORCE STOP
    # force_close(pkg) <-- Dihapus agar tidak reset ke fullscreen
    
    # 2. Langsung Timpa/Inject Game Baru
    launch_game(pkg)
    
    # 3. Jeda
    print("⏳ Menunggu 25 detik agar stabil...")
    time.sleep(25) 

# ================= INPUT & SAVE MENU =================

def load_last_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f: return json.load(f)
        except: return None
    return None

def save_current_config(restart_time):
    data = {"restart_seconds": restart_time, "packages": PACKAGE_SETTINGS}
    with open(CONFIG_FILE, 'w') as f: json.dump(data, f, indent=4)
    print("✅ Konfigurasi tersimpan.")

def setup_configuration():
    global PACKAGE_SETTINGS
    saved_data = load_last_config()
    loaded_packages = False
    
    if saved_data:
        print(f"\n📂 Ditemukan data lama.")
        try:
            if input("Gunakan settingan lama? (y/n): ").lower().strip() == 'y':
                PACKAGE_SETTINGS = saved_data['packages']
                loaded_packages = True
        except: pass

    if not loaded_packages:
        print("\n--- PENGATURAN BARU ---")
        try:
            mode = input("1. Satu Game / 2. Beda Game: ").strip()
            if mode == "1":
                print("\n[MODE SERAGAM]")
                pid = input("Masukkan Place ID: ").strip()
                vip = input("Link Private (Enter jika Public): ").strip()
                for pkg in BASE_PACKAGES: PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
            else:
                print("\n[MODE INDIVIDUAL]")
                for pkg in BASE_PACKAGES:
                    clean = get_pkg_name(pkg)
                    print(f"\nSetting untuk {clean}:")
                    pid = input(f"  - Place ID: ").strip()
                    vip = ""
                    if pid: vip = input(f"  - Link Private: ").strip()
                    PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
        except: pass

    print("\n--- WAKTU RESTART ---")
    try:
        default_menit = 0
        if saved_data and 'restart_seconds' in saved_data:
            default_menit = int(saved_data['restart_seconds'] / 60)
        inp = input(f"Restart tiap berapa menit? (Enter={default_menit} mnt): ").strip()
        restart_seconds = (default_menit * 60) if inp == "" else (int(inp) * 60)
    except:
        restart_seconds = 0
    
    save_current_config(restart_seconds)
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (HOT RELOAD / NO KILL) ===")
    
    RESTART_INTERVAL = setup_configuration()
    
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    for pkg in BASE_PACKAGES:
        settings = PACKAGE_SETTINGS.get(pkg)
        if settings and settings['place_id']: ACTIVE_PACKAGES.append(pkg)
        # Jalankan Hot Reload
        jalankan_siklus_login(pkg)
    
    if not ACTIVE_PACKAGES: return

    print(f"\n✅ {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")
    if RESTART_INTERVAL > 0: print(f"⏳ Auto-Restart: {int(RESTART_INTERVAL/60)} Menit")
    else: print("⏸️  Tanpa Auto-Restart")
    print("="*50)

    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10)
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ WAKTU HABIS! REFRESHING GAMES...")
                    print("   (Me-refresh game tanpa menutup jendela...)")
                    
                    for pkg in ACTIVE_PACKAGES:
                        # Jalankan metode yang sama (Hot Reload)
                        jalankan_siklus_login(pkg)
                    
                    last_restart_time = time.time()
                    print(f"\n✅ Refresh Selesai. Menunggu {int(RESTART_INTERVAL/60)} menit.")
                    
        except KeyboardInterrupt:
            print("\n🛑 Script Dihentikan.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
