程序 `parser.py` 接受的参数形式如下：
usage: parser.py [-h] (-t | -i INPUT) [-o OUTPUT]
  -t, --test            使用样例程序测试语法分析器
  -i INPUT, --input INPUT
                        输入文件路径
  -o OUTPUT, --output OUTPUT
                        输出文件路径
一种样例测试方法如下：
在src目录下，运行python parser.py -t
输出结果为out文件夹下的同名json文件。