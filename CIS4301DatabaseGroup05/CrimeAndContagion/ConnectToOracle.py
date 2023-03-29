import cx_Oracle

cx_Oracle.init_oracle_client(lib_dir=r"C:\instantclient_21_9")

connection = cx_Oracle.connect(
    user = "tphan1",
    password = "",
    dsn = "oracle.cise.ufl.edu:1521/orcl"
)

print("Successfully connected to Oracle Database.")

# cursor = connection.cursor()

# # Create a table

# cursor.execute("""
#     begin 
#         execute immediate 'drop table Characters';
#         exception when others then if sqlcode <> -942 then raise; end if;
#     end;"""
# )

# cursor.execute("""
#     CREATE TABLE Characters
#         (
#             FULL_NAME VARCHAR(35),
#             BIRTHDAY DATE,
#             NATIONALITY VARCHAR(25),
#             PROFESSION VARCHAR(25),
#             POSTING VARCHAR(64),
#             VICTOM VARCHAR(40)
#         )
# """)

# records = [
#                 ("Donald Lu", "10-AUG-1996", "United States", "Blackmailer, Diplomat", "Assistant", "Prime Minister)"),
#                 ("Don ", "01-JAN-1965", "Unknown", "Hidden", "None", "Many")
# ]

# cursor.executemany("insert into Characters values(:1, :2, :3, :4, :5, :6)", records)
# print(cursor.rowcount, "Rows Inserted")
                   

# connection.comit()

# cursor.execute("SELECT FULL_NAME, TO_CHAR(BIRTHDAY, 'fmDay, Month DD, YYYY'), NATIONALITY, PROFESSION, POSTING, VICTOM FROM Characters")
# resultSet = cursor.fetchall()
# print(resultSet)

# cursor.close()
# connection.close()


#============================== SECOND ATTEMPT ===============================#

# query.py

# import cx_Oracle

# # Establish the database connection
# connection = cx_Oracle.connect(user="hr", password=userpwd,
#                                dsn="dbhost.example.com/orclpdb1")

# Obtain a cursor
cursor = connection.cursor()

# Data for binding
manager_id = 145
first_name = "Peter"

# Execute the query
sql = """SELECT first_name, last_name
         FROM employees
         WHERE manager_id = :mid AND first_name = :fn"""
cursor.execute(sql, mid=manager_id, fn=first_name)

# Loop over the result set
for row in cursor:
    print(row)



#================================ FIRST ATTEMPT ====================================#

# connectionStr = 'tphan1@//oracle.cise.ufl.edu:1521/orcl' 

# connection = None
# try:
#     connection = cx_Oracle.connect(connectionStr)
#     cursor = connection.cursor()

# except Exception as err:
#     print('Error while connecting to the db')
#     print(err)
# finally:
#     if(connection):
#         cursor.close()
#         connection.close()
# print("excution completed!")    


