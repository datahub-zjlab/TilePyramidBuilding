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

# Ignore warnings
warnings.filterwarnings("once")

def process_h5(data_dir, h5_dir, oss_download_url, file_list, sds_name=None, max_zoom=None, stretch_method=None,
               resolution=None,
               tile_size=None,
               nodata_value=None,
               src_crs=None,
               channel_count=None, upload_npy_url=None, oss_upload_url=None, overwrite_oss=False):
    tiff_dir = os.path.join(data_dir, 'TIFF')
    tiles_dir = os.path.join(data_dir, 'TILES')
    npy_dir = os.path.join(data_dir, 'NPY')
    tmp_dir = os.path.join(data_dir, 'TMP')
    png_dir = os.path.join(data_dir, 'PNG')

    os.makedirs(tiff_dir, exist_ok=True)
    os.makedirs(tiles_dir, exist_ok=True)
    os.makedirs(npy_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)

    base_tile_dict = {}
    base_tile_index_list = []

    for fn in tqdm(file_list, desc=f"Processing {sds_name}"):
        h5_file = os.path.join(h5_dir, fn)
        tiff_file = os.path.join(tiff_dir, fn.replace('.h5', '.tiff'))
        try:
            download_object_from_oss(download_bucket, os.path.join(oss_download_url, fn), h5_file)
            h5_to_tiff(h5_file, tiff_file, sds_name=sds_name)
        except Exception as E:
            logging.error(f"{h5_file} download failed: {E}")
            print(f"{h5_file} download failed: {E}")
            continue
        try:

            tile_name_list = tiff2tiles(tiff_file, tiles_dir, resolution=resolution, tile_size=tile_size, src_crs=src_crs,
                                        channel_count=channel_count)
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
            logging.error(f"{h5_file} processed failed: {E}")
            continue

    try:
        print("正在合并重复瓦片...")
        merged_base_tile_list = merge_tiles(data_dir, base_tile_dict)
        print("正在计算统计值...")
        statistic_dict = statistical_analysis(data_dir, npy_dir, max_zoom=max_zoom, sds_name=sds_name, nodata_value=nodata_value)
        os.makedirs(os.path.join(data_dir, stretch_method), exist_ok=True)
        print(f"正在生成{max_zoom}级瓦片...")
        npy2png(data_dir, merged_base_tile_list, statistic_dict, stretch_method=stretch_method)
    except Exception as E:
        logging.error(f"Zoom-{max_zoom} merged failed: {E}")

    for zoom_level in range(max_zoom - 1, 0, -1):
        try:
            print(f"正在生成{zoom_level}级瓦片...")
            merged_next_tile_list = generate_multilevel_png(data_dir, merged_base_tile_list)
            npy2png(data_dir, merged_next_tile_list, statistic_dict, stretch_method=stretch_method)
            merged_base_tile_list = merged_next_tile_list
        except Exception as E:
            logging.error(f"Zoom-{zoom_level} generation failed: {E}")

    # Validate
    plot_tiles_recursive(data_dir=png_dir,
                         output_dir=os.path.join(data_dir, stretch_method))

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


if __name__ == '__main__':
    h5_dir = '/data/AsterGEDv3/'
    os.makedirs(h5_dir, exist_ok=True)
    data_dir = '/data/NDVI_full'
    sds_name = 'NDVI Mean'
    # data_list_file = "Data/AsterGEDv3_filelist.txt"
    data_list_file = "Data/AG100_filelist.txt"
    oss_download_url = 'Aster-GEDv3/h5/'
    oss_upload_url = 'AsterGEDv3/NDVI_PNG/'
    upload_npy_url = 'AsterGEDv3/NDVI_TIFF/'
    resolution = 100
    tile_size = 1024
    max_zoom = 9
    stretch_method = '02-98'
    src_crs = 'epsg:4326'
    nodata_value = -9999

    # fn_list = ['AG100.v003.-01.-065.0001.h5']

    # Set logs
    logging.basicConfig(filename=f'{get_dataset_name(sds_name)}.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting the script with the following hyperparameters:")
    logging.info(f"h5_dir: {h5_dir}")
    logging.info(f"data_dir: {data_dir}")
    logging.info(f"data_list_file: {data_list_file}")
    logging.info(f"oss_download_url: {oss_download_url}")
    logging.info(f"oss_upload_url: {oss_upload_url}")
    logging.info(f"upload_npy_url: {upload_npy_url}")
    logging.info(f"resolution: {resolution}")
    logging.info(f"tile_size: {tile_size}")
    logging.info(f"stretch_method: {stretch_method}")

    with open(data_list_file, 'r', encoding='utf-8') as f:
        fn_list = [fn.strip() for fn in f.readlines()]

    process_h5(data_dir=data_dir,
               h5_dir=h5_dir,
               oss_download_url=oss_download_url,
               file_list=fn_list,
               sds_name=sds_name,
               max_zoom=max_zoom,
               src_crs=src_crs,
               nodata_value=nodata_value,
               stretch_method=stretch_method,
               resolution=resolution,
               tile_size=tile_size,
               upload_npy_url=None,
               oss_upload_url=None,
               overwrite_oss=True)
