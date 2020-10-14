#!/usr/bin/env python3

#Paul Croft
#October 13, 2020

import codecs
import os
from pprint import pformat, pprint
import sqlite3
import string

conn = sqlite3.connect("frink.db")
c = conn.cursor()


vfiletypes = ["mkv","avi","mp4"]

def insert_subs(infilm, insubtrack):
    # print("Inserting subs for {} from {}".format(infilm, insubtrack))
    full_text = None
    with open(insubtrack, 'rb') as subfile:
        full_bytes = subfile.read()
        full_text = codecs.decode(full_bytes,errors='ignore')#Thanks mom-python3. Reading binary _should_ be more complicated
        full_text = ''.join(filter(lambda x:x in string.printable, full_text))
    sub_chunks = list(filter(lambda x:x.strip(), full_text.split('\r\n\r\n')))
    print("for {} I found {} chunks".format( infilm.rsplit('/',1)[1], len(sub_chunks) ) ) 
    if len(sub_chunks) < 5:
        return
    # print(sub_chunks[-5])

def build_tables():

    c.execute("CREATE TABLE films (filepath TEXT)")
    c.execute("CREATE TABLE subtitles (film_id INT, start_time TEXT, end_time TEXT, payload TEXT)")

    top_levels = open("config").readlines()
    top_levels = map(lambda x:x.strip(), top_levels)
    retval = []
    for tl in top_levels:
        allinodes = list(map(lambda x:"{}/{}".format(tl,x), os.listdir(tl)))
        subfolders = filter(os.path.isdir, allinodes)
        # retval += list(subfolders)
        for sf in subfolders:
            # pass
            subfolder_inodes = os.listdir(sf)
            for sin in subfolder_inodes:
                if sin[-4:] == '.srt':
                    temp = sin[:-3]
                    for vft in vfiletypes:
                        film_abs = "{}/{}{}".format(sf,temp,vft)
                        if temp + vft in subfolder_inodes:
                            c.execute("INSERT INTO films VALUES (?)", (film_abs, ) )
                            break
                    insert_subs(film_abs, "{}/{}".format(sf, sin))
    conn.commit()
    return retval



def main():
    c.execute("DROP TABLE IF EXISTS films")
    c.execute("DROP TABLE IF EXISTS subtitles")

    build_tables()

    return 0

if __name__ == '__main__':
    exit(main())