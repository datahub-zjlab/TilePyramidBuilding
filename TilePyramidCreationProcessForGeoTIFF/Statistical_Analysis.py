from utils import load_json, save_json, get_dataset_name
import os
import numpy as np


def statistical_analysis(data_dir, npy_dir, max_zoom=None, sds_name=None, contact_info="", nodata_value=None):
    '''
    遍历npy文件最大瓦片级数, 得到图像像素的统计信息, 归一化时使用。统计信息包括:
    --max, 最大值
    --min, 最小值
    --mean, 平均值
    --std, 标准差
    --02%, 从小到大排列, 2%的截断点
    --98%, 从小到大排列, 98%的截断点
    --25%, 从小到大排列, 25%的截断点
    --75%, 从小到大排列, 75%的截断点

    注意: 该函数按通道来进行计算, 因此三通道的npy文件会得到例如: max=[1,5,10], 表示三个通道分别最大值
    Args:
        data_dir: 输出数据存储主目录
        npy_dir:  输出数据NPY文件存储目录
        max_zoom: 最大瓦片等级
        sds_name: 数据集名称
        contact_info: 数据集处理人员
        nodata_value: Nodata值

    Returns:
        statistic_dict: 统计值字典，包含总体统计信息和各瓦片(npy)的统计信息

    '''
    json_file = os.path.join(data_dir, f'merged_base_tile_index_list_zoom-{max_zoom}.json')
    tile_dict_list = load_json(json_file)
    statistic_dict = {}
    statistic_dict["dataset_name"] = get_dataset_name(sds_name)
    statistic_dict["contact"] = contact_info
    statistic_dict["nums"] = len(tile_dict_list)  # 瓦片数量
    statistic_dict["npy_dir"] = npy_dir
    statistic_dict["max_zoom"] = max_zoom

    _max_list, _min_list, _mean_list, _std_list = [], [], [], []
    _25_list, _75_list, _02_list, _98_list = [], [], [], []
    statis_dict_list = []
    for tile_dict in tile_dict_list:
        _max, _min, _mean, _std = [], [], [], []
        _25, _75, _02, _98 = [], [], [], []
        statis_dict = {}

        for key, value in tile_dict.items():
            tile_data = np.load(value['data_dir'])[:, :, :-1]
            statis_dict[key] = {}
            tile_data[tile_data == nodata_value] = 0

            for n in range(tile_data.shape[-1]):
                # 获取非零值的掩码
                non_zero_values = tile_data[:, :, n][tile_data[:, :, n] != 0]

                # 只有当非零值存在时才计算统计值
                if non_zero_values.size > 0:
                    _max.append(np.max(non_zero_values))
                    _min.append(np.min(non_zero_values))
                    _mean.append(np.mean(non_zero_values))
                    _std.append(np.std(non_zero_values))

                    _25.append(np.percentile(non_zero_values, 25))
                    _75.append(np.percentile(non_zero_values, 75))
                    _02.append(np.percentile(non_zero_values, 2))
                    _98.append(np.percentile(non_zero_values, 98))
                else:
                    # 如果没有非零值，填充默认值，例如 np.nan 或 0
                    _max.append(0)
                    _min.append(0)
                    _mean.append(0)
                    _std.append(0)
                    _25.append(0)
                    _75.append(0)
                    _02.append(0)
                    _98.append(0)

            statis_dict[key]['data_dir'] = value['data_dir']
            statis_dict[key]['current_index'] = value['current_index']
            statis_dict[key]['current_level'] = value['current_level']

            statis_dict[key]['max'] = _max
            statis_dict[key]['min'] = _min
            statis_dict[key]['mean'] = _mean
            statis_dict[key]['std'] = _std
            statis_dict[key]['75%'] = _75
            statis_dict[key]['25%'] = _25
            statis_dict[key]['98%'] = _98
            statis_dict[key]['02%'] = _02

        statis_dict_list.append(statis_dict)

        _max_list.append(_max)
        _min_list.append(_min)
        _mean_list.append(_mean)
        _std_list.append(_std)
        _25_list.append(_25)
        _75_list.append(_75)
        _02_list.append(_02)
        _98_list.append(_98)

    statistic_dict["mean"] = list(np.mean(_mean_list, axis=0))
    statistic_dict["std"] = list(np.mean(_std_list, axis=0))
    statistic_dict["max"] = list(np.max(_max_list, axis=0))
    statistic_dict["min"] = list(np.min(_min_list, axis=0))
    statistic_dict["75%"] = list(np.median(_75_list, axis=0))
    statistic_dict["25%"] = list(np.median(_25_list, axis=0))
    statistic_dict["98%"] = list(np.median(_98_list, axis=0))
    statistic_dict["02%"] = list(np.median(_02_list, axis=0))

    statistic_dict["statistics"] = statis_dict_list

    save_json(statistic_dict, os.path.join(data_dir, "statistics.json"))
    return statistic_dict


if __name__ == '__main__':
    data_dir = '../Data/NDVI/'
    npy_dir = '../Data/NDVI/NPY/'

    json_file = os.path.join(data_dir, 'merged_base_tile_index_list.json')
    tile_dict_list = load_json(json_file)
    nodata_value = -32760
    statistic_dict = statistical_analysis(data_dir=data_dir, npy_dir=npy_dir, max_zoom=9, sds_name="NDVI Mean",
                                          nodata_value=nodata_value)
    print(statistic_dict["mean"])