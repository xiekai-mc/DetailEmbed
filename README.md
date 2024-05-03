# DetailEmbed
DetailEmbed 是一个软件项目，旨在无缝地将较小的局部图像嵌入到的低分辨率的完整图像中。通过使用高清的局部图像，DetailEmbed 可以增强完整图像的局部清晰度。

## 例子
- 低分辨率的大图
  
![alt text](images/Low-resolution.png)

- 高分辨率的局部小图
  
![alt text](images/Deformed-high-resolution-partial.png)   
![alt text](images/High-resolution-partial2.png)

- 处理后的结果
  
（带黑边）

![alt text](images/out-keep-edge.png) 

（不带黑边）

![alt text](images/out.png)

## 依赖
- OpenCV (cv2)
- NumPy (numpy)
- PyQt5 (for GUI)

## 用法
### GUI
#### 打开主图片
  
![alt text](images/1.png)

#### 打开要嵌入的图片
  
![alt text](images/2.png)

#### 使用鼠标左键拖动，滚轮调整大小以完全覆盖要主图片对应区域

![alt text](images/3.png)

#### 点击嵌入按钮后可继续嵌入或保存 
 
![alt text](images/4.png)

### `embed_images_to_large_image`函数
#### 参数

`big_image_path`: 大图的路径，要将小图嵌入其中。

`small_image_paths`: 要嵌入的小图的路径列表。

`params`: `EmbedParams`类，用于设置其他参数设置。
#### 输出
该函数返回嵌入了小图的大图。
#### 示例
```python
from src import EmbedParams, embed_images_to_large_image


big_image_path = "images/Low-resolution.png"
small_image_paths = [
    "images/Deformed-high-resolution-partial.png",
    "images/High-resolution-partial2.png",
]
out_image = embed_images_to_large_image(
    big_image_path, small_image_paths, EmbedParams(
        small_edge_cut=0, corrosion=1, use_corner_matching=True)
)


```