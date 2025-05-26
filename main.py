from seedgen import seedgen
from bitcoinkeygen import bitcoinkeygen

# $$$$$$$\  $$\   $$\  $$$$$$\   $$$$$$\
# $$  __$$\ $$ |  $$ |$$  __$$\ $$  __$$\
# $$ |  $$ |$$ |  $$ |$$ /  $$ |$$ /  \__|
# $$$$$$$\ |$$$$$$$$ |$$ |  $$ |$$ |
# $$  __$$\ $$  __$$ |$$ |  $$ |$$ |
# $$ |  $$ |$$ |  $$ |$$ $$\$$ |$$ |  $$\
# $$$$$$$  |$$ |  $$ |\$$$$$$ / \$$$$$$  |
# \_______/ \__|  \__| \___$$$\  \______/
#                          \___|


ascii_art = r'''
$$$$$$$\  $$\   $$\  $$$$$$\   $$$$$$\  
$$  __$$\ $$ |  $$ |$$  __$$\ $$  __$$\ 
$$ |  $$ |$$ |  $$ |$$ /  $$ |$$ /  \__|
$$$$$$$\ |$$$$$$$$ |$$ |  $$ |$$ |      
$$  __$$\ $$  __$$ |$$ |  $$ |$$ |      
$$ |  $$ |$$ |  $$ |$$ $$\$$ |$$ |  $$\ 
$$$$$$$  |$$ |  $$ |\$$$$$$ / \$$$$$$  |
\_______/ \__|  \__| \___$$$\  \______/ 
                         \___|          

'''
print(ascii_art)


def main():
    print("Welcome to BHQC protocol")

    #Generation of seed
    seed = seedgen()
    print(f"Your seed: {seed}")

    #Generation of Bitcoin private key (dg)
    bitcoinkeygen(seed)







if __name__ == "__main__":
    main()