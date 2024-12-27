import os
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from config_save import download_bucket, aster_bucket
from utils import download_object_from_oss


def download_file(bucket, oss_url, download_file):
    '''
    多线程从oss下载数据
    Args:
        bucket: oss bucket
        oss_url: oss url
        download_file: 下载文件存储地址

    '''
    try:
        download_object_from_oss(bucket, oss_url, download_file)
        # print(f"Succeed to download {fn}")
        return download_file, True  # 返回文件名和成功标志
    except Exception as e:
        print(f"Failed to download {download_file}: {e}")
        return download_file, False  # 返回文件名和失败标志

if __name__ == '__main__':
    download_dir = '/home/data2/ASTWBD/'
    os.makedirs(download_dir, exist_ok=True)
    data_list_file = "Data/ASTWBD.txt"
    oss_download_url = 'ASTWBD/'

    with open(data_list_file, 'r', encoding='utf-8') as f:
        fn_list = [fn.strip() for fn in f.readlines()]

    progress_bar = tqdm(total=len(fn_list), desc="ASTWBD")

    # 使用列表来记录已完成任务数量，初始值设为0
    completed_tasks = [0]

    def update_progress_bar(future):
        # 获取列表中的值
        current_completed = completed_tasks[0]
        future.result()  # 触发可能存在的异常（如果有异常会在这里抛出）
        # 更新列表中的值，实现计数加1的效果
        completed_tasks[0] = current_completed + 1
        progress_bar.update(1)


    # 创建一个上下文管理器来处理进程池
    with ProcessPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(download_file, aster_bucket, os.path.join(oss_download_url, fn),
                                   os.path.join(download_dir, fn)) for fn in fn_list]

        for future in futures:
            future.add_done_callback(update_progress_bar)

    # 确保进度条关闭
    progress_bar.close()
