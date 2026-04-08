# CAGP: Canary Address Generation Protocol

This repository implements a distributed protocol to create a Bitcoin canary address that is less secure in comparison to Bitcoin's native address' by design. The canary trap serves as a public alert: if its funds are ever spent, it signals that a quantum computer has broken the ECDLP on `secp192r1` (and is approaching the security of Bitcoin's `secp256k1`) with a very high probability. The protocol is implemented in Python and leverages several cryptographic libraries.

---

## Protocol Overview: CAGP

The Canary Address Generation Protocol (CAGP) is a multi-phase, distributed protocol involving `n` participants and a coordinator. 
-- Add the diagram

### Key Naming Convention

Here we will explain how the naming here in this repo matches the paper. ( do this after cleaning up the repo)

---

## Protocol Phases

### 1. Key Pair and Proof Generation (p1_KeyPairGenerator.py)
- Each participant generates a pair of random Bitcoin private key and derives their corresponding public keys on both `secp192r1` and `secp256k1` curves.
- Outputs are saved in `../outputs/participant/participant_id/keys`.
- Each participant generates the proofs for the DLEQ, DELQAG, and rangeproofs for the generatd keys and stores them in `../outputs/participant/participant_id/proofs`.
### 2. Public Key Aggregation (c2_PublicKeyAggregator.py)
- The coordinator verifies the proofs provided by the participants. 
- The coordinator aggregates the public keys proved valid (from both `secp192r1` and `secp256k1`) via elliptic curve point addition.
### 3. Proof File Generation (c3_generateIPFSFile.py)
- The coordinator generates the file containing all public information of the protocol to be uploaded to the IPFS and saves it as `../outputs/IPFS.json`.
### 4. Honeypot Commitment (c4_HoneypotCommitment.py)
- The coordinators creates the tweaked public key for the taproot address from the aggregated public key on `secp256k1`. 
- It then created the `OP-RETURN` for the funding transaction being the CID of the IPFS file. 
- It initiates the crowdfunding process by publshing the transaction sending some initial funds to the created taproot address from the aggregated public key. 

---

## Implementation Details 

- **Languages/Libraries**: 
  - Python: `bitcoinutils`, `coincurve`, `cryptography`, `tinyec`, `secrets`, `hashlib`
  - Javascript: `secp256k1`, `bulletproof-js`
- **Directory Structure**:
  - `outputs/participant/keys`: Participant key pairs
  - `outputs/participant/ecies_output`: Encrypted keys
  - `outputs/coordinator/key_agg_input`: Public keys for aggregation
  - `outputs/coordinator/key_agg_output`: Aggregation results
  - `outputs/coordinator/honeypot_commitment`: Commitment data
  - `outputs/coordinator/honeypot_address.txt`: Final address
  - `outputs/attacker/bitcoin_core_import.txt`: Wallet descriptor

---

## Instructions

---

## References

- [bitcoinutils](https://github.com/karask/python-bitcoin-utils)
- [coincurve](https://github.com/ofek/coincurve)
- [cryptography](https://cryptography.io/)
- [tinyec](https://github.com/alexmgr/tinyec)
