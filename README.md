# BHQC
**Bitcoin Honeypot for Quantum Computers**

This project explores the design of a Bitcoin honeypot for Quantum Computers. It simulates a scenario where a quantum computer is able to break elliptic curve cryptography, specifically using Shor’s algorithm, and recovers private keys from weaker elliptic curves.

The implementation uses the following libraries:
- `bitcoinutils` for Bitcoin address and transaction handling
- `cryptography` for elliptic curve operations and encryption
- `secrets` for secure key generation
- `coincurve` for elliptic curve operations


## Code Flow Overview

> **Note:** Always test all individual components using Bitcoin testnet.

### Key Naming Convention
- **Pb / db** refer to public/private keys using the `secp256k1` curve (Bitcoin standard).
- **Pw / dw** refer to public/private keys using the `secp192r1` curve (weakened for quantum feasibility).
- The suffixes `b` and `w` stand for Bitcoin and Weak respectively.

---

## Script Descriptions

### 1. KeyPairGenerator
Each participant independently runs this script.

- A random private key (**db**) is generated using the `secrets` library.
- The corresponding public key (**Pb**) is derived using the `secp256k1` curve.

> Uses `secrets` library to generate a random private key (db) of 256 bits and `bitcoinutils` to generate the corresponding public key (Pb) using the secp256k1 curve.


### 2. PublicKeyAggregator
This script performs collaborative aggregation of public keys.

- All participant public keys (**Pb**) are aggregated into a single public key (**Pba**) using **Schnorr key aggregation**, providing robustness against malicious actors.
- The aggregated key (**Pba**) is hashed with SHA-256 and truncated to 24 bytes. This resulting bytes will be used as x-coordinate to derive a point on the `secp192r1` curve to generate the **Pw** key.
- This process creates a cryptographic **commitment** to the participants’ public keys and ensures no single party knows the honeypot’s private key (**db**).

**Pw** is then distributed to all participants.

> Uses `coincurve` and `bitcoinutils` for key aggregation and format conversion.


### 3. ReducedSecurityKeyCipher
Each participant uses this script to encrypt their private key (**db**) using the received **Pw**.

- Encryption is performed using **ECIES** (Elliptic Curve Integrated Encryption Scheme).
- Each encryption will return:
  - The ciphertext (**C**) which is the encrypted version of the private key (**db**),
  - An initialization vector (**IV**),
  - An ephemeral public key (**Pe**).
- The outputs (**C**, **Pe**, **IV**) are sent to be included in the honeypot commitment, called **E1**, **E2**, ..., **Ex**.

> Uses the `cryptography` library for encryption and secure ephemeral key generation.


### 4. HoneypotCommitment
This script constructs the honeypot's final Taproot address.

- All commitment data (**Pw**, **E1**, **E2**, ..., **Ex**) is encoded into a **Taproot script path**, which is not meant to be executed (always resolves to false) but serves as a verifiable commitment.
- The Taproot address where the honeypot funds will be sent to is created by tweaking the original **Pba** with the hash of the full commitment.
- An **OP_RETURN** is added to the funding transaction of the honeypot with a link to a webpage containing honeypot details and documentation.

> Uses `bitcoinutils` to generate and tweak Taproot addresses and insert OP_RETURN metadata.


### 5. WalletReadyKeyRetriever
This script simulates the quantum attack scenario.

- A quantum computer recovers the private key (**dw**) corresponding to **Pw** by solving the discrete logarithm problem with Shor's algorithm.
- With **dw**, each encrypted private key (**db**) can be decrypted using ECIES.
- Once all **db** keys are obtained, they are aggregated via **Schnorr aggregation** to reconstruct the final private key (**db**) corresponding to **Pba**.
- This **final private key** can be imported into any standard Bitcoin wallet to spend the funds from the honeypot.

> Uses `cryptography` for ECIES decryption and `coincurve`/`bitcoinutils` for aggregation and wallet import formatting.


## Important considerations
There are two main failure points with different consequences:

1· If all participants share dg they can move the funds of the honeypot, meaning that if just one person is honest, the protocol works.

2· If one participant encrypts anything that is not dg, the protocol fails because one dg is missing and the funds cannot be redeemed. This can be solved using ZeroKnowledge Proofs.
plus encourage sending dust there.

