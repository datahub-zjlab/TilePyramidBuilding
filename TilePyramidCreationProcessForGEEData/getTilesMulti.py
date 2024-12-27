#--------------------------------处理所有级别的切片------------------------------------
import os
from osgeo import gdal
from rasterio.coords import BoundingBox
from global_grid2tiles import BaseTileGenerator,OverviewTileGenerator,save_matrix_as_png
import numpy as np
from tqdm import tqdm
from PIL import Image
import matplotlib.pyplot as plt
import glob

def geotransform_to_bbox(geotransform, width, height):
    """
    Convert GDAL geotransform to rasterio BoundingBox.

    Parameters:
    geotransform (tuple): GDAL geotransform tuple (x_origin, pixel_width, x_rotation, y_origin, y_rotation, pixel_height).
    width (int): Width of the raster in pixels.
    height (int): Height of the raster in pixels.

    Returns:
    BoundingBox: rasterio BoundingBox object.
    """
    x_origin, pixel_width, x_rotation, y_origin, y_rotation, pixel_height = geotransform

    # Calculate the coordinates of the bottom-left and top-right corners
    x_min = x_origin
    y_max = y_origin
    x_max = x_origin + (width * pixel_width) + (height * x_rotation)
    y_min = y_origin + (height * pixel_height) + (width * y_rotation)

    return BoundingBox(left=x_min, bottom=y_min, right=x_max, top=y_max)

# 颜色映射配置
config = {
    'min': 1.0,
    'max': 17.0,
    'palette': [
        '05450a', '086a10', '54a708', '78d203', '009900', 'c6b044', 'dcd159',
        'dade48', 'fbff13', 'b6ff05', '27ff87', 'c24f44', 'a5a5a5', 'ff6d4c',
        '69fff8', 'f9ffa4', '1c0dff'
    ]
}
# 将十六进制颜色转换为RGB元组
def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def map_to_RGB(data):
    # 创建颜色映射
    palette = [hex_to_rgb(color) for color in config['palette']]

    # 获取图像的宽度和高度
    width = len(data[0])
    height = len(data)

    # 创建一个新的图像
    image = Image.new('RGB', (width, height))

    # 将数据映射到颜色并填充图像
    for y in range(height):
        for x in range(width):
            value = data[y][x]
            # 将值映射到调色板索引
            index = int((value - config['min']) / (config['max'] - config['min']) * (len(palette) - 1))
            color = palette[index]
            image.putpixel((x, y), color)
            # print(f'{value}-----{color}')
    return image




#---------------导入完整的tiff文件----------------------------
mcdPath = '/home/data2/qwy/MCD12Q1'
#存放npy中间文件
rootPath = '/home/data2/qwy/MCD12Q1/tiles3'
#存放最终瓦片文件
rootPath2 = '/home/data2/qwy/MCD12Q1/tiles4'
maxScale = 3
# 使用 glob 匹配形如 modis_* 的文件
modis_files = glob.glob(f'{mcdPath}/modis_*')
#modis_files含有多个tif文件，对每个tif切瓦片
for modis_tif in tqdm(modis_files):
    ds = gdal.Open(modis_tif)
    geotransform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    bbox = geotransform_to_bbox(geotransform, ds.RasterXSize, ds.RasterYSize)
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    ds = None
    #切分
    #data3  = np.stack([data, data, data], axis=0)
    #data = np.transpose(data,[1,0])
    data3  = np.expand_dims(data, axis=0)
    print(np.shape(data3))
    #假定为3级
    for i in range(maxScale):
        basetileList = BaseTileGenerator(data3, geotransform, bbox, max_zoom=i, min_zoom=1, nodata_value=0, tile_size=256, xyz_flag=True, max_zoom_level=32)
        myList = basetileList.generate_tiles()

        #保存为对应级别tile
        
        for imagedict in myList:
            outpath = f"{rootPath}/{imagedict['current_index']}.npy"
            outpathPGN = f"{rootPath2}/{imagedict['current_index']}.png"
            if os.path.exists(outpath):
                existData = np.load(outpath)
                #existData = existData+imagedict['data']
                existData[existData==0] += imagedict['data'][existData==0]
            else:
                existData = imagedict['data']
            os.makedirs(os.path.dirname(outpath), exist_ok=True)
            np.save(outpath,existData)
            #这里改你的映射函数
            savedData = map_to_RGB(existData)
            #映射之后savedData需为3通道RGB矩阵
            save_matrix_as_png(np.array(savedData),outpathPGN)




