#!C:/Python27/python.exe

##############################################################
#
# This tool is used to convert Tacotron predicted mel-spectrum
# to htk format, as Tacotron do not predicted beginning silence
# in this tool will pad begin silence feature and ending 
# silence for WaveNet local condition.
#
##############################################################

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
SIL_THRESHOLD = 0.1
END_FRAMES = 16


def loadSpec(specfile):
	specdata = np.load(specfile)
	(frames, vecsize) = specdata.shape

	return (frames, specdata)
 

def detectPadding(specdata):
	frames, vecsize = specdata.shape

	i = frames - 1
	pad_frames = 0
	summary = np.sum(specdata[i]) 
	while i >= 0 and summary < SIL_THRESHOLD:
		pad_frames += 1 
		summary = np.sum(specdata[i])
		i -= 1
 
	# !!!the ending silence should keep as 0.2s = 16 frames
	 
	return pad_frames
 

def SaveHTKSpec(specdata, adddata, cut_frames, newfile):

    (frames, vecsize) = specdata.shape 

    # save as HTK parameter file
    htk_file = open(newfile, 'wb')
    byte = 4 * vecsize
    htktype = 9
    frameshift = 125000 
    totalframes = len(specdata) + len(adddata) - cut_frames + END_FRAMES

    header = struct.pack(HTK_HEADER_FORMAT, totalframes, frameshift, byte, htktype)
    htk_file.write(header) 
    newdata = np.concatenate((adddata, specdata)) 
    # remove the padding data
    if cut_frames == 0:
        cut_frames = 1
    print('cut end frame:' + str(cut_frames))
    newdata = newdata[:-cut_frames]
    # add fixed ending silence
    taildata = adddata[END_FRAMES:]
    newdata = np.concatenate((newdata, taildata))

    print(len(newdata))
    for i in range (0, totalframes):   
        array_data = np.array(newdata[i], dtype = np.float32)
        array_data.tofile(htk_file)  

    htk_file.close()


def Process(paramDir, sampleSpec, outDir, silframes=48):
    if not os.path.isdir(outDir):
        os.makedirs(outDir)

    # load the sample Mel file to add the silence mel-spectrum feature
    aux = glob.glob(os.path.join(paramDir, "*.predicted.npy"))
    (sframes, sampleData) = loadSpec(sampleSpec)
    if sframes <= silframes:
        print("Wrong sample spec files , not enough silence")

    sil_data = sampleData[:silframes]

    for filename in aux:
        print("Processing " + filename)
        pframes, pred_data = loadSpec(filename)
        basename = os.path.splitext(os.path.basename(filename))[0]
        newfile = os.path.join(outDir, basename+'.mel')
        cut_frames = detectPadding(pred_data)
        SaveHTKSpec(pred_data, sil_data, cut_frames, newfile)


def main(argv=None): 
    usage="MakeMelData.py paramDir sampleSpec outDir"
    parser=OptionParser(usage=usage)
 
    (options,args)=parser.parse_args()

    if len(args)!=3:
        print(usage)
        sys.exit()
     
    paramDir = args[0]
    sampleSpec = args[1] 
    outDir = args[2] 
    Process(paramDir, sampleSpec, outDir)

if __name__== "__main__":
    main()

