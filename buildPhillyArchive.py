#!/usr/bin/env python
import os, sys
import numpy
import glob
import array
import struct
import wave
from optparse import OptionParser

HTK_HEADER_LENGTH = 12
HTK_HEADER_FORMAT = "<2l2h"

def check_and_create_folder(folder_name):
    if not os.path.isdir(folder_name):
        os.makedirs(folder_name)


def loadHTKParam_numpy(paramfile):
    """read data from one single file"""
    f = open(paramfile, 'rb')
    s = f.read(HTK_HEADER_LENGTH)

    hdr = struct.unpack(HTK_HEADER_FORMAT, s)
    nframes = hdr[0]
    frameshift = hdr[1]
    byte = hdr[2]
    htktype = hdr[3]
    vec_size = (int)(byte/4)
    data = numpy.fromfile(f, '<' + str(nframes*vec_size) + 'f')
    f.close()
    return hdr, data[0]


def get_file_index(file_name):
    file_name = file_name.replace('\\','/')
    idx = file_name.rfind('/')
    name = file_name[idx+1:-4]
    return name


def write_bigger_wave(wave_folder, bigger_wave_file, wavescp_file, sample_rate=16000):
    wave_files = glob.glob(os.path.join(wave_folder, '*.wav')) 
    bigger_wave_file_name = bigger_wave_file.replace('\\', '/')

    # get wave header info from one file
    dummy_file_handler = wave.open(wave_files[0], 'rb')
    nchannels, sampwidth, framerate, totalsamples, comptype, compname = dummy_file_handler.getparams()
    dummy_file_handler.close()

    wave_file = wave.open(bigger_wave_file_name, 'wb')
    wave_file.setparams((nchannels, sampwidth, framerate, totalsamples, comptype, compname))

    totalsamples = 0

    for f in wave_files:
        print("wave / " + f)
        name = get_file_index(f)
        fw = wave.open(f, 'rb')
        nchannels, sampwidth, framerate, nframes, comptype, compname = fw.getparams()
        data = fw.readframes(nframes)
        wave_file.writeframes(data)

        line = name + '=' + bigger_wave_file_name + '[' + str(totalsamples) + ',' + str(totalsamples+nframes-1) + ']\n'
        wavescp_file.write(line)

        totalsamples += nframes

    # wave_file.setparams((nchannels, sampwidth, framerate, totalsamples, comptype, compname))
    wave_file.close()


def write_lin_htk(folder, htk_file, scp_file, ext='hpf'):
    files = glob.glob(os.path.join(folder, '*.' + ext))

    htk_file_name = htk_file.replace('\\', '/')
    htk_file = open(htk_file, 'wb')
    byte = 4
    htktype = 9
    frameshift = 50000
    data = []
    totalframes = 0

    header = struct.pack(HTK_HEADER_FORMAT, totalframes, frameshift, byte, htktype)
    htk_file.write(header)

    for f in files:
        print(ext + " / " + f)
        name = get_file_index(f)
        hdr, data = loadHTKParam_numpy(f)
        nframes, frameshift, byte, htktype = hdr[0], hdr[1], hdr[2], hdr[3]
        line = name + '=' + htk_file_name + '[' + str(totalframes) + ',' + str(totalframes+nframes-1) + ']\n'
        scp_file.write(line)
        totalframes += nframes

        array_data = array.array('f', data)
        array_data.tofile(htk_file)
        del array_data, data

    header = struct.pack('<2l2h', totalframes, frameshift, byte, htktype)
    htk_file.seek(0)
    htk_file.write(header)
    htk_file.close()


def write_pit_htk(folder, htk_file, scp_file, ext='pit'):
    write_lin_htk(folder, htk_file, scp_file, ext)
    
def write_cmp_htk(folder, htk_file, scp_file, ext='cmp'):
    write_lin_htk(folder, htk_file, scp_file, ext)

def process_subdir(rootDir, subDir, wave_htk_file, lin_htk_file, pit_htk_file, wavescp_file, linscp_file, pitscp_file):
    wave_folder = os.path.join(rootDir, "wave/" + subDir)
    lin_folder = os.path.join(rootDir, "lin/" + subDir)
    pit_folder = os.path.join(rootDir, "pit/" + subDir)

    wave_folder = wave_folder.replace('\\', '/')
    lin_folder = lin_folder.replace('\\', '/')
    pit_folder = pit_folder.replace('\\', '/')

    write_wave_htk(wave_folder, wave_htk_file, wavescp_file)
    write_lin_htk(lin_folder, lin_htk_file, linscp_file)
    write_pit_htk(pit_folder, pit_htk_file, pitscp_file)


def process(rootDir, outputDir, outputScpName='scp'):
    # use the sub directory(s) in waveDir as base line to generate HTK file
    waveDir = os.path.join('\\\\stchost-37\\xwang\\FastAdaptation\\enUS\\Eva\\wave_addsil_align')
    linDir = os.path.join('\\\\stchost-39\\xwang\\data\\Hongyu\\NNTraining_7K_Hongyu\\Intermediate\\nnData\\nnSilRemovedLinguistic')
    pitDir = os.path.join('\\\\stchost-39\\xwang\\data\\Hongyu\\chunk\\pit_file')
    cmpDir = os.path.join('\\\\stchost-39\\xwang\\data\\Hongyu\\NNTraining_7K_Hongyu\\Intermediate\\nnData\\silRemovedCmp')

    # save scp file, record each file location in bigger file
    wavescp_file = os.path.join(outputDir, outputScpName + '_wave.scp')
    linscp_file = os.path.join(outputDir, outputScpName + '_lin.scp')
    pitscp_file = os.path.join(outputDir, outputScpName + '_pit.scp')
    cmpscp_file = os.path.join(outputDir, outputScpName + '_cmp.scp')

    wavescp_file = open(wavescp_file, 'w')
    linscp_file = open(linscp_file, 'w')
    pitscp_file = open(pitscp_file, 'w')
    cmpscp_file = open(cmpscp_file, 'w')

    wave_htk_folder = outputDir + '/wave'
    lin_htk_folder = outputDir + '/lin'
    pit_htk_folder = outputDir + '/pit'
    cmp_htk_folder = outputDir + '/cmp'
    check_and_create_folder(wave_htk_folder)
    check_and_create_folder(lin_htk_folder)
    check_and_create_folder(pit_htk_folder)
    check_and_create_folder(cmp_htk_folder)

    # process wave data
    for subdir in os.listdir(waveDir):
        bigger_wave_file = os.path.join(wave_htk_folder, subdir + '.wav')
        #bigger_wave_file.replace('\\','/')
        wave_folder = os.path.join(waveDir, subdir)
        #wave_folder = wave_folder.replace('\\', '/') 
        write_bigger_wave(wave_folder, bigger_wave_file, wavescp_file)

    for subdir in os.listdir(linDir):
        lin_htk_file = os.path.join(lin_htk_folder, subdir + '.hpf')
        #lin_htk_file.replace('\\','/')
        lin_folder = os.path.join(linDir,  subdir)
        #lin_folder = lin_folder.replace('\\', '/')
        #write_lin_htk(lin_folder, lin_htk_file, linscp_file)

    for subdir in os.listdir(pitDir):
        pit_htk_file = os.path.join(pit_htk_folder, subdir + '.pit')
        #pit_htk_file.replace('\\','/')
        pit_folder = os.path.join(pitDir, subdir)
        pit_folder = pit_folder.replace('\\', '/')
        #write_pit_htk(pit_folder, pit_htk_file, pitscp_file)

    for subdir in os.listdir(cmpDir):
        cmp_htk_file = os.path.join(cmp_htk_folder, subdir + '.cmp')
        #cmp_htk_file.replace('\\','/')
        cmp_folder = os.path.join(cmpDir, subdir)
        #cmp_folder = cmp_folder.replace('\\', '/')
        #write_cmp_htk(cmp_folder, cmp_htk_file, cmpscp_file)

    # close file
    wavescp_file.flush()
    linscp_file.flush()
    pitscp_file.flush()
    cmpscp_file.flush()
    wavescp_file.close()
    linscp_file.close()
    pitscp_file.close()
    cmpscp_file.close()

def main():
    usage = "buildPhillyArchive.py rootDir [out]outputDir [out]outputScpName"
    parser = OptionParser(usage=usage)

    options, args = parser.parse_args()
    if len(args) != 3:
        print(usage)
        sys.exit()

    rootDir = args[0]
    outputDir = args[1]
    outputScpName = args[2]
    check_and_create_folder(outputDir)

    process(rootDir, outputDir, outputScpName)


if __name__ == '__main__':
    main()
