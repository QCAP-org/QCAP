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


## Limitations and Future Improvements

While this protocol demonstrates a novel approach to creating a Bitcoin honeypot for Quantum Computers, there are several limitations and areas for future improvement.

### Protocol Integrity and Verification

One of the strengths of the protocol is that key aggregation increases the honeypot’s security: the more participants involved, the more resistant it becomes. In fact, as long as at least one participant is fully honest, any transaction spending the honeypot’s funds would imply that a quantum computer has been used.

However, the protocol has a critical single point of failure. Any dishonest or careless participant can encrypt arbitrary data using the `ReducedSecurityKeyCipher` script instead of their actual private key (`db`). This would make the honeypot permanently inaccessible—or at least inaccessible using the intended reconstruction process—thereby breaking its intended guarantees.

**Future improvement**: Integrate zero-knowledge proofs to verify that each encrypted value is indeed the correct `db`, without revealing it. This would ensure that only valid data is accepted without compromising private information.

### Decentralization and Coordination

Currently, the protocol assumes cooperation between participants through external means. The key aggregation and address generation steps are not fully trustless and involve some centralization.

**Future improvement**: Develop or integrate a decentralized coordination system that allows participants to securely exchange information and collaboratively generate the honeypot without relying on any centralized authority or external coordination channels.

### Data Hosting

At present, honeypot data and documentation are published on a centralized webpage (e.g., GitHub Pages), with the link included in an `OP_RETURN` output of the funding transaction. This creates dependency on a third-party hosting provider.

**Future improvement**: Use decentralized storage systems such as IPFS or Zeronet to publish and store this data. Alternatively, although technically complex, an on-chain solution could be explored to ensure full permanence and censorship resistance.

### Mainnet Deployment

Once these issues are addressed, the protocol could be deployed on Bitcoin mainnet as a real honeypot. It could then be proposed to the community as a public dust donation address or as a long-term quantum security experiment.

---

This project serves as a proof-of-concept, and opens up new possibilities for exploring quantum-aware Bitcoin constructs. Contributions and suggestions for improvement are welcome.
