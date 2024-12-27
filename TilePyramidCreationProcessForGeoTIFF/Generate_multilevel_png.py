from aster_core.global_grid2tiles import OverviewTileGenerator
import os
from utils import save_json
import numpy as np

def generate_multilevel_png(data_dir, base_tile_index_list):
    '''
    生成下一级瓦片
    Args:
        data_dir: 数据目录
        base_tile_index_list: 上一级瓦片信息字典

    Returns:
        merged_base_tile_list: 下一级瓦片信息字典

    '''
    npy_dir = os.path.join(data_dir, 'NPY')
    merged_base_tile_index_list = []
    next_tile_dict = {}
    for base_tile_dict in base_tile_index_list:
        for key, value in base_tile_dict.items():
            next_tile_index = f'{value["min_index"]}'
            if next_tile_index in merged_base_tile_index_list:
                next_tile_dict[next_tile_index].append(value)
            else:
                merged_base_tile_index_list.append(next_tile_index)
                next_tile_dict[next_tile_index] = []
                next_tile_dict[next_tile_index].append(value)
    merged_base_tile_list = []
    for key, value in next_tile_dict.items():
        merged_base_tile_dict = {}
        _OverviewTileGenerator = OverviewTileGenerator(value)
        merged_base_tile_dict[key] = _OverviewTileGenerator.generate_next_tiles(data_dir_flag=True, save_dir=npy_dir)
        merged_base_tile_list.append(merged_base_tile_dict)
    current_level = list(merged_base_tile_list[0].values())[0]['current_level']
    json_file_name = f"merged_base_tile_index_list_zoom-{current_level}.json"
    save_json(merged_base_tile_list, os.path.join(data_dir, json_file_name))
    return merged_base_tile_list