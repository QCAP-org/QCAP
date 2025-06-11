from coincurve import PrivateKey
from bitcoinutils.keys import PrivateKey as BitcoinPrivateKey
from bitcoinutils.keys import PublicKey as BitcoinPublicKey

# List of WIF keys
wif_keys = ['WIF']

# Convert WIF to coincurve.PrivateKey
coincurve_privs = []
for wif in wif_keys:
    btc_priv = BitcoinPrivateKey(wif)
    priv_bytes = btc_priv.to_bytes()
    cc_priv = PrivateKey(priv_bytes)
    coincurve_privs.append(cc_priv)

print(coincurve_privs)

# Aggregate the private keys
n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
x_sum = sum(int.from_bytes(priv.secret, 'big') for priv in coincurve_privs) % n
agg_secret = PrivateKey(x_sum.to_bytes(32, 'big'))

print("Aggregated private key (hex):", agg_secret.secret.hex())

# Derive the public key
agg_pubkey = agg_secret.public_key
agg_pubkey_hex = agg_pubkey.format().hex()
agg_pubkey_btc = BitcoinPublicKey.from_hex(agg_pubkey_hex)

print("Aggregated public key (hex):", agg_pubkey_hex)
print("Aggregated public key (bitcoinutils):", agg_pubkey_btc.to_hex())