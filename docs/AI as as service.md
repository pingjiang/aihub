# 使用Docker实现AI as a service

在AI测试平台项目中需要一些AI能力来辅助数据标注，因为网络安全等因素无法使用公司外商业公司提供的AI服务，公司自研的AI服务需要还不完善，很多能力都没有。所以尝试使用开源的AI框架和训练好的模型，封装为服务后使用。

将AI模型封装为服务的基本要求：

1. 实现人脸关键点检测，包括5个和68个点；
2. 实现图像分割和图像语义分割。为了实现精细的图像分割，还需要一些抠图算法支持；
3. 实现骨骼关键点检测（目前是14个点检测）；
4. 实现图片和视频分类；
5. 实现OCR识别；
6. 接口能够接受一个图片，然后给一个结果。对于人脸和骨骼关键点的检测的情况可能会出现多个对象；
7. 每个接口提供一个服务，定义一个通用的请求参数和响应结果的格式，便于客户端消费；
8. 服务易于部署和扩展；
9. 服务实现请求的访问日志的记录，以及接口性能的统计；
10. 服务易于开发和调试，提供错误日志，便于问题定位；

## 技术架构选型

* 选择python作为主要的开发语言。因为大多数的AI模型都是使用python开发，而且python属于动态语言，比较灵活，就我个人而言，擅长JavaScript开发，对于python也能够快速上手；
* 选择Docker部署服务，解决不同模型的环境依赖；

## 服务的系统设计

### aihub_gateway

接口网关，可以注册多个服务，每个服务使用轮询的方式实现负载均衡；

### aihub_serve

通用接口服务，定义了统一的请求和响应的格式，能够动态加载AI服务。每个服务只需要实现初始化和请求处理2个接口即可加载使用。使用jsonpath实现模型返回结果和接口返回结果的transformer变换；

请求消息格式：

```json
{
	"image_base64": "/9j/4AAQSkZ",
	"use_dlib": true,
	"transformer": {"content":{"objects":["$",{"location":"$.location","feature_point_face_68":["$.faces",{"x":"$[0]","y":"$[1]"}]}]}}
}
```

注意：

1. 所有请求参数中的包含image_base64的参数名称都会约定为base64格式的图片格式，会保存为本地图片，然后传递到模型去处理。
2. transformer的用法可以参考 [https://github.com/innovationgarage/python-jsonpath-object-transform](https://github.com/innovationgarage/python-jsonpath-object-transform) 来定义。最关键的是需要知道`$`表示当前处理值的根节点，数组的变换参考上述用法即可。
3. 所有的body参数在服务的处理函数中可以使用。不同的服务可以使用不同的参数，服务自己完成对参数的校验。

响应的消息格式：

```json
{
    "code": 0,
    "data": {
        "content": {
            "objects": [
                {
                    "feature_point_face_68": [
                        {
                            "x": 97,
                            "y": 359
                        }, ...
                    ],
                    "location": {
                        "height": 446,
                        "width": 446,
                        "x": 39,
                        "y": 237
                    }
                }
            ]
        }
    },
    "elapsed": 2806,
    "msg": "success"
}
```

### services/xxx/xxx/service.py

每个模型的服务定义一个Service类，并实现init和handle方法

```python
class Service:
	def init(self, base_path, config={}):
		"""初始化模型
		base_path 模型的根路径
		config 请求参数
		"""
		pass

	def handle(self, data, request=None):
		"""使用模型处理
		data 请求参数，可以获取图片路径
		request 可以获取额外请求参数，可以读取.json, .args, .form等dict类型的值，需要自己判断空的情况"""
		pass
```

注意：

1. services/xxx是一个标准的python的库，使用requirements.txt管理依赖，setup.py实现自动构建和部署。只有部署到系统中后才可以被aihub_serve动态加载运行。
2. 一般services/xxx下面是xxx/{__init__.py, service.py}文件；

## 开源模型

### 人脸检测


* 每个接口的实现和对应的模型作为一个
目前主流的AI框架有Tensorflow, Torch, Caffe等不同框架下面训练出来的模型的使用方法都不一样，有些相同的框架下训练出来的模型，也因为缺乏统一的接口等，使用起来也是不一样的。而且不同的框架运行环境都有很多的依赖和要求，如果使用传统的方式实现，是无法实现自动化按需部署的。

为了便于快速开发一个新的服务，这里做了一系列的约定和统一的封装。