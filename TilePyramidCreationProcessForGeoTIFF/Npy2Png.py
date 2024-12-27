from utils import normalize, array_to_png, load_json
import numpy as np
import os
from pathlib import Path

def npy2png(data_dir, tile_dict_list, statistic_dict, stretch_method, cmap=None, customized_cmap=None, selected_channels=[]):
    '''
    对npy文件进行归一化处理，再将归一化的RGBA四通道矩阵存储为.png格式文件

    Args:
        data_dir: 输出文件主目录
        tile_dict_list: 瓦片信息对应字典
        statistic_dict: 统计信息，跑Statistical_Analysis可以得到该文件，字典格式
        stretch_method: 拉伸方法，定义在utils.normalize函数里
        cmap: matplotlib中色卡关键词
        customized_cmap: 自定义的基于matplotlib的色卡，定义在color_config.py里
        selected_channels: List, 多通道图像按顺序选择RGB通道的index

    Returns: None

    '''
    png_dir = os.path.join(data_dir, 'PNG')
    for tile_dict in tile_dict_list:
        for key, value in tile_dict.items():
            tile_data = np.load(value['data_dir'])

            current_level, index_x, index_y = value['current_index'].split('/')
            # 归一化
            norm_tile_data = normalize(tile_data, statistic_dict, stretch_method=stretch_method)

            png_file = os.path.join(png_dir, current_level, index_x, f'{index_y}.png')
            Path(png_file).parent.mkdir(parents=True, exist_ok=True)
            # 将归一化的四通道RGBA矩阵存储为png文件
            array_to_png(norm_tile_data, png_file, cmap=cmap, customized_cmap=customized_cmap, selected_channels=selected_channels)
            # 维护瓦片信息对应的字典
            tile_dict[key]['png_dir'] = png_file



