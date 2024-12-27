
from utils import normalize, array_to_png, load_json
import numpy as np
import os
from pathlib import Path
from Validate import plot_tiles_recursive
from tqdm import tqdm

def regenerate_png(npy_dir, png_dir, statistic_dict, stretch_method, cmap, customized_cmap, selected_channels):
    '''
        按照stretch_method方法，重新遍历npy文件目录，生成新的调色图片

    Args:
        npy_dir: NPY文件目录
        png_dir: PNG文件目录
        statistic_dict: 统计信息字典
        stretch_method: 拉伸方法, 在utils.normalize中使用
        cmap: matplotlib色卡关键词
        customized_cmap: 自定义色卡, 在color_config中定义
        selected_channels: List, 多通道图像按顺序选择RGB通道的index

    Returns:

    '''
    npy_tiles = {}
    # 读取数据
    for root, _, files in os.walk(npy_dir):
        # 获取当前目录的 group 和 index_x
        rel_path = os.path.relpath(root, npy_dir)
        parts = rel_path.split(os.sep)

        if len(parts) < 2:
            continue  # 跳过没有足够层级的目录

        try:
            group = int(parts[0])  # 第二层级 group
            index_x = int(parts[1])  # index_x
        except ValueError:
            continue  # 跳过非数字目录

        for file in files:
            if file.endswith('.npy'):
                try:
                    # 提取文件名中的 index_y
                    index_y = int(file.replace('.npy', ''))
                    npy_tiles.setdefault(group, []).append(
                        (index_x, index_y, os.path.join(root, file))
                    )
                except ValueError:
                    continue

    if not npy_tiles:
        print("未找到npy数据！")
        return

    for zoom_level in npy_tiles.keys():
        for npy_info in tqdm(zip(npy_tiles[zoom_level]), desc=f"Regenerate zoom-{zoom_level} PNG"):
            index_x, index_y, npy_file = npy_info[0]
            data = np.load(npy_file)
            norm_tile_data = normalize(data, statistic_dict, stretch_method=stretch_method)
            png_file = f"{png_dir}/{zoom_level}/{index_x}/{index_y}.png"
            Path(png_file).parent.mkdir(parents=True, exist_ok=True)
            array_to_png(norm_tile_data, png_file, cmap=cmap, customized_cmap=customized_cmap, selected_channels=selected_channels)




if __name__ == '__main__':
    data_dir = '/data/NDVI_full'
    npy_dir = os.path.join(data_dir, 'NPY')
    png_dir = os.path.join(data_dir, 'PNG_linear')
    selected_channels = []
    cmap = "Greens"
    customized_cmap = None
    stretch_method = "linear-stretch"
    print(f"Stretching method: {stretch_method}")
    statistic_json = load_json(os.path.join(data_dir, "statistics.json"))
    regenerate_png(npy_dir, png_dir, statistic_json, stretch_method=stretch_method, selected_channels=selected_channels, cmap=cmap, customized_cmap=customized_cmap)

    # Validate
    plot_tiles_recursive(data_dir=png_dir, output_dir=os.path.join(data_dir, stretch_method))

