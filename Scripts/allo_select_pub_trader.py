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
from pkgs.allocation import BaseAllocation
from pkgs.logger import MyLogger


"""
根据Allocation.csv 更改 publisherBM 中的strategies文件，使得publisher只需要preload 在Allocation中"上线"的策略

0 需要完整的全部 strategies/trader.config 文件。因为更新后的 strategies/ 并不包含全部trader。
    （存放在publisher的目录下, "bak_Strategies//_init_Strategies//）
1 需要Allocation.txt
2 （输出1）备份每次根据Allocation 选出的trader.config        （存放在publisher的目录下）
3 （输出2）更改 /publisher/Config/strategies/ 

注:
1. 备份（存放在publisher的目录下）:
        /bak_Strategies/bak/
            (1) /_new_selected/
            (2) /_last_selected/
            (3) /%Y%m%d%H%M%S/
        每次更新，将(1)改为(2)，新建(1)和(3)
2. 最终放入 '4.' 中的trader，不仅需要由本次Allocation.txt选入的trader，还需要包括上一次选入的trader
        即，将(1)和(2)拷贝至publisherBM
3. Allocation.csv 
        
"""


def main():
    with open(PATH_CONFIG, encoding='utf-8') as f:
        d_config = json.loads(f.read(), encoding='utf-8')[FILE_NAME]
    l_publisher_path = [os.path.abspath(i) for i in d_config['PublisherPath']]
    path_allocation_file = os.path.abspath(d_config['AllocationFile'])

    for n, publisher_path in enumerate(l_publisher_path):
        # 【0】整理 检查目录
        publisher_path = os.path.abspath(publisher_path)
        logger.info('selecting publisher trader: %s' % publisher_path)
        path_bak = os.path.join(publisher_path, "Config", "bak_Strategies", "bak")
        path_init_files = os.path.join(publisher_path, 'Config', 'bak_Strategies', '_init_Strategies')
        path_bm_strategies = os.path.join(publisher_path, 'Config', 'Strategies')

        if not os.path.isdir(path_init_files):
            logger.error('不存在此目录: %s' % path_init_files)
            raise FileExistsError
        if not os.path.isdir(path_bak):
            os.makedirs(path_bak)

        # 【1】读取 Allocation.csv
        my_allocation = BaseAllocation.read_file(path=path_allocation_file)
        # 得到 ”选入”的trader   （Allocation != 0 的trader）
        selected_traders: list = my_allocation.get_selected_trader()
        if not selected_traders:
            logger.error('新Allocation.csv 为空: %s' % path_allocation_file)
            raise Exception

        # 【2】备份，上次
        path_new_selected_bak = os.path.join(path_bak, '_new_selected')
        path_last_selected_bak = os.path.join(path_bak, '_last_selected')
        path_dt_bak = os.path.join(path_bak, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        # 将 new 转为 last
        if os.path.isdir(path_new_selected_bak):
            if os.path.isdir(path_last_selected_bak):
                shutil.rmtree(path_last_selected_bak)
                time.sleep(0.00001)
            shutil.copytree(src=path_new_selected_bak, dst=path_last_selected_bak)
            time.sleep(0.00001)
            shutil.rmtree(path_new_selected_bak)
            time.sleep(0.00001)
        # /bak/dt
        os.makedirs(path_dt_bak)
        for trader_name in selected_traders:
            path_trader_file = os.path.join(path_init_files, trader_name + '.config')
            if not os.path.isfile(path_trader_file):
                logger.error(f'不存在此文件: {path_trader_file}')
                raise FileExistsError
            else:
                # 拷贝
                path_file_bak = os.path.join(path_dt_bak, trader_name.replace('.csv', '.config'))
                shutil.copyfile(src=path_trader_file, dst=path_file_bak)
        # /bak/new
        shutil.copytree(src=path_dt_bak, dst=path_new_selected_bak)

        # 【3】将 /bak/last /bak/new 拷贝至strategies
        if os.path.exists(path_bm_strategies):
            shutil.rmtree(path_bm_strategies)
        time.sleep(0.00001)

        list_new_selected = list(os.listdir(path_new_selected_bak))
        os.makedirs(path_bm_strategies)
        for file_name in list_new_selected:
            path_file = os.path.join(path_new_selected_bak, file_name)
            path_bm_file = os.path.join(path_bm_strategies, file_name)
            shutil.copyfile(src=path_file, dst=path_bm_file)
        if os.path.isdir(path_last_selected_bak):
            list_last_selected = list(os.listdir(path_last_selected_bak))
            for file_name in list_last_selected:
                path_file = os.path.join(path_last_selected_bak, file_name)
                path_bm_file = os.path.join(path_bm_strategies, file_name)
                if os.path.exists(path_bm_file):
                    continue
                else:
                    shutil.copyfile(src=path_file, dst=path_bm_file)
        else:
            list_last_selected = []

        # 结果
        logger.info('总数量  :\t%s' % str(len(list(set(list_new_selected + list_last_selected)))))
        logger.info('本次选入:\t%s' % str(len(list_new_selected)))
        logger.info('本次新上:\t%s' % str(len(list(set(list_new_selected).difference(set(list_last_selected))))))
        logger.info('本次下线:\t%s\n' % str(len(list(set(list_last_selected).difference(set(list_new_selected))))))


if __name__ == "__main__":
    logger = MyLogger(name=os.path.basename(__file__))
    logger.info('start...')

    main()

    logger.info('Finished.')
