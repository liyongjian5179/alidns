# 命令行解析阿里云 DNS

支持列出账号下的所有域名，并对任意一个域名的解析记录进行增删改查。

## 安装依赖

```bash
pip3 install alibabacloud-alidns20150109 alibabacloud-tea-openapi
```

## 配置凭证

推荐使用环境变量（避免把 AccessKey 写进代码）：

```bash
export ALIYUN_AK=your_access_key_id
export ALIYUN_SK=your_access_key_secret
```

也可以直接修改 `aliyun.py` 中的 `ACCESS_KEY_ID` / `ACCESS_KEY_SECRET` 占位符，
并把 `DEFAULT_DOMAIN` 改为你常用的域名。

## 使用说明

```bash
[root@lyj]# ./aliyun.py -h
usage: aliyun.py [-h] [--domain DOMAIN] [--json] [-l | -L | -a | -d | -u | -g] [ARG ...]

阿里云云解析 DNS 操作脚本（支持账号下多域名）

positional arguments:
  ARG              记录参数：RR [TYPE ADDRESS]（--list 时无需参数）

options:
  -h, --help       show this help message and exit
  --domain DOMAIN  指定操作的域名（默认 example.com；不指定且执行 a/d/u/g/L 时进入交互选择）
  --json           以 JSON 格式输出（配合 --records 使用）
  -l, --list       列出账号下所有域名
  -L, --records    列出指定域名下所有解析记录
  -a, --add        新增记录 (--add RR TYPE ADDRESS)
  -d, --delete     删除记录 (--delete RR)
  -u, --update     修改记录 (--update RR TYPE ADDRESS)
  -g, --get        查询记录 IP (--get RR)
```

e.g.

列出账号下所有域名 `./aliyun.py --list`

列出某域名所有解析 `./aliyun.py --domain example.com -L`

列出某域名所有解析（JSON）`./aliyun.py --domain example.com -L --json`

增加解析 `./aliyun.py --domain example.com -a www A x.x.x.x`

更新解析 `./aliyun.py --domain example.com -u www A x.x.x.x`

获取解析 `./aliyun.py --domain example.com -g www`

删除解析 `./aliyun.py --domain example.com -d www`

不带 `--domain` 执行 `-a/-d/-u/-g/-L` 时，会先列出账号下所有域名，让你输入编号选择要操作的域名。

- [阿里云DNS解析API文档](https://help.aliyun.com/zh/dns/api-alidns-2015-01-09-overview)
