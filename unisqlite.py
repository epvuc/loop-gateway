#! /usr/bin/env python
# 
# This downloads the official UnicodeData.txt file which gives the textual names
# of all unicode characters (particularly Emoji) and then creates a sqlite database
# from it which the inbound SMS receiving modules use to translate emoji into text.
# This only needs to be run very occasionally, to update the database of Emoji names. 
#  
# This is necessary because the raspberry pi is too slow to do the lookups directly
# from the text file fast enough to not time out the web hook requests. 
# 
# The file comes from ftp://ftp.unicode.org/Public/UNIDATA/UnicodeData.txt
# TODO: update files under temp names, sanity check, and move into place. 

import csv, os, sqlite3, urllib 

flatfile = '/opt/ttycommands/UnicodeData.txt'
dbfile = '/opt/ttycommands/uninames.db'

print "Fetching UnicodeData.txt"
urllib.urlretrieve('ftp://ftp.unicode.org/Public/UNIDATA/UnicodeData.txt', flatfile)

print "Removing old", dbfile
try:
    os.unlink(dbfile)
except:
    pass

print "Creating uninames.db tables"
conn = sqlite3.connect(dbfile)
c= conn.cursor()
c.execute('''CREATE TABLE uninames (value text, name text)''')
conn.commit()

print "Reading", flatfile
tbl = []
with open(flatfile, 'rb') as f:
    blob = csv.reader(f, delimiter=';')
    for row in blob:
        val = int(row[0], base=16)
        name = row[1]
        tbl.append((val,name))

print "Writing sqlite3 database"
c.executemany('INSERT INTO uninames VALUES (?, ?)', tbl)
conn.commit()
print "Finishing."
conn.close()

