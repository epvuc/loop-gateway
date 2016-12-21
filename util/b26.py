#! /usr/bin/python

import sys
import argparse
from bitstring import *

def chop(s, n):
    return [s[i:i+n] for i in range(0, len(s), n)]

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def base_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)

def base_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='base 26 encode/decode')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--encode', dest='encode', action='store_const', const=True, default=False, help='Encode 8 bit to base 26')
    group.add_argument('-d', '--decode', dest='decode', action='store_const', const=True, default=False, help='Decode base 26 to 8 bit')
    args = parser.parse_args()

    s = sys.stdin.read()
    if args.encode:
        input_blocks = chop(s, 17)
        blob = ''
        for ib in input_blocks:
            n = BitArray(bytes=ib)
            c = base_encode(n.uint)
            if (len(c) < 29):
                pad="A"*(29-len(c));
                c=pad+c
            
            blob = blob + c

        if len(blob) % 5 != 0:
            blob = blob + 'A' * (5 - (len(blob) % 5))
            
        blob = " ".join(blob[i:i+5] for i in range(0, len(blob), 5))
        blob = "\n".join(blob[i:i+60] for i in range(0, len(blob), 60))
        groups = len(blob.split())
        print len(s), groups
        print blob

    if args.decode:
        # first line is numeric length
        firstline = s.splitlines()[0]
        (length, groups) = firstline.split()
        length = int(length)
        groups = int(groups)
        # strip off first line
        s = ' '.join(s.splitlines()[1:])
        # concatenate the rest together into a blob with no whitespace
        s = ''.join(s.split())
        # chop it into 29 character blocks
        input_blocks = chop(s, 29)
        blob = ''
        # decode each block as a base-26 number
        for ib in input_blocks:
            # discard trailing partial block which is just group padding
            if len(ib) < 29:
                break
            # convert into string of 17 8-bit bytes
            e = BitArray(uint = base_decode(ib), length = 17*8)
            if length >= 17:
                blob = blob + e.bytes
                length = length - 17

            else: # this is the last block
                lastchunk = e.bytes[(17-length):17]
                blob = blob + lastchunk

        sys.stdout.write(blob)
        
            
        
        
