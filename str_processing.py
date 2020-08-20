import numpy as np

def str2ascii(str):
    return np.fromstring(str, dtype=np.uint8)