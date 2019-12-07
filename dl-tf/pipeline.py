#!/usr/bin/env python
import os
import subprocess
import argparse
import glob
import shutil
import threading
from optparse import OptionParser
from MakeF0AndStats import normalize_f0
from multiprocessing import Pool

lock = threading.Lock()


DEFAULT_PROCESSES = 5  # open multiple processes to generate wave simultaneous
DEFAULT_REPEAT_NUM = 1  # repeat number for each sentences
DEFAULT_LANGUAGE = 'enUS'
DEFAULT_INTERMEDIATE_DATA_PATH = r'./intermidate'
DEFAULT_OUTPUT_WAVE_PATH = r'./wavenet_generated_waves'
FILE_MAP = 'filemap.txt'


## Vocoder params
NNLSPRuntimeVocoder = r"D:\git\SpeechCore\target\distrib\debug\amd64\dev\TTS\Server\bin\Offline\NNLSPRuntimeVocoder"

DEFAULT_VOICE_MODEL = r'\\stcgpu-16\xwang\exp\eva\full\NNTraining_20K_All_Output_addSilence\1033'
DEFAULT_VOICE_MODEL_CONFIG = r'\\stcgpu-16\xwang\exp\eva\full\NNTraining_20K_All_Output_addSilence\Intermediate\env\mge_train.conf'
DEFAULT_VOICE_MODEL_INI = r'\\stcgpu-16\xwang\exp\eva\full\NNTraining_20K_All_Output_addSilence\1033.ini'
DEFAULT_VOICE_MODEL_HEQ = r'\\stcgpu-16\xwang\exp\eva\full\NNTraining_20K_All_Output_addSilence\1033.heq'
DEFAULT_VOICE_MODEL_SMOOTH_WINDOW = r'\\stcgpu-16\xwang\exp\eva\full\NNTraining_20K_All_Output_addSilence\f0window.info'

## pitch norm params
DEFAULT_PITCH_NORM_TOOL = r'./predict_pitch.pl'
DEFAULT_PITCH_NORM_DATA = r'\\stcgpu-16\xwang\TF\data\f0.stats.txt'

## Wavenet params
WAVENET_PARAMS = r'../wavenet_params.json'
WAVENET_GENERATION_SCRIPT = r'../generate.py'
WAVENET_SEED = r'./seed.wav'


## step 1 command
TEXT_ANALYSIS_COMMAND = r'{0} -l {1} -v {2} -c {3} -i {4} -g {5} -heq {6} -smoothwindow {7} -t {8} -w {9} -fn false'

## step 3 command
GENERATE_COMMAND = 'python {0} --wav_out_path={1} --linfile={2} --pitfile={3} --wav_seed={4} --qrnn_lc={5} --wavenet_params={6} {7}'

## model type
MODEL_TYPES = ('QRNN', 'BN', 'Vanilla')


current_file_path = os.path.abspath(__file__)
idx = current_file_path.rfind("\\")
current_folder_path = current_file_path[:idx]


def get_arguments():
    def _relative_path_2_abs(path, root):
        """Convert relative path to absolute path"""
        return os.path.join(root, path)

    parser = argparse.ArgumentParser(description='Mean Loss Tool')
    parser.add_argument('--model', type=str, default=None, required=True,
                        help='model file to use to generate wave')
    parser.add_argument('--lang', type=str, default=DEFAULT_LANGUAGE, help='language')
    parser.add_argument('--text', type=str, default=None, required=True,
                        help='input text file to process, need to be Unicode text file')
    parser.add_argument('--processes', type=int, default=DEFAULT_PROCESSES,
                        help='how many processes to work together')

    parser.add_argument('--repeat_num', type=int, default=DEFAULT_REPEAT_NUM,
                        help='repeat times for each wave generation')
    parser.add_argument('--model_type', type=str, default='QRNN',
                        help='BN model, QRNN model, Vanilla model')

    parser.add_argument('--current_folder', type=str, default=current_folder_path)
    parser.add_argument('--intermidate', type=str, default=DEFAULT_INTERMEDIATE_DATA_PATH)
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_WAVE_PATH,
                        help='output folder for generated waves')

    ## Voice model params, do not change it if not necessary
    parser.add_argument('--vocoder', type=str, default=NNLSPRuntimeVocoder,
                        help='NNLSPRuntimeVocoder used for generated frontend data and pitch data')
    parser.add_argument('--voice_model', type=str, default=DEFAULT_VOICE_MODEL,
                        help='path for voice model')
    parser.add_argument('--voice_model_config', type=str, default=DEFAULT_VOICE_MODEL_CONFIG,
                        help='path for voice model config file')
    parser.add_argument('--voice_model_ini', type=str, default=DEFAULT_VOICE_MODEL_INI,
                        help='path for voice model ini file')
    parser.add_argument('--voice_model_heq', type=str, default=DEFAULT_VOICE_MODEL_HEQ,
                        help='path for voice model heq file')
    parser.add_argument('--voice_model_smooth_window', type=str, default=DEFAULT_VOICE_MODEL_SMOOTH_WINDOW,
                        help='path for voice model smooth window file')

    ## Pitch norm
    parser.add_argument('--pitch_norm_tool', type=str, default=DEFAULT_PITCH_NORM_TOOL,
                        help='path for pitch norm tool')
    parser.add_argument('--pitch_stats', type=str, default=DEFAULT_PITCH_NORM_DATA,
                        help='pitch stats file')
    parser.add_argument('--filemap', type=str, default=FILE_MAP, help='filemap')

    ## Wavenet params
    parser.add_argument('--wavenet_params', type=str, default=WAVENET_PARAMS,
                        help='wavenet parameter file')
    parser.add_argument('--wavenet_generate_script', type=str, default=WAVENET_GENERATION_SCRIPT,
                        help='wavenet generation file')
    parser.add_argument('--wavenet_seed', type=str, default=WAVENET_SEED,
                        help='wavenet seed.wav for generation guidence')

    return parser.parse_args()


def unicode_input_file_check(input_file):
    pass


def check_and_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def generate_filemap(file_map_name, path):
    files = glob.glob(os.path.join(path, '*.cmp'))
    filemap = open(file_map_name, 'w')
    for f in files:
        idx = f.rfind('\\')
        idx2 = f.rfind('.')
        file_name = f[idx+1:idx2]
        filemap.write(file_name + ' ' + file_name + '\n')

    filemap.close()


def step_1(args):
    print("=========================================================")
    print("====== Step 1: Extracting Linguistic feature ============")
    print("=========================================================")

    command = TEXT_ANALYSIS_COMMAND.format(args.vocoder, args.lang, args.voice_model, args.voice_model_config,
        args.voice_model_ini, args.voice_model_config, args.voice_model_heq, args.voice_model_smooth_window, args.text, args.intermidate)
    print(command)
    try:
        status = subprocess.call(command, shell=True)
    except OSError as e:
        print(e)

    generate_filemap(args.filemap, args.intermidate)


def step_2(args):
    print("=========================================================")
    print("====== Step 2: compute pitch and normalize pitch ========")
    print("=========================================================")

    normalize_f0(args.intermidate, args.filemap, args.intermidate, args.pitch_stats,
        pitch_tool=args.pitch_norm_tool, gen_test=False, gen_pitch=True)


def call_generation(wav_out_path, linfile, pitfile, args):
    is_qrnn = False
    if args.model_type == 'QRNN':
        is_qrnn = True

    command = GENERATE_COMMAND.format(args.wavenet_generate_script, wav_out_path, linfile, pitfile,
        args.wavenet_seed, str(is_qrnn), args.wavenet_params, args.model)

    print('running command: %s' % command)
    try:
        FNULL = open(os.devnull, 'w')
        status = subprocess.call(command, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
    except OSError as e:
        print(e)


def generate_waves(args, input_file):


    while True:
        # check if file is end
        if input_file.tell() == os.fstat(input_file.fileno()).st_size:
            break

        lock.acquire()
        try:
            line = input_file.readline()
        finally:
            lock.release()

        filename = line.split()[0]
        wav_out_path = os.path.join(args.output, filename + '.wav')
        linfile = os.path.join(args.intermidate, filename + '.hpf')
        pitfile = os.path.join(args.intermidate, filename + '.pit')
        call_generation(wav_out_path, linfile, pitfile, args)
        print('generation finished: %s' % wav_out_path)


def step_3(args):
    print("=========================================================")
    print("====== Step 3: Generating Waves                  ========")
    print("=========================================================")

    check_and_create_folder(args.output)
    input_file = open(args.filemap, 'r')
    threads = []
    for i in range(args.processes):
        t = threading.Thread(target=generate_waves, args=(args, input_file))
        threads.append(t)
        t.daemon = True
        t.start()

    for t in threads:
        t.join()

    input_file.close()


def main():
    args = get_arguments()
    args.intermidate = os.path.join(args.current_folder, args.intermidate)
    args.filemap = os.path.join(args.current_folder, args.filemap)

    if os.path.exists(args.intermidate):
        shutil.rmtree(args.intermidate)

    check_and_create_folder(args.intermidate)

    try:
        # step 1
        step_1(args)

        # step 2: compute pitch and normalize pitch
        step_2(args)

        # step 3: generate wave
        step_3(args)
    except KeyboardInterrupt:
        print("user Interrupt")
        return


if __name__ == '__main__':
    main()
