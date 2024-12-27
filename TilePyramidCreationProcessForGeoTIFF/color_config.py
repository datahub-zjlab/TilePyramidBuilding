import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

class WhiteGreen():
    def __init__(self):
        start_color = [1, 1, 1]
        end_color = [0, 1, 0.5]

        # 创建一个线性分段的颜色映射
        cmap_name = "white_green"
        n_bins = 256  # 颜色映射的分辨率，可以根据需要调整
        self.cmap = mcolors.LinearSegmentedColormap.from_list(
            cmap_name, [start_color, end_color], N=n_bins
        )
class Greens():
    def __init__(self):
        start_color = [1, 1, 1]
        end_color = [0, 1, 0]

        # 创建一个线性分段的颜色映射
        cmap_name = "greens"
        n_bins = 256  # 颜色映射的分辨率，可以根据需要调整
        self.cmap = mcolors.LinearSegmentedColormap.from_list(
            cmap_name, [start_color, end_color], N=n_bins
        )

class OceanBlue():
    def __init__(self):

        start_color = [1, 1, 1]
        end_color = [0, 121/255, 158/255]

        # 创建一个线性分段的颜色映射
        cmap_name = "ocean_blue"
        n_bins = 256  # 颜色映射的分辨率，可以根据需要调整
        self.cmap = mcolors.LinearSegmentedColormap.from_list(
            cmap_name, [start_color, end_color], N=n_bins
        )
class BlackWhite():
    def __init__(self):

        start_color = [0, 0, 0]
        end_color = [1, 1, 1]

        # 创建一个线性分段的颜色映射
        cmap_name = "white"
        n_bins = 256  # 颜色映射的分辨率，可以根据需要调整
        self.cmap = mcolors.LinearSegmentedColormap.from_list(
            cmap_name, [start_color, end_color], N=n_bins
        )
class BlueReds():
    def __init__(self):

        start_color = [0, 0, 1]
        end_color = [1, 0, 0]

        # 创建一个线性分段的颜色映射
        cmap_name = "bluereds"
        n_bins = 256  # 颜色映射的分辨率，可以根据需要调整
        self.cmap = mcolors.LinearSegmentedColormap.from_list(
            cmap_name, [start_color, end_color], N=n_bins
        )


oceanblue = OceanBlue().cmap
