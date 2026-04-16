# Copyright (c) 2025-present nebula, Gazelle
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

import json
import os
import secrets
import math
import re
import subprocess
from cryptography.hazmat.primitives.asymmetric import ec
from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey
from modules.curves import Secp192r1, Secp256k1
from modules.dleqag import DLEQAG
from modules.dleq import DLEQ
from modules.tools import load_setup

SETUP_DIR = "../setup.json"
CURRENT_PARTICIPANT_DIR = None

def create_new_participant_dir():
    """Create and return a new participant_N directory for this execution."""
    global CURRENT_PARTICIPANT_DIR
    base = "../outputs/participant"
    os.makedirs(base, exist_ok=True)
    existing = []
    for name in os.listdir(base):
        m = re.match(r'^participant_(\d+)$', name)
        if m:
            existing.append(int(m.group(1)))
    # Use the next numeric suffix to avoid overwriting prior participant runs.
    next_idx = max(existing) + 1 if existing else 0
    participant_dir = os.path.join(base, f"participant_{next_idx}")
    os.makedirs(participant_dir, exist_ok=True)
    os.makedirs(os.path.join(participant_dir, "keys"), exist_ok=True)
    os.makedirs(os.path.join(participant_dir, "proofs"), exist_ok=True)
    CURRENT_PARTICIPANT_DIR = participant_dir
    return participant_dir

def get_latest_participant_dir():
    """Return the latest participant_N directory path and its numeric index."""
    base = "../outputs/participant"
    if not os.path.exists(base):
        raise FileNotFoundError(f"No participant base directory found: {base}")
    existing = []
    for name in os.listdir(base):
        m = re.match(r'^participant_(\d+)$', name)
        if m:
            existing.append(int(m.group(1)))
    if not existing:
        raise FileNotFoundError(f"No participant_* directories found in {base}")
    latest_idx = max(existing)
    return os.path.join(base, f"participant_{latest_idx}"), latest_idx

def seed_bits_calc_keygen(num_participants):
    """Return seed bit length for key generation as floor(log2(n_192) - log2(p))."""
    bits_seed = math.log2(Secp192r1.field.n) - math.log2(num_participants)
    return math.floor(bits_seed)

def seed_bits_calc_proofgen(num_participants):
    """Return seed bit length for proof generation as ceil(log2(p))."""
    bits_seed = math.log2(num_participants)
    return math.ceil(bits_seed)

def seedgen(num_participants):
    """Generate a random seed with the required key-generation bit length."""
    seed = secrets.randbits(seed_bits_calc_keygen(num_participants))
    return seed

def bitcoinkeygen(seed, network):
    """Generate and persist a Bitcoin private key for a new participant directory."""
    setup(network)

    priv = PrivateKey(secret_exponent=seed)
    pub = priv.get_public_key()
   
    keys_dir = os.path.join(create_new_participant_dir(), "keys")
    os.makedirs(keys_dir, exist_ok=True)


    # Extract x-coordinate from public key (uncompressed)
    pub_hex_uncompressed = pub.to_hex(compressed=False)
    pub_x_hex = pub_hex_uncompressed[2:66]
    pub_x_int = int(pub_x_hex, 16)

    priv_path = os.path.join(keys_dir, f"private_key_{pub_x_int}_{network}_DO_NOT_SHARE.txt")
    with open(priv_path, "w") as priv_file:
        priv_file.write(priv.to_wif(compressed=True))


def derive_private_key():
    """Load and return the latest private key as an EC object plus participant index."""
    dir, id = get_latest_participant_dir()
    priv_key_int = load_private_key(os.path.join(dir, "keys"))
    priv_key = ec.derive_private_key(priv_key_int, ec.SECP256K1())
    return priv_key, id

def wif_to_int(wif):
    """Convert a WIF-encoded private key into its integer representation."""
    priv = PrivateKey(wif)
    priv_bytes = priv.to_bytes()
    di = int.from_bytes(priv_bytes, 'big')
    return di

def load_private_key(keys_dir):
    """Load the single private key file in keys_dir and return it as an integer."""
    files = [f for f in os.listdir(keys_dir) if re.match(r'private_key_.*_DO_NOT_SHARE\.txt', f)]
    if not files:
        raise FileNotFoundError(f"No private key file found in {keys_dir}")
    if len(files) > 1:
        raise FileExistsError(f"Multiple private key files found in {keys_dir}. Expected only one.")
    # Enforce a single key file to keep participant state unambiguous.
    priv_key_filename = files[0]
    priv_key_path = os.path.join(keys_dir, priv_key_filename)
    # Recover network from the filename so WIF decoding uses the right prefix rules.
    match = re.search(r'_(mainnet|testnet|regtest)_DO_NOT_SHARE\.txt$', priv_key_filename)
    if not match:
        raise ValueError(f"Network not found in private key filename: {priv_key_filename}")
    network = match.group(1)
    setup(network)
    with open(priv_key_path, "r") as f:
        wif_key = f.read().strip()

    priv_key_int = wif_to_int(wif_key)
    return priv_key_int

def bulletproof_generation(input, number_of_chunks, b_x, over_flow_bits):
    """Generate one Bulletproof per chunk by invoking the Node.js generator."""
    assert b_x > over_flow_bits, "Too many participants."
    script_path = os.path.join(os.path.dirname(__file__), "modules", "bulletproofs", "bulletproof.js")
    path, _ = get_latest_participant_dir()
    proofs_dir = os.path.join("../../"+path, "proofs/")
    proofs = []
    for index in range(number_of_chunks):
        # The final chunk uses fewer bits to account for overflow trimming.
        result = subprocess.run(
        ["node", script_path, "gen", proofs_dir , str( b_x - int(index == number_of_chunks -1) * over_flow_bits), str(input["private_key_chunks"][index]), str(input["random_chunks"][index]), str(index), "1"],  # Pass CLI arguments.
        capture_output=True,
        text=True
        )
        if (result.returncode == 0):
            proofs.append(result.stdout)
        else: 
            print(result.stderr)
            raise ValueError("Couldn't generate bulletproofs")
    return proofs


def generate_private_key(max_number_of_participants):
    """Prompt for a network, generate a private key, and save it to disk."""
    while True:
        net_choice = input("Select network: (m)ainnet, (t)estnet, or regtest(r)?: ").strip().lower()
        if net_choice == "t":
            network = "testnet"
            break
        if net_choice == "m":
            network = "mainnet"
            break
        if net_choice == "r":
            network = "regtest"
            break
        print("Invalid input. Please enter 't' for testnet or 'm' for mainnet.")
    
    print("Generating your private key and saving into .txt files...\n")
    seed = seedgen(max_number_of_participants)
    bitcoinkeygen(seed, network)
    keys_saved_dir = os.path.join(CURRENT_PARTICIPANT_DIR, "keys") if CURRENT_PARTICIPANT_DIR else KEYS_DIR
    print("Private key generated and saved successfully into ", keys_saved_dir)

def main():
    """Run key generation and produce DLEQ and Bulletproof artifacts."""
    print("Welcome to HAGP protocol!\n")
    max_number_of_entities, b_x, b_f, b_c, number_of_chunks  = load_setup(SETUP_DIR)
    generate_private_key(max_number_of_entities) 
    over_flow_bits = seed_bits_calc_proofgen(max_number_of_entities)
    private_key, _ = derive_private_key()
    # Shift by overflow bits to define the range proven by chunked proofs.
    private_key_range = Secp192r1.field.n >> over_flow_bits
    dleqag_inst = DLEQAG(b_x, b_f, b_c, number_of_chunks, private_key_range, Secp256k1, Secp192r1)
    dleqag_proof, bulletproof_input = dleqag_inst.proof_gen(private_key.private_numbers().private_value)
    dleq_secp256k1_inst = DLEQ(Secp256k1)
    dleq_proof_secp256k1 = dleq_secp256k1_inst.proof_gen(dleqag_proof["r_HS"], private_key.private_numbers().private_value)
    dleq_secp192r1_inst = DLEQ(Secp192r1)
    dleq_proof_secp192r1 = dleq_secp192r1_inst.proof_gen(dleqag_proof["r_LS"],  private_key.private_numbers().private_value)
    json_data = {
        "pub_key_256": dleqag_proof["pub_key_HS"],
        "pub_key_192": dleqag_proof["pub_key_LS"],
        "X_256": dleqag_proof["X_HS"],
        "X_192": dleqag_proof["X_LS"],
        "K_256": dleqag_proof["K_HS"],
        "C_256": dleqag_proof["C_HS"],
        "s_256": dleqag_proof["s_HS"], 
        "K_192": dleqag_proof["K_LS"],
        "C_192": dleqag_proof["C_LS"],
        "s_192": dleqag_proof["s_LS"],
        "z": dleqag_proof["z"], 
        "dleq_192": dleq_proof_secp192r1, 
        "dleq_256": dleq_proof_secp256k1
    }
    bulletproof_generation(bulletproof_input, number_of_chunks, b_x, over_flow_bits)
    participant_dir , id = get_latest_participant_dir()
    proofs_dir = os.path.join(participant_dir, "proofs")
    if not os.path.exists(proofs_dir):
        os.makedirs(proofs_dir)
    with open(os.path.join(proofs_dir, f"proof_{private_key.public_key().public_numbers().x }.json"), "w") as proof_file:
        proof_file.write(json.dumps(json_data))
    
    print("Proofs generated and saved successfully into ", proofs_dir)

if __name__ == "__main__":
    main()