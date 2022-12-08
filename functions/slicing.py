import json
import shutil
import os
import numpy as np
from tqdm import tqdm
import SimpleITK as sitk
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt


class Data(object):

    def __init__(self, path):
        # 读取path中的数据
        self.path = path
        self._ds = sitk.ReadImage(self.path)
        self._spacing = np.array(list(reversed(self._ds.GetSpacing())))
        self._origin = np.array(list(reversed(self._ds.GetOrigin())))
        self._image = sitk.GetArrayFromImage(self._ds)


    def readMha(self):
        pass


if __name__ == '__main__':
    path = "Z:/PycharmProjects/LuSNAP/data/xuyi20201223/xuyi.mhd"
    d = Data(path)

