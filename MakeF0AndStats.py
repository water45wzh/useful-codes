
import os, sys
import glob
import struct
import array
import math
import argparse
import numpy as np
from optparse import OptionParser


predict_pitch = r"./predict_pitch.pl"
STDFLOOR = 1e-9
HTK_HEADER_LENGTH = 12
HTK_HEADER_FORMAT = "2l2h"
HTK_HEADER_FORMAT_S = ">2l2h"


def loadcmp(cmpfile):
    '''Load cmp feature files in frames'''
    with open(cmpfile, "rb") as f:
        s = f.read(HTK_HEADER_LENGTH)
        hdr = struct.unpack(HTK_HEADER_FORMAT, s)
        (nframes, frameshift, byte, htktype) = hdr
        vec_size = (int)(byte / 4)
        data = np.fromfile(f, '<' + str(nframes * vec_size) + 'f')
        cmpdata = data.reshape(nframes, vec_size)
        return cmpdata


def loadcmp_s(cmpfile):
    '''Load cmp feature files in frames'''
    with open(cmpfile, "rb") as f:
        s = f.read(HTK_HEADER_LENGTH)

        hdr = struct.unpack(HTK_HEADER_FORMAT_S, s)
        (nframes, frameshift, byte, htktype) = hdr
        vec_size = (int)(byte / 4)
        data = np.fromfile(f, '>' + str(nframes * vec_size) + 'f')
        cmpdata = data.reshape(nframes, vec_size)
        return cmpdata


def extractF0(cmpdata):
    ''' It is supposed that the last 4 data is logF0, delta lf0, delta-delta, uv'''
    
    (nframes, vec_size) = np.shape(cmpdata)

    lf0list = np.array([], dtype=float)
    uvlist = np.array([], dtype=float)
    for vector in cmpdata:
        [lf0, delta, detla2, uv] = vector[-4:]
        lf0list = np.append(lf0list, [lf0])
        uvlist = np.append(uvlist, [uv])

    return (lf0list, uvlist)


def extractUV(f0file):
    pitch = loadF0(f0file)

    uvlist = np.array([], dtype=float)
    for p in pitch:
        if p == 0:
            uvlist = np.append(uvlist, [1.0])
        else:
            uvlist = np.append(uvlist, [0.0])

    return uvlist


def loadF0(f0file):
    """ load f0 file  
    """
    pitch = []
    with open(f0file) as f:
        for line in f:
            f0 = float(line.strip())
            pitch.append(f0)

    return pitch


def meanVarNormalization(data, mean, std):
    # s = numpy.array(data, dtype='float')
    data = (data - mean) / std
    return data


def saveCmp(lf0data, uvdata, pitchfile):
    assert len(lf0data) == len(uvdata)
    nframes = len(lf0data)
    # (nframes, vec_size) = np.shape(lf0data)
    byte = 4 * 2
    htktype = 9
    frameshift = 50000
    hdr = struct.pack(HTK_HEADER_FORMAT, nframes, frameshift, byte, htktype)
    fp = open(pitchfile, 'wb')
    fp.write(hdr)
    data = np.column_stack((lf0data, uvdata))
    sdata = np.reshape(data, [-1])
     
    s = array.array('f', sdata)
    s.tofile(fp)
    fp.close()


def loadFileList(fileList):
    lines = []
    with open(fileList) as f:
        lines = f.readlines()

    fileListMap = {}
    for line in lines:
        seq = line.split()
        (basename, filepath) = seq
        fileListMap[basename] = filepath

    return fileListMap


def loadStats(statsFile):
    with open(statsFile) as f:
        lines = f.readlines()
        lf0mean, lf0std = (float)(lines[0]), (float)(lines[1])

    return (lf0mean, lf0std)


def f02lf0(f0):
    """Convert lf0 to f0
    """
    return np.log(f0)


def Process(inCmpDir, fileListFile, outF0Dir, statsFile, pitch_tool, gen_test=False, gen_pitch=False):
    if not os.path.isdir(outF0Dir):
        os.makedirs(outF0Dir)

    fileListMap = loadFileList(fileListFile)
    fileList = fileListMap.keys()

    pitchDic = {}
    lf0sum, lf0sqr, lf0mean, lf0std = 0.0, 0.0, 0.0, 1.0
 
    count = 0
    if not gen_test and not gen_pitch:
        for filename in fileList:
            print("Processing " + filename)
            cmpfile = os.path.join(inCmpDir, fileListMap[filename] + '.cmp')
            cmpdata = loadcmp(cmpfile)
            (lf0data, uvdata) = extractF0(cmpdata)
            pitchDic[filename] = (lf0data, uvdata)

            lf0sum += sum(lf0data)
            lf0sqr += sum(np.multiply(lf0data, lf0data))
            count += len(lf0data)

        lf0mean = lf0sum / count
        lf0std = np.sqrt((lf0sqr - count * lf0mean * lf0mean) / (count - 1))
        if lf0std < STDFLOOR:
            print("lf0 std {} is too small, floor to {}".format(str(lf0std), str(STDFLOOR)))
            lf0std = STDFLOOR

        # save f0 stats
        f = open(statsFile, "w")
        f.write(format(str(lf0mean) + '\n'))
        f.write(format(str(lf0std) + '\n'))
        f.close()
    else:
        (lf0mean, lf0std) = loadStats(statsFile)
        print(lf0mean)
        print(lf0std)

    for filename in fileList:
        # sub = fileListMap[filename].split('\\')[0]
        # subdir = os.path.join(outF0Dir, sub)
        # if not os.path.isdir(subdir):
        #     os.makedirs(subdir)

        lf0data, uvdata = None, None
        if gen_test:
            print("Processing " + filename)
            cmpfile = os.path.join(inCmpDir, fileListMap[filename] + '.cmp')
            cmpdata = loadcmp(cmpfile)
            (lf0data, uvdata) = extractF0(cmpdata)
        elif gen_pitch:
            print("Processing " + filename)
            f0file = os.path.join(inCmpDir, fileListMap[filename] + '.lf0.heq.f0')
            uvdata = extractUV(f0file)
            sf0file = os.path.join(inCmpDir, fileListMap[filename] + '.sf0')
            cmd = "perl " + pitch_tool + " " + f0file + " " + sf0file
            os.system(cmd)
            smoothf0 = loadF0(sf0file)
            lf0data = f02lf0(smoothf0)
        else:
            (lf0data, uvdata) = pitchDic[filename]

        lf0data = meanVarNormalization(lf0data, lf0mean, lf0std)
        pitchfile = os.path.join(outF0Dir, fileListMap[filename] + '.pit')
        saveCmp(lf0data, uvdata, pitchfile)


def get_arguments():
    parser = argparse.ArgumentParser(description='Mean Loss Tool')
    parser.add_argument('--inCmpDir', type=str, default=None, required=True,
                        help='input dir of cmp files')
    parser.add_argument('--fileListMap', type=str, default=None, required=True,
                        help='fileListMap')
    parser.add_argument('--outF0Dir', type=str, default=None, required=True,
                        help='output dir of f0 files')
    parser.add_argument('--statsFile', type=str, default=None, required=True,
                        help='statsFile')
    parser.add_argument('--pitch_tool', type=str, default=predict_pitch,
                        help='ipitch tool to normalize the pitch features')
    parser.add_argument('-t', type=bool, default=False,
                        help='set the test data generation')
    parser.add_argument('-f', type=bool, default=False,
                        help='calcuate the pitch from f0, interpolate and then log with normalization')

    return parser.parse_args()


def normalize_f0(inCmpDir, fileListMap, outF0Dir, statsFile, pitch_tool=predict_pitch, gen_test=False, gen_pitch=False):
    Process(inCmpDir, fileListMap, outF0Dir, statsFile, pitch_tool, gen_test, gen_pitch)


def main():
    args = get_arguments()
    inCmpDir, fileListMap, outF0Dir, statsFile = args.inCmpDir, args.fileListMap, args.outF0Dir, args.statsFile
    Process(inCmpDir, fileListMap, outF0Dir, statsFile, args.pitch_tool, args.t, args.f)


if __name__ == "__main__":
    main()
