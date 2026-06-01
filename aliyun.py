#!/usr/bin/env python3
# coding=utf-8
# liyongjian5179@163.com
#
# 阿里云云解析 DNS 操作脚本（支持账号下多域名）
# 依赖新版 SDK：
#   pip3 install alibabacloud-alidns20150109 alibabacloud-tea-openapi
#
# 凭证读取顺序：环境变量 ALIYUN_AK / ALIYUN_SK > 脚本内占位符
#   export ALIYUN_AK=your_access_key_id
#   export ALIYUN_SK=your_access_key_secret
#
# 用法示例：
#   列出账号下所有域名：           aliyun.py --list
#   查询某域名某条记录：           aliyun.py --domain example.com -g www
#   新增记录：                     aliyun.py --domain example.com -a www A 1.2.3.4
#   修改记录：                     aliyun.py --domain example.com -u www A 1.2.3.4
#   删除记录：                     aliyun.py --domain example.com -d www
#   不带 --domain 执行 a/d/u/g：   交互式从域名列表中选择

import os
import sys
import json
import argparse

from alibabacloud_alidns20150109.client import Client as AlidnsClient
from alibabacloud_alidns20150109 import models as alidns_models
from alibabacloud_tea_openapi import models as open_api_models
from Tea.exceptions import TeaException

# 凭证：优先环境变量，回退到占位符（请替换为你自己的 AccessKey 或使用环境变量）
ACCESS_KEY_ID = os.environ.get('ALIYUN_AK', 'AccessKeyID')
ACCESS_KEY_SECRET = os.environ.get('ALIYUN_SK', 'AccessKeySecret')
ENDPOINT = 'alidns.cn-hangzhou.aliyuncs.com'

# 默认域名（不传 --domain 且非交互时使用），请替换为你自己的域名
DEFAULT_DOMAIN = 'example.com'


def create_client():
    config = open_api_models.Config(
        access_key_id=ACCESS_KEY_ID,
        access_key_secret=ACCESS_KEY_SECRET,
    )
    config.endpoint = ENDPOINT
    return AlidnsClient(config)


def list_domains(client):
    """列出账号下所有域名（分页），返回域名字符串列表。"""
    domains = []
    page_number = 1
    page_size = 100
    while True:
        req = alidns_models.DescribeDomainsRequest(
            page_number=page_number,
            page_size=page_size,
        )
        resp = client.describe_domains(req)
        body = resp.body
        batch = body.domains.domain if body.domains else []
        for d in batch:
            domains.append(d.domain_name)
        total = body.total_count or 0
        if page_number * page_size >= total:
            break
        page_number += 1
    return domains


def print_domains(client):
    domains = list_domains(client)
    if not domains:
        print('账号下没有域名。')
        return
    print(f'账号下共 {len(domains)} 个域名：')
    for i, name in enumerate(domains, 1):
        print(f'  [{i}] {name}')


def choose_domain(client):
    """交互式选择域名，返回选中的域名字符串。"""
    domains = list_domains(client)
    if not domains:
        print('账号下没有域名，无法操作。')
        sys.exit(1)
    print('请选择要操作的域名：')
    for i, name in enumerate(domains, 1):
        print(f'  [{i}] {name}')
    while True:
        choice = input(f'输入编号 (1-{len(domains)}): ').strip()
        if choice.isdigit() and 1 <= int(choice) <= len(domains):
            return domains[int(choice) - 1]
        print('输入无效，请重新输入。')


def add_domain_record(client, domain_name, rr, add_type, address):
    req = alidns_models.AddDomainRecordRequest(
        domain_name=domain_name,
        rr=rr,
        type=add_type,
        value=address,
        ttl=600,
        line='default',
    )
    resp = client.add_domain_record(req)
    print(f'新增成功：RecordId={resp.body.record_id}, RequestId={resp.body.request_id}')


def get_record_id(client, domain_name, rr):
    """通过子域名查询第一条记录的 RecordId。"""
    sub_domain = rr + '.' + domain_name
    req = alidns_models.DescribeSubDomainRecordsRequest(sub_domain=sub_domain)
    resp = client.describe_sub_domain_records(req)
    records = resp.body.domain_records.record if resp.body.domain_records else []
    if not records:
        print(f'未找到记录：{sub_domain}')
        sys.exit(1)
    return records[0].record_id


def fetch_all_records(client, domain_name):
    """获取域名下所有解析记录（自动翻页），返回记录对象列表。"""
    records = []
    page_number = 1
    page_size = 500
    while True:
        req = alidns_models.DescribeDomainRecordsRequest(
            domain_name=domain_name,
            page_number=page_number,
            page_size=page_size,
        )
        resp = client.describe_domain_records(req)
        body = resp.body
        batch = body.domain_records.record if body.domain_records else []
        records.extend(batch)
        total = body.total_count or 0
        if page_number * page_size >= total:
            break
        page_number += 1
    return records


def get_ip_address(client, domain_name, rr):
    records = fetch_all_records(client, domain_name)
    found = False
    for item in records:
        if item.rr == rr:
            print(f'{item.rr}.{domain_name}  {item.type}  {item.value}')
            found = True
    if not found:
        print(f'未找到记录：{rr}.{domain_name}')


def list_records(client, domain_name, as_json=False):
    """列出域名下所有解析记录（表格或 JSON）。"""
    records = fetch_all_records(client, domain_name)
    if as_json:
        data = [
            {
                'RecordId': r.record_id,
                'RR': r.rr,
                'Type': r.type,
                'Value': r.value,
                'TTL': r.ttl,
                'Line': r.line,
                'Status': r.status,
            }
            for r in records
        ]
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if not records:
        print(f'{domain_name} 下没有解析记录。')
        return
    print(f'{domain_name} 共 {len(records)} 条解析记录：')
    ordered = sorted(records, key=lambda x: (x.type or '', x.rr or ''))
    rr_w = max([len('RR')] + [len(r.rr or '') for r in ordered]) + 2
    val_w = max([len('Value')] + [len(r.value or '') for r in ordered]) + 2
    header = (
        f'{"RR":<{rr_w}}{"Type":<8}{"Value":<{val_w}}'
        f'{"TTL":<8}{"Line":<12}{"Status":<10}RecordId'
    )
    print(header)
    print('-' * len(header))
    for r in ordered:
        print(
            f'{(r.rr or ""):<{rr_w}}{(r.type or ""):<8}{(r.value or ""):<{val_w}}'
            f'{str(r.ttl or ""):<8}{(r.line or ""):<12}{(r.status or ""):<10}{r.record_id or ""}'
        )


def delete_domain_record(client, domain_name, rr):
    req = alidns_models.DeleteSubDomainRecordsRequest(
        domain_name=domain_name,
        rr=rr,
    )
    resp = client.delete_sub_domain_records(req)
    print(f'删除成功：RR={rr}, 删除条数={resp.body.total_count}, RequestId={resp.body.request_id}')


def update_domain_record(client, record_id, rr, update_type, address):
    req = alidns_models.UpdateDomainRecordRequest(
        record_id=record_id,
        rr=rr,
        type=update_type,
        value=address,
    )
    resp = client.update_domain_record(req)
    print(f'修改成功：RecordId={resp.body.record_id}, RequestId={resp.body.request_id}')


def main():
    parser = argparse.ArgumentParser(
        description='阿里云云解析 DNS 操作脚本（支持账号下多域名）',
    )
    parser.add_argument(
        'LIST', metavar='ARG', type=str, nargs='*',
        help='记录参数：RR [TYPE ADDRESS]（--list 时无需参数）',
    )
    parser.add_argument(
        '--domain', type=str, default=None,
        help=f'指定操作的域名（默认 {DEFAULT_DOMAIN}；不指定且执行 a/d/u/g/L 时进入交互选择）',
    )
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出（配合 --records 使用）')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--list', action='store_true', help='列出账号下所有域名')
    group.add_argument('-L', '--records', action='store_true', help='列出指定域名下所有解析记录')
    group.add_argument('-a', '--add', action='store_true', help='新增记录 (--add RR TYPE ADDRESS)')
    group.add_argument('-d', '--delete', action='store_true', help='删除记录 (--delete RR)')
    group.add_argument('-u', '--update', action='store_true', help='修改记录 (--update RR TYPE ADDRESS)')
    group.add_argument('-g', '--get', action='store_true', help='查询记录 IP (--get RR)')

    args = parser.parse_args()
    client = create_client()

    try:
        if args.list:
            print_domains(client)
            return

        # 需要域名的操作：确定目标域名
        domain_name = DEFAULT_DOMAIN
        if args.add or args.delete or args.update or args.get or args.records:
            if args.domain:
                domain_name = args.domain
            elif sys.stdin.isatty():
                domain_name = choose_domain(client)
            # 非交互（脚本调用）-> 沿用默认域名 DEFAULT_DOMAIN

        if args.records:
            list_records(client, domain_name, as_json=args.json)

        elif args.add:
            if len(args.LIST) != 3:
                parser.error('--add 需要 3 个参数：RR TYPE ADDRESS')
            add_domain_record(client, domain_name, args.LIST[0], args.LIST[1], args.LIST[2])

        elif args.delete:
            if len(args.LIST) != 1:
                parser.error('--delete 需要 1 个参数：RR')
            delete_domain_record(client, domain_name, args.LIST[0])

        elif args.update:
            if len(args.LIST) != 3:
                parser.error('--update 需要 3 个参数：RR TYPE ADDRESS')
            rr, update_type, address = args.LIST[0], args.LIST[1], args.LIST[2]
            record_id = get_record_id(client, domain_name, rr)
            update_domain_record(client, record_id, rr, update_type, address)

        elif args.get:
            if len(args.LIST) != 1:
                parser.error('--get 需要 1 个参数：RR')
            get_ip_address(client, domain_name, args.LIST[0])

        else:
            parser.print_help()
            sys.exit(1)

    except TeaException as e:
        print(f'阿里云 API 调用失败：{e.code} - {e.message}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
