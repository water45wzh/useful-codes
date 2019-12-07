#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import glob
import argparse
import threading

REPEAT_NUM = 2
MODES = ('all', 'training', 'testing', 'frontend')
DEFAULT_MODE = 'all'
MODEL_TYPES = ('QRNN', 'BN', 'Vanilla')

def get_arguments():
    parser = argparse.ArgumentParser(description='Mean Loss Tool')
    parser.add_argument('--model', type=str, default=None, required=True,
                        help='which model to use to generate wave')
    parser.add_argument('--data_path', type=str, default=None, required=True,
                        help='data path')
    parser.add_argument('--repeat_num', type=int, default=REPEAT_NUM,
                        help='repeat times for each wave generation')
    parser.add_argument('--mode', type=str, default=DEFAULT_MODE,
                        help='all, training, testing, frontend')
    parser.add_argument('--wave_folder', type=str, required=True,
                        help='folder to save all waves')
    parser.add_argument('--model_type', type=str, default='Vanilla',
                        help='BN model, QRNN model, Vanilla model')

    return parser.parse_args()


def check_wave_save_folder(wave_folder):
    if not os.path.exists(wave_folder):
        os.makedirs(wave_folder)

    training = os.path.join(wave_folder, 'training')
    if not os.path.exists(training):
        os.makedirs(training)

    testing = os.path.join(wave_folder, 'testing')
    if not os.path.exists(testing):
        os.makedirs(testing)

    frontend = os.path.join(wave_folder, 'frontend')
    if not os.path.exists(frontend):
        os.makedirs(frontend)


def check_data_folder(data_path):
    if not os.path.exists(data_path):
        raise Exception("folder %s not exist" % data_path)

    # check sub folder: training_data
    training_data = os.path.join(data_path, 'training_data')
    if not os.path.exists(training_data):
        raise Exception("folder %s not exist" % training_data)

    # check sub folder: testing_data
    testing_data = os.path.join(data_path, 'testing_data')
    if not os.path.exists(testing_data):
        raise Exception("folder %s not exist" % testing_data)

    # check sub folder: frontend_data
    frontend_data = os.path.join(data_path, 'frontend_data')
    if not os.path.exists(frontend_data):
        raise Exception("folder %s not exist" % frontend_data)


def call_generation(wav_out_path, linfile, pitfile, wav_seed, model, mode, args):
    command = 'python generate.py --wav_out_path=%s --linfile=%s --pitfile=%s --wav_seed=%s %s' % (wav_out_path, linfile, pitfile, wav_seed, model)
    if mode == 'frontend':
        command += ' --frontend=True'

    if args.model_type == 'QRNN':
        command += ' --qrnn_lc=True'

    print('running command: %s' % command)

    retvalue = os.system(command)
    return retvalue


def generate_waves(data_path, args, mode):
    print('generate waves for: %s' % mode)

    if args.model_type == 'BN':
        lin_folder = os.path.join(data_path, 'bn')
    else:
        lin_folder = os.path.join(data_path, 'lin')

    pit_folder = os.path.join(data_path, 'pit')
    wave_seed = os.path.join(data_path, 'Seed.wav')

    wave_folder = os.path.join(args.wave_folder, mode)
    lin_files = glob.glob(os.path.join(lin_folder, '*.hpf'))
    for lin_file in lin_files:
        idx1 = lin_file.rfind('/')
        idx2 = lin_file.rfind('.')
        file_name = lin_file[idx1 + 1: idx2]

        lin_file_name = lin_file
        pit_file_name = os.path.join(pit_folder, file_name + '.pit')

        if not os.path.isfile(lin_file_name) or not os.path.isfile(pit_file_name):
            print("file not exit")
            continue

        idx = args.model.rfind('-')
        model_number = args.model[idx+1:]
        wave_name_base = file_name + '_seed_' + str(model_number) + '_' + mode + '_' + args.model_type + '_'
        for i in range(args.repeat_num):
            wave_name = wave_name_base + str(i) + '.wav'
            wave_name = os.path.join(wave_folder, wave_name)
            call_generation(wave_name, lin_file_name, pit_file_name, wave_seed, args.model, mode, args)


def main():
    args = get_arguments()
    check_data_folder(args.data_path)
    check_wave_save_folder(args.wave_folder)

    threads = []

    if args.mode == 'all' or args.mode == 'training':
        print('start thread training')
        training_data = os.path.join(args.data_path, 'training_data')
        t = threading.Thread(target=generate_waves, args=(training_data, args, 'training'))
        threads.append(t)
        t.daemon = True
        t.start()

    if args.mode == 'all' or args.mode == 'testing':
        print('start thread testing')
        test_data = os.path.join(args.data_path, 'testing_data')
        t = threading.Thread(target=generate_waves, args=(test_data, args, 'testing'))
        threads.append(t)
        t.daemon = True
        t.start()

    if args.mode == 'all' or args.mode == 'frontend':
        print('start thread frontend')
        frontend_data = os.path.join(args.data_path, 'frontend_data')
        t = threading.Thread(target=generate_waves, args=(frontend_data, args, 'frontend'))
        threads.append(t)
        t.daemon = True
        t.start()

    for t in threads:
        t.join()

if __name__ == '__main__':
    main()
