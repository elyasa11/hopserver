import os
import time
import subprocess
import re

# ================= KONFIGURASI PAKET =================
# Daftar nama paket Roblox yang kamu gunakan (Clone)
BASE_PACKAGES = [
    "com.roblox.client",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

# Penyimpanan Setting
PACKAGE_SETTINGS = {}

# Daftar Paket yang AKTIF (Punya ID Game)
ACTIVE_PACKAGES = []

# ================= FUNGSI SISTEM (NON-ROOT) =================

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
    
    # Ambil setting dari memori
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    # Filter Terakhir (Jaga-jaga)
    if not specific_place_id:
        return

    final_uri = ""
    
    # LOGIC LINK
    if vip_link_input and ("http" in vip_link_input or "roblox.com" in vip_link_input):
        final_uri = vip_link_input.strip()
        print(f"    -> Target: 🔗 Private Server (Direct Link)")
    elif vip_link_input and vip_link_input.strip() != "":
        final_uri = f"roblox://placeId={specific_place_id}&privateServerLinkCode={vip_link_input.strip()}"
        print(f"    -> Target: 🔒 Private Server (Code Injection)")
    else:
        final_uri = f"roblox://placeId={specific_place_id}"
        print(f"    -> Target: 🎲 Public/Random Server")

    # EKSEKUSI
    print(f"    -> Meluncurkan {clean}...")
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" {clean}"
    os.system(f"{cmd} > /dev/null 2>&1")

# ================= INPUT MENU =================

def setup_configuration():
    print("\n--- PENGATURAN MODE GAME ---")
    print("1. SATU GAME untuk SEMUA AKUN")
    print("2. BEDA GAME setiap AKUN")
    mode = input("Pilih Mode (1/2): ").strip()

    if mode == "1":
        print("\n[MODE SERAGAM]")
        pid = input("Masukkan Place ID: ").strip()
        print("Masukkan Link Private Server (Share Link / Code):")
        vip = input("(Kosongkan jika Public): ").strip()
        
        # Simpan ke semua, nanti di filter di main()
        for pkg in BASE_PACKAGES:
            PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
            
    else:
        print("\n[MODE INDIVIDUAL]")
        print("Tip: Kosongkan Place ID (Tekan Enter) jika ingin melewati akun ini.")
        for pkg in BASE_PACKAGES:
            clean = get_pkg_name(pkg)
            print(f"\nSetting untuk {clean}:")
            pid = input(f"  - Place ID: ").strip()
            
            vip = ""
            if pid: # Hanya tanya VIP jika ID diisi
                print(f"  - Link Private Server (Enter jika Public):")
                vip = input(f"    > ").strip()
            
            PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    print("\n--- PENGATURAN AUTO RESTART ---")
    try:
        inp = input("Restart (Re-join) setiap berapa MENIT? (0 = Mati): ").strip()
        if not inp: inp = "0"
        restart_minutes = int(inp)
        restart_seconds = restart_minutes * 60
    except:
        restart_seconds = 0
        
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (SMART FILTER) ===")
    
    RESTART_INTERVAL = setup_configuration()
    
    # 1. PELUNCURAN AWAL & FILTERISASI
    print(f"\n[PHASE 1] INITIAL LAUNCH & FILTERING")
    
    for pkg in BASE_PACKAGES:
        clean_pkg = get_pkg_name(pkg)
        settings = PACKAGE_SETTINGS.get(pkg)
        
        # >>> LOGIKA FILTER: Cek apakah Place ID ada? <<<
        if not settings or not settings['place_id']:
            print(f"\n⏩ SKIP: {clean_pkg} (ID Kosong / Tidak Diisi)")
            continue # Lewati loop ini, jangan launch
        
        # Jika lolos filter, masukkan ke daftar AKTIF
        ACTIVE_PACKAGES.append(pkg)
        
        print(f"\n--> Memproses: {clean_pkg}")
        force_close(pkg)
        time.sleep(1)
        launch_game(pkg)
        
    print("\n" + "="*50)
    print(f"✅ SELESAI. {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")
    
    if len(ACTIVE_PACKAGES) == 0:
        print("❌ Tidak ada akun yang dijalankan. Script berhenti.")
        return

    if RESTART_INTERVAL > 0:
        print(f"⏳ Jadwal Restart Aktif: Setiap {int(RESTART_INTERVAL/60)} Menit")
    else:
        print("⏸️  Mode Standby (Tanpa Auto-Restart)")
    print("="*50)

    # 2. LOOP WAKTU (Hanya untuk Paket Aktif)
    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10) 
            
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ WAKTUNYA JADWAL RESTART! MELUNCURKAN ULANG...")
                    
                    # Hanya loop paket yang ada di ACTIVE_PACKAGES
                    for pkg in ACTIVE_PACKAGES:
                        print(f"   -> Re-launching {get_pkg_name(pkg)}...")
                        force_close(pkg) 
                        time.sleep(2)    
                        launch_game(pkg) 
                    
                    last_restart_time = time.time()
                    print(f"\n✅ Selesai. Menunggu siklus berikutnya ({int(RESTART_INTERVAL/60)} menit lagi).")
                    
        except KeyboardInterrupt:
            print("\n🛑 Script Dihentikan.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
