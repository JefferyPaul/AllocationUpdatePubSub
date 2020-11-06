# -*- coding: utf-8 -*-
# @Time    : 2020/11/5 17:27
# @Author  : Jeffery Paul
# @File    : subscribe_csv_move_zero.py


import os
import shutil
import time
import datetime
import json
import sys

# 设置项目目录
PATH_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(PATH_ROOT)
os.chdir(PATH_ROOT)
PATH_CONFIG = os.path.join(PATH_ROOT, 'Config', 'Config.json')
FILE_NAME = os.path.basename(__file__).replace('.py', '')


# 导入我的模块
from pkgs.brokermini import SubscribeCSVData
from pkgs.logger import MyLogger


def main():
    with open(PATH_CONFIG, encoding='utf-8') as f:
        d_config = json.loads(f.read(), encoding='utf-8')[FILE_NAME]
    l_subscriber_path: list = d_config['SubscriberPath']

    for n, subscriber_path in enumerate(l_subscriber_path):
        path_subscribe_csv = os.path.join(subscriber_path, 'Config', 'Subscribe.csv')
        if not os.path.isfile(path_subscribe_csv):
            logger.error('不存在此文件: %s' % path_subscribe_csv)
            raise FileExistsError
        subscribe_csv_obj = SubscribeCSVData.read_file(path=path_subscribe_csv)
        subscribe_csv_obj_rm_zero = subscribe_csv_obj.remove_zero()
        subscribe_csv_obj_rm_zero.write(path=path_subscribe_csv)
        logger.info('changed: %s' % path_subscribe_csv)


if __name__ == "__main__":
    logger = MyLogger(name=os.path.basename(__file__))
    logger.info('start...')

    main()

    logger.info('Finished.')
