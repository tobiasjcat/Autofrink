#!/usr/bin/env python3

#Paul Croft
#October 13, 2020

from bottle import get, run, static_file, template

import json
import os
from pprint import pformat, pprint
import subprocess
import tempfile
import threading


#HOW TO RAMPART
#sudo mount -t tmpfs tmpfs results/ -o size=3g


import db_utils

@get("/results/<rfile>")
def get_rgif(rfile):
    return static_file(rfile, root="results")

@get("/static/<sfile>")
def get_stat(sfile):
    return static_file(sfile, root="static")

@get("/api/get_query_results/<inquery>")
def return_query_results(inquery):
    return template("templates/formatted_results.html", data=db_utils.get_matching_subs(inquery))

@get("/api/get_gif_url/<inid>")
def api_get_gif(inid):
    db_results = db_utils.get_gif_details(inid)

    special_chars = " ()[]"

    outpath = "results/{}.gif".format(inid)
    # outpath = "results/{}.gif".format(hash(''.join(db_results)))
    # print("HERE", outpath)

    outfile = "temps/{}.srt".format(inid)
    with open(outfile,'w') as outfile_obj:
        outfile_obj.write("0\r\n00:00:00,000 --> 00:00:10,000\r\n{}\r\n\r\n".format(db_results[3]))

    film_path = db_results[0]
    srt_path = film_path.rsplit('.',1)[0] + ".srt"
    for spc in special_chars:
        srt_path = srt_path.replace(spc, '\\' + spc)
    # outpath = "results/1.gif"
    toexec = [ \
        "ffmpeg", \
        #-ss MUST MUST MUST go before -i to prevent ffmpeg from taking forever to seek the the start
        "-ss", \
        db_results[1].split(',')[0], \
        "-to", \
        db_results[2].split(',')[0], \
        "-i", \
        '{}'.format(film_path), \
        "-vf", \
        # 'subtitles={}'.format(srt_path), \
        'subtitles={}'.format(outfile), \
        # "-t", \
        # "4", \
        "-n", \
        "-fs", \
        "50M", \
        # "-pix_fmt", \
        # "bgr8", \
        "-hide_banner", \
        "-loglevel", \
        "panic", \
        outpath, \
    ]

    # pprint(toexec)

    exec_worker = threading.Thread(target=subprocess.call, args=[toexec])
    exec_worker.start()
    exec_worker.join(20)

    try:
        thread_results = os.stat(outpath)
        if thread_results.st_size == 0:
            outpath = None
    except FileNotFoundError:
        outpath = None

    return template("templates/gif_area.html", gurl=outpath, inid=inid)

@get("/")
@get("/index.html")
def main_page():
    return template("templates/index.html")

def main():
    run(host="0.0.0.0", port=15243, server="eventlet")
    # pprint(db_utils.get_matching_subs("some"))
    # api_get_gif(1000)
    return 0

if __name__ == '__main__':
    exit(main())