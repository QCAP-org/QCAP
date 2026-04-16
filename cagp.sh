#!/bin/bash
# Copyright (c) 2025-present nebula, Gazelle
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://www.opensource.org/licenses/mit-license.php.

set +e
number_of_participants=$(cat setup.json | jq -r ".number_of_participants")
network=$(cat setup.json | jq -r ".network") 

if [ "$network" == "t" ]; then
    echo "The network is set to testnet in the setup.json file"
elif [ "$network" == "m" ]; then
    echo "The network is set to mainnet in the setup.json file"
elif [ "$network" == "r" ]; then
    echo "The network is set to regtest in the setup.json file"
else
    echo "Unknown network in setup.json"
fi

rm -rf outputs/*
rm errors.log stdout.log > /dev/null 2>&1
cd src
echo "Note that this script can't be ran in case the network is chosen to be testnet or mainnet"
echo "Please run the python scripts manually in case you need to select any other network than regtest"

echo 
echo "The output of the running scripts is logged into ./stdout.log"
echo 
for i in $(seq 0 $((number_of_participants -1 ))); do  
    echo "Generating keys for participant number $i"
    echo "$network" | python3 p1_KeyPair_and_ProofGenerator.py >> ../stdout.log 2>>../errors.log
    if [ $? -ne 0 ]; then
        echo 
        echo "Script failed for participant number $i, check the error in ../errors.log"
    fi
done

echo "Moving to the coordinator ..." 

echo "Running the public key aggregator script"
echo "Note that this script verifies the proofs for each participant and only aggregates the ones validated" 

python3 c2_PublicKeyAggregator.py >> ../stdout.log  2>> ../errors.log
if [ $? -ne 0 ]; then
    echo 
    echo "Couldn't aggregated the public keys, check the error in ../errors.log"
    exit
fi
echo "Creating the proof file to be uploaded to the IPFS"
python3 c3_generateIPFSFile.py >> ../stdout.log 2>> ../errors.log
if [ $? -eq 0 ]; then
    echo "The file to be uploaded to the IPFS is generated and can be found in /outputs/"
else   
    echo 
    echo "Failed creating the file, check the error in ../errors.log"
    exit
fi
echo "Creating the commitment transaction"

echo "$network" | python3 c4_HoneypotCommitment.py >> ../stdout.log 2>>../errors.log

if [ $? -eq 0 ]; then
    echo "Successfully created the commitment transaction!"
else
    echo 
    echo "Failed creating the transaction, check the error in ../errors.log"
    exit 1
fi