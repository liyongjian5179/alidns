# 命令行解析阿里云 DNS

首先需要获取阿里云账号账号的`AccessKeyID`及`AccessKeySecret`，并将其替换至 `alidns.py` 文件中

然后安装阿里云的接口

```bash
pip3 install aliyun-python-sdk-core-v3
```

使用说明：

```bash
[root@lyj]# ./alidns.py -h
usage: alidns.py [-h] [-a | -d | -u | -g]
                 RR TYPE ADDRESS [RR TYPE ADDRESS ...]

针对 xxx.com 域名记录进行相关操作

positional arguments:
  RR TYPE ADDRESS  记录 类型 地址

optional arguments:
  -h, --help       show this help message and exit
  -a, --add        add domain record. (e.g. --add RR TYPE ADDRESS)
  -d, --delete     delete domain record. (e.g. --delete RR)
  -u, --update     update domain record. (e.g. --update RR TYPE ADDRESS)
  -g, --get        get record ip. (e.g. --get RR)
```

e.g.

增加解析 `./alidns.py -a www A x.x.x.x`

更新解析 `./alidns.py -u www A x.x.x.x`

获取解析 `./alidns.py -g www`

删除解析 `./alidns.py -d www`

- [阿里云DNS解析API文档](https://help.aliyun.com/document_detail/29739.html?spm=a2c4g.11186623.6.584.8Yriq8)

