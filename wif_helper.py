import binascii, hashlib, base58

# alias method
decode_hex = binascii.unhexlify

# wallet import format key - base58 encoded format
def gen_wif_key(private_key):
    # prepended mainnet version byte to private key
    mainnet_private_key = '80' + private_key

    # perform SHA-256 hash on the mainnet_private_key
    sha256 = hashlib.sha256()
    sha256.update( decode_hex(mainnet_private_key) )
    hash = sha256.hexdigest()

    # perform SHA-256 on the previous SHA-256 hash
    sha256 = hashlib.sha256()
    sha256.update( decode_hex(hash) )
    hash = sha256.hexdigest()

    # create a checksum using the first 4 bytes of the previous SHA-256 hash
    # append the 4 checksum bytes to the mainnet_private_key
    checksum = hash[:8]
    hash = mainnet_private_key + checksum

    # convert mainnet_private_key + checksum into base58 encoded string
    return base58.b58encode( decode_hex(hash) )