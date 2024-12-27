本代码旨在通过GEE导出geotif格式的全球图，然后按需切割成金字塔式瓦片。同时也适用于单张或者多张geotif格式其他来源图像。

1.GEE数据导出

参考mcd12q1，以modis土地覆盖数据为例，自定义导出数据类型，波段，地域范围，时间，分辨率，以及镶嵌方式等等。
导出数据需为EPSG：3857

2.色板设置

以modis土地覆盖数据为例，单波段调试板为
  palette: [
    '05450a', '086a10', '54a708', '78d203', '009900', 'c6b044', 'dcd159',
    'dade48', 'fbff13', 'b6ff05', '27ff87', 'c24f44', 'a5a5a5', 'ff6d4c',
    '69fff8', 'f9ffa4', '1c0dff'
  ]
  
  其他数据情况，需自行更改getTiles.py以及getTilesMulti.py中的map2RGB函数，完成调色。
  
3.建立金字塔

如果是单张geotif图，修改对应路径，以及设置瓦片等级maxscale，执行python getTiles.py；

如果是多张geotif图，修改对应路径，以及设置瓦片等级maxscale，执行python getTilesMulti.py；
