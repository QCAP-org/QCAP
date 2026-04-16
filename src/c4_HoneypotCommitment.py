# Copyright (c) 2025-present nebula, Gazelle
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

import os
import hashlib
import json
from modules.tools import compute_cid, is_hex
from bitcoinutils.setup import setup
from bitcoinutils.keys import PublicKey
from bitcoinutils.utils import tweak_taproot_pubkey, tagged_hash
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from bitcoinutils.keys import PrivateKey
from bitcoinutils.script import Script


def coords_to_compressed(pub_coords):
    """Convert affine public key coordinates to compressed SEC format."""
    x, y = pub_coords
    x_bytes = x.to_bytes(32, "big")          
    y_odd = y & 1
    prefix = b'\x03' if y_odd else b'\x02'
    comp = prefix + x_bytes
    return comp.hex(), comp


def load_internal_pubkey_hex_from_ipfs():
    """Load the first aggregated secp256k1 public key from IPFS.json as hex."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ipfs_path = os.path.join(base_dir, 'outputs', 'IPFS.json')
    with open(ipfs_path, 'r') as f:
        j = json.load(f)
    # Adjust this path if the JSON schema changes.
    pub_coords = j['dleqag_proofs'][0]['pub_key_256']
    hex_str, _ = coords_to_compressed(pub_coords)
    return hex_str


def compute_sha256_of_ipfs_file():
    """Return raw SHA-256 bytes and hex digest of IPFS.json."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ipfs_path = os.path.join(base_dir, 'outputs', 'IPFS.json')
    with open(ipfs_path, 'rb') as f:
        data = f.read()
    hash = hashlib.sha256(data).digest()
    return hash, hash.hex()


def tweak_public_key(tweak, agg_key_hex):
    """Taproot-tweak an internal public key using the provided commitment bytes."""
    # Load internal public key.
    internal_pubkey = PublicKey(agg_key_hex)
    internal_pubkey_bytes = internal_pubkey.to_bytes()
    
    # Ensure x-only (32 bytes).
    if len(internal_pubkey_bytes) == 33:
        xonly = internal_pubkey_bytes[1:]
    else:
        xonly = internal_pubkey_bytes

    # Derive tweak from internal key and commitment message.
    tap_tweak = tagged_hash(xonly + tweak, "TapTweak")
    tweak_int = int.from_bytes(tap_tweak, 'big')

    # Tweak the internal public key and reconstruct compressed encoding.
    tweaked_pubkey_bytes, is_odd = tweak_taproot_pubkey(internal_pubkey_bytes,tweak_int)
    prefix = b'\x03' if is_odd else b'\x02'
    compressed_key = prefix + tweaked_pubkey_bytes
    tweaked_pubkey_hex = compressed_key.hex()

    # Create tweaked public key and taproot address.
    tweaked_pubkey = PublicKey.from_hex(tweaked_pubkey_hex)
    taproot_address = tweaked_pubkey.get_taproot_address()
    print("Honeypot Address:", taproot_address.to_string())

    return taproot_address


def get_tx_info() -> tuple[PrivateKey, str, int, float, float, any]:
    """Prompt the user for transaction inputs needed to fund the honeypot output."""
    while True:
        response = input("Creating the honeypot funding transaction, " \
                    "please enter your private key WIF: ")
        try:
            priv = PrivateKey(response)
            print("Private key:", priv.to_wif())
            pub = priv.get_public_key()
            break  # Exit loop if successful
        except ValueError as e:
            print(f"Invalid WIF: {e}. Please try again.")


    from_address = pub.get_taproot_address()
    print("From address:", from_address.to_string())

    txid = input("Enter the txid of your UTXO: ").strip()
    if not is_hex(txid):
        raise ValueError("The txid should be in hex format")
    vout = int(input("Enter the vout of your UTXO (as integer): ").strip())
    amount_btc = float(input("Enter the amount of the input UTXO (in BTC): ").strip())
    pay_amount_btc = float(input("Enter the payment output amount (in BTC) "
                        "(!!!REMINDER: the rest will be the fee!!!): ").strip())
    return priv, txid, vout, amount_btc, pay_amount_btc, from_address


def generate_dummy_regtest_data():
    """Generate placeholder UTXO data for local regtest usage."""
    priv = PrivateKey()
    pub = priv.get_public_key()
    from_address = pub.get_taproot_address()

    txid = os.urandom(32).hex()
    vout = 0
    amount_btc = 1.0
    pay_amount_btc = 0.999

    return priv, txid, vout, amount_btc, pay_amount_btc, from_address


def create_op_return_tx(network, taproot_address):
    """Build and sign a transaction funding taproot output plus OP_RETURN."""
    # Initialize the selected Bitcoin network.
    setup(network)
    if network in ("testnet", "mainnet") :
        priv, txid, vout, amount_btc, pay_amount_btc, from_address = get_tx_info()
    else :
        priv, txid, vout, amount_btc, pay_amount_btc, from_address = generate_dummy_regtest_data()

    amounts = [to_satoshis(amount_btc)]
    utxos_script_pubkeys = [from_address.to_script_pub_key()]
    to_address = taproot_address
    txin = TxInput(txid, vout)
    payment_output = TxOutput(to_satoshis(pay_amount_btc), to_address.to_script_pub_key())

    ipfs_cid = compute_cid('../outputs/IPFS.json')
    op_return_script = ["OP_RETURN", ipfs_cid.encode('utf-8').hex()]
    op_return_script = Script(op_return_script)
    op_return_output = TxOutput(0, op_return_script)

    tx = Transaction([txin], [op_return_output, payment_output], has_segwit=True)

    sig = priv.sign_taproot_input(tx, 0, utxos_script_pubkeys, amounts)
    tx.witnesses.append(TxWitnessInput([sig]))

    explorer = ""
    if network == "testnet":
        explorer = "https://mempool.space/testnet4/tx/preview#tx="
    elif network == "mainnet":
        explorer = "https://mempool.space/tx/preview#tx="
    elif network == "regtest":
        explorer = "local network "

    print(f"\nRaw signed transaction ready to preview and broadcast on: {explorer}" + tx.serialize())
    print(f"\nCheck your IPFS upload here: https://ipfs.io/ipfs/" + ipfs_cid)


if __name__ == '__main__':
    # Ask the user to choose the network before creating the transaction.
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

    setup(network)
    agg_key_hex = load_internal_pubkey_hex_from_ipfs()
    digest_bytes, digest_hex = compute_sha256_of_ipfs_file()
    taproot_address = tweak_public_key(digest_bytes, agg_key_hex)
    create_op_return_tx(network, taproot_address)
