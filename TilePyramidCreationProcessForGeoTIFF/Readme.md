# 遥感数据切瓦片Pipeline

## 使用说明
### 1. 配置环境:
新建python=3.9的conda环境，再安装相关依赖

`pip install -r requirements.txt`

注意，onda=3.6.2 使用pip可能安装失败，可以尝试使用conda install进行安装

安装aster_core工具包到当前目录：
请参考 https://github.com/datahub-zjlab/AsterL1T_SWIR-VNIR_pipeline

### 2. 配置OSS服务器

在config_save.py里面配置你要用到的oss bucket，方便下载和上传

### 3. 获取数据和数据列表

(1) 如果数据存储在OSS，需要先爬到数据列表，可以先使用get_filelist.py，对指定oss路径下的指定后缀(suffix)进行遍历，获取数据列表，
再使用download_files.py，根据数据列表对进行下载；数据列表存储为txt格式，在主程序也需要使用；

(2) 如果数据存储在本地，则直接使用os.listdir()获取数据列表即可。

### 4. 主程序(Process_Pipeline)：切瓦片
在运行主程序之前，你需要通过阅读数据文档得到以下信息：

(1) 数据格式：目前仅支持 GeoTIFF、H5；

(2) 数据的投影坐标系：一般数据的主流存储方式为WGS84(=epsg4326)；如果是以UTM存储，需要查找对应的epsg坐标，分区处理；

(3) 数据分辨率以及对应的最大瓦片分级：请参考[语雀文档](https://mkxzg8.yuque.com/hoq002/nqhq6v/zo7c4yqmkqessd8p)；

(4) 数据的nodata存储值：图像数据通常在没有采集数据的位置填放一个nodata值，nodata值通常为负值；

(5) 数据的通道：TIFF数据支持多通道图像，而瓦片只能展示三通道结果，若数据大于三通道，请先确定需要展示RGB三通道序号；

(6) 数据的物理意义：方便标准化处理，例如城市人口数据集中的负值一般为nodata值或者异常值，可以在标准化时去除；

如果是需要对GeoTIFF进行切片，则打开Process_pipeline_tiff2png.py，并按注释填写超参信息，运行脚本；若为H5数据，还需根据H5数据的包头字段，对数据子集进行拆分，拆分方法写在了utils.read_h5_data；

### 5. 可视化调色
调色过程非常重要且繁琐。调色过程包括标准化方法的调整和色卡的调整。

(1) 标准化：代码运行后会在目标文件目录生成statistic.json，包含所有切片的平均统计信息和各切片单独的统计信息，请根据这些信息，在utils.normalize中调整你的标准化方法，例如调整截断点(min_value, max_value)、拉伸方法(线性拉伸、高斯拉伸、log拉伸、Gamma拉伸等)；

(2) 色卡：在color_config.py中自定义你的色卡，如果是线性变换，可以直接调整start_color和end_color，通过实例属性调用，赋值给主函数中的变量customized_color；

调整完毕后单独运行Regenerate_png.py，在新的目录生成PNG瓦片和可视化拼接结果。

### 6. 上传到oss

使用upload_files.py向指定oss目录上传瓦片目录中所有png文件，同时也可以备份未归一化切片结果(.npy)；

## 一些已知风险

全球一张TIFF时进行处理时会出现未知错误，导致切片数量严重不足，亲测可以先将脚本运行到函数tiff2tiles之后，检查TILES文件是否正确，再将TILES文件目录作为主函数遍历目标，重新运行切片脚本，注意TILES的坐标系为epsg:3857。

## 一些Tips

(1) 由于数据种类丰富，很容易出现需要二次开发的情况，当数据量较大时可以将tile_size增大、max_zoom减小来加快调试过程，同时尽量不要去动aster_core内部代码。

(2) Log文件只记录实验基本信息和报错信息

