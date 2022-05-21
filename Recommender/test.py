#sudo python3 -m pip install mysql-connector-python

import mysql.connector
from mysql.connector import errorcode

try:
  cnx = mysql.connector.connect(user='admin', password='606HaoYunLai606!', port='3306',
                              host='database-1.c50spqkkfz7j.us-west-1.rds.amazonaws.com',
                              database='db')
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with your user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)
else:
  print("Successfully connected to the database")
  
  print("Querying data using Connector/Python...")
  cursor = cnx.cursor()
  query = ("SELECT * FROM Users")
  cursor.execute(query)

  for (uid) in cursor: 
  	print(uid)

  print("Closing the connection and cursor...")
  cursor.close()
  cnx.close()