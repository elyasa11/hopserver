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

# ================= FUNGSI SISTEM =================

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

# FUNGSI FORCE CLOSE DIMATIKAN (Agar Floating Tetap Aman)
def force_close(pkg):
    pass 

def wake_up_app(pkg):
    """
    Menggunakan 'monkey' untuk mensimulasikan ketukan jari pada icon aplikasi.
    Ini 100% ampuh membangunkan aplikasi yang 'tertidur' di background.
    """
    clean = get_pkg_name(pkg)
    # Perintah monkey: -p [package] 1 (artinya kirim 1 event sentuhan)
    cmd = f"monkey -p {clean} -c android.intent.category.LAUNCHER 1"
    os.system(f"su -c '{cmd}' > /dev/null 2>&1")

def join_game_link(pkg, specific_place_id=None, vip_link_input=None):
    """
    Mengirim sinyal Link Game ke aplikasi yang SUDAH BANGUN.
    """
    clean = get_pkg_name(pkg)
    
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    if not specific_place_id:
        return

    final_uri = ""
    if vip_link_input and ("http" in vip_link_input or "roblox.com" in vip_link_input):
        final_uri = vip_link_input.strip()
    elif vip_link_input and vip_link_input.strip() != "":
        final_uri = f"roblox://placeId={specific_place_id}&privateServerLinkCode={vip_link_input.strip()}"
    else:
        final_uri = f"roblox://placeId={specific_place_id}"

    # Flag Hot Reload: Clear Top & Single Top
    cmd = (
        f"am start --user 0 "
        f"-a android.intent.action.VIEW "
        f"-d \"{final_uri}\" "
        f"--activity-clear-top "
        f"--activity-single-top "
        f"{clean}"
    )
    
    os.system(f"su -c '{cmd}' > /dev/null 2>&1")

# === FUNGSI SIKLUS (MONKEY METHOD) ===
def jalankan_siklus_login(pkg):
    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    
    # 1. BANGUNKAN DULU (Pake Monkey)
    print(f"    🐵 Monkey Tap: Membangunkan aplikasi...")
    wake_up_app(pkg)
    
    # Beri waktu si Monkey bekerja & app muncul di layar
    time.sleep(5)
    
    # 2. SUNTIKKAN LINK GAME
    print(f"    🚀 Inject Link: Masuk ke server...")
    join_game_link(pkg)
    
    # 3. Jeda Stabilisasi
    print("    ⏳ Menunggu 20 detik...")
    time.sleep(20) 

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
    print("=== ROBLOX MANAGER (MONKEY WAKE-UP FIX) ===")
    os.system("su -c 'echo ✅ Root OK' || echo '⚠️ Cek Root'")
    
    RESTART_INTERVAL = setup_configuration()
    
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    for pkg in BASE_PACKAGES:
        settings = PACKAGE_SETTINGS.get(pkg)
        if settings and settings['place_id']: ACTIVE_PACKAGES.append(pkg)
        # Jalankan Siklus
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
                    print("   (Menggunakan Monkey Tap + Hot Reload)")
                    
                    for pkg in ACTIVE_PACKAGES:
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
