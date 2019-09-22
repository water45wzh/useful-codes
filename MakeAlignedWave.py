#!C:/Python27/python.exe

import os, sys
import glob
import wave
import audioop
import struct
import random
import numpy
import array

from xml.etree.ElementTree import ElementTree
from multiprocessing import Pool
from optparse import OptionParser

def loadNNSchema(schemafile):
    tree=ElementTree()
    tree.parse(schemafile)
    root=tree.getroot()

    nnlingnum = len(root)
    NNSchema = root  
    silpos = 0
    for child in root:
        tag = child.tag
        attrib = child.attrib
        idx = attrib['ID']
        name = attrib['name']
        mean = float(attrib['Mean'])
        invStd = float(attrib['InvStdDev'])
        if name == "Phone.PhoneIdentity": 
            for subchild in child:
                subtag = subchild.tag
                subattrib = subchild.attrib
                subname = subattrib['name']
                if subname in ("SIL", "Sil", "sil"):
                    silpos = idx

    return NNSchema, silpos


def loadLabel(labelfile, statenum=5, frameRate=50000):
    '''Load alignment label and get start and end silence frames '''
    f = open(labelfile)
    lines = f.readlines()
    f.close()

    if len(lines) <= statenum:
        print "Warning: malformed label "+labelfile
        return None
    
    # Find the last state for starting silence frames index (in ns)
    (s, startIdx, label1) = lines[statenum - 1].split()
    # Find the first state for ending silence frame index (in ns)
    (endIdx, e, label2) = lines[len(lines) - statenum].split()[:3]
    # Find the last state for ending silence 
    (endSIdx, se, label3) = lines[len(lines) - 1].split()

    start=int(startIdx) / frameRate
    end=(int(se)-int(endIdx)) / frameRate
    speechlen=(int(endIdx) - int(startIdx)) / frameRate 
    return (start, speechlen, end)
        
def loadLinguistic(linfile, silpos=0):
    '''Load linguistic feature and find the silence frames'''
    f = open(linfile,'rb')
    s = f.read(12)

    hdr = struct.unpack('<2l2h', s)
    (nframes, frameshift, byte, htktype) = hdr
    vec_size = (int)(byte / 4)
    data = numpy.fromfile(f, '<' + str(nframes * vec_size) + 'f') 
    f.close()
    linData = data.reshape(nframes, vec_size)
    silpos = int(silpos)
    # find the start silence
    i=0
    while linData[i][silpos]==1.0:
        i = i+1 
    start = i

    # find the end silence
    j = nframes-1
    while linData[j][silpos] == 1.0:
        j = j-1
    end = nframes-j-1

    speechlen = nframes - start - end
    
    return (start, speechlen, end) 

def loadWave(wavefile, newwave, aligned, matched, frameRate=80):
        
    fw = wave.open(wavefile, 'rb')
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = fw.getparams()
    astr = fw.readframes(nframes)
    fw.close()

    if (aligned[0] < matched[0]) or (aligned[1] < matched[1]):
        print "Error: aligned start or end silence frames is less than linguistic feature" + wavefile
        print aligned
        print matched
        return None 

    # sampData=struct.unpack("%ih" % (nframes * nchannels), astr) 
    
    # Delete some start and end silence samples
    sStartIdx = (aligned[0] - matched[0]) * frameRate * sampwidth
    sEndIdx = aligned[0]*frameRate * sampwidth
    speechStartIdx = aligned[0] * frameRate * sampwidth
    speechEndIdx = (aligned[0]+aligned[1]) * frameRate * sampwidth
    eStartIdx = (aligned[0]+aligned[1]) * frameRate * sampwidth
    eEndIdx = (aligned[0]+aligned[1]+matched[2]) * frameRate * sampwidth
  
    # Pick the speech as exactly the same length as linguistic features,
    # and keep the same silence length around speech.
    startData = astr[sStartIdx : sEndIdx] 
    speechData = astr[speechStartIdx : speechEndIdx]
    endData = astr[eStartIdx : eEndIdx]

    newastr = startData + speechData + endData
    newframes = sum(matched * frameRate)
    
    # save to new waveform
    fp = wave.open(newwave,'wb')
    fp.setparams([nchannels, sampwidth, framerate, newframes, comptype, compname])
 
    fp.writeframes(newastr)
    fp.close()

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

def Process(inWaveDir, inLabelDir, inLinDir, fileListFile, nnschemaFile, outWaveDir):
    if not os.path.isdir(outWaveDir):
        os.makedirs(outWaveDir)


    NNSchema, silpos = loadNNSchema(nnschemaFile)
    fileListMap = loadFileList(fileListFile)
    fileList = fileListMap.keys()
    fileList.sort()
    for filename in fileList:
        print "Processing "+filename
        wavefile = os.path.join(inWaveDir, fileListMap[filename]+'.wav')
        basename = os.path.splitext(os.path.basename(wavefile))[0]
        labfile = os.path.join(inLabelDir,basename+'.lab')
        linfile = os.path.join(inLinDir, fileListMap[filename]+'.hpf')
        newwavefn = os.path.join(outWaveDir,fileListMap[filename]+'.wav')
        aligned = loadLabel(labfile)
        matched = loadLinguistic(linfile, silpos)
        sub = fileListMap[filename].split('\\')[0]
        subdir = os.path.join(outWaveDir, sub)
        if not os.path.isdir(subdir):
            os.makedirs(subdir)
        
        loadWave(wavefile, newwavefn, aligned, matched)
  
   
def main(argv=None): 
    usage="MakeAlignedWave.py inWaveDir inLabelDir inLinDir fileListMap nnschemaFile outWaveDir"
    parser=OptionParser(usage=usage)
 
    (options,args)=parser.parse_args()

    if len(args)!=6:
        print usage
        sys.exit()
     
    inWaveDir = args[0]
    inLabelDir = args[1]
    inLinDir = args[2]
    fileListMap = args[3]
    nnschemaFile = args[4]
    outWaveDir = args[5] 
    Process(inWaveDir, inLabelDir, inLinDir, fileListMap, nnschemaFile, outWaveDir)

if __name__== "__main__":
    main()
    
    
    
