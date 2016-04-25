#Achilles

##TODO
+ Server端数据库，持久化
+ Client端
    * 目录猜解
    * 登录表单猜解
    * 命令执行
    * 文件包含

##Client端 - Achilles-Client
运行命令：
```
python run.py -h 监听地址 -p 端口  
```
依赖：
```
pip install zerorpc gevent lxml requests
```
说明： 
+ Client
    * 运行后会监听对应的地址端口，然后在服务器端配置对应地址，服务器会找到这个Client并且启动扫描器
    * 这个脚本运行后就不用关闭了，可以一直开着，服务器有新任务的时候就会来找这个Client，不过要注意，服务器启动的时候，这个Client必须已经启动了。
+ SQLMAP
    * 本例中自带的sqlmap是修改过的，见log信息
+ PhantomJS
    * 设计应该是跨平台的，所以有四个版本的phantomjs，分别命名为
        - Linux 32bit -- phantomjs-linux-x86
        - Linux 64bit -- phantomjs-linux-x64
        - Windows -- phantomjs-windows.exe
        - Mac OSX -- phantomjs-macosx
    * 程序会自己判断自己在哪个平台，然后执行对应的文件
    * 嫌体积太大的话，可以把多余的三个都删掉
+ 目前实现了
    * 爬虫、Robots.txt
    * SQL，XSS
    * 代理（在服务器端）

##Server - Achilles-Server
运行命令：
```
python manage.py runserver
```
依赖：
```
pip install django gevent zerorpc mitmproxy
```
说明：
+ Server
    * 上面的client在对应的机器上部署之后，再找一台机器部署Server，然后开启Server，本机就可以通过网页端访问Server，通过Server去控制Client，加上代理也实现在Server上，所以本机就可以一点压力都没有了。
    * 此外，Server和Client都可以长期开着，什么时候要扫了开网页就行。本机随便关。
+ 数据库
    *  还没有实现数据库，所有内容只是log出来，网页端也只是显示log，二次执行会覆盖
+  代理
    *  如果需要代理SSL的东西，要先装mitmproxy的证书，在thirdparty目录下，不然可能会报错吧
+ 配置
    *  Client地址为ip:addr形式，多个用'|'分开
    *  代理开启之后，注意是在Server上
    *  其他配置与之前相同
    *  提供视频一个 http://v.youku.com/v_show/id_XMTU0NjYwODAyMA==.html 密码 zxcvbnm