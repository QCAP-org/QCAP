import os
from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey

KEYS_DIR = "../../keys/participant"

def bitcoinkeygen(seed):

    # always remember to setup the network
    setup("testnet")

    # create a private key (from our generated bits)
    priv = PrivateKey(secret_exponent=seed)

    # compressed is the default
    print("\nPrivate key WIF:", priv.to_wif(compressed=True))

    # get the public key
    pub = priv.get_public_key()

    taprootpub = pub.get_taproot_address()
    print("\nTaproot address:", taprootpub.to_string())

    # create the directory if it doesn't exist
    os.makedirs(KEYS_DIR, exist_ok=True)

    # compressed is the default
    print("Public key:", pub.to_hex(compressed=True))

    # save public and private keys to files
    pub_path = os.path.join(KEYS_DIR, "public_key_SHARE_THIS_FILE.txt")
    with open(pub_path, "w") as pub_file:
        pub_file.write(pub.to_hex(compressed=True))

    priv_path = os.path.join(KEYS_DIR, "private_key_DO_NOT_SHARE.txt")
    with open(priv_path, "w") as priv_file:
        priv_file.write(priv.to_wif(compressed=True))


