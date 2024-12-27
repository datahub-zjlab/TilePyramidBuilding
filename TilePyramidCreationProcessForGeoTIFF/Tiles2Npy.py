import os
from utils import extract_x_y_from_filename, save_json
from aster_core.global_grid2tiles import BaseTileGenerator, MergeTileRecords
from aster_core.global_grid import GlobalRasterGrid
from aster_core.mosaic_tile import extract_geotif
from aster_core.utils import affine_to_geotransform
from pathlib import Path
import numpy as np


def tiles2npy(data_dir, tile_name_list, base_tile_dict, base_tile_index_list, current_level=None,
              resolution=None, tile_size=None):
    '''
    栅格-->瓦片 计算函数
    主要过程为: 1.地理坐标转化; 2.瓦片生成; 3.瓦片合并 (func merge_tiles)
    其中, base_tile_dict和base_tile_index_list是瓦片生成的信息, 包含index对应关系, 数据存放地址等等, 在loop中不断维护, 即使入参也是返回值
    Args:
        data_dir: 数据主目录
        tile_name_list: 瓦片信息字典中包含index对应关系的list
        base_tile_dict: 瓦片信息字典
        base_tile_index_list:
        current_level: 当前切片等级
        resolution: 栅格分辨率
        tile_size: 栅格尺寸

    Returns:
        base_tile_dict: 瓦片信息字典
        base_tile_index_list: 瓦片信息字典中包含index对应关系的list

    '''
    tiles_dir = os.path.join(data_dir, 'TILES')
    tmp_dir = os.path.join(data_dir, 'TMP')
    # Define the Grid in EPSG:3857
    global_grid = GlobalRasterGrid(resolution=resolution, tile_size=tile_size)

    for tile_name in tile_name_list:
        tile_index = extract_x_y_from_filename(tile_name)
        tile_bbox = global_grid.get_tile_bounds(tile_index)

        geotif = extract_geotif(geotif_file=os.path.join(tiles_dir, tile_name),
                                tile_bbox=tile_bbox,
                                tile_size=tile_size,
                                dst_crs='epsg:3857',
                                return_dst_transform_flag=True,
                                return_dst_crs_flag=True)
        if geotif is not None:
            tile_data, tile_affine, projection = geotif
        else:
            return None

        if tile_data is not None:

            if tile_data.ndim == 2:
                tile_data = tile_data.reshape((1, tile_data.shape[0], tile_data.shape[1]))

            base_tile_generator = BaseTileGenerator(tile_data, affine_to_geotransform(tile_affine), tile_bbox,
                                                    max_zoom=current_level, min_zoom=current_level - 1)
            base_tile_list = base_tile_generator.generate_tiles()
        else:
            return None

        # 数据和index分开，数据存储，index建表
        for base_tile_info in base_tile_list:
            current_zoom, index_x, index_y = base_tile_info["current_index"].split('/')
            npy_name = f'{current_zoom}/{index_x}/x-{tile_index[0]}_y-{tile_index[1]}_index-{index_y}.npy'

            tmp_file = os.path.join(tmp_dir, npy_name)

            Path(tmp_file).parent.mkdir(parents=True, exist_ok=True)
            np.save(tmp_file, base_tile_info['data'])

            base_tile = {
                'data_dir': tmp_file,
                'current_index': base_tile_info['current_index'],
                'current_level': base_tile_info['current_level'],
                'min_index': base_tile_info['min_index'],
                'min_level': base_tile_info['min_level'],
            }

            if np.count_nonzero(base_tile_info['data'][:, :, 0]):
                base_tile_index = f'{base_tile_info["current_index"]}'

                if base_tile_index in base_tile_index_list:
                    base_tile_dict[base_tile_index].append(base_tile)
                else:
                    base_tile_index_list.append(base_tile_index)
                    base_tile_dict[base_tile_index] = []
                    base_tile_dict[base_tile_index].append(base_tile)

    return base_tile_dict, base_tile_index_list


def merge_tiles(data_dir, base_tile_dict):
    '''

    遍历瓦片信息字典, 合并重复的瓦片/切片

    Args:
        data_dir: 生成文件主目录
        base_tile_dict: 瓦片信息字典

    Returns:

        merged_base_tile_list: 合并之后的瓦片信息字典

    '''
    npy_dir = os.path.join(data_dir, 'NPY')
    merged_base_tile_list = []

    # 合并瓦片并存储为npy
    for key, value in base_tile_dict.items():
        merged_base_tile_dict = {}
        merged_base_tile_dict[key] = MergeTileRecords(value, data_dir_flag=True, save_dir=npy_dir)
        # data = np.load(base_tile_dict[key]['data_dir'])
        merged_base_tile_list.append(merged_base_tile_dict)

    current_level = list(merged_base_tile_list[0].values())[0]['current_level']
    json_file_name = f"merged_base_tile_index_list_zoom-{current_level}.json"
    save_json(merged_base_tile_list, os.path.join(data_dir, json_file_name))

    # json_file_name = "merged_base_tile_index_list.json"
    # save_json(merged_base_tile_index_list, os.path.join(data_dir, json_file_name))
    return merged_base_tile_list
