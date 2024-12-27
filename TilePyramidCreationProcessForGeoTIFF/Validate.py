import os
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np


def plot_tiles_recursive(data_dir, target_group=None, output_dir=None):
    """
    递归搜索瓦片数据并按第二层级拼接生成多张完整的图。路径格式为 data_dir/group/index_x/index_y.png。

    :param data_dir: 瓦片数据的根目录
    :param output_dir: 输出拼接图的目录。
    """
    # 存储每个组的瓦片信息
    group_tiles = {}

    # 递归查找符合结构的文件
    for root, _, files in os.walk(data_dir):
        # 获取当前目录的 group 和 index_x
        rel_path = os.path.relpath(root, data_dir)
        parts = rel_path.split(os.sep)

        if len(parts) < 2:
            continue  # 跳过没有足够层级的目录

        try:
            group = int(parts[0])  # 第二层级 group
            index_x = int(parts[1])  # index_x
        except ValueError:
            continue  # 跳过非数字目录

        for file in files:
            print(group, index_x)
            if target_group:
                if group != target_group:
                    continue
            if file.endswith('.png'):
                try:
                    # 提取文件名中的 index_y
                    index_y = int(file.replace('.png', ''))
                    group_tiles.setdefault(group, []).append(
                        (index_x, index_y, os.path.join(root, file))
                    )
                except ValueError:
                    continue

    # if not group_tiles:
    #     print("未找到瓦片数据！")
    #     return

    # 对每个组生成完整拼接图
    for group, tile_positions in group_tiles.items():

        # 确定瓦片的网格范围
        min_x = min(pos[0] for pos in tile_positions)
        max_x = max(pos[0] for pos in tile_positions)
        min_y = min(pos[1] for pos in tile_positions)
        max_y = max(pos[1] for pos in tile_positions)

        # 计算完整图像的大小
        tile_size = 256
        full_width = (max_x - min_x + 1) * tile_size
        full_height = (max_y - min_y + 1) * tile_size

        # 初始化空白大图
        full_image = np.zeros((full_height, full_width, 4), dtype=np.uint8)

        # 将瓦片放入对应的位置
        for index_x, index_y, tile_path in tile_positions:
            tile_image = Image.open(tile_path).convert("RGBA")  # 确保图像是 RGBA 格式
            tile_array = np.array(tile_image)

            x_offset = (index_x - min_x) * tile_size
            y_offset = (index_y - min_y) * tile_size

            # 使用透明度进行混合
            alpha = tile_array[:, :, 3] / 255.0  # 归一化的透明度通道
            for c in range(4):  # 对 RGBA 四个通道逐一处理
                full_image[y_offset:y_offset + tile_size, x_offset:x_offset + tile_size, c] = (
                        full_image[y_offset:y_offset + tile_size, x_offset:x_offset + tile_size, c] * (1 - alpha)
                        + tile_array[:, :, c] * alpha
                )

        # 绘制完整的大图
        plt.figure(figsize=(10, 10))
        plt.imshow(full_image)
        plt.axis('off')
        plt.tight_layout()

        # 保存或显示
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"zoom-{group}.png")
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"zoom-{group} 的拼接图保存到: {output_file}")
        else:
            plt.title(f"zoom-{group}")
            plt.show()
        plt.close()
if __name__ == '__main__':
    # 示例用法
    data_dir = "/home/data2/ASTWBD/PNG"

    plot_tiles_recursive(data_dir, target_group=12, output_dir="/home/data2/ASTWBD/Zoom12_Plot")
