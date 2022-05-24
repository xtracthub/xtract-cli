import os
import psycopg2

"""
Learning to use Python context manager:
https://stackoverflow.com/questions/55189511/with-psycopg2-how-to-avoid-using-the-connection-context-manager
"""

class Xtract_Db:
    def __init__(self):
        """
        should probably have something here that maintains
        the actual query that we are going to run
        """
        self._db_pass = os.getenv("xtractdb_pass")
        self._db_conn = psycopg2.connect(f"dbname='xtractdb' user='xtract' host='xtractdb.c80kmwegdwta.us-east-1.rds.amazonaws.com' password='{self._db_pass}'")

    def exec(self, sql, args):
        cur = self._db_conn.cursor()
        try:
            cur.execute(sql, args)
        except Exception as e:
            self._db_conn.rollback()
            print(f"Error: {e}")
            return
        self._db_conn.commit()
        cur.close()

    def exit(self):
        self._db_conn.close()

