在MongoDB的bin目录下，输入代码
```
mongoexport -h ip和端口 -d 库名 -c 表名 -f 字段名 --type=csv -o ./文件名.csv
```
可以将存储在MongoDB中的数据输出为csv文件！

房天下爬虫一共有两张表，分别是EsfHouse （二手房信息）、NewHouse （新房信息）

结果：

百度云盘：链接：https://pan.baidu.com/s/1sZJFSXsBm9iWs9x0y_rxdg 密码：h2ut

项目启动文件：start.py

```
Master端：

redis-cli > lpush sfwSpider:start_urls http://www.fang.com/SoufunFamily.htm

```