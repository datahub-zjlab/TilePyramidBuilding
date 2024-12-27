from utils import get_all_files, upload_object_to_oss
from config_save import geocloud_bucket, center_bucket
import os
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

def upload_files(bucket, oss_url, upload_file):
    normalized_path = os.path.normpath(upload_file)
    parts = normalized_path.split(os.sep)
    current_level = parts[-3]  # 倒数第3层是 current_level
    index_x = parts[-2]  # 倒数第2层是 index_x
    index_y = parts[-1].replace('.png', '')  # 文件名部分是 index_y

    oss_upload_file = os.path.join(oss_url, current_level, index_x, index_y) + '.png'
    upload_object_to_oss(bucket, oss_upload_file, normalized_path, overwrite=overwrite_oss)


if __name__ == '__main__':
    png_dir = 'Data/GHS-V_0/PNG'
    png_list = get_all_files(png_dir, suffix='png')
    overwrite_oss = True
    # oss_upload_url = 'aster_functional_group/GlobalDatasets/Aster-GEDV3_NDVI/NPY/'
    oss_upload_url = 'earth/tiles/72'
    for png_path in tqdm(png_list):
        upload_files(geocloud_bucket, oss_upload_url, png_path)

    print(f"Upload to OSS {oss_upload_url} OK, overwrite is {overwrite_oss}")




# def upload_files(bucket, oss_url, upload_file):
#     try:
#         normalized_path = os.path.normpath(upload_file)
#         parts = normalized_path.split(os.sep)
#         current_level = parts[-3]  # 倒数第3层是 current_level
#         index_x = parts[-2]  # 倒数第2层是 index_x
#         index_y = parts[-1].replace('.png', '')  # 文件名部分是 index_y
#
#         oss_upload_file = os.path.join(oss_url, current_level, index_x, index_y) + '.png'
#         upload_object_to_oss(bucket, oss_upload_file, normalized_path, overwrite=overwrite_oss)
#         return upload_file, True  # 返回文件名和成功标志
#     except Exception as e:
#         print(f"Failed to upload {upload_file}: {e}")
#         return upload_file, False  # 返回文件名和失败标志
#
#
# if __name__ == '__main__':
#     png_dir = '/data/NDVI_full/PNG(0,100)'
#     png_list = get_all_files(png_dir, suffix='png')
#     overwrite_oss = True
#     oss_upload_url = 'earth/tiles/60'
#
#     progress_bar = tqdm(total=len(png_list), desc="Upload to OSS")
#     completed_tasks = [0]  # 使用列表来记录已完成任务数量，初始值设为0
#
#     def update_progress_bar(future):
#         current_completed = completed_tasks[0]
#         future.result()  # 触发可能存在的异常（如果有异常会在这里抛出）
#         completed_tasks[0] = current_completed + 1
#         progress_bar.update(1)
#
#     # 创建一个上下文管理器来处理进程池
#     with ProcessPoolExecutor(max_workers=16) as executor:
#         futures = [executor.submit(upload_files, geocloud_bucket, oss_upload_url, os.path.join(png_dir, png_path))
#                    for png_path in png_list]
#         for future in futures:
#             future.add_done_callback(update_progress_bar)
#
#     # 确保进度条关闭
#     progress_bar.close()
#     print(f"Upload to OSS {oss_upload_url} OK, overwrite is {overwrite_oss}")