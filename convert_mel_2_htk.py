#!/usr/bin/env python

##############################################################
#
# This tool is used convert mel-spectrum directly to htk format
#
##############################################################


import os
import struct
import glob
import numpy as np

mel_folder = r'D:\work\extract_mel_xi\mel_spectrum'
target_folder = r'D:\work\extract_mel_xi\mel_htk'


HTK_HEADER_LENGTH = 12
HTK_HEADER_FORMAT = "<2l2h"


def SaveHTKSpec(data, newfile):
    frames, vecsize = data.shape

    # save as HTK parameter file
    htk_file = open(newfile, 'wb')
    byte = 4 * vecsize
    htktype = 9
    frameshift = 125000
    totalframes = frames

    header = struct.pack(HTK_HEADER_FORMAT, totalframes, frameshift, byte, htktype)
    htk_file.write(header)

    for i in range (0, totalframes):   
        array_data = np.array(data[i], dtype = np.float32)
        array_data.tofile(htk_file)  

    htk_file.close()


def main():
    files = glob.glob(os.path.join(mel_folder, '*.npy'))
    for f in files:
        print(f)
        data = np.load(f)
        frames, vecsize = data.shape

        idx1 = f.rfind('\\')
        idx2 = f.rfind('.')
        file_name = f[idx1+1:idx2] + '.mel'
        file_path = os.path.join(target_folder, file_name)

        SaveHTKSpec(data, file_path)


if __name__== "__main__":
    main()
