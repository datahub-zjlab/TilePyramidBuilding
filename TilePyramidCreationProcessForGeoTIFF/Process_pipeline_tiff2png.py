from H5_to_Tiff import h5_to_tiff
from Tiff2Tiles import tiff2tiles
from Statistical_Analysis import statistical_analysis
from Tiles2Npy import tiles2npy, merge_tiles
from Npy2Png import npy2png
from Generate_multilevel_png import generate_multilevel_png
import os
from tqdm import tqdm
from config_save import download_bucket, upload_bucket
from utils import download_object_from_oss, upload_object_to_oss, get_dataset_name
from Validate import plot_tiles_recursive
import numpy as np
from pathlib import Path
from utils import get_all_files
import logging
import warnings
from color_config import *

# Ignore warnings
warnings.filterwarnings("once")


def process_tiff(data_dir,
                 tiff_dir,
                 file_list,
                 sds_name=None,
                 max_zoom=None,
                 stretch_method=None,
                 resolution=None,
                 tile_size=None,
                 nodata_value=None,
                 src_crs=None,
                 upload_npy_url=None,
                 oss_upload_url=None,
                 overwrite_oss=False,
                 selected_channels=[],
                 cmap=None,
                 customized_cmap=None):
    '''
    主函数, 对指定坐标系(src_crs)的GeoTIFF数据进行本地多级瓦片切片处理；
    记录了瓦片的统计信息在<data_dir>/statistics.json，可根据统计信息后期调色；
    在color_config.py定义调色色卡；
    请根据自己的数据集情况，物理意义，统计信息，选择合适的拉伸方法(utils.normalize)，使用stretch_method进行调用；
    '''

    tiles_dir = os.path.join(data_dir, 'TILES')
    npy_dir = os.path.join(data_dir, 'NPY')
    tmp_dir = os.path.join(data_dir, 'TMP')
    png_dir = os.path.join(data_dir, 'PNG')

    os.makedirs(tiles_dir, exist_ok=True)
    os.makedirs(npy_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)

    base_tile_dict = {}
    base_tile_index_list = []

    for fn in tqdm(file_list, desc=f"Processing {sds_name}"):
        tiff_file = os.path.join(tiff_dir, fn)
        try:
            tile_name_list = tiff2tiles(tiff_file, tiles_dir, src_crs=src_crs, resolution=resolution,
                                        tile_size=tile_size)
            if tile_name_list:
                tile_dict_info = tiles2npy(data_dir,
                                           tile_name_list,
                                           base_tile_dict,
                                           base_tile_index_list,
                                           current_level=max_zoom,
                                           resolution=resolution,
                                           tile_size=tile_size)
                if tile_dict_info is not None:
                    base_tile_dict, base_tile_index_list = tile_dict_info
        except Exception as E:
            logging.error(f"{tiff_file} processed failed: {E}")
            continue

    try:
        print("正在合并重复瓦片...")
        merged_base_tile_list = merge_tiles(data_dir, base_tile_dict)
        print("正在计算统计值...")
        statistic_dict = statistical_analysis(data_dir, npy_dir, max_zoom=max_zoom, sds_name=sds_name, nodata_value=nodata_value)
        os.makedirs(os.path.join(data_dir, stretch_method), exist_ok=True)
        print(f"正在生成{max_zoom}级瓦片...")
        npy2png(data_dir, merged_base_tile_list, statistic_dict, stretch_method=stretch_method, cmap=cmap,
                customized_cmap=customized_cmap, selected_channels=selected_channels)
    except Exception as E:
        logging.error(f"Zoom-{max_zoom} merged failed: {E}")

    for zoom_level in range(max_zoom - 1, 0, -1):
        try:
            print(f"正在生成{zoom_level}级瓦片...")
            merged_next_tile_list = generate_multilevel_png(data_dir, merged_base_tile_list)
            npy2png(data_dir, merged_next_tile_list, statistic_dict, stretch_method=stretch_method, cmap=cmap,
                    customized_cmap=customized_cmap, selected_channels=selected_channels)
            merged_base_tile_list = merged_next_tile_list
        except Exception as E:
            logging.error(f"Zoom-{zoom_level} generation failed: {E}")

    # Validate
    plot_tiles_recursive(data_dir=png_dir,
                         output_dir=os.path.join(data_dir, stretch_method))

    # 未归一化的中间结果上传 OSS
    if upload_npy_url:
        npy_list = get_all_files(npy_dir, suffix='npy')
        for npy_path in npy_list:
            normalized_path = os.path.normpath(npy_path)
            parts = normalized_path.split(os.sep)
            current_level = parts[-3]  # 倒数第3层是 current_level
            index_x = parts[-2]  # 倒数第2层是 index_x
            index_y = parts[-1].replace('.npy', '')  # 文件名部分是 index_y

            oss_upload_file = os.path.join(upload_npy_url, current_level, index_x, index_y) + '.npy'
            upload_object_to_oss(upload_bucket, oss_upload_file, normalized_path, overwrite=overwrite_oss)

        print(f"Upload to OSS {upload_npy_url} OK, overwrite is {overwrite_oss}")

    if oss_upload_url:
        png_list = get_all_files(png_dir, suffix='png')
        for png_path in png_list:
            normalized_path = os.path.normpath(png_path)
            parts = normalized_path.split(os.sep)
            current_level = parts[-3]  # 倒数第3层是 current_level
            index_x = parts[-2]  # 倒数第2层是 index_x
            index_y = parts[-1].replace('.png', '')  # 文件名部分是 index_y

            oss_upload_file = os.path.join(oss_upload_url, current_level, index_x, index_y) + '.png'
            upload_object_to_oss(upload_bucket, oss_upload_file, normalized_path, overwrite=overwrite_oss)

        print(f"Upload to OSS {oss_upload_url} OK, overwrite is {overwrite_oss}")


if __name__ == '__main__':
    # TIFF 文件存放文件夹 (输入)
    tiff_dir = '/home/data2/ASTWBD_TIFF'

    # 生成文件的主文件目录 (输出)
    data_dir = '/home/data2/ASTGTM_tiny'
    os.makedirs(data_dir, exist_ok=True)

    # 数据集简称,可以在utils.get_dataset_name添加
    sds_name = 'ASTGTM'

    # fn_list->List, 你要处理的所有tiff数据
    data_list_file = "Data/ASTWBD.txt"
    with open(data_list_file, 'r', encoding='utf-8') as f:
        fn_list = [fn.strip().replace('.zip', '_dem.tif') for fn in f.readlines()]

    # fn_list = os.listdir(tiff_dir)

    # 瓦片上传目录
    oss_upload_url = ''
    # 中间结果(未归一化)上传目录
    upload_npy_url = ''

    tile_size = 1024  # 栅格尺寸, 不用更改

    resolution = 30  # TIFF数据分辨率, 随数据集更改
    max_zoom = 12  # 最大的瓦片级别

    # 归一化方法, 在utils.normalize里面自定义
    stretch_method = 'dem'

    # colormap 色卡, 注意:使用自定义色卡时cmap需要置None, 反之亦然
    cmap = None  # matplotlib色卡关键词
    customized_cmap = BlueReds().cmap  # 自定义色卡,在color_config.py里面

    # GeoTIFF文件的投影坐标系
    src_crs = 'epsg:4326'
    # GeoTIFF文件nodata值
    nodata_value = -9999

    # selected_channels: List, 多通道图像按顺序选择RGB通道的index，单通道图像赋值[]
    selected_channels = []

    # Set logs
    logging.basicConfig(filename=f'{get_dataset_name(sds_name)}.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting the script with the following hyperparameters:")
    logging.info(f"data_dir: {data_dir}")
    logging.info(f"data_list_file: {data_list_file}")
    logging.info(f"oss_upload_url: {oss_upload_url}")
    logging.info(f"upload_npy_url: {upload_npy_url}")
    logging.info(f"resolution: {resolution}")
    logging.info(f"tile_size: {tile_size}")
    logging.info(f"stretch_method: {stretch_method}")

    process_tiff(data_dir=data_dir,
                 tiff_dir=tiff_dir,
                 file_list=fn_list,
                 sds_name=sds_name,
                 max_zoom=max_zoom,
                 stretch_method=stretch_method,
                 resolution=resolution,
                 tile_size=tile_size,
                 src_crs=src_crs,
                 nodata_value=nodata_value,
                 upload_npy_url=None,
                 oss_upload_url=None,
                 overwrite_oss=True, # 是否对oss文件进行覆盖
                 selected_channels=selected_channels,
                 cmap=cmap,
                 customized_cmap=customized_cmap)
