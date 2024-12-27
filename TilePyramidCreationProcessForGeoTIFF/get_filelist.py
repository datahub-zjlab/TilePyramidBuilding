from config_save import aster_bucket, geocloud_bucket, download_bucket

def count_files_with_suffix(bucket, oss_url, file_suffix):
    '''

    Args:
        bucket: oss bucket
        oss_url: oss url
        file_suffix: 指定读取文件后缀

    Returns:
        total_size: 文件集占用空间
        fn_list: 文件目录

    '''
    fn_list = []
    total_size = 0

    marker = None
    while True:
        result = bucket.list_objects(prefix=oss_url, marker=marker)

        a = result.object_list
        for item in a:
            if file_suffix:
                if item.key.split('.')[-1] == file_suffix:
                    fn_list.append(item.key.split('/')[-1])
                    total_size += item.size
                    # print(item.size)
            else:
                fn_list.append(item.key.split('/')[-1])
                total_size += item.size


        if not result.is_truncated:
            break

        marker = result.next_marker

    return total_size, fn_list


if __name__ == '__main__':
    oss_url = 'ASTWBD/'
    suffix = 'zip'
    total_size_bytes, file_list = count_files_with_suffix(aster_bucket, oss_url, suffix)
    print(f'File num: {len(file_list)}, total size: {total_size_bytes / (1024 ** 3)}GB')
    with open('Data/ASTWBD.txt', 'w', encoding='utf-8') as f:
        for fn in file_list:
            f.write(fn+'\n')
    f.close()
