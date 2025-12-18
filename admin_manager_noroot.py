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

# ================= FUNGSI BANTUAN =================

def input_aman(prompt):
    """
    Mengambil input dengan membersihkan buffer keyboard sebelumnya.
    Mencegah input loncat, tapi membolehkan user menekan Enter (kosong).
    """
    try:
        sys.stdin.flush() # Bersihkan sisa input hantu
    except:
        pass
        
    try:
        return input(prompt).strip()
    except EOFError:
        return ""

def force_close(pkg):
    clean = get_pkg_name(pkg)
    try:
        os.system(f"am force-stop {clean} > /dev/null 2>&1")
    except:
        pass

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
    # Ambil setting jika tidak dipassing langsung
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    # --- LOGIKA SKIP JIKA ID KOSONG ---
    if not specific_place_id:
        print(f"⚠️  {clean} di-skip (ID Game kosong).")
        return

    final_uri = ""
    
    # Logika Link Original
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
    # Cek dulu sebelum memproses, apakah ada settingannya?
    settings = PACKAGE_SETTINGS.get(pkg)
    
    # LOGIKA SKIP UTAMA:
    if not settings or not settings['place_id']:
        # Jangan print apa-apa atau print skip simple, lalu return
        # Agar tidak mematikan paksa aplikasi yang tidak dipakai
        return 

    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    
    # 1. Matikan (Hanya jika ID ada)
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
    
    # Bersihkan buffer sebelum mulai
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
        print("Note: Kosongkan Place ID (Tekan Enter) jika ingin men-skip akun tersebut.")
        
        mode = input_aman("1. Satu Game Semua Akun / 2. Beda-beda: ")

        if mode == "1":
            print("\n[MODE SERAGAM]")
            pid = input_aman("Masukkan Place ID: ")
            vip = ""
            if pid: # Cuma tanya link jika ID diisi
                vip = input_aman("Link Private (Enter jika Public): ")
            
            for pkg in BASE_PACKAGES:
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
                
        else:
            print("\n[MODE INDIVIDUAL]")
            for pkg in BASE_PACKAGES:
                clean = get_pkg_name(pkg)
                print(f"\nSetting untuk {clean}:")
                
                # Di sini inputnya BOLEH KOSONG
                pid = input_aman(f"  - Place ID (Enter utk Skip): ")
                vip = ""
                
                if pid: # Hanya tanya VIP link jika ID diisi
                    vip = input_aman(f"  - Link Private: ")
                else:
                    print(f"    (Akun {clean} akan dinonaktifkan)")
                    
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    # Waktu Restart
    print("\n--- WAKTU RESTART ---")
    try:
        def_menit = 0
        if saved_data and 'restart_seconds' in saved_data:
            def_menit = int(saved_data['restart_seconds'] / 60)
            
        inp = input_aman(f"Restart tiap berapa menit? (Enter={def_menit}): ")
        
        if inp == "":
            restart_seconds = def_menit * 60
        else:
            restart_seconds = int(inp) * 60
            
    except:
        restart_seconds = 0
    
    save_current_config(restart_seconds)
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (SKIP EMPTY ID) ===")
    
    RESTART_INTERVAL = setup_configuration()
    
    # 1. PELUNCURAN AWAL (PHASE 1)
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    
    for pkg in BASE_PACKAGES:
        # Cek apakah setting ada DAN Place ID tidak kosong
        settings = PACKAGE_SETTINGS.get(pkg)
        
        if not settings or not settings['place_id']:
            # Skip diam-diam atau info kecil
            # print(f"ℹ️  Skip {get_pkg_name(pkg)} (Tidak disetting)")
            continue 
        
        ACTIVE_PACKAGES.append(pkg)
        
        # Jalankan Siklus
        jalankan_siklus_login(pkg)
        
    print("\n" + "="*50)
    print(f"✅ SELESAI. {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")
    
    if len(ACTIVE_PACKAGES) == 0:
        print("⚠️  Tidak ada akun aktif. Pastikan ID Game diisi minimal satu.")
        return

    if RESTART_INTERVAL > 0:
        print(f"⏳ Auto-Restart: {int(RESTART_INTERVAL/60)} Menit")
    else:
        print("⏸️  Tanpa Auto-Restart")
    print("="*50)

    # 2. LOOP AUTO RESTART (PHASE 2)
    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10)
            
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ WAKTU HABIS! RESTARTING SIKLUS...")
                    
                    for pkg in ACTIVE_PACKAGES:
                        # Panggil fungsi yang sama persis
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
