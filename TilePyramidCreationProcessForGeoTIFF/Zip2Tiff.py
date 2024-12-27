import zipfile
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor


def unzip_file(zip_file, extract_to):
    '''
    多线程解压缩方法

    Args:
        zip_file: 待解压缩文件地址
        extract_to: 解压缩目的目录
    Returns:

    '''
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return zip_file, True  # 返回文件名和成功标志
    except Exception as e:
        print(f"Failed to unzip {zip_file}: {e}")
        return zip_file, False  # 返回文件名和失败标志


if __name__ == '__main__':
    data_dir = '/home/data2/ASTWBD/'
    tiff_dir = '/home/data2/ASTWBD_TIFF/'
    os.makedirs(tiff_dir, exist_ok=True)
    fn_list = os.listdir(data_dir)

    # 创建进度条
    progress_bar = tqdm(total=len(fn_list), desc='Unzip ASTWBD')

    # 更新进度条的函数
    def update_progress_bar(_):
        progress_bar.update(1)

    # 创建一个上下文管理器来处理线程池
    with ThreadPoolExecutor(max_workers=16) as executor:
        # 提交解压缩任务并设置回调函数实时更新进度条
        futures = [executor.submit(unzip_file, os.path.join(data_dir, fn), tiff_dir) for fn in fn_list]
        for future in futures:
            future.add_done_callback(update_progress_bar)

    # 确保进度条关闭
    progress_bar.close()
