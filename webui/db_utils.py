#!/usr/bin/env python3

#Paul Croft
#October 13, 2020

import codecs
from datetime import timedelta
from operator import itemgetter
import os
from pprint import pformat, pprint
import pyphen
import sqlite3
import string
import sys


def fastwrite(instr):
    sys.stdout.write(instr)
    sys.stdout.flush()


def str_to_delta(instr):
    timefields = instr.split(':')#dont forget miliseconds
    secs,mss = timefields[2].split(',')
    # print(timefields, secs, mss)
    retval = timedelta( \
        hours=int(timefields[0]), \
        minutes=int(timefields[1]), \
        seconds=int(secs), \
        milliseconds=int(mss) \
    )

    return retval

def delta_to_str(indelta):
    return '0' + str(indelta).replace('.',',')[:-3]


conn = sqlite3.connect("frink.db")
# conn = sqlite3.connect(":memory:")
c = conn.cursor()

vfiletypes = ["mkv","avi","mp4"]

pdic = pyphen.Pyphen(lang="en")

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


#To test in isolation
"""
sqlite3 frink.db "DROP TABLE IF EXISTS wordlevel_subtitles" && python -c "import db_utils; db_utils.build_word_tables()"
"""
def build_word_tables():
    SUBCHUNK_SIZE = 1000
    ignorable_substrings = [ \
        "<b>","<B>","</b>","</B>","{b}","{B}","{/b}","{/B}", \
        "<i>","<I>","</i>","</I>","{i}","{I}","{/i}","{/I}", \
        "<u>","<U>","</u>","</U>","{u}","{U}","{/u}","{/U}", \
        "'" \
        ]
    whitelist_chrs = string.ascii_letters + ' '
    d = conn.cursor()

    c.execute("""
CREATE TABLE wordlevel_subtitles (
    film_id INT,
    start_time TEXT,
    end_time TEXT,
    payload TEXT)
""")
    all_subs = c.execute( \
        # "SELECT film_id, start_time, end_time, payload FROM subtitles LIMIT 2000")
        "SELECT film_id, start_time, end_time, payload FROM subtitles")
    texts = all_subs.fetchmany(SUBCHUNK_SIZE)
    while texts:
        fulllines = list(map(itemgetter(3),texts))
        clean_lines = []
        for lidx,line in enumerate(fulllines):
            for i in ignorable_substrings:
                line = line.replace(i,'')
            for punc in string.punctuation + string.whitespace:
                line = line.replace(punc,' ')
            tempres = []
            for char in line:
                if char in whitelist_chrs:
                    tempres.append(char)
            line = ''.join(tempres).lower()
            line = ' '.join([x for x in line.split(' ') if x])
            clean_lines.append(line)
            # pprint([line,str_to_delta(texts[lidx][1]),str_to_delta(texts[lidx][2])])
            line_duration = str_to_delta(texts[lidx][2]) - str_to_delta(texts[lidx][1])
            line_num_syllables = len(pdic.inserted(line.replace(' ','-')).split('-'))
            # print(line,line_duration,line_num_syllables)
            syllable_delta = line_duration / line_num_syllables
            start_delta = str_to_delta(texts[lidx][1])
            insert_values = []
            for cword in line.split(' '):
                cword_dur = len(pdic.inserted(cword).split('-')) * syllable_delta

                new_end = start_delta + cword_dur
                # print("HERE",cword,cword_dur, start_delta, new_end)
                insert_values.append((texts[lidx][0],delta_to_str(start_delta),delta_to_str(new_end),cword,))
                start_delta = new_end
            d.executemany("INSERT INTO wordlevel_subtitles VALUES (?,?,?,?)", insert_values)


        fastwrite('\r')
        fastwrite("Inserting words..."+ str(d.execute("SELECT Count(*) FROM wordlevel_subtitles").fetchall()[0][0]))
        texts = all_subs.fetchmany(SUBCHUNK_SIZE)

    fastwrite("\rInserting words...Done                       \n")
    fastwrite("Indexing words...")
    d.execute("CREATE INDEX widx ON wordlevel_subtitles(payload)")
    fastwrite("Done\n")

    conn.commit()



def main():
    fastwrite("Dropping old data...")
    c.execute("DROP TABLE IF EXISTS films")
    c.execute("DROP TABLE IF EXISTS subtitles")
    c.execute("DROP TABLE IF EXISTS wordlevel_subtitles")
    fastwrite("Done\n")

    fastwrite("Building new data...")
    build_tables()
    fastwrite("Done\n")


    fastwrite("Indexing...")
    c.execute("CREATE INDEX fidx ON films(filepath)")
    c.execute("CREATE INDEX sindex1 ON subtitles(film_id)")
    c.execute("CREATE INDEX sindex2 ON subtitles(payload)")
    fastwrite("Done\n")

    # fastwrite("Building word database...")
    build_word_tables()
    # fastwrite("Done\n")

    fastwrite("Vacuuming...")
    c.execute("VACUUM")
    fastwrite("Done\n")
    conn.commit()

    nfilms = c.execute("SELECT Count(rowid) FROM films").fetchone()[0]
    nsubs = c.execute("SELECT Count(rowid) FROM subtitles").fetchone()[0]
    nwords = c.execute("SELECT Count(rowid) FROM wordlevel_subtitles").fetchone()[0]
    frinksize_megs = int(os.path.getsize("frink.db") / 1e6)


    print("Built tables for {} films, {} subtitles and {} individual words".format(nfilms, nsubs, nwords))
    print("The total frink database is roughly {}MBs".format(frinksize_megs))

    return 0

if __name__ == '__main__':
    exit(main())
