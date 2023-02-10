import pymysql
from dbutils.pooled_db import PooledDB
from config import keys

class OPMysql(object):

    __pool = None

    def __init__(self):
        # 构造函数，创建数据库连接、游标
        self.conn = OPMysql.getmysqlconn()
        self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)


    # 数据库连接池连接
    @staticmethod
    def getmysqlconn():
        if OPMysql.__pool is None:
            __pool = PooledDB(creator=pymysql, mincached=1, maxcached=10, host=keys['mysql']['host'], user=keys['mysql']['username'], passwd=keys['mysql']['passwd'], db=keys['mysql']['database'], port=keys['mysql']['port'])
            # logging.info(__pool)
        return __pool.connection()

    # 插入\更新\删除sql
    def op_insert(self, sql):
        # logging.info('op_insert %s' % sql)
        insert_num = self.cur.execute(sql)
        self.conn.commit()
        return insert_num

    # 查询
    def op_select(self, sql):
        # logging.info('op_select %s' % sql)
        self.cur.execute(sql)  # 执行sql
        select_res = self.cur.fetchall()  # 返回结果为字典
        return select_res

    #释放资源
    def dispose(self):
        self.conn.close()
        self.cur.close()


if __name__ == "__main__":
    mysql_client = OPMysql()
    sql = "insert into test (id) values (1);"
    mysql_client.op_insert(sql)
    mysql_client.dispose()
