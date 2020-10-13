#!/usr/bin/env python3

#Paul Croft
#October 13, 2020

from bottle import get, run, static_file, template


@get("/static/<sfile>")
def get_stat(sfile):
	return static_file(sfile, root="static")


@get("/")
@get("/index.html")
def main_page():
	return template("templates/index.html")

def main():
	run(host="0.0.0.0", port=15243, server="eventlet")


if __name__ == '__main__':
	exit(main())