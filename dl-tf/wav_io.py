import librosa
import os
import re
import scipy
import numpy as np
import tensorflow as tf
from scipy import signal

sample_rate = 48000

def load_wav(path):
    return librosa.core.load(path, sr=sample_rate)[0]


def save_wav(wav, path):
    wav *= 32767 / max(0.01, np.max(np.abs(wav)))
    scipy.io.wavfile.write(path, sample_rate, wav.astype(np.int16))