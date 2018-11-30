import base64
from Crypto import Random
from Crypto.Cipher import AES

# install Cryptodome instead of pycrypto

BS = AES.block_size


def pad(s: str) -> str:
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)


def unpad(s: bytes) -> bytes:
    return s[0:-s[-1]]


def read(file):
    with open(file, 'rb') as f:
        return f.read()


def encrypt(string: str) -> str:
    byte = pad(string).encode()
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(read('key'), AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(byte)).decode()


def decrypt(encrypted: str) -> str:
    enc = base64.b64decode(encrypted)
    iv = enc[:16]
    cipher = AES.new(read('key'), AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc[16:])).decode()
