# -*- coding:utf-8 -*-
# @Time    : 2018/6/25 1:23
# @Author  : Brady
# @File    : __init__.py
# @Software: PyCharm
# @Contact : bradychen1024@gmail.com
# @Introduction : 一些常用功能与重复代码的封装

__version__ = '0.0.3'

import pymssql
import time
import traceback

from functools import wraps
from urllib.parse import unquote


class SqlServer(object):
    """
    SqlServer工具类
    """

    def __init__(self, host, user, pwd, db):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.db = db

    def get_connect(self):
        if not self.db:
            raise (NameError, '没有设置数据库信息')
        conn = pymssql.connect(host=self.host, user=self.user, password=self.pwd, database=self.db, charset='utf8')
        if conn.cursor():
            return conn
        else:
            raise (NameError, '连接数据库失败')

    def exec_query(self, sql):
        """
        :param sql:查询sql
        :return: 查询操作
        """
        conn = self.get_connect()
        cur = conn.cursor()
        cur.execute(sql)
        res_list = cur.fetchall()

        # 单线程查询完毕后必须关闭连接
        conn.close()
        return res_list

    def exec_non_query(self, sql):
        """
        单次增删改操作，适用于某些不想多次操作的场景
        :param sql: 非查询sql
        :return: 操作结果
        """
        conn = self.get_connect()
        cur = conn.cursor()
        try:
            cur.execute(sql)
            conn.commit()
            return True
        except Exception:
            print(sql)
            print('提交sql失败')
            print(traceback.format_exc())
            return False
        finally:
            conn.close()

    def exec_safety_non_query(self, sql):
        """
        安全的非查询操作
        :param sql: 非查询sql
        :return: 操作结果
        """
        try:
            conn = self.get_connect()
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            return True
        except Exception as e:
            try:
                print(sql)
                print("提交sql失败，重新提交中...")
                cur.execute(sql)
                conn.commit()
                return True
            except Exception as e:
                print('提交sql失败，报错原因为%s,请检查sql代码' % e)
                print(traceback.format_exc())
                return False


def convert_parameter(new_params=None):
    """
    修改函数参数值装饰器
    :param new_params: 要转换成新值的常量字典，为空则不转换
    :return:将被装饰函数中的参数(必须为字典)的值进行转换，返回新参数的函数运行结果
    example:
    @convert_parameter({'name':'brady'})
    def func(*args, **kwargs):
        print('arg结果：', args)
        print('kwarg结果：', kwargs)
    if __name__ == '__main__':
        func({'name':'becky'}, new_name={'name':'alice'})
    """
    def _convert_parameter(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def update(param_dict):
                if isinstance(param_dict, dict):
                    for key in param_dict.keys():
                        param_dict.update({key: new_params.get(key)}) if new_params.get(key) else ''
            if new_params:
                [update(arg) for arg in args]
                [update(arg) for _, arg in kwargs.items()]
            return func(*args, **kwargs)
        return wrapper
    return _convert_parameter


def retry_wrapper(retry_times, exception=Exception, error_handler=None, interval=0.1):
    """
    函数重试装饰器
    :param retry_times: 重试次数
    :param exception: 需要重试的异常
    :param error_handler: 出错时的回调函数
    :param interval: 重试间隔时间
    example:
    def func_b(*args):
        print('调用了func_b')
        print(args)
    @retry_wrapper(2, IndexError, func_b, 2)
    def func_a():
        a = [0]
        print('调用了func_a')
        print(a[1])
    if __name__ == '__main__':
        func_a()
    """
    def out_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            count = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    count += 1
                    if error_handler:
                        result = error_handler(func.__name__, count, e, *args, **kwargs)
                        if result:
                            count -= 1
                    if count >= retry_times:
                        raise
                    time.sleep(interval)
        return wrapper
    return out_wrapper


def format_headers(string):
    """
    将在Chrome上复制下来的浏览器UA格式化成字典，以\n为切割点
    :param string: 使用三引号的字符串
    :return:
    """
    string = string.strip().replace(' ', '').split('\n')
    dict_ua = {}
    for key_value in string:
        dict_ua.update({key_value.split(':')[0]: key_value.split(':')[1]})
    return dict_ua


def format_parameter(request_url):
    """
    格式化url并返回接口链接与格式化后的参数
    :param request_url:请求链接
    :return:接口链接，格式化后的参数
    """
    assert isinstance(request_url, str)
    param_dict = {}
    [param_dict.update({p.split('=')[0]:p.split('=')[1]}) for p in unquote(request_url).split('?')[1].split('&')]
    return request_url.split('?')[0], param_dict
