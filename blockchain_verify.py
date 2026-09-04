from web3 import Web3
import json
import hashlib


# Connect to local Hardhat blockchain
w3 = Web3(
    Web3.HTTPProvider("http://127.0.0.1:8545")
)

print("Blockchain connected:", w3.is_connected())


# Your deployed contract
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"


# Load contract ABI
with open(
    "artifacts/contracts/FaceVerification.sol/FaceVerification.json",
    "r"
) as f:
    contract_data = json.load(f)


contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=contract_data["abi"]
)


# Local Hardhat account
account = w3.eth.accounts[0]

print("Account:", account)


# Example discovered webpage
matched_url = "https://www.fox5vegas.com/2022/09/08/us-rep-adult-animated-sitcom-with-danny-devito-voice-satan-is-evil/"


# Create fingerprint of the discovered post URL
post_hash = hashlib.sha256(
    matched_url.encode("utf-8")
).hexdigest()

print("Post hash:", post_hash)


# Store hash on blockchain
tx = contract.functions.registerFace(
    post_hash
).transact({
    "from": account
})


receipt = w3.eth.wait_for_transaction_receipt(tx)

tx_hash = receipt["transactionHash"].hex()

print("Transaction:", tx_hash)


# Read the record back from blockchain
record = contract.functions.verifyFace(account).call()

stored_hash = record[0]
verified = record[1]
timestamp = record[2]

print()
print("Stored hash:", stored_hash)
print("Verified:", verified)
print("Timestamp:", timestamp)


# Verify blockchain data
if stored_hash == post_hash and verified:
    print()
    print("✅ BLOCKCHAIN VERIFICATION SUCCESS")
else:
    print()
    print("❌ BLOCKCHAIN VERIFICATION FAILED")