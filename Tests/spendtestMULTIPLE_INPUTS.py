from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from bitcoinutils.keys import P2pkhAddress, PrivateKey, P2trAddress


def main():
    # always remember to setup the network
    setup("testnet")

    # the key that corresponds to the P2WPKH address
    priv = PrivateKey("your_private_key_here")

    pub = priv.get_public_key()

    fromAddress = pub.get_taproot_address()
    print(fromAddress.to_string())

    # UTXO of fromAddress
    txid1 = "your_txid_here"
    vout1 = 0
    txid2 = "your_txid_here"
    vout2 = 0
    txid3 = "your_txid_here"
    vout3 = 0
    txid4 = "your_txid_here"
    vout4 = 1
    txid5 = "your_txid_here"
    vout5 = 0


    # all amounts are needed to sign a taproot input     #This is needed because in segwit, the signature also depends on the amount of the input.
    # (depending on sighash)
    first_amount = to_satoshis(0.005)
    second_amount = to_satoshis(0.005)
    third_amount = to_satoshis(0.00749657)
    fourth_amount = to_satoshis(0.0024)
    fifth_amount = to_satoshis(0.005)
    amounts = [first_amount, second_amount, third_amount, fourth_amount, fifth_amount]

    # all scriptPubKeys are needed to sign a taproot input
    # (depending on sighash) but always of the spend input        #When a taproot input is signed, the scriptPubKey of the input is needed to sign it. This is because the signature depends on the scriptPubKey of the input.
    first_script_pubkey = fromAddress.to_script_pub_key()
    second_script_pubkey = fromAddress.to_script_pub_key()
    third_script_pubkey = fromAddress.to_script_pub_key()
    fourth_script_pubkey = fromAddress.to_script_pub_key()
    fifth_script_pubkey = fromAddress.to_script_pub_key()

    # alternatively:
    # first_script_pubkey = Script(['OP_1', pub.to_taproot_hex()])

    utxos_script_pubkeys = [first_script_pubkey, second_script_pubkey, third_script_pubkey, fourth_script_pubkey, fifth_script_pubkey]

    toAddress = P2trAddress("your_destination_address_here")
    #change_txOut = P2trAddress("your_change_address_here")


    # create transaction input from tx id of UTXO
    txin1 = TxInput(txid1, vout1)
    txin2 = TxInput(txid2, vout2)
    txin3 = TxInput(txid3, vout3)
    txin4 = TxInput(txid4, vout4)
    txin5 = TxInput(txid5, vout5)

    # create transaction output
    txOut = TxOutput(to_satoshis(0.0248), toAddress.to_script_pub_key())

    # create transaction without change output - if at least a single input is
    # segwit we need to set has_segwit=True
    tx = Transaction([txin1, txin2, txin3, txin4, txin5], [txOut], has_segwit=True)

    print("\nRaw transaction:\n" + tx.serialize())

    print("\ntxid: " + tx.get_txid())
    print("\ntxwid: " + tx.get_wtxid())

    # sign taproot input
    # to create the digest message to sign in taproot we need to
    # pass all the utxos' scriptPubKeys and their amounts
    #sig = priv.sign_taproot_input(tx, 0, utxos_script_pubkeys, amounts) #The index 0 indicates which input of the tx you are signing. #####sign also utxos_script_pubkeys and amounts
    # print(sig)

    #tx.witnesses.append(TxWitnessInput([sig]))

    #tx.witnesses = []

    for i in range(len(tx.inputs)):             #for each input of the transaction, we sign it individually. Each signature includes all input amounts and all the scriptPubKeys of the inputs (bip341).
        sig = priv.sign_taproot_input(tx, i, utxos_script_pubkeys, amounts)
        tx.witnesses.append(TxWitnessInput([sig]))

    # print raw signed transaction ready to be broadcasted
    print("\nRaw signed transaction:\n" + tx.serialize())

    print("\nTxId:", tx.get_txid())
    print("\nTxwId:", tx.get_wtxid())

    print("\nSize:", tx.get_size())
    print("\nvSize:", tx.get_vsize())


if __name__ == "__main__":
    main()
