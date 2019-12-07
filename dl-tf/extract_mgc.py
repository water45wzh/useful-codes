#!/usr/bin/env python

import os
import wave
import struct
import array
from multiprocessing import Pool
import scipy.io.wavfile
import numpy as np


wave_foler = r'/home/weso/weso/Evan_MGC/WaveAligned/'
mgc_root_folder = '/home/weso/weso/Evan_MGC/mgc/'
wave_raw_short_folder = '/home/weso/weso/Evan_MGC/WaveRawShort/'
target_wave_folder = r'/home/weso/weso/Evan_MGC/WaveAlignedUlaw/'
filemap = 'fileList.txt'

COMMAND = "x2x +sf < {0} | frame -l 400 -p 80 | window -l 400 -L 512 | mgcep -m 60 -a 0.42 -c 2 -l 512 > {1}"


def write_wav(waveform, sample_rate, filename):
    MAX_VALUE_16BIT = (1 << 15) - 1
    # convert sample range from [-1, 1] to [-32768, 32767]
    waveform = list(map(lambda x: int(x * MAX_VALUE_16BIT), waveform))
    waveout = wave.open(filename, "wb")
    waveout.setparams((1, 2, sample_rate, len(waveform), "NONE", ""))
    raw_ints = struct.pack("<%dh" % len(waveform), *waveform)
    waveout.writeframes(raw_ints)
    waveout.close()
    print('Updated wav file at {}'.format(filename))


def decode(data, quantization_channels=256.0):
    mu = quantization_channels - 1
    signal = 2 * (data / mu) - 1
    magnitude = (1 / mu) * ((1 + mu)**abs(signal) - 1)
    return np.sign(signal) * magnitude


def process(wave_file, target_file, target_raw_short_file, mgc_file, quantization_channels=256.0):
    print(wave_file)
    sr, wavdata = scipy.io.wavfile.read(wave_file)

    if wavdata.dtype != np.int16:
        raise Exception("not supported wave format, not 16Bit wave")

    # write to short file
    short_f = open(target_raw_short_file, 'wb')
    temp = wavdata.astype(np.int16)
    temp.tofile(short_f)
    short_f.close()

    # extract mgc
    command = COMMAND.format(target_raw_short_file, mgc_file)
    retvalue = os.system(command)

    # convert to [-1, 1]
    wavdata = np.array(wavdata, dtype=np.float32) / np.power(2.0, 16 - 1)

    # u-law
    mu = quantization_channels - 1
    wavtrans = np.sign(wavdata) * np.log(1.0 + mu * np.abs(wavdata)) / np.log(1.0 + mu)

    # convert to [0, quantization_channels - 1]
    wavtrans = np.round((wavtrans + 1.0) * mu / 2.0)

    wavdata = wavtrans
    # write data
    format = '<f4'
    datatype = np.dtype((format, 1))
    data = wavdata.astype(datatype)
    f = open(target_file, 'wb')
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
            target_folder = os.path.join(target_wave_folder, sub_folder)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            target_raw_folder = os.path.join(wave_raw_short_folder, sub_folder)
            if not os.path.exists(target_raw_folder):
                os.makedirs(target_raw_folder)

            mgc_target_folder = os.path.join(mgc_root_folder, sub_folder)
            if not os.path.exists(mgc_target_folder):
                os.makedirs(mgc_target_folder)

            target_wave_path = os.path.join(target_folder, arr[0] + '.raw')
            mgc_raw_file_path = os.path.join(mgc_target_folder, arr[0] + '.mgc')
            target_wave_raw_short_path = os.path.join(target_raw_folder, arr[0] + '.short')
            wave_path = os.path.join(wave_foler, arr[1] + '.wav')
            p.apply_async(process, args=(wave_path, target_wave_path, target_wave_raw_short_path, mgc_raw_file_path))

    p.close()
    p.join()

    print("done!")


if __name__ == '__main__':
    main()
