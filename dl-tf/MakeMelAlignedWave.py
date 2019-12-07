#!C:/Python27/python.exe

import os, sys
import glob
import wave
import audioop
import struct
import random

import array

import numpy as np

from optparse import OptionParser

HTK_HEADER_LENGTH = 12
HTK_HEADER_FORMAT = "<2l2h"


def loadSpec(specfile):

	specdata = np.load(specfile)
	(frames, vecsize) = specdata.shape

	return (frames, specdata)

def loadWave(wavefile, specframes, newwave, frameRate=200):

    fw = wave.open(wavefile, 'rb')
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = fw.getparams()
    astr = fw.readframes(nframes)
    fw.close()

    # it assumes the Tacotron extracted Mel-spectrum feature frames large than the waveform length.
    newfeatFrames = int(nframes / frameRate) 
    if (newfeatFrames > specframes):
    	print("Warning: the waveform {} is shorter than the spectrum feature frames {} <-> {}".format(str(wavefile), str(newfeatFrames), str(specframes)))
    	return

    newframes = newfeatFrames * frameRate 
    newastr = astr[:newframes * sampwidth]
    # save to new waveform
    fp = wave.open(newwave,'wb')
    fp.setparams([nchannels, sampwidth, framerate, newframes, comptype, compname])
 
    fp.writeframes(newastr)
    fp.close()

    return newfeatFrames

def SaveHTKSpec(specdata, alignedframes, newfile):

    (frames, vecsize) = specdata.shape
    if (frames < alignedframes): 
        print("Warning: the feature {} is shorter than the desired spectrum feature frames {} <-> {}".format(newfile, str(frames), str(alignedframes)))
    	return 

    # save as HTK parameter file
    htk_file = open(newfile, 'wb')
    byte = 4 * vecsize
    htktype = 9
    frameshift = 125000 
    totalframes = alignedframes

    header = struct.pack(HTK_HEADER_FORMAT, totalframes, frameshift, byte, htktype)
    htk_file.write(header) 
    newdata=specdata[:totalframes]   
    for i in range (0, totalframes):   
        array_data = np.array(newdata[i], dtype = np.float32)
        array_data.tofile(htk_file)  

    htk_file.close()


def loadFileList(fileList):
    f = open(fileList)
    lines = f.readlines()
    f.close()

    fileListMap = {}
    for line in lines:
        seq = line.split()
        (basename, filepath) = seq 
        fileListMap[basename] = filepath
 
    return fileListMap

def Process(inWaveDir, inSpecDir, fileListFile, outWaveDir, outSpecDir):
    if not os.path.isdir(outWaveDir):
        os.makedirs(outWaveDir)
    if not os.path.isdir(outSpecDir):
        os.makedirs(outSpecDir)

    fileListMap = loadFileList(fileListFile)
    fileList = fileListMap.keys()
    fileList.sort()

    for filename in fileList:
        print "Processing "+filename
        wavefile = os.path.join(inWaveDir, fileListMap[filename]+'.wav')
        basename = os.path.splitext(os.path.basename(wavefile))[0]
        specfile = os.path.join(inSpecDir,basename+'.npy')
        (frames, specdata) = loadSpec(specfile)
        newWaveFile = os.path.join(outWaveDir,fileListMap[filename]+'.wav')
        sub = fileListMap[filename].split('\\')[0]
        subdir = os.path.join(outWaveDir, sub)
        if not os.path.isdir(subdir):
            os.makedirs(subdir) 
        newframes = loadWave(wavefile, frames, newWaveFile)

        subSpecdir = os.path.join(outSpecDir, sub)
        if not os.path.isdir(subSpecdir):
            os.makedirs(subSpecdir)

        newSpecFile = os.path.join(outSpecDir, fileListMap[filename]+'.mel')
        SaveHTKSpec(specdata, newframes, newSpecFile)


def main(argv=None): 
    usage="MakeMelAlignedWave.py inWaveDir inSpecDir fileListMap outWaveDir outSpecDir"
    parser=OptionParser(usage=usage)
 
    (options,args)=parser.parse_args()

    if len(args)!=5:
        print usage
        sys.exit()
     
    inWaveDir = args[0]
    inSpecDir = args[1] 
    fileListMap = args[2]
    outWaveDir = args[3] 
    outSpecDir = args[4] 
    Process(inWaveDir, inSpecDir, fileListMap, outWaveDir, outSpecDir)

if __name__== "__main__":
    main()




