#!/usr/bin/python3

"""
This file will take a text file as an argument and then convert the encoded powershell saving it to a new file as
decoded.txt. The format works for powershell maldocs which execute a powershell script in the form of
base64 -> character encoded -> raw command
"""

import base64
import re
import sys


# open the file and convert it from base64
def open_file(path):
    print(path)
    file = open(path)
    encstring = file.read()
    decstring = base64.b64decode(encstring)
    return decstring.decode('UTF-16')


# Remove the junk which is normally done with the .join and .split in the ps command
def remove_non_char_numbs(junk):
    junk = (re.sub(r'\D', ',', junk)).strip(',')
    return junk


# Convert the left over character from decimal format to text
def convert_to_ascii(dec):
    ints = [int(s) for s in dec.split(',')]
    converted = " ".join(str(chr(decimal)) for decimal in ints)
    converted = converted.replace(" ", "")
    converted = re.sub(r'http', 'hxxp', converted)
    return converted


def main(argv):
    unbase64 = open_file(argv)
    unjunked = remove_non_char_numbs(unbase64)
    readable = convert_to_ascii(unjunked)
    f = open("decoded.txt", 'a+')
    f.write(readable)
    print("Finished Decoding! Check file: 'decoded.txt'")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Missing argument. Please use in form of: \n"
              "./PowershellDecode.py /path/to/file")
    else:
        main(sys.argv[1])
