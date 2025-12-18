print("🔍 SEDANG MEMERIKSA JANTUNG SCRIPT...")

print("\n1. Cek Keygen...")
try:
    from adb_shell.auth.keygen import keygen
    print("✅ Keygen OK")
except Exception as e:
    print(f"❌ Keygen GAGAL: {e}")

print("\n2. Cek RSA Signer (Cryptography)...")
try:
    from adb_shell.auth.sign_pythonrsa import PythonRSASigner
    print("✅ RSA OK")
except Exception as e:
    print(f"❌ RSA GAGAL: {e}")

print("\n3. Cek TCP Transport...")
try:
    from adb_shell.transport.tcp_transport import TcpTransport
    print("✅ TCP OK")
except Exception as e:
    print(f"❌ TCP GAGAL: {e}")

print("\n🔍 DIAGNOSA SELESAI.")
