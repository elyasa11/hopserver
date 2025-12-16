import os
import subprocess
import time
import json
import random
import glob
import urllib.request
import re 
# === TAMBAHAN UNTUK FIX ERROR RISH ===
os.environ['RISH_APPLICATION_ID'] = 'com.termux'
# =====================================

# ================= KONFIGURASI DASAR =================
BASE_PACKAGES = [
    "com.roblox.client",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

WORKSPACE_PATH = "/storage/emulated/0/Delta/Workspace"
FREEZE_THRESHOLD = 120
MAPPING_TIMEOUT = 60

# Global Config Storage
PACKAGE_SETTINGS = {} 

# ================= FUNGSI SISTEM (MODIFIED FOR SHIZUKU) =================

def run_rish(cmd):
    """
    Menjalankan perintah menggunakan rish (interface Shizuku untuk terminal).
    Menggantikan fungsi run_root(su).
    """
    # Menggunakan rish -c sebagai pengganti su -c
    # Pastikan rish sudah terinstall di /usr/bin termux
    return subprocess.run(f"rish -c '{cmd}'", shell=True, capture_output=True, text=True).stdout.strip()

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def force_close(pkg):
    clean = get_pkg_name(pkg)
    # Menggunakan rish untuk force stop
    os.system(f"rish -c 'am force-stop {clean}'")

def extract_vip_code(input_str):
    if not input_str or input_str.strip() == "": return None
    match_share = re.search(r'code=([a-zA-Z0-9\-]+)', input_str)
    if match_share: return match_share.group(1)
    match_old = re.search(r'privateServerLinkCode=([a-zA-Z0-9\-]+)', input_str)
    if match_old: return match_old.group(1)
    if "http" not in input_str and "roblox.com" not in input_str: return input_str.strip()
    return input_str 

def launch_game(pkg, specific_place_id=None, job_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    if not specific_place_id:
        print(f"ERROR: Tidak ada Place ID untuk {clean}")
        return

    final_uri = ""
    # LOGIC LINK HYBRID
    if vip_link_input and ("http" in vip_link_input or "roblox.com" in vip_link_input):
        final_uri = vip_link_input.strip()
        print("    -> Target: Private Server (Direct Link)")
    elif vip_link_input and vip_link_input.strip() != "":
        final_uri = f"roblox://placeId={specific_place_id}&privateServerLinkCode={vip_link_input.strip()}"
        print("    -> Target: Private Server (Code Injection)")
    elif job_id:
        final_uri = f"roblox://placeId={specific_place_id}&gameId={job_id}"
        print(f"    -> Target: Public Server {job_id[:8]}...")
    else:
        final_uri = f"roblox://placeId={specific_place_id}"
        print("    -> Target: Random Server")

    # MODIFIKASI: Membungkus perintah AM START ke dalam rish
    # Escape tanda kutip ganda pada URI agar tidak bentrok dengan command shell
    safe_uri = final_uri.replace('"', '\\"')
    
    # --- PERUBAHAN UNTUK FLOAT/WINDOW MODE ---
    # --windowingMode 5 : Memaksa mode Freeform (Float)
    # --activity-multiple-task : Memastikan ini dianggap tugas baru (agar bisa banyak window)
    # --activity-new-task : Wajib untuk start dari terminal
    
    cmd = f"rish -c 'am start --user 0 --windowingMode 5 --activity-multiple-task --activity-new-task -a android.intent.action.VIEW -d \"{safe_uri}\" {clean}'"
    
    os.system(f"{cmd} > /dev/null 2>&1")

def is_app_running(pkg):
    clean = get_pkg_name(pkg)
    try:
        # MODIFIKASI: Menggunakan pidof via rish
        cmd = f"rish -c 'pidof {clean}'"
        output = subprocess.check_output(cmd, shell=True, text=True).strip()
        return bool(output)
    except:
        return False

# ================= API & FILE OPS =================

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

def get_status_files():
    # Menggunakan rish untuk listing file (jika butuh akses folder khusus)
    # Jika folder ada di internal storage biasa, os.listdir sebenarnya cukup,
    # tapi kita pakai rish agar konsisten dengan izin file yang dibuat Executor.
    files = run_rish(f"ls {WORKSPACE_PATH}/status_*.json")
    if "No such file" in files or not files: return []
    return [f for f in files.split('\n') if f.strip()]

def read_json_root(filepath):
    try:
        content = run_rish(f"cat {filepath}")
        if content: return json.loads(content)
    except: pass
    return None

def write_json_root(filepath, data):
    try:
        json_str = json.dumps(data).replace('"', '\\"')
        run_rish(f"echo \"{json_str}\" > {filepath}")
    except: pass

def inject_hop_signal(filepath, data):
    data['action'] = "HOP"
    write_json_root(filepath, data)

def inject_restart_status(filepath, data):
    data['status'] = "RESTARTING"
    data['timestamp'] = data.get('timestamp', 0) + 1 
    write_json_root(filepath, data)

# ================= SETUP =================

def setup_configuration():
    print("\n--- PENGATURAN MODE GAME (SHIZUKU EDITION) ---")
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
            pid = input("  - Place ID: ").strip()
            print("  - Link Private Server (Enter jika Public):")
            vip = input("    > ").strip()
            PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    print("\n--- PENGATURAN AUTO RESTART ---")
    try:
        inp = input("Restart setiap berapa MENIT? (0 = Mati): ").strip()
        if not inp: inp = "0"
        restart_minutes = int(inp)
        restart_seconds = restart_minutes * 60
    except:
        restart_seconds = 0
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER V5.4: SHIZUKU EDITION ===")
    
    # Cek apakah Rish berfungsi
    check_rish = subprocess.run("rish -c 'echo OK'", shell=True, capture_output=True, text=True).stdout.strip()
    if check_rish != "OK":
        print("\n[FATAL ERROR] 'rish' tidak terdeteksi atau Shizuku belum aktif!")
        print("Pastikan Shizuku berjalan dan rish sudah di-setup di Termux.")
        return

    RESTART_INTERVAL = setup_configuration()
    LAST_GLOBAL_RESTART = time.time()
    
    package_map = {}
    claimed_files = set()

    print("\n[PHASE 1] INITIAL LAUNCH")
    
    server_pools = {} 
    
    for i, pkg in enumerate(BASE_PACKAGES):
        clean_pkg = get_pkg_name(pkg)
        settings = PACKAGE_SETTINGS[pkg]
        pid = settings['place_id']
        vip = settings['vip_code']
        
        print(f"\n--> Meluncurkan: {clean_pkg}")
        
        target_job_id = None
        if not vip or vip.strip() == "":
            if pid not in server_pools:
                server_pools[pid] = get_public_servers(pid)
                random.shuffle(server_pools[pid])
            if len(server_pools[pid]) > 0:
                target_job_id = server_pools[pid].pop(0)
        
        files_state_before = {}
        for f in get_status_files():
            d = read_json_root(f)
            if d and 'timestamp' in d: files_state_before[f] = float(d['timestamp'])
        
        force_close(pkg)
        time.sleep(1)
        launch_game(pkg, job_id=target_job_id) 
        
        print("    Mencari file milik dia...", end="", flush=True)
        detected_info = None

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
    print("[PHASE 2] MONITORING AKTIF")
    print("="*50)

    while True:
        now = time.time()
        
        # === A. RESTART ===
        if RESTART_INTERVAL > 0 and (now - LAST_GLOBAL_RESTART > RESTART_INTERVAL):
            print("\n[ALARM] JADWAL RESTART! MELUNCURKAN ULANG...")
            for pkg in BASE_PACKAGES:
                print(f"   -> Restarting {get_pkg_name(pkg)}...")
                force_close(pkg)
                time.sleep(1)
                launch_game(pkg) 
                if pkg in package_map:
                    package_map[pkg]['last_change_time'] = time.time()
            LAST_GLOBAL_RESTART = time.time()
            print("RESTART SELESAI.\n")
            time.sleep(10)
            continue 

        # === B. ANTI-FREEZE ===
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
                        user_name = info.get('user', 'Unknown')
                        print(f"\n[FREEZE] {user_name} ({clean}) macet {int(stagnant_duration)}s!")
                        
                        inject_restart_status(fpath, data)
                        print("         -> Restarting...")
                        force_close(pkg)
                        time.sleep(2)
                        launch_game(pkg)
                        info['last_change_time'] = now
                        info['last_ts'] = current_file_ts + 1

        # === C. ANTI-TABRAKAN ===
        server_map = {}
        all_files = get_status_files()
        
        for f in all_files:
            d = read_json_root(f)
            if d and 'jobId' in d:
                jid = d['jobId']
                if jid not in server_map: server_map[jid] = []
                server_map[jid].append({'file': f, 'data': d, 'user': d.get('username')})
        
        for jid, sessions in server_map.items():
            if len(sessions) > 1:
                sample_data = sessions[0]['data']
                if sample_data.get('isPrivate', False):
                    continue 
                else:
                    for victim in sessions[1:]:
                        inject_hop_signal(victim['file'], victim['data'])
        
        print(".", end="", flush=True)
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStop.")
