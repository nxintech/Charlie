# -*- coding:utf-8 -*-

# install on windws
# http://www.voidspace.org.uk/python/modules.shtml#pycrypto
# py3 https://github.com/sfbahr/PyCrypto-Wheels

from Crypto.Cipher import AES

BS = AES.block_size
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[0:-ord(s[-1])]
with open('key', 'rb') as key:
    cipher = AES.new(key.read())


def encode(text):
    encrypted = cipher.encrypt(pad(text)).encode('hex')
    return "{{NxinEncrypted}}{}".format(encrypted)


def decode(encrypted):
    decrypted = unpad(cipher.decrypt(encrypted.decode('hex')))
    print(decrypted)
