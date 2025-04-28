import secrets


def seedgen():
    print("Generating random 256 bits seed")

    #Use secrets to generate random bit sequence
    seed = secrets.randbits(256)

    return seed