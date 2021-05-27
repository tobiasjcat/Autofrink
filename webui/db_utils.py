#!/usr/bin/env python3

#Paul Croft
#October 13, 2020

import codecs
import os
from pprint import pformat, pprint
import sqlite3
import string
import sys


def fastwrite(instr):
    sys.stdout.write(instr)
    sys.stdout.flush()


conn = sqlite3.connect("frink.db")
# conn = sqlite3.connect(":memory:")
c = conn.cursor()

vfiletypes = ["mkv","avi","mp4"]


def get_matching_subs(inquery):
    return c.execute("SELECT rowid, * FROM subtitles WHERE payload LIKE ? ORDER BY payload LIMIT 20", ("%{}%".format(inquery), )).fetchall()


def get_gif_details(insubrowid):
    results = c.execute("""
SELECT 
    films.filepath,
    start_time,
    end_time,
    payload
FROM 
    subtitles 
JOIN 
    films 
ON 
    films.rowid = subtitles.film_id 
WHERE 
    subtitles.rowid == ?""", (insubrowid, )).fetchone()

    return results



def insert_subs(infilm, insubtrack):
    # print("Inserting subs for {} from {}".format(infilm, insubtrack))
    fid = c.execute("SELECT rowid FROM films WHERE filepath == ?", (infilm, )).fetchone()[0]

    # print(fid, infilm)
    full_text = None
    with open(insubtrack, 'rb') as subfile:
        full_bytes = subfile.read()
        full_text = codecs.decode(full_bytes,errors='ignore')#Thanks mom-python3. Reading binary _should_ be more complicated
        full_text = ''.join(filter(lambda x:x in string.printable, full_text))
    sub_chunks = list(filter(lambda x:x.strip(), full_text.split('\r\n\r\n')))
    # print("for {} I found {} chunks".format( infilm.rsplit('/',1)[1], len(sub_chunks) ) ) 
    if len(sub_chunks) < 5:
        return
    vals_to_insert = []
    for chunk in sub_chunks:
        temp = list(filter(None, chunk.split('\r\n',2)))
        if len(temp) < 3:#badly formatted chunk
            # pprint(temp)
            continue
        st, et = '',''
        st,et = temp[1].split("-->")
        st, et = st.strip(), et.strip()
        # newval = (fid,st,et,temp[2].strip().replace('\r\n',' '), )
        newval = (fid,st,et,temp[2].strip(), )
        vals_to_insert.append(newval)
    # pprint(vals_to_insert)
    c.executemany("INSERT INTO subtitles VALUES (?, ?, ?, ?)", vals_to_insert)
    conn.commit()

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
                        if (temp + vft) in subfolder_inodes:
                            # print(temp + vft)
                            # pprint(subfolder_inodes)
                            c.execute("INSERT INTO films VALUES (?)", (film_abs, ) )
                            insert_subs(film_abs, "{}/{}".format(sf, sin))
                            break
    conn.commit()
    return retval



def main():
    fastwrite("Dropping old data...")
    c.execute("DROP TABLE IF EXISTS films")
    c.execute("DROP TABLE IF EXISTS subtitles")
    fastwrite("Done\n")

    fastwrite("Building new data...")
    build_tables()
    fastwrite("Done\n")

    fastwrite("Indexing...")
    c.execute("CREATE INDEX fidx ON films(filepath)")
    c.execute("CREATE INDEX sindex1 ON subtitles(film_id)")
    c.execute("CREATE INDEX sindex2 ON subtitles(payload)")
    fastwrite("Done\n")

    fastwrite("Vacuuming...")
    c.execute("VACUUM")
    fastwrite("Done\n")
    conn.commit()

    nfilms = c.execute("SELECT Count(rowid) FROM films").fetchone()[0]
    nsubs = c.execute("SELECT Count(rowid) FROM subtitles").fetchone()[0]

    print("Built tables for {} films and {} subtitles".format(nfilms, nsubs))

    return 0

if __name__ == '__main__':
    exit(main())