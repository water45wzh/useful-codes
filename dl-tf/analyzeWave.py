#!\usr\bin\env python
# -*- encoding: utf-8 -*-

"""
File name should be same for record and generated wave
0000000001.wav  training\0000000001.wav
0000000002.wav  training\0000000002.wav
0000000003.wav  training\0000000003.wav
0000000004.wav  training\0000000004.wav
0000000005.wav  training\0000000005.wav
0000000006.wav  training\0000000006.wav
"""

import os, sys
import argparse
import array
import math
import struct
from dtwclass import Dtw

LZERO = float(-10000000000.000)
LSP_order = 40
sampleRate      = 16000
lowFrequency    = 300
highFrequency   = 4000
FFTDim          = 1024

MODES = ('training', 'frontend')
DEFAULT_MODE = 'training'

Get_F0_tool = r'Extern\HTS\get_f0.exe'
Get_F0_conf = r'Extern\HTS\get_f0.conf'

LSP_tool = r'Extern\HTS\STRAIGHT_All.exe'

Evaluate_RMSE = r'Evaluation_RMSE.exe'
QualityMeasure_tool = r'ObjectiveMeasure\QualityMeasure.exe'

ConsistencyMeasure_tool = r'ObjectiveMeasure\ConsistencyMeasure.exe'


def get_arguments():
    parser = argparse.ArgumentParser(description='Mean Loss Tool')
    parser.add_argument('--generated_wave_dir', type=str, default=None, required=True,
                        help='generated waves directory')
    parser.add_argument('--record_wave_dir', type=str, default=None, required=True,
                        help='recorded wave directory')
    parser.add_argument('--tool_dir', type=str, default=None, required=True,
                        help='offline tools directory.')
    parser.add_argument('--filemap', type=str, default=None, required=True,
                        help='file map input')
    parser.add_argument('--mode', type=str, default=DEFAULT_MODE,
                        help='all, training, testing, frontend')

    return parser.parse_args()


def log_command(command):
    print("RUN COMMAND ====> %s" % command)

def compute_f0(wave_file, offline_tool_dir, output_f0):
    f0_tool = os.path.join(offline_tool_dir, Get_F0_tool)
    f0_conf = os.path.join(offline_tool_dir, Get_F0_conf)

    f0_command = '%s -C %s -r 0.005 -n 50 -x 500 -g 1 %s %s' % (f0_tool, f0_conf, wave_file, output_f0)
    log_command(f0_command)
    retvalue = os.system(f0_command)
    return retvalue


def compute_lsp(wave_file, f0_file, offline_tool_dir, output_lsp, output_f0):
    lsp_tool = os.path.join(offline_tool_dir, LSP_tool)
    lsp_command = '%s %s %s %s %s 0 1024 %i 0.005 0.005' % (lsp_tool, wave_file, f0_file, output_lsp, output_f0, LSP_order)
    log_command(lsp_command)
    retvalue = os.system(lsp_command)
    return retvalue


def compute_RMSE_4_f0(lf0RefFile, lf0SynFile, offline_tool_dir, output_file):
    rmse_tool = os.path.join(offline_tool_dir, Evaluate_RMSE)
    rmse_f0_command = '%s -F0 -B %s -B %s > %s' % (rmse_tool, lf0RefFile, lf0SynFile, output_file)
    log_command(rmse_f0_command)
    retvalue = os.system(rmse_f0_command)
    return retvalue
 
def compute_RMSE_4_lsd(lspRefFile, lspSynFile, refF0File, offline_tool_dir, output_file):
    rmse_tool = os.path.join(offline_tool_dir, Evaluate_RMSE) 
    rmse_lsp_command = '%s -LogSpe %s %s %s %i %i %i %i %i %i  > %s' % (rmse_tool, lspRefFile, refF0File, lspSynFile, 
                        LSP_order, LSP_order, FFTDim, sampleRate, lowFrequency, highFrequency, output_file)
    log_command(rmse_lsp_command)
    retvalue = os.system(rmse_lsp_command)
    return retvalue


def compute_wave_f0_and_lsp(wave_file, data_path, offline_tool_dir):
    idx = wave_file.rfind('\\')
    idx2 = wave_file.rfind('.')
    filename = wave_file[idx+1:idx2]

    feature_path = os.path.join(data_path, 'feature')
    check_folder(feature_path)

    # compute F0 of record wave
    f0_file = os.path.join(feature_path, filename + '.f0')
    ret = compute_f0(wave_file, offline_tool_dir, f0_file)
    if ret != 0:
        sys.exit()

    # compute LSP of record wave
    lsp_file = os.path.join(feature_path, filename + '.lsp')
    f0_ofolder = os.path.join(data_path, 'of0')
    check_folder(f0_ofolder)
    f0_ofile = os.path.join(f0_ofolder, filename + '.f0')
    ret = compute_lsp(wave_file, f0_file, offline_tool_dir, lsp_file, f0_ofile)
    if ret != 0:
        sys.exit()

    return f0_file, lsp_file


def check_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def compute_wave_distortion(record_wave, generated_wave, offline_tool_dir, output_file):
    wave_distrotion_tool = os.path.join(offline_tool_dir, QualityMeasure_tool)
    wave_distrotion_command = '%s -r %s -s %s -od %s -a on' % (wave_distrotion_tool, record_wave, generated_wave, output_file)
    log_command(wave_distrotion_command)
    retvalue = os.system(wave_distrotion_command)
    return retvalue

def load_param(filename):
    data=[]
    f=open(filename)
    lines=f.readlines()
    f.close()

    #(vec_size, framenum) = map(int, list(lines[0].split())) 
    framenum = len(lines)
    for i in range(0, framenum):
        featline = map(float, list(lines[i].split()))
        data += [(featline[:])]
    return data

def load_bin_param(filename, vecsize):

    pdata = array.array('f')
    n = int(os.stat(filename).st_size) / 4
    f = open(filename, 'rb')
    pdata.fromfile(f, n)
    f.close()
    nframes = int(n / vecsize)
    
    feature = [] 
    for i in range(0,nframes):        
        feature += [(pdata[i * vecsize : (i + 1) * vecsize])]
    
    return feature

def dtw_align(ref, test, vecsize):
    ''' DTW align to make the reference lsp and test to match in same length
    '''
    ref_lsp = load_bin_param(ref, vecsize)
    test_lsp = load_bin_param(test, vecsize)

    dtw = Dtw(ref_lsp, test_lsp)
    warp = dtw.warp_distance()

    return warp


def write_binary_param(filename, length, data):
    fp=open(filename,'wb')
    for i in range(0, length):
        s=array.array('f',data[i])
        s.tofile(fp)
    fp.close()

def write_param(filename, length, data):

    fp=open(filename,'w')
    vecsize = len(data[0])
    for i in range(0, length):
        for j in range(0, vecsize):
            fp.write(str(data[i][j])+' ')
        fp.write('\n')
    fp.close()

def generate_dtw_feature(warp, test_file, new_file, vecsize, isBinary=True):

    test_data = None
    if isBinary:
        test_data = load_bin_param(test_file, vecsize)
    else:
        test_data = load_param(test_file)

    r_index = []
    t_index = []

    new_data =[]

    for i in range(0, len(warp)):
        r_index += [int(warp[i][0])]
        t_index += [int(warp[i][1])]
  
    # the reference total length
    ref_len = len(r_index) 
    print ref_len  
    index = 0
    for i in range(0, ref_len):
        new_data += [test_data[r_index[i]]] 

    print len(new_data)
    # save the new data
    if isBinary:
        write_binary_param(new_file, ref_len, new_data)  
    else:
        write_param(new_file, ref_len, new_data)  

def f02lf0(f0):
         
    lf0=[]
    T=0
    for i in range(0,len(f0)):
        if f0[i][0]<=0.0:
            lf0+=[LZERO]
        else: 
            lf0+=[math.log(f0[i][0])]
        T+=1
    
    return lf0

def writeBfile(filename, framenum, data ):
    """ write binary data file
        data type is always be float
    """    
    f=open(filename,'wb')
    for i in range(0, framenum):
         f.write(struct.pack('f', data[i]))
    f.close()

def convert_f0_to_lf0(f0file,lf0file):
    f0data = load_param(f0file)
    lf0data = f02lf0(f0data)
    writeBfile(lf0file, len(lf0data), lf0data)

def analysis_f0_rmse(f0log, average, corrAver, u2vAver, v2uAver):
    f = open(f0log)
    line = f.readlines()[0].strip() 
    f.close()
         
    seq = line.split()
 
    average += float(seq[6])
    corrAver += float(seq[11])
    u2vAver += float(seq[9])/(float(seq[1])+float(seq[2]))
    v2uAver += float(seq[10])/(float(seq[1])+float(seq[2]))

    return [average, corrAver, u2vAver, v2uAver]

def analysis_lsd_rmse(lsdlog, average, averFreq, averGains, corrAver):
    f = open(lsdlog)
    line = f.readlines()[0].strip()
    f.close()
    
    seq = line.split()
        
    average += float(seq[3])
    averFreq += float(seq[2])
    averGains += float(seq[5])
    corrAver += float(seq[6])

    return [average, averFreq, averGains, corrAver]

def evaluate_two_waves(record_wave, generated_wave, offline_tool_dir, data_path, args):
    # compute F0 and LSP for record wave
    record_wave_data_path = os.path.join(data_path, 'record')
    check_folder(record_wave_data_path)
    f0_file, lsp_file = compute_wave_f0_and_lsp(record_wave, record_wave_data_path, offline_tool_dir)

    # compute F0 and LSP for generated wave
    generaterd_data_path = os.path.join(data_path, 'generated')
    check_folder(generaterd_data_path)
    f0_generated_file, lsp_generated_file = compute_wave_f0_and_lsp(generated_wave, generaterd_data_path, offline_tool_dir)

    # dtw aligned for test data according to reference
    warp = dtw_align(lsp_file, lsp_generated_file, LSP_order + 1)
    basename = os.path.splitext(os.path.basename(lsp_generated_file))[0]
    lsp_aligned_file = os.path.join(generaterd_data_path, 'feature', basename + '.dtw.lsp')
    f0_aligned_file = os.path.join(generaterd_data_path, 'feature', basename + '.dtw.f0')
    generate_dtw_feature(warp, lsp_generated_file, lsp_aligned_file, LSP_order + 1, True)
    generate_dtw_feature(warp, f0_generated_file, f0_aligned_file, 1, False)

    # convert f0 to lf0 as binary file
    lf0_file = os.path.join(record_wave_data_path, 'feature', basename + '.lf0')
    lf0_aligned_file = os.path.join(generaterd_data_path, 'feature', basename + '.dtw.lf0')
    convert_f0_to_lf0(f0_file, lf0_file)
    convert_f0_to_lf0(f0_aligned_file, lf0_aligned_file)


    idx = record_wave.rfind('\\')
    idx2 = record_wave.rfind('.')
    filename = record_wave[idx+1:idx2]
    RMSE_data_path = os.path.join(data_path, 'RMSE')

    # compute RMSE of F0
    f0_RMSE_data_path = os.path.join(RMSE_data_path, 'f0')
    check_folder(f0_RMSE_data_path)
    output_file = os.path.join(f0_RMSE_data_path, filename + '.txt')
    ret = compute_RMSE_4_f0(lf0_file, lf0_aligned_file, offline_tool_dir, output_file)
    if ret != 0:
        sys.exit()

    # compute RMSE of LSP
    lsp_RMSE_data_path = os.path.join(RMSE_data_path, 'lsp')
    check_folder(lsp_RMSE_data_path)
    output_file = os.path.join(lsp_RMSE_data_path, filename + '.txt')
    ret = compute_RMSE_4_lsd(lsp_file, lsp_aligned_file, lf0_file, offline_tool_dir, output_file)
    if ret != 0:
        sys.exit()

    #if args.mode == 'training':
    #    # compute wave distortion
    #    wave_distrotion_data_path = os.path.join(data_path, 'distortion')
    #    check_folder(wave_distrotion_data_path)
    #    wave_distrotion_file_name = os.path.join(wave_distrotion_data_path, filename + '.txt')
    #    ret = compute_wave_distortion(record_wave, generated_wave, offline_tool_dir, wave_distrotion_file_name)
    #    if ret != 0:
    #        sys.exit()


def compute_frontend_distortion(refDir, testDir, offline_tool_dir, output_file):
    wave_distrotion_tool = os.path.join(offline_tool_dir, ConsistencyMeasure_tool)
    wave_distrotion_command = '%s -r %s -t %s -order %i -od %s' % (wave_distrotion_tool, refDir, testDir, LSP_order, output_file)
    log_command(wave_distrotion_command)
    retvalue = os.system(wave_distrotion_command)
    return retvalue


def create_file_map(filelist):
    f_map = {}
    with open(filelist, 'r') as f:
        for line in f:
            line = line.strip()
            if line == None or line == '':
                continue

            items = line.split()
            key, value = items[0], items[1]
            f_map[key] = value

    return f_map

def analysis_result(data_path, filelist, file_map):
    # analysis result
    # F0 RMSE
    RMSE_data_path = os.path.join(data_path, 'RMSE')

    F0_RMSE_data_path = os.path.join(RMSE_data_path, 'f0')
    averageF0 = 0.0
    corrAver = 0.0
    u2vAver = 0.0
    v2uAver = 0.0

    for key in filelist:
        value = file_map[key]
        basename = os.path.splitext(value)[0]
        f0_log = os.path.join(F0_RMSE_data_path, basename + '.txt')
        averageF0, corrAver, u2vAver, v2uAver = analysis_f0_rmse(f0_log, averageF0, corrAver, u2vAver, v2uAver)

    filenum = len(filelist)
    averageF0 = float(averageF0)/filenum
    corrAver = float(corrAver)/filenum
    u2vAver = float(u2vAver)/filenum
    v2uAver = float(v2uAver)/filenum

    # LSD RMSE
    LSD_RMSE_data_path = os.path.join(RMSE_data_path, 'lsp')
    averageLSD = 0.0
    averFreq = 0.0
    averGains = 0.0
    corrAver = 0.0
    
    for key in filelist:
        value = file_map[key] 
        basename = os.path.splitext(value)[0]
        lsd_log = os.path.join(LSD_RMSE_data_path, basename + '.txt')
        averageLSD, averFreq, averGains, corrAver = analysis_lsd_rmse(lsd_log, averageLSD, averFreq, averGains, corrAver)

    averageLSD = float(averageLSD)/filenum
    averFreq = float(averFreq)/filenum
    averGains = float(averGains)/filenum
    corrAver = float(corrAver)/filenum

    # write final log
    fp = open(os.path.join(RMSE_data_path, 'Final_result.txt'), 'w')
    fp.write('Test file in total = {}'.format(str(filenum)))
    fp.write('RMSE of F0 :'+ str(averageF0)+'(Hz/frame)\n')
    fp.write('CorrCoef of F0 :'+ str(corrAver)+'\n') 
    fp.write('Unvoiced to Voiced rate :'+str(u2vAver)+'\n')
    fp.write('Voiced to unvoiced rate :'+str(v2uAver)+'\n')

    fp.write('Log-Spectral Distance :\t' + str(averageLSD)+'(dB)\n')
    fp.write('Log-Spectral Distance (gain ignored)*: \t' +str(averFreq)+'(dB)\n')
    fp.write('RMSE of Gains: \t'+str(averGains)+'(dB)\n')
    fp.write('Correlation Coefficients of gains:\t' + str(corrAver)+'\n')
    fp.close()


def test():
    args = get_arguments()

    offline_tool_dir = r'D:\git\SpeechCore\target\distrib\debug\amd64\dev\TTS\Server\bin\Offline'
    
    # test compute_f0
    compute_f0(r'D:\test\1.wav', offline_tool_dir, r'D:\test\1.f0')

    # test compute_lsp
    compute_lsp(r'D:\test\1.wav', r'D:\test\1.f0', offline_tool_dir, r'D:\test\1.lsp', r'D:\test\1.of0')

    # test compute_RMSE_4_f0
    compute_RMSE_4_f0(r'D:\test\of0\1.f0', r'D:\test\of0\1_g.f0', offline_tool_dir, r'D:\test\f0.txt')

    # test compute_RMSE_4_lsp
    compute_RMSE_4_lsp(r'D:\test\lsp\1.lsp', r'D:\test\lsp\1_g.lsp', offline_tool_dir, r'D:\test\lsp.txt')

    # test evaluate_two_waves
    evaluate_two_waves(r'D:\test\1.wav', r'D:\test\1_g.wav', offline_tool_dir, r'D:\test\imtermediate', args)


def main():
    args = get_arguments()
    file_map = create_file_map(args.filemap)
    file_path = os.path.join(os.path.abspath(__file__))
    idx = file_path.rfind('\\')
    file_path = file_path[:idx]
    data_path = os.path.join(file_path, 'intermediate2')
    check_folder(data_path)
 
    filelist = file_map.keys()
    filelist.sort()
    for key in filelist:
        print('====================================================================')
        value = file_map[key]
        record_wave = os.path.join(args.record_wave_dir, key)
        generated_wave = os.path.join(args.generated_wave_dir, value)
        evaluate_two_waves(record_wave, generated_wave, args.tool_dir, data_path, args)

    analysis_result(data_path, filelist, file_map)

    if args.mode == 'frontend':
        # compute distortion for frontend mode
        refDir = os.path.join(data_path, 'record\\feature')
        testDir = os.path.join(data_path, 'generated\\feature')
        output_file = os.path.join(data_path, 'frontend_distortion.txt')
        ret = compute_frontend_distortion(refDir, testDir, args.tool_dir, output_file)
        if ret != 0:
            sys.exit()


if __name__ == '__main__':
    main()
