import os
from utils import get_bbox_from_geotiff, process_tile
from aster_core.utils import bbox2bbox
import numpy as np
from aster_core.global_grid import GlobalRasterGrid
from osgeo import gdal
import rasterio


def tiff2tiles(tiff_file, tiles_dir, src_crs='epsg:4326', resolution=100, tile_size=1024):
    '''

    Args:
        tiff_file: tiff文件路径
        tiles_dir: 栅格生成目录
        resolution: 栅格分辨率
        tile_size: 栅格尺寸
        channel_count: tiff文件通道数

    Returns:
        tile_name_list: 生成有效栅格文件名称
    '''
    bbox = get_bbox_from_geotiff(tiff_file)
    bbox_3857 = bbox2bbox(bbox, src_crs, 'epsg:3857')

    # Define the Grid in EPSG:3857
    global_grid = GlobalRasterGrid(resolution=resolution, tile_size=tile_size)

    # Find the Intersect grid indexes
    tile_index_list = global_grid.get_tile_list(bbox_3857)
    tile_name_list = []
    # Reproject the data from 4326 to 3857, and assign the grid array
    for tile_index in tile_index_list:
        tile_index_x, tile_index_y = tile_index
        fn = f"res-{resolution}_tilesize-{tile_size}_x-{tile_index_x}_y-{tile_index_y}.tiff"

        tiles_file = os.path.join(tiles_dir, fn)
        tile_geotransform = global_grid.get_tile_geotransform((tile_index_x, tile_index_y), affine_flag=True)
        try:
            data = process_tile(tile_index, tiff_file, global_grid)
        except:
            continue
        if data is not None:
            if data.ndim == 2:
                data = data.reshape((1, data.shape[0], data.shape[1]))
            if os.path.exists(tiles_file):
                data_exist = gdal.Open(tiles_file).ReadAsArray()
                data = np.where(data_exist != 0, data_exist, data)
            channel_count = data.shape[0]

            # 保存为GeoTIFF
            with rasterio.open(
                    tiles_file,
                    'w',
                    driver='GTiff',
                    height=tile_size,
                    width=tile_size,
                    count=channel_count,
                    dtype=np.int16,
                    crs="epsg:3857",
                    transform=tile_geotransform,
            ) as dst:
                dst.write(data)

            tile_name_list.append(fn)

    return tile_name_list
