# import os
# import psycopg2
#
#
#
#     sql = """INSERT INTO container_to_endpoint(name, globus_eid, path, source_ep) VALUES (%s, %s, %s, %s);"""
#     db_pass = os.getenv("xtractdb_pass")
#     db_conn = psycopg2.connect(f"dbname='xtractdb' user='xtract' host='xtractdb.c80kmwegdwta.us-east-1.rds.amazonaws.com' password='{db_pass}'")
#     cur = db_conn.cursor()
#     cur.execute(sql, ("some_name", "some_globus_eid", "some_path", "some_source_ep"))
#     db_conn.commit()
#     cur.close()
#     db_conn.close()
#
#
