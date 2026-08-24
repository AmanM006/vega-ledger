import os
import json
import secrets
from web3 import Web3
from eth_account import Account

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
LOG_PATH = os.path.join(DATA_DIR, "verifiable_log.json")
# Using Base Sepolia public RPC
RPC_URL = "https://sepolia.base.org"

def get_latest_hash():
    if not os.path.exists(LOG_PATH):
        return None
    with open(LOG_PATH, 'r') as f:
        chain = json.load(f)
    if not chain:
        return None
    return chain[-1].get("hash")

def anchor_hash(root_hash: str):
    print(f"--- VCP Anchor Agent ---")
    print(f"Attempting to anchor hash: {root_hash}")
    print(f"Network: Base Sepolia ({RPC_URL})")

    # Connect to Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("[ERROR] Could not connect to RPC endpoint.")
        return

    # Load or generate private key
    # In a real setup, this comes from an env var. For this demo, we generate a persistent local one
    key_path = os.path.join(DATA_DIR, ".anchor_key")
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            pk = f.read().strip()
    else:
        pk = "0x" + secrets.token_hex(32)
        with open(key_path, 'w') as f:
            f.write(pk)
            
    account = Account.from_key(pk)
    print(f"Anchor Wallet Address: {account.address}")
    
    # Check balance
    balance = w3.eth.get_balance(account.address)
    print(f"Wallet Balance: {w3.from_wei(balance, 'ether')} ETH")
    
    if balance == 0:
        print("\n[HALT] Cannot anchor to blockchain: Insufficient funds for gas.")
        print(f"ACTION REQUIRED: Fund the anchor wallet ({account.address}) with testnet ETH from a Base Sepolia faucet (e.g. https://faucet.quicknode.com/base/sepolia).")
        print("Once funded, re-run this script to successfully anchor the log.")
        return
        
    # Prepare transaction with the hash as a memo (in the data payload)
    nonce = w3.eth.get_transaction_count(account.address)
    # Convert hex hash string to bytes
    memo_bytes = root_hash.encode('utf-8')
    
    tx = {
        'nonce': nonce,
        'to': account.address, # Send to self
        'value': 0,
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
        'data': memo_bytes,
        'chainId': 84532 # Base Sepolia Chain ID
    }
    
    # Estimate gas to be precise
    try:
        gas_estimate = w3.eth.estimate_gas(tx)
        tx['gas'] = gas_estimate
    except Exception as e:
        print(f"Gas estimation failed: {e}")
        
    # Sign and send
    try:
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=pk)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction) # Changed raw_transaction to rawTransaction due to web3py versions, wait, raw_transaction is v6, rawTransaction is v5
        
        # We will use raw_transaction if available, else rawTransaction
        raw_tx = getattr(signed_tx, 'raw_transaction', None) or getattr(signed_tx, 'rawTransaction')
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        
        print(f"\n[SUCCESS] Anchored to Base Sepolia!")
        print(f"Transaction Hash: {tx_hash.hex()}")
        print(f"View on block explorer: https://sepolia.basescan.org/tx/{tx_hash.hex()}")
    except Exception as e:
        print(f"\n[ERROR] Failed to send transaction: {e}")

if __name__ == "__main__":
    latest_hash = get_latest_hash()
    if latest_hash:
        anchor_hash(latest_hash)
    else:
        print("No hash found to anchor.")
