# -*- coding: utf-8 -*-
# @Time    : 2020/11/5 15:23
# @Author  : Jeffery Paul
# @File    : subscribe_csv.py


from collections import defaultdict


class SubscribeCSVData(list):
    def __init__(self, *args):
        super().__init__(*args)
        self._self_check()

    def _self_check(self):
        for n, line in enumerate(self):
            if len(line) != 3:
                print('Subscribe实例数据格式有误: %s' % self)
                raise BaseException
            sub_trader_name = line[0]
            pub_trader_name = line[1]
            mul = line[2]
            if (type(sub_trader_name) is not str) or (type(pub_trader_name) is not str):
                print('Subscribe实例数据格式有误: %s' % self)
                raise Exception
            if sub_trader_name == '' or pub_trader_name == '':
                print('Subscribe实例数据格式有误: %s' % self)
                raise Exception
            try:
                f_mul = float(mul)
            except:
                print('Subscribe实例数据格式有误: %s' % self)
                raise Exception

    @classmethod
    def read_file(cls, path):
        l_data = []
        with open(path, encoding='utf-8') as f:
            l_lines = f.readlines()
        for line in l_lines:
            line = line.strip()
            if line == '':
                continue
            else:
                line_split = line.split(',')
                if len(line_split) != 3:
                    print('Subscribe.csv 数据行有误:\n\t%s\n\t%s' % (line, path))
                    raise Exception
                sub_trader_name = line_split[0]
                pub_trader_name = line_split[1]
                mul = float(line_split[2])
                l_data.append([sub_trader_name, pub_trader_name, mul])
        return SubscribeCSVData(l_data)

    def write(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            for line in self:
                f.write('%s,%s,%s\n' % (line[0], line[1], str(line[2])))

    def get_sub_trader(self) -> list:
        return [i[0] for i in self]

    def get_pub_trader(self) -> list:
        return [i[1] for i in self]

    def get_sub_mul(self) -> dict:
        d = defaultdict(float)
        for (sub, pub, mul) in self:
            d[sub] += mul
        return d

    def get_pub_mul(self) -> dict:
        d = defaultdict(float)
        for (sub, pub, mul) in self:
            d[pub] += mul
        return d

    def has_same_sub(self) -> bool:
        l_sub = self.get_sub_trader()
        if len(list(set(l_sub))) == len(l_sub):
            return False
        else:
            return True

    def has_same_pub(self):
        l_pub = self.get_pub_trader()
        if len(list(set(l_pub))) == len(l_pub):
            return False
        else:
            return True

    def remove_zero(self):
        return SubscribeCSVData([[sub, pub, mul] for (sub, pub, mul) in self if mul != 0])
