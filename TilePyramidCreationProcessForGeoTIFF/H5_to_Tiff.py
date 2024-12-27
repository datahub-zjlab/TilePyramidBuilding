from utils import read_h5_data, get_rasterio_meta, writearray2GeoTiff
from pyproj import CRS
import rasterio
from pathlib import Path


def h5_to_tiff(h5_file, tiff_file, sds_name=None):
    '''
    读取H5文件并转换为GeoTIFF文件

    Args:
        h5_file: h5文件地址
        tiff_file: 生成的tiff文件地址
        sds_name: h5文件子数据集名称

    Returns:
        None
    '''
    data = read_h5_data(h5_file, sds_name=sds_name)
    Path(tiff_file).parent.mkdir(parents=True, exist_ok=True)

    # Read geological info
    latitude = read_h5_data(h5_file, sds_name='Latitude')
    longitude = read_h5_data(h5_file, sds_name='Longitude')
    affine = get_rasterio_meta(latitude, longitude)

    # save to TIFF file
    writearray2GeoTiff(output_file=tiff_file,
                       data=data,
                       affine=affine,
                       descriptions=["Normalized Difference Vegetation Index"],
                       crs=CRS.from_epsg(4326), dtype=rasterio.int16)

