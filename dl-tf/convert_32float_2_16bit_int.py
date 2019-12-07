#!/usr/bin/env python
import os
import struct
import wave
import soundfile
from multiprocessing import Pool


wave_32float_root_folder = r'D:\data\StewardWills\splited\wave'
target_save_folder = r'D:\data\StewardWills\splited\wave_16bit_integer'

MAX_VALUE_16BIT = (1 << 15) - 1

def write_wav(waveform, sample_rate, filename):
    # convert sample range from [-1, 1] to [-32768, 32767]
    waveform = list(map(lambda x: int(x * MAX_VALUE_16BIT), waveform))
    waveout = wave.open(filename, "wb")
    waveout.setparams((1, 2, sample_rate, len(waveform), "NONE", ""))
    raw_ints = struct.pack("<%dh" % len(waveform), *waveform)
    waveout.writeframes(raw_ints)
    waveout.close()


def convert_2_16bit(file_path, target_path):
    try:
        print(target_path)
        audio, sr = soundfile.read(file_path)
        assert sr == 16000
        write_wav(audio, sr, target_path)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    p = Pool(8)

    for root, dirs, files in os.walk(wave_32float_root_folder):
        for file in files:
            file_path = os.path.join(root, file)
            file_name = file[:-4]

            target_path = os.path.join(target_save_folder, file_name + '.wav')
            p.apply_async(convert_2_16bit, args=(file_path, target_path))

    p.close()
    p.join()

    print("done!")
