# import cx_Oracle

# conStr = 'natalie.valcin/umGb8Uul71wMtOTXtLQPzyIG@oracle.cise.ufl.edu:1521/orcl'

# conn = cx_Oracle.connect(conStr)
# cur = conn.cursor()


# cur.close()
# conn.close()


# import oracledb

# connection = oracledb.connect(
#     user = "natalie.valcin",
#     password= "umGb8Uul71wMtOTXtLQPzyIG",
#     dsn = "oracle.cise.ufl.edu/orcl",
#     port = "1521"
# )

# print("Do we have a good connection: ", connection.is_healthy())
# print("Are we using a Thin connection: ", connection.thin)
# print("Database version: ", connection.version)

# cursor = connection.cursor()

# # do something like fetch, insert, etc.
# # cursor.execute("SELECT * FROM TPHAN1.COVID_19")
# cursor.execute("SELECT * FROM TPHAN1.PATIENT")
# # cursor.execute("SELECT * FROM GONGBINGWONG.CRIME")
# # cursor.execute("SELECT * FROM GONGBINGWONG.VICTIM")
# # cursor.execute("SELECT CASE_ID FROM TPHAN1.COVID_19 WHERE CASE_DATE = '01-NOV-20' AND WHERE ")
# # cursor.execute("SELECT CASE_ID, COUNT(*) FROM TPHAN1.COVID_19 WHERE CURRENT_STATUS = 'PROBABLE CASE'")
# # cursor.execute("SELECT * FROM TPHAN1.PATIENT")
# for row in cursor:
#     print(row)

# cursor.close()
# connection.close() 