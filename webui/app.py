#!/usr/bin/env python3

#Paul Croft
#October 13, 2020

from bottle import get, post, request, run, static_file, template

import json
from operator import itemgetter
import os
from pprint import pformat, pprint
import pyphen
import subprocess
import time
import tempfile
import threading


#HOW TO RAMPART
#sudo mount -t tmpfs tmpfs results/ -o size=3g
#mkdir results/clipfolder

import db_utils
import utils

@get("/results/<rfile>")
def get_rgif(rfile):
    return static_file(rfile, root="results")

@get("/favicon.ico")
def favicon_only():
    return static_file("favicon.ico", root="static")

@get("/static/<sfile>")
def get_stat(sfile):
    return static_file(sfile, root="static")

@get("/clips/<cfile>")
def get_clip_video(cfile):
    return static_file(cfile.rsplit('-')[0], root="results/clipfolder")

@get("/api/get_query_results/<inquery>")
def return_query_results(inquery):
    return template("templates/formatted_results.html", data=db_utils.get_matching_subs(inquery))


def clean_results_folder():
    return True
    #TODO: write this securely
    # MAX_CACHE_SIZE = 5
    # mytime = int(time.time())
    # results_files = os.listdir("results")
    # if len(results_files) < MAX_CACHE_SIZE:
    #     return
    # results_files = sorted(results_files, key=lambda x:os.stat(os.path.abspath("results/{}".format(x)).st_size))
    # while len(results_files) > MAX_CACHE_SIZE:
    #     results_files.pop()


@get("/api/get_gif_url/<inid>")
def api_get_gif(inid):
    clean_results_folder()

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
        # "-c",\
        # "copy",\
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

    # print(' '.join(toexec))

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

@get("/words")
def word_page():
    return template("templates/words.html")

@post("/api/get_words_results/")
def api_word_query():
    payload = json.loads(request.body.read())
    # pprint(payload)
    instr = payload["query"]
    vocab_table = payload["vocab_results_table"]
    # print("THERE",pformat(vocab_table))
    if vocab_table is not None:
        vocab_table = list(map(itemgetter(1),vocab_table))
    else:
        vocab_table = []
    results = utils.build_ffmpeg_line(instr,"00:00:08,000", vocab_table)
    # results = utils.build_ffmpeg_line(instr)
    clip_ids = utils.create_clips_from_commands(results)
    retval = ["clips/{:0>5}.mp4".format(x) for x in range(len(results))]
    retval = zip(retval,clip_ids)
    return template("templates/word_clips.html",clips=retval)


@get("/api/get_clip_vocabs/<instr>")
def api_clip_vocabs(instr):
    results = utils.check_vocab(instr)
    return template("templates/vocab_table.html", results=results, asjson=json.dumps(results))

def main():
#    run(host="127.0.0.1", port=15243, server="eventlet")
    run(host="0.0.0.0", port=15243, server="eventlet")
    # pprint(db_utils.get_matching_subs("some"))
    # api_get_gif(1000)
    return 0

if __name__ == '__main__':
    exit(main())
