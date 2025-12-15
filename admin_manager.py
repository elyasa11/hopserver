import os
import subprocess
import time
import json
import random
import glob
import urllib.request
import re # Tambahan untuk membaca link

# ================= KONFIGURASI DASAR =================
BASE_PACKAGES = [
    "com.roblox.clienx",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

WORKSPACE_PATH = "/storage/emulated/0/Delta/Workspace"
FREEZE_THRESHOLD = 120
MAPPING_TIMEOUT = 60

# Penyimpanan Setting (Diisi otomatis lewat menu nanti)
PACKAGE_SETTINGS = {} 

# ================= FUNGSI SISTEM =================

def run_root(cmd):
    return subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True).stdout.strip()

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def force_close(pkg):
    clean = get_pkg_name(pkg)
    os.system(f"/system/bin/am force-stop {clean}")

# [BARU] Fungsi Pintar Ekstrak Kode dari Link Share
def extract_vip_code(input_str):
    if not input_str or input_str.strip() == "": return None
    
    # 1. Cek format Share Link (https://www.roblox.com/share?code=...)
    match_share = re.search(r'code=([a-zA-Z0-9\-]+)', input_str)
    if match_share:
        return match_share.group(1)
        
    # 2. Cek format Link VIP Lama (privateServerLinkCode=...)
    match_old = re.search(r'privateServerLinkCode=([a-zA-Z0-9\-]+)', input_str)
    if match_old:
        return match_old.group(1)

    # 3. Jika cuma kode pendek (bukan url), anggap itu kodenya
    if "http" not in input_str and "roblox.com" not in input_str:
        return input_str.strip()
        
    return input_str # Fallback (kembalikan aslinya kalau bingung)

# [UPDATE] Launch Game Support Config & VIP
def launch_game(pkg, specific_place_id=None, job_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
    # Ambil setting dari memori jika parameter kosong
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    if not specific_place_id:
        print(f"❌ Error: Tidak ada Place ID untuk {clean}")
        return

    # Bersihkan Kode VIP (Ambil kode dari link panjang)
    clean_vip_code = extract_vip_code(vip_link_input)

    # Susun Link Deep Link Android
    uri = f"roblox://placeId={specific_place_id}"
    
    if clean_vip_code:
        # Masukkan kode yang sudah dibersihkan
        uri += f"&privateServerLinkCode={clean_vip_code}"
        print(f"    -> Target: 🔒 Private Server (Code: {clean_vip_code[:6]}...)")
    elif job_id:
        uri += f"&gameId={job_id}"
        print(f"    -> Target: 🌍 Public Server {job_id[:8]}...")
    else:
        print(f"    -> Target: 🎲 Random Server")

    cmd = f"/system/bin/am start --user 0 -a android.intent.action.VIEW -d \"{uri}\" {clean}"
    os.system(f"{cmd} > /dev/null 2>&1")

def is_app_running(pkg):
    clean = get_pkg_name(pkg)
    try:
        cmd = f"/system/bin/pidof {clean}"
        output = subprocess.check_output(cmd, shell=True, text=True).strip()
        return bool(output)
    except:
        return False

# ================= API ROBLOX =================

def get_public_servers(place_id):
    if not place_id: return []
    print(f"[API] Mengambil daftar server untuk Place {place_id}...")
    url = f"https://games.roblox.com/v1/games/{place_id}/servers/Public?sortOrder=Asc&limit=100"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        valid_servers = []
        if 'data' in data:
            for s in data['data']:
                if s.get('playing', 0) < s.get('maxPlayers', 0):
                    valid_servers.append(s['id'])
        return valid_servers
    except Exception as e:
        print(f"[API ERROR] {e}")
        return []

# ================= FILE OPERATIONS =================

def get_status_files():
    files = run_root(f"ls {WORKSPACE_PATH}/status_*.json")
    if "No such file" in files or not files: return []
    return [f for f in files.split('\n') if f.strip()]

def read_json_root(filepath):
    try:
        content = run_root(f"cat {filepath}")
        if content: return json.loads(content)
    except: pass
    return None

def write_json_root(filepath, data):
    try:
        json_str = json.dumps(data).replace('"', '\\"')
        run_root(f"echo \"{json_str}\" > {filepath}")
    except: pass

def inject_hop_signal(filepath, data):
    data['action'] = "HOP"
    write_json_root(filepath, data)

def inject_restart_status(filepath, data):
    data['status'] = "RESTARTING"
    data['timestamp'] = data.get('timestamp', 0) + 1 
    write_json_root(filepath, data)

# ================= INPUT MENU (SETUP) =================

def setup_configuration():
    print("\n--- PENGATURAN MODE GAME ---")
    print("1. SATU GAME untuk SEMUA AKUN")
    print("2. BEDA GAME setiap AKUN")
    mode = input("Pilih Mode (1/2): ").strip()

    if mode == "1":
        pid = input("Masukkan Place ID: ").strip()
        print("Masukkan Link Private Server (Share Link):")
        vip = input("(Kosongkan jika Public): ").strip()
        
        # Simpan ke semua paket
        for pkg in BASE_PACKAGES:
            PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
            
    else:
        # Input satu per satu
        for pkg in BASE_PACKAGES:
            clean = get_pkg_name(pkg)
            print(f"\nSetting untuk {clean}:")
            pid = input(f"  - Place ID: ").strip()
            print(f"  - Link Private Server (Enter jika Public):")
            vip = input(f"    > ").strip()
            PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    print("\n--- PENGATURAN AUTO RESTART ---")
    restart_input = input("Restart semua akun setiap berapa MENIT? (0 = Matikan): ").strip()
    try:
        restart_minutes = int(restart_input)
        restart_seconds = restart_minutes * 60
    except:
        restart_seconds = 0
        
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER V5.1: AUTO RESTART & SHARE LINK ===")
    
    # 1. Jalankan Setup Menu
    RESTART_INTERVAL = setup_configuration()
    LAST_GLOBAL_RESTART = time.time()
    
    package_map = {}
    claimed_files = set()

    print(f"\n[PHASE 1] INITIAL LAUNCH")
    
    server_pools = {} 
    
    # 2. Loop Peluncuran Awal
    for i, pkg in enumerate(BASE_PACKAGES):
        clean_pkg = get_pkg_name(pkg)
        
        # Ambil setting yang sudah diinput
        settings = PACKAGE_SETTINGS[pkg]
        pid = settings['place_id']
        vip = settings['vip_code'] 
        
        print(f"\n--> Meluncurkan: {clean_pkg}")
        
        target_job_id = None
        # Hanya cari server public jika VIP KOSONG
        if not vip or vip.strip() == "":
            if pid not in server_pools:
                server_pools[pid] = get_public_servers(pid)
                random.shuffle(server_pools[pid])
            
            # Ambil server dari pool biar beda-beda
            if len(server_pools[pid]) > 0:
                target_job_id = server_pools[pid].pop(0)
        
        # Snapshot file
        files_state_before = {}
        for f in get_status_files():
            d = read_json_root(f)
            if d and 'timestamp' in d: files_state_before[f] = float(d['timestamp'])
        
        # Launch (Pass vip string mentah, nanti launch_game yg bersihkan)
        force_close(pkg)
        time.sleep(1)
        launch_game(pkg, job_id=target_job_id) 
        
        print("    Mencari file milik dia...", end="", flush=True)
        detected_info = None

        # Mapping Logic
        for _ in range(MAPPING_TIMEOUT):
            time.sleep(1)
            files_now = get_status_files()
            for f in files_now:
                if f in claimed_files: continue 
                
                data = read_json_root(f)
                if data and 'timestamp' in data:
                    ts = float(data['timestamp'])
                    prev_ts = files_state_before.get(f, 0)
                    if ts > prev_ts:
                        detected_info = {
                            'file': f,
                            'user': data.get('username', 'Unknown'),
                            'last_ts': ts,
                            'last_change_time': time.time()
                        }
                        claimed_files.add(f)
                        break
            if detected_info: break
        
        if detected_info:
            print(f" OK! ({detected_info['user']})")
            package_map[pkg] = detected_info
        else:
            print(" Timeout! (Gagal mapping)")

    print("\n" + "="*50)
    print(f"[PHASE 2] MONITORING AKTIF")
    if RESTART_INTERVAL > 0:
        print(f"⚠️  Auto-Restart Aktif: Setiap {int(RESTART_INTERVAL/60)} Menit")
    print("="*50)

    while True:
        now = time.time()
        
        # === A. CEK JADWAL RESTART GLOBAL ===
        if RESTART_INTERVAL > 0 and (now - LAST_GLOBAL_RESTART > RESTART_INTERVAL):
            print("\n⏰ WAKTUNYA JADWAL RESTART! MELUNCURKAN ULANG SEMUA...")
            
            for pkg in BASE_PACKAGES:
                clean_pkg = get_pkg_name(pkg)
                print(f"   -> Restarting {clean_pkg}...")
                force_close(pkg)
                time.sleep(1)
                launch_game(pkg) # Re-launch sesuai config awal
                
                # Reset Timer Freeze agar tidak error
                if pkg in package_map:
                    package_map[pkg]['last_change_time'] = time.time()
            
            LAST_GLOBAL_RESTART = time.time()
            print("✅ Restart Selesai. Kembali Monitoring.\n")
            time.sleep(10) # Beri waktu napas
            continue # Skip loop kali ini

        # === B. LOOP MONITORING (ANTI-FREEZE) ===
        for pkg in BASE_PACKAGES:
            if pkg not in package_map: continue
            
            clean = get_pkg_name(pkg)
            info = package_map[pkg]
            fpath = info['file']
            
            if not is_app_running(pkg):
                print(f"\n[CRASH] {clean} mati. Relaunching...")
                launch_game(pkg)
                info['last_change_time'] = now 
                continue
            
            data = read_json_root(fpath)
            if data and 'timestamp' in data:
                current_file_ts = float(data['timestamp'])
                status = data.get('status', 'UNKNOWN')
                
                if status == "RESTARTING":
                    info['last_change_time'] = now
                    info['last_ts'] = current_file_ts
                    continue

                if current_file_ts > info['last_ts']:
                    info['last_ts'] = current_file_ts
                    info['last_change_time'] = now
                else:
                    stagnant_duration = now - info['last_change_time']
                    if stagnant_duration > FREEZE_THRESHOLD:
                        print(f"\n[FREEZE] {info['user']} ({clean}) macet {int(stagnant_duration)}s!")
                        inject_restart_status(fpath, data)
                        print("         -> Restarting...")
                        force_close(pkg)
                        time.sleep(2)
                        launch_game(pkg)
                        info['last_change_time'] = now
                        info['last_ts'] = current_file_ts + 1

        # === C. LOOP TABRAKAN (COLLISION) ===
        server_map = {}
        all_files = get_status_files()
        
        for f in all_files:
            d = read_json_root(f)
            if d and 'jobId' in d:
                # Jangan masukkan user VIP ke logic tabrakan (karena VIP server cuma 1, pasti JobID sama)
                # Kita cek manual apakah paket ini pake VIP atau tidak
                # (Sederhananya: Kalau VIP, script Python JANGAN inject HOP)
                
                jid = d['jobId']
                if jid not in server_map: server_map[jid] = []
                server_map[jid].append({'file': f, 'data': d, 'user': d.get('username')})
        
        for jid, sessions in server_map.items():
            if len(sessions) > 1:
                # Tabrakan terdeteksi. Inject HOP ke korban.
                # Tapi tunggu, kalau mereka main di VIP Server, jangan di HOP!
                # Karena kita gak punya akses mudah cek 'apakah ini VIP' dari file JSON,
                # kita biarkan saja. User yang main VIP harusnya paham risiko tabrakan jika share link sama.
                for victim in sessions[1:]:
                    inject_hop_signal(victim['file'], victim['data'])
        
        print(".", end="", flush=True)
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStop.")
