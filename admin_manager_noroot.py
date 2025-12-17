import subprocess
import time
import sys

# --- KONFIGURASI ---
# Ganti link di bawah ini dengan link Private Server kamu
PRIVATE_SERVER_LINK = "https://www.roblox.com/share?code=6734243a12342943a951f2d972c305a7&type=Server"
PACKAGE_NAME = "com.roblox.client"
CHECK_INTERVAL = 5  # Cek status setiap 5 detik

def is_roblox_running():
    """
    Mengecek apakah proses Roblox sedang berjalan menggunakan pidof.
    Mengembalikan True jika berjalan, False jika tidak.
    """
    try:
        # Menjalankan perintah 'pidof' untuk mencari Process ID aplikasi
        result = subprocess.check_output(["pidof", PACKAGE_NAME])
        return True
    except subprocess.CalledProcessError:
        return False

def launch_roblox():
    """
    Membuka Roblox langsung menuju link Private Server menggunakan Activity Manager (am).
    """
    print(f"[!] Meluncurkan Roblox ke Private Server...")
    try:
        # Command 'am start' dengan action VIEW dan data URL.
        # Kita spesifikasikan package name agar langsung masuk ke app, bukan browser.
        subprocess.run([
            "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", PRIVATE_SERVER_LINK,
            PACKAGE_NAME
        ], check=True)
        print("[✓] Perintah peluncuran dikirim.")
    except Exception as e:
        print(f"[X] Gagal meluncurkan: {e}")

def monitor_loop():
    print("--- MONITORING ANTI-FORCE CLOSE AKTIF ---")
    print(f"Target: {PRIVATE_SERVER_LINK}")
    print("Tekan CTRL+C untuk berhenti.\n")

    first_run = True

    try:
        while True:
            running = is_roblox_running()

            if not running:
                if first_run:
                    print("[!] Memulai sesi pertama...")
                    launch_roblox()
                    first_run = False
                    # Beri waktu ekstra saat pertama kali buka agar tidak looping cepat
                    time.sleep(15) 
                else:
                    print("[!] TERDETEKSI FORCE CLOSE / APP MATI!")
                    print("[!] Mencoba menyuntikkan ulang link...")
                    launch_roblox()
                    # Tunggu agak lama setelah launch agar app sempat loading
                    time.sleep(15)
            else:
                # Update status di satu baris (agar tidak spam terminal)
                sys.stdout.write(f"\r[Status] Roblox berjalan normal... (Cek lagi dalam {CHECK_INTERVAL}d)")
                sys.stdout.flush()
            
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n[!] Monitoring dihentikan oleh pengguna.")

if __name__ == "__main__":
    monitor_loop()
