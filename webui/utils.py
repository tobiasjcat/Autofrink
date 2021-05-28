#!/usr/bin/env python3

#Paul Croft
#May 27, 2020

from datetime import timedelta
from pprint import pformat, pprint
import random
import pyphen
import sqlite3
import subprocess
import string
import sys
import threading

pdic = pyphen.Pyphen(lang="en")
conn = sqlite3.connect("frink.db")
c = conn.cursor()

onesecond = timedelta(seconds=1)
zeroseconds = timedelta()

def num_syllables(instr):
    return len(pdic.inserted(instr.replace(" ","-")).split('-'))

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

def string_cleaner(instr):
    temp = instr
    chr_whitelist = string.ascii_letters + ' '
    for ws in string.whitespace:
        temp = temp.replace(ws,' ')
    retval = ''.join([x for x in temp if x in chr_whitelist])
    retval = ' '.join(filter(None,retval.split(' ')))

    return retval

def build_ffmpeg_line(instr, indur):
    requested_dur = str_to_delta(indur)
    cleaned_input = string_cleaner(instr).lower()
    total_syllables = num_syllables(cleaned_input)
    syllable_dur = requested_dur / total_syllables
    retval = []
    clip_count=0
    for word in cleaned_input.split(' '):
        word_dur = syllable_dur * num_syllables(word)
        word_matches = c.execute("""
SELECT
    films.filepath,
    start_time,
    end_time,
    payload,
    duration,
    wordlevel_subtitles.rowid
FROM
    wordlevel_subtitles
JOIN
    films
ON
    wordlevel_subtitles.film_id = films.rowid
WHERE
    payload LIKE ?
ORDER BY
    duration
""",(word, )).fetchall()
        # print("THERE",word_matches[0])
        random.shuffle(word_matches)
        closest_match = word_matches[0]
        closest_delta = abs(word_dur - str_to_delta(closest_match[4]))
        for match in word_matches:
            match_delta = abs(word_dur - str_to_delta(match[4]))
            if match_delta < closest_delta:
                closest_match = match
                closest_delta = match_delta
        retval.append((closest_match[5],[ \
            "ffmpeg", \
            "-y", \
            "-ss", \
            closest_match[1].replace(",","."), \
            "-to", \
            closest_match[2].replace(",","."), \
            "-i", \
            closest_match[0], \
            "-fs", \
            "-50M", \
            "-hide_banner", \
            "-loglevel", \
            "panic", \
            "results/clipfolder/{:0>5}.mp4".format(str(clip_count))
            ]))
        clip_count += 1
        # print("query         :",word, word_dur)
        # print("closest match :",closest_match)
    # retval.extend([\
    #     "-n", \
    #     "-fs", \
    #     "150M", \
    #     # "-pix_fmt", \
    #     # "bgr8", \
    #     "-hide_banner", \
    #     # "-loglevel", \
    #     # "panic", \
    #     "results/" + cleaned_input.replace(" ","_") + ".mp4", \
    #
    #     ])

    return retval

def create_clips_from_commands(incmds,mods=[]):
    for res in incmds:
        subprocess.call(res[1])
    return [x[0] for x in incmds]

def main():
    # print(build_ffmpeg_line("One FOR the.,\t\r\n)!(*#)(@&!) money!","00:00:10,000"))
    # print(build_ffmpeg_line("One FOR the money!","00:00:10,000"))
    test_string = "One FOR the money!"
    results = build_ffmpeg_line(test_string,"00:00:08,000")
    # print("executing: ", ' '.join(results))
    # pprint(results)
    for res in results:
        subprocess.call(res)
    with open("cliplist.txt",'w') as outfile:
        num_files = len(results)
        for i in range(num_files):
            outfile.write("file 'results/clipfolder/{:0>5}.mp4'\n".format(i))
    subprocess.call("ffmpeg -y -f concat -i cliplist.txt -c copy -loglevel panic results/{}.mp4" \
    .format(string_cleaner(test_string).lower().replace(" ","_")).split(' '))

    # exec_worker = threading.Thread(target=subprocess.call, args=[results])
    # exec_worker.start()
    # exec_worker.join(20)
    # subprocess.call(results,stdout=sys.stdout,stderr=sys.stderr)



if __name__ == '__main__':
    exit(main())
