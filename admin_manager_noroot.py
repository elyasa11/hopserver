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

# ================= FUNGSI SISTEM (NON-ROOT) =================

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def force_close(pkg):
    clean = get_pkg_name(pkg)
    # Tanpa root, kita coba pakai perintah standar Android.
    # Jika gagal (Permission Denied), script akan lanjut ke launch (Re-join).
    try:
        os.system(f"am force-stop {clean} > /dev/null 2>&1")
    except:
        pass

def extract_vip_code(input_str):
    if not input_str or input_str.strip() == "": return None
    # Cek format Share Link
    match_share = re.search(r'code=([a-zA-Z0-9\-]+)', input_str)
    if match_share: return match_share.group(1)
    # Cek format Link VIP Lama
    match_old = re.search(r'privateServerLinkCode=([a-zA-Z0-9\-]+)', input_str)
    if match_old: return match_old.group(1)
    # Cek Raw Code
    if "http" not in input_str and "roblox.com" not in input_str: return input_str.strip()
    return input_str 

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
    # Ambil setting dari memori
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    if not specific_place_id:
        print(f"❌ Error: Tidak ada Place ID untuk {clean}")
        return

    final_uri = ""
    
    # LOGIC LINK (Sama seperti V5.4)
    if vip_link_input and ("http" in vip_link_input or "roblox.com" in vip_link_input):
        final_uri = vip_link_input.strip()
        print(f"    -> Target: 🔗 Private Server (Direct Link)")
    elif vip_link_input and vip_link_input.strip() != "":
        final_uri = f"roblox://placeId={specific_place_id}&privateServerLinkCode={vip_link_input.strip()}"
        print(f"    -> Target: 🔒 Private Server (Code Injection)")
    else:
        final_uri = f"roblox://placeId={specific_place_id}"
        print(f"    -> Target: 🎲 Public/Random Server")

    # EKSEKUSI (Tanpa 'su -c')
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
        pid = input("Masukkan Place ID: ").strip()
        print("Masukkan Link Private Server (Share Link / Code):")
        vip = input("(Kosongkan jika Public): ").strip()
        
        for pkg in BASE_PACKAGES:
            PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
            
    else:
        for pkg in BASE_PACKAGES:
            clean = get_pkg_name(pkg)
            print(f"\nSetting untuk {clean}:")
            pid = input(f"  - Place ID: ").strip()
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
    print("=== ROBLOX MANAGER (NO ROOT VERSION) ===")
    
    RESTART_INTERVAL = setup_configuration()
    
    # 1. PELUNCURAN AWAL
    print(f"\n[PHASE 1] INITIAL LAUNCH")
    for pkg in BASE_PACKAGES:
        clean_pkg = get_pkg_name(pkg)
        print(f"\n--> Memproses: {clean_pkg}")
        
        # Coba tutup dulu (Best Effort)
        force_close(pkg)
        time.sleep(1)
        launch_game(pkg)
        
    print("\n" + "="*50)
    print(f"✅ SEMUA AKUN DILUNCURKAN")
    if RESTART_INTERVAL > 0:
        print(f"⏳ Jadwal Restart Aktif: Setiap {int(RESTART_INTERVAL/60)} Menit")
    else:
        print("⏸️  Mode Standby (Tanpa Auto-Restart)")
    print("="*50)

    # 2. LOOP WAKTU (TIMER)
    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10) # Cek waktu setiap 10 detik
            
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                remaining = RESTART_INTERVAL - elapsed
                
                # Tampilkan countdown sederhana di log (opsional, biar gak sepi)
                # print(f"\rSisa waktu restart: {int(remaining)} detik...", end="")

                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ WAKTUNYA JADWAL RESTART! MELUNCURKAN ULANG...")
                    
                    for pkg in BASE_PACKAGES:
                        print(f"   -> Re-launching {get_pkg_name(pkg)}...")
                        force_close(pkg) # Coba matikan
                        time.sleep(2)    # Beri jeda napas
                        launch_game(pkg) # Buka lagi
                    
                    last_restart_time = time.time()
                    print(f"\n✅ Selesai. Menunggu siklus berikutnya ({int(RESTART_INTERVAL/60)} menit lagi).")
                    
        except KeyboardInterrupt:
            print("\n🛑 Script Dihentikan.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
