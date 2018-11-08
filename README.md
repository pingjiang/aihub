# aihub
OSS AI models hub

设计方案：

1. 每个服务封装为一个docker，作为一个服务启动。使用jsonpath-object-transform处理结果格式。所有依赖都是一个docker命令；
  - 使用setup.py全局安装？
  - 使用配置指定模型？
  - 如何从请求中提取参数？
    + img图片使用base64还是文件？
    + transform格式？字段定义？
  - 如何封装一个独立的service文件，可以动态加载这个service文件，这样就不用重复开发了？
  - 如何调试dockerfile？
  

## fileinfo

启动服务：

```sh
docker run -it -p 5000:80 -v $(pwd)/userscripts:/userscripts aihub_fileinfo
```

测试请求：

```json
{
	"transformer": {"property":{"format":"$.format", "width": "$.width", "height": "$.height"}, "data": "$.data.entry"},
	"entry": "image_info",
	"url": "http://192.168.0.103:8080/assets/aflw-test.jpg"
}
```
