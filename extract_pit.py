#!/usr/bin/env python
import os
import wave
import struct
import array
from multiprocessing import Pool
import scipy.io.wavfile
import numpy as np

target_pit_raw_folder = '/home/weso/weso/Evan_MGC/pit_raw/'
pit_root_folder = '/home/weso/weso/Evan_MGC/pit/'

filemap = 'fileList.txt'


def process(pit_path, target_pit_raw_path):
    print(pit_path)
    f = open(pit_path)
    s = f.read(12)
    hdr = struct.unpack('<2l2h', s)
    nframes, frameshift, byte, htktype = hdr[0], hdr[1], hdr[2], hdr[3]
    vec_size = (int)(byte/4)
    format = '<f4'
    datatype = np.dtype((format, (vec_size,)))
    data = np.fromfile(f, dtype=datatype)
    pit_data = data[:,0]

    # write to raw file
    format = '<f4'
    datatype = np.dtype((format, 1))
    data = pit_data.astype(datatype)
    f = open(target_pit_raw_path, 'wb')
    data.tofile(f)
    f.close()


def main():
    p = Pool(8)

    with open(filemap, 'r') as f:
        for line in f:
            line = line.rstrip()
            if line.find('\\') != -1:
                line = line.replace('\\', '/')

            # check target folder
            arr = line.split(" ")
            sub_folder = arr[1].split('/')[0]  # 0000000001 0000000001-0000000500\0000000001
            target_folder = os.path.join(target_pit_raw_folder, sub_folder)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            pit_path = os.path.join(pit_root_folder, arr[1] + '.pit')
            target_pit_raw_path = os.path.join(target_folder, arr[0] + '.raw')
            p.apply_async(process, args=(pit_path, target_pit_raw_path))

    p.close()
    p.join()

    print("done!")


if __name__ == '__main__':
    main()