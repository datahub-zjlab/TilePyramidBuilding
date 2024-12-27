import h5py
import rasterio
from rasterio.transform import Affine
from rasterio.coords import BoundingBox
from rasterio.warp import calculate_default_transform, reproject, Resampling
from aster_core.mosaic_tile import extract_granule, extract_geotif
import re
from pyproj import CRS
import json

import numpy as np
import os
from PIL import Image
import matplotlib.pyplot as plt


def read_h5_data(filename, sds_name):
    # open HDF5 file
    with h5py.File(filename, 'r') as f:
        # list sub-dataset
        def print_name(name):
            print(name)

        # f.visit(print_name)
        emis_mean = f['Emissivity']['Mean'][:]
        emis_std = f['Emissivity']['SDev'][:]
        latitude = f['Geolocation']['Latitude'][:]
        longitude = f['Geolocation']['Longitude'][:]
        observations = f['Observations']['NumObs'][:]
        water_map = f['Land Water Map']['LWmap'][:]
        ndvi_mean = f['NDVI']['Mean'][:]
        ndvi_std = f['NDVI']['SDev'][:]
        tem_mean = f['Temperature']['Mean'][:]
        tem_std = f['Temperature']['SDev'][:]
        gdem = f['ASTER GDEM']['ASTGDEM'][:]

    res = {
        'Emissivity Mean': emis_mean,
        'Emissivity SDev': emis_std,
        'Latitude': latitude,
        'Longitude': longitude,
        'Observations': observations,
        'NDVI Mean': ndvi_mean,
        'NDVI SDev': ndvi_std,
        'NDWI': water_map,
        'Temperature Mean': tem_mean,
        'Temperature SDev': tem_std,
        'GDEM': gdem,
    }
    return res[sds_name]


def get_rasterio_meta(latitude, longitude):
    h, w = latitude.shape
    pixelHeight = (np.max(latitude) - np.min(latitude)) / (h - 1)
    pixelWidth = (np.max(longitude) - np.min(longitude)) / (w - 1)
    originX = longitude[0, 0]
    originY = latitude[0, 0]
    rotationX = 0
    rotationY = 0
    affine = Affine(pixelWidth, rotationX, originX, rotationY, -pixelHeight, originY)
    return affine


def writearray2GeoTiff(output_file, data, affine, descriptions, crs=CRS.from_epsg(4326), dtype=rasterio.int16):
    if data.ndim == 2:
        count = 1
        height, width = data.shape
        data = data.reshape((1, height, width))
    elif data.ndim == 3:
        count, height, width = data.shape
    else:
        assert f"writearray2GeoTiff 不支持该纬度的数组，data.shape={data.shape}"

    out_meta = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "transform": affine,
        "dtype": dtype,
        "crs": crs,
        "count": count
    }

    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(data)
        for i in range(1, count + 1):
            dest.update_tags(i, DESCRIPTION=descriptions[i - 1])


def get_bbox_from_geotiff(geotiff_path):
    """
    从GeoTIFF文件中获取边界框（Bounding Box）

    :param geotiff_path: GeoTIFF文件的路径
    :return: rasterio.coords.BoundingBox对象
    """
    with rasterio.open(geotiff_path) as src:
        # 获取图像的宽度和高度
        width = src.width
        height = src.height

        # 获取图像的变换矩阵
        transform = src.transform

        # 计算边界框的四个角点坐标
        left = transform.c
        top = transform.f
        right = left + transform.a * width
        bottom = top + transform.e * height

        left = max(left, -180.0)
        bottom = max(bottom, -90.0)
        top = min(top, 90.0)
        right = min(right, 180.0)

        # 创建BoundingBox对象
        bbox = BoundingBox(left=left, bottom=bottom, right=right, top=top)
        return bbox


def process_tile(tile_index, input_file, global_grid, bands=None):
    tile_bbox = global_grid.get_tile_bounds(tile_index)

    if '.tif' in input_file:
        _data = extract_geotif(input_file, tile_bbox, global_grid.tile_size, global_grid.projection)

    elif '.hdf' in input_file:
        _data = extract_granule(input_file, bands, tile_bbox, global_grid.tile_size, global_grid.projection)
    else:
        assert f"Wrong file type in function 'process_tile', index: {tile_index}"

    # if _data is not None:
    #     _data[_data < 0] = 0
    return _data


def extract_x_y_from_filename(filename):
    """
    从给定的文件名字符串中提取 x 和 y 的值。

    :param filename: 文件名字符串
    :return: 包含 x 和 y 值的字典，如果未找到则返回 None
    """
    # 正则表达式模式：匹配 'x-' 和 'y-' 后面的数字
    pattern = r'x-(?P<x>\d+)_y-(?P<y>\d+)'

    # 使用 re.search 查找符合模式的第一个匹配
    match = re.search(pattern, filename)

    if match:
        # 如果匹配成功，返回包含 x 和 y 值的字典
        return int(match.group('x')), int(match.group('y'))
    else:
        # 如果没有找到匹配，返回 None
        return None


def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data


def normalize(data, statistic_dict, stretch_method='gaussian'):
    data_rgb = data[:, :, :-1]
    data_alpha = data[:, :, -1]
    # 高斯线性拉伸
    if stretch_method == 'gaussian':
        mean, std = statistic_dict["mean"], statistic_dict["std"]
        for n in range(data_rgb.shape[-1]):
            max_value = min(mean[n] + 3 * std[n], 1)
            min_value = max(mean[n] - 3 * std[n], 0)
            # clip by (min, max)
            data_rgb[data_rgb[:, :, n] > max_value] = max_value
            data_rgb[data_rgb[:, :, n] < min_value] = min_value
            # norm to (0,255)
            data_rgb[:, :, n] = (data_rgb[:, :, n] - min_value) / (
                    max_value - min_value)
    # 截断2%~98%,线性拉伸
    elif stretch_method == '02-98':
        for n in range(data_rgb.shape[-1]):
            min_value = statistic_dict["02%"][n]
            max_value = statistic_dict["98%"][n]
            # clip by (min, max)
            data_rgb[data_rgb[:, :, n] > max_value] = max_value
            data_rgb[data_rgb[:, :, n] < min_value] = min_value
            # norm to (0,255)
            data_rgb[:, :, n] = (data_rgb[:, :, n] - min_value) / (
                    max_value - min_value)
    # 没有截断的线性拉伸
    elif stretch_method == 'linear-stretch':
        for n in range(data_rgb.shape[-1]):
            min_value = statistic_dict["min"][n]
            max_value = statistic_dict["max"][n]
            # clip by (min, max)
            data_rgb[data_rgb[:, :, n] > max_value] = max_value
            data_rgb[data_rgb[:, :, n] < min_value] = min_value
            # norm to (0,255)
            data_rgb[:, :, n] = (data_rgb[:, :, n] - min_value) / (
                    max_value - min_value)
    # 掩码0-1拉伸
    elif stretch_method == '0-1':
        min_value = 0
        max_value = 1
        for n in range(data_rgb.shape[-1]):
            data_rgb[data_rgb[:, :, n] > max_value] = 1
            data_rgb[data_rgb[:, :, n] < min_value] = 0

    elif stretch_method == 'ghs':
        nodata_value = -32760
        data_rgb[data_rgb==nodata_value] = 0
        max_value = 32757
        min_value = 0
        for n in range(data_rgb.shape[-1]):
            data_rgb[data_rgb[:, :, n] > max_value] = 1
            data_rgb[data_rgb[:, :, n] < min_value] = 0
            data_rgb[:, :, n] = (data_rgb[:, :, n] - min_value) / (
                    max_value - min_value)

    elif stretch_method == 'dem':
        for n in range(data_rgb.shape[-1]):
            max_value = statistic_dict["max"][n]
            min_value = 0

            data_rgb[data_rgb[:, :, n] > max_value] = max_value
            data_rgb[data_rgb[:, :, n] < min_value] = min_value
            data_rgb[:, :, n] = (data_rgb[:, :, n] - min_value) / (
                    max_value - min_value)

    return np.concatenate((data_rgb, np.expand_dims(data_alpha, -1)), axis=-1)


def array_to_png(array, output_path, cmap=None, customized_cmap=None, selected_channels=None):
    # 创建NDVI颜色映射（从白色到绿色）
    if customized_cmap:
        cmap = customized_cmap
    else:
        cmap = plt.get_cmap(cmap)

    if selected_channels:
        colors = array[:,:,selected_channels]
    else:
        colors = cmap(array[:,:,0])

    # 提取 RGBA 通道
    r = (colors[:, :, 0] * 255).astype(np.uint8)
    g = (colors[:, :, 1] * 255).astype(np.uint8)
    b = (colors[:, :, 2] * 255).astype(np.uint8)
    a = array[:, :, -1].astype(np.uint8) * 255

    # 创建 RGBA 图像
    rgba_image = np.dstack((r, g, b, a))

    # 使用 Pillow 保存图像
    image = Image.fromarray(rgba_image, mode='RGBA')
    image.save(output_path)


def download_object_from_oss(bucket, oss_url, download_file):
    if os.path.exists(download_file):
        pass
    else:
        bucket.get_object_to_file(oss_url, download_file)


def upload_object_to_oss(bucket, oss_url, upload_file, overwrite=False):
    oss_url = oss_url.replace("\\", "/")
    exists = bucket.object_exists(oss_url)
    if exists:
        if overwrite:
            bucket.put_object_from_file(oss_url, upload_file)
    else:
        bucket.put_object_from_file(oss_url, upload_file)


import os


def get_all_files(data_dir, suffix):
    """
    获取 data_dir 下所有文件的完整路径。
    """
    file_list = []

    # 遍历目录
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith(f'.{suffix}'):
                file_list.append(os.path.join(root, file))

    return file_list


def get_dataset_name(sds_name):
    if sds_name == 'NDVI Mean':
        return "Aster-GEDV3 植被NDVI均值"
    elif sds_name == 'ASTWBD':
        return "ASTWBDv001 30m水体掩码"
    elif sds_name == 'Temperature':
        return "Aster-GEDV3 温度"
    elif sds_name == 'ASTGTM':
        return "ASTGTMv003 高程均值"
    else:
        return sds_name
