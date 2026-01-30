from random import choice, choices, shuffle
from time import time
from typing import List, Union
import string


def generateOID(count:int=1) -> Union[str, List[str]]:
    syntax1 = [
        '1ngg01pp', '1ngg00p9', '03000000', '1ngg01a0', '1ngg0140',
        '000g00p9', '04136psg', '00000300', '038g01ah', '000g0136',
        '1ngg013h', '1ngg019n', '1ngg01ah', '000g019n'
    ]
    syntax2 = ['1og7', '1mo7', '1o07', '1ng7', '1o87', '1no7', '1n87', '1n07', '1mg7']

    oids = []
    for n in range(count):
        charset = string.ascii_lowercase + string.digits # 'abcdefghijklmnopqrstuvwxyz0123456789'
        timestamp = str(int(time() * 1000000))
        randomkey = list(timestamp[-8:]) + choices(charset, k=5)
        shuffle(randomkey)
        oids.append(f'_040g{choice(syntax1)}{choice(syntax2)}{"".join(randomkey)}')
    if len(oids) == 1:
        return oids[0]
    return oids


if __name__ == "__main__":
    for oid in generateOID(100):
        print(oid)
