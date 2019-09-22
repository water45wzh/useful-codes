#!/usr/bin/env python
import os
import wave
import struct
import array
from multiprocessing import Pool
import scipy.io.wavfile
import numpy as np


data_root = '/home/weso/weso/Evan_MGC/mgc_merged_f0_raw/'
mean_var_binary = open('data_mgcf0.mv.bin', 'wb')


vec_size = 62
format = '<f4'
datatype = np.dtype((format, (vec_size,)))

feature_sum = np.zeros((1, vec_size))
counter = 0.0
file_counter = 0
for root, dirs, files in os.walk(data_root, topdown=True):
    for aco_file in files:
        file_counter += 1
        features_f = open(os.path.join(root, aco_file), 'rb')
        aco_data = np.fromfile(features_f, dtype=datatype)
        frames, dim = aco_data.shape[0], aco_data.shape[1]
        feature_sum += np.sum(aco_data, axis=0)
        counter += frames

        if file_counter % 100 == 0:
            print("processed files %d" % (file_counter,))


mean = feature_sum / counter

print(mean.shape)
print(mean)

# reset f0
mean[0, 61] = 0.0

# compute var
var_sum = np.zeros((1, vec_size))
counter = 0.0
file_counter = 0
for root, dirs, files in os.walk(data_root, topdown=True):
    for aco_file in files:
        file_counter += 1
        features_f = open(os.path.join(root, aco_file), 'rb')
        aco_data = np.fromfile(features_f, dtype=datatype)
        frames, dim = aco_data.shape[0], aco_data.shape[1]
        aco_data = (aco_data - mean) ** 2
        var_sum += np.sum(aco_data, axis=0)
        counter += frames

        if file_counter % 100 == 0:
            print("processed files %d" % (file_counter,))

var = var_sum / counter
print(var.shape)
print(var)

# reset f0
var[0, 61] = 1.0

# save to file

format = '<f4'
datatype = np.dtype((format, 1))
mean = mean.astype(datatype)
mean.tofile(mean_var_binary)

var = var.astype(datatype)
var.tofile(mean_var_binary)

mean_var_binary.close()
