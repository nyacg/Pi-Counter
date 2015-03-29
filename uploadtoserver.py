#!/usr/bin/python

#import required packages
import MySQLdb
import time
import sys

#initalise variables as global
global count
global meal

#read values from script call
args = sys.argv;
print str(args)
if len(args) >= 3:
	count = int(args[1])
	meal = args[2]
else:
	sys.exit("Invalid parameters, should be: <number> <meal>")

# databse details as variables
hostname = "192.168.1.73"
username = ""
password = ""
initalDb = "hurstmenu"
table = "attendance"
column = "actual_" + meal

print "running"
db = MySQLdb.connect(host = hostname, user = username, passwd = password, db = initalDb, port = 3306)
print "connected"
cursor = db.cursor()

date = time.strftime("%Y-%m-%d")
query = "UPDATE %s SET %s='%s' WHERE date='%s'" % (table, column, count, date)

result = cursor.execute(query)

if not result:
	query = "INSERT INTO %s (date, %s) VALUES ('%s', '%s')" % (table, column, date, count)
	result = cursor.execute(query)
	print "adding"
else: 
	print "updated"

db.commit()
print cursor._last_executed

cursor.close()