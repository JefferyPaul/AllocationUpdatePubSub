import os
import shutil
import json
import time
import sys
import pprint

# 设置项目目录
PATH_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(PATH_ROOT)
os.chdir(PATH_ROOT)
PATH_CONFIG = os.path.join(PATH_ROOT, 'Config', 'Config.json')
FILE_NAME = os.path.basename(__file__).replace('.py', '')


# 导入我的模块
from pkgs.logger import MyLogger
from pkgs.brokermini import SubscribeCSVData
from pkgs.allocation import BaseAllocation

"""
根据Allocation.csv 更改subscriberBM/Config/Subscribe.csv 中各Trader的Allocation

0 需要 完整的 _initSubscribe.csv 文件，用于记录全部 subscriber trader。
    因为更新后的 Subscribe.csv可能不包含全部trader。 （存放在subscriber的目录下, "Config//_initSubscribe.csv）
1 需要 mapping.csv:  PMTrader 和 PubTrader的对应表。  读取 mapping.csv -> dict[PubTrader] = PMTrader
2 需要 Allocation.csv: 各PMTrader的Allocation       读取 Allocation.csv -> dict[PMTrader] = mul
3 更改 Subscribe.csv: [SubTrader, PubTrader, mul]

"""


# 修改subscribe.csv
def update_subscribe_csv(path, d_trader_mapping: dict, d_allocation: dict):
    logger.info('Changing subscriber.csv: %s' % path)

    path_subscribe_csv = os.path.join(path, 'Config', 'Subscribe.csv')
    path_init_subscribe_csv = os.path.join(path, 'Config', '_initSubscribe.csv')
    if not os.path.exists(path_init_subscribe_csv):
        logger.info('不存在此文件 _initSubscribe.csv:\t%s' % path_init_subscribe_csv)
        raise FileExistsError

    # 读取 (init) 所有 sub - pub 对
    init_subscribe_obj: SubscribeCSVData = SubscribeCSVData.read_file(path=path_init_subscribe_csv)

    # 遍历所有 sub - pub 对
    # 在 d_allocation（Allocation.csv）中查找新Allocation
    new_subscribe_lines = []
    for (subscribe_sub, subscribe_pub, _)in init_subscribe_obj:
        # 查找 pub trader 的 Allocation
        if subscribe_pub in d_trader_mapping.keys():
            # 通过 实盘publisher名字，根据d_trader_mapping 查找对应 pm_trader_name
            pm_trader_name = d_trader_mapping[subscribe_pub]
            if pm_trader_name in d_allocation.keys():
                new_mul = d_allocation[pm_trader_name]
            else:
                new_mul = 0
        else:
            # 如果 d_trader_mapping中不存在此 publisher_trader名字
            logger.error('【!】此Publisher_trader出现在subscribe.csv但不存在于Mapping.csv中： %s' % subscribe_pub)
            raise FileExistsError
        # 新数据行
        new_subscribe_lines.append([subscribe_sub, subscribe_pub, new_mul])

    # 写新的subscriber.csv 并 备份
    os.remove(path_subscribe_csv)
    new_subscribe_obj = SubscribeCSVData(new_subscribe_lines)
    new_subscribe_obj.write(path=path_subscribe_csv)
    # 备份
    path_subscribe_csv_bak_new = os.path.join(path, 'Config', 'Subscribe_%s.csv.bak' % time.strftime('%Y%m%d_%H%M%S'))
    shutil.copyfile(src=path_subscribe_csv, dst=path_subscribe_csv_bak_new)


# 读取mapping
# d_trader_mapping = {publisher_trader_name: pm_trader_name, }
def read_mapping(path) -> dict:
    d_trader_mapping = {}
    logger.info('Reading Trader Mapping')
    with open(path) as f:
        l_live_trader_name = []
        l_pm_trader_name = []
        for line in f.readlines():
            line = line.strip()
            line = line.replace('\n', '')
            if line == '':
                continue

            line_split = line.split(',')
            if len(line_split) < 2:
                logger.warning('Wrong allocation line: %s' % line)
                continue
            live_trader_name = line_split[0].replace('.csv', '')
            pm_trader_name = line_split[1].replace('.csv', '')

            # LivePubTrader 只会对应 一个 PMTrrader，所以需要检查
            if live_trader_name in l_live_trader_name:
                logger.warning('Wrong mapping line, same LivePub trader name, %s' % live_trader_name)
            else:
                l_live_trader_name.append(live_trader_name)
                d_trader_mapping[live_trader_name] = pm_trader_name
    return d_trader_mapping


# 读取allocation
# d_allocation = {pm_trader_name: mul, }
# 重复，sum

def combine_new_old_subscribe(d_new: dict, d_old: dict) -> dict:
    d = {}
    for name, mul in d_new.items():
        d[name] = {'new': mul, 'old': 0}
    for name, mul in d_old.items():
        if name in d:
            d[name]['old'] = mul
        else:
            d[name] = {'new': 0, 'old': mul}
    return d


def main():
    # 读取config
    with open(PATH_CONFIG, encoding='utf-8') as f:
        d_config = json.loads(f.read(), encoding='utf-8')[FILE_NAME]
    path_allocation = os.path.abspath(d_config['AllocationFile'])
    l_subscriber_path: list = d_config['SubscriberPath']
    path_mapping = os.path.abspath(d_config['MappingFile'])

    # 读取 Mapping.csv
    # d_trader_mapping = {publisher_trader_name: pm_trader_name, }
    d_trader_mapping: dict = read_mapping(path_mapping)
    # 读取 allocation.csv
    # d_allocation = {pm_trader_name: mul, }
    d_allocation: dict = BaseAllocation.read_file(path=path_allocation).gen_trader_allocation()

    #
    d_new_old_mul_all = {}
    for subscriber_path in l_subscriber_path:
        # 旧 subscribe.csv
        path_subscribe_csv = os.path.join(subscriber_path, 'Config', 'Subscribe.csv')
        if os.path.isfile(path_subscribe_csv):
            old_subscribe_obj = SubscribeCSVData.read_file(path=path_subscribe_csv)
        else:
            logger.warning('此BM不存在初始的 subscribe.csv: %s' % path_subscribe_csv)
            old_subscribe_obj = {}
        # 更新 subscribe.csv
        update_subscribe_csv(path=subscriber_path, d_trader_mapping=d_trader_mapping, d_allocation=d_allocation)
        new_subscribe_obj = SubscribeCSVData.read_file(path=path_subscribe_csv)

        # 新旧对比
        d_new_old_mul_all[subscriber_path] = combine_new_old_subscribe(
            d_new=new_subscribe_obj.get_pub_mul(), d_old=old_subscribe_obj.get_pub_mul()
        )

    # pprint.pprint(d_new_old_mul_all)


if __name__ == "__main__":
    logger = MyLogger(name=os.path.basename(__file__))
    logger.info('start...')

    main()

    logger.info('Finished.')
