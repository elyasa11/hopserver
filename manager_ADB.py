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
ADB_ADDRESS = "localhost:9698" # Alamat dari SSH Tunnel kamu

# ================= FUNGSI BANTUAN & ADB =================

def adb_connect():
    """Mencoba menghubungkan ke ADB secara otomatis"""
    print(f"🔌 Menghubungkan ADB ke {ADB_ADDRESS}...")
    os.system(f"adb connect {ADB_ADDRESS} > /dev/null 2>&1")
    time.sleep(2)

def run_adb_cmd(cmd):
    """
    Menjalankan perintah Android lewat ADB Shell.
    Format: adb -s localhost:9698 shell [perintah]
    """
    full_cmd = f"adb -s {ADB_ADDRESS} shell {cmd}"
    os.system(f"{full_cmd} > /dev/null 2>&1")

def input_aman(prompt):
    """Input anti-skip untuk Termux"""
    try:
        sys.stdin.flush()
    except:
        pass
    try:
        return input(prompt).strip()
    except EOFError:
        return ""

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

# ================= FUNGSI LOGIKA UTAMA =================

def force_close(pkg):
    clean = get_pkg_name(pkg)
    try:
        # Perintah Force Stop lewat ADB
        # Kita gunakan am force-stop untuk mematikan total
        run_adb_cmd(f"am force-stop {clean}")
    except:
        pass

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    # SKIP jika ID kosong
    if not specific_place_id:
        print(f"⚠️  {clean} di-skip (ID Game kosong).")
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

    print(f"    -> 🚀 Meluncurkan {clean} via ADB...")
    
    # Perintah Launch lewat ADB
    # --activity-clear-task memastikan tidak sekedar resume
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" --activity-clear-task {clean}"
    run_adb_cmd(cmd)

# === FUNGSI SIKLUS (DIPAKAI DI AWAL & RESTART) ===
def jalankan_siklus_login(pkg):
    """
    Fungsi Satu Pintu: Mematikan Paksa -> Menunggu -> Menyalakan.
    Dipanggil saat Phase 1 (Awal) dan Phase 2 (Restart).
    """
    settings = PACKAGE_SETTINGS.get(pkg)
    if not settings or not settings['place_id']:
        return 

    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    
    # 1. PAKSA BERHENTI (ADB)
    print(f"    🛑 Mematikan paksa aplikasi...")
    force_close(pkg)
    
    # Jeda agar sistem benar-benar kill process
    time.sleep(2)
    
    # 2. LUNCURKAN GAME (ADB)
    launch_game(pkg)
    
    # 3. JEDA STABILISASI
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
    try: sys.stdin.flush() 
    except: pass

    if saved_data:
        print(f"\n📂 Ditemukan data lama.")
        pilih = input_aman("Gunakan settingan lama? (y/n): ").lower()
        if pilih == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded_packages = True

    if not loaded_packages:
        print("\n--- PENGATURAN BARU ---")
        mode = input_aman("1. Satu Game Semua Akun / 2. Beda-beda: ")

        if mode == "1":
            print("\n[MODE SERAGAM]")
            pid = input_aman("Masukkan Place ID: ")
            vip = ""
            if pid: vip = input_aman("Link Private (Enter jika Public): ")
            for pkg in BASE_PACKAGES:
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
        else:
            print("\n[MODE INDIVIDUAL]")
            for pkg in BASE_PACKAGES:
                clean = get_pkg_name(pkg)
                print(f"\nSetting untuk {clean}:")
                pid = input_aman(f"  - Place ID (Enter utk Skip): ")
                vip = ""
                if pid: vip = input_aman(f"  - Link Private: ")
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    print("\n--- WAKTU RESTART ---")
    try:
        def_menit = 0
        if saved_data and 'restart_seconds' in saved_data:
            def_menit = int(saved_data['restart_seconds'] / 60)
        inp = input_aman(f"Restart tiap berapa menit? (Enter={def_menit}): ")
        if inp == "": restart_seconds = def_menit * 60
        else: restart_seconds = int(inp) * 60
    except:
        restart_seconds = 0
    
    save_current_config(restart_seconds)
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (ADB + FORCE STOP) ===")
    
    # 1. KONEKSI ADB DULU
    adb_connect()
    
    # Cek apakah koneksi berhasil
    check = os.system(f"adb -s {ADB_ADDRESS} shell echo 'connected' > /dev/null 2>&1")
    if check != 0:
        print("\n❌ GAGAL KONEK ADB!")
        print(f"Pastikan kamu sudah menjalankan perintah SSH Tunnel:")
        print("ssh -oHostKeyAlgorithms=+ssh-rsa ... -Nf")
        return

    RESTART_INTERVAL = setup_configuration()
    
    # 2. PELUNCURAN AWAL (PHASE 1)
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    print("(Aplikasi akan dipaksa berhenti dulu sebelum dibuka)")
    
    for pkg in BASE_PACKAGES:
        settings = PACKAGE_SETTINGS.get(pkg)
        if not settings or not settings['place_id']: continue 
        ACTIVE_PACKAGES.append(pkg)
        
        # Panggil fungsi siklus (Matikan -> Hidupkan)
        jalankan_siklus_login(pkg)
        
    print(f"\n✅ SELESAI. {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")
    if len(ACTIVE_PACKAGES) == 0: return

    if RESTART_INTERVAL > 0:
        print(f"⏳ Auto-Restart: {int(RESTART_INTERVAL/60)} Menit")
    else:
        print("⏸️  Tanpa Auto-Restart")
    print("="*50)

    # 3. LOOP RESTART (PHASE 2)
    last_restart_time = time.time()
    while True:
        try:
            time.sleep(10)
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ WAKTU HABIS! MEMULAI RESTART...")
                    print("   (Mematikan paksa semua aplikasi...)")
                    
                    for pkg in ACTIVE_PACKAGES:
                        # Panggil fungsi siklus (Matikan -> Hidupkan)
                        jalankan_siklus_login(pkg)
                        
                    last_restart_time = time.time()
                    print(f"\n✅ Restart Selesai. Menunggu {int(RESTART_INTERVAL/60)} menit lagi.")
        except KeyboardInterrupt:
            print("\n🛑 Stop.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
