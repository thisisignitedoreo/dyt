#!/usr/bin/env python3

from PIL import Image, ImageTk
import tkinter as tk
import subprocess
import traceback
import requests
import random
import json
import sys
import os
import io

app_name = "DYT"

# UX
# {

def notify_send(title, description=""):
	subprocess.run(["notify-send", "--app-name", app_name, title, description])


def ask_dmenu(*args, prefix):
	cmdargs = ["dmenu", *(["-p", prefix] if prefix is not None else [])]
	print_cmd(*cmdargs)
	print("IN: \"" + ",".join(args) + "\"")
	p = subprocess.Popen(cmdargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	a = p.communicate("\n".join(args).encode())[0][:-1].decode()
	print("OUT: \"" + a + "\"")
	if a == "": exit()
	return a

def text_dmenu(prefix):
	cmdargs = ["dmenu", "-p", prefix]
	print_cmd(*cmdargs)
	print("IN: \"" + ",".join(args) + "\"")
	p = subprocess.Popen(cmdargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	a = p.communicate(b"")[0][:-1].decode()
	print("OUT: \"" + a + "\"")
	if a == "": exit()
	return a


def ask_rofi(*args, prefix=None):
	cmdargs = ["rofi", "-dmenu", *(["-p", prefix] if prefix is not None else [])]
	print_cmd(*cmdargs)
	print("IN: \"" + ",".join(args) + "\"")
	p = subprocess.Popen(cmdargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	a = p.communicate("\n".join(args).encode())[0][:-1].decode()
	print("OUT: \"" + a + "\"")
	if a == "": exit()
	return a

def text_rofi(prefix):
	cmdargs = ["rofi", "-dmenu", "-p", prefix]
	print_cmd(*cmdargs)
	print("IN: \"" + ",".join(args) + "\"")
	p = subprocess.Popen(cmdargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	a = p.communicate(b"")[0][:-1].decode()
	print("OUT: \"" + a + "\"")
	if a == "": exit()
	return a


def ask_cmd(*args, prefix=None):
	print("Select:" if prefix is None else f"{prefix}:")
	for k, i in enumerate(args, start=1):
		print(f"{k}. {i}")

	while True:
		ask = input(f"Select [1-{len(args)}]: ")
		if isint(ask) and 0 <= int(ask) - 1 < len(args): return args[int(ask) - 1]

def text_cmd(prefix):
	return input(prefix + ": ")

# }

# YOUTUBE COMMUNICATION
# {

def handle_to_id(handle):
	return json.loads(requests.get("https://yt.lemnoslife.com/channels?handle=@" + handle).content)["items"][0]["id"]

def get_channel_name(cid):
	if cid not in cache["c"]:
		data = json.loads(requests.get(f"https://{settings['instance']}/api/v1/channels/{cid}").content)
		cache["c"][cid] = data["author"]
		cache_save()

	return cache["c"][cid]

def get_channel_subs(cid):
	if cid not in cache["s"]:
		data = json.loads(requests.get(f"https://{settings['instance']}/api/v1/channels/{cid}").content)
		cache["s"][cid] = data["subCount"]
		cache_save()

	return cache["s"][cid]

def fetch_channel(cid, continuation=None):
	data = json.loads(requests.get(f"https://{settings['instance']}/api/v1/channels/{cid}/videos" + (f"?continuation={continuation}" if continuation is not None else "")).content)	
	return (list(map(lambda x: (f"https://youtu.be/{x['videoId']}", x["title"]), data['videos'])), data.get("continuation"))

def search_for_channels(query):
	used = []
	res = []
	data = json.loads(requests.get(f"https://{settings['instance']}/api/v1/search" + ejoin(type="channels", q=query)).content)
	for i in data:
		if i["authorId"] not in used: res.append(i["authorId"])
		used.append(i["authorId"])
	return res

def search_videos(query, page=1):
	used = []
	res = []
	data = json.loads(requests.get(f"https://{settings['instance']}/api/v1/search" + ejoin(type="video", q=query, page=page)).content)
	for i in data:
		if i["videoId"] not in used: res.append((i["videoId"], i["title"]))
		used.append(i["videoId"])

	return res

# }	

# DX
# {

def ejoin(**kwargs):
	return "?" + "&".join([f"{k}={i}" for k, i in  kwargs.items()])

def print_cmd(*cmdargs):
	print("$", *[("'" if any([str.isspace(i) for i in j]) else '') + j + ("'" if any([str.isspace(i) for i in j]) else '') for j in cmdargs])

def settings_save():
	json.dump(settings, open("settings.json", "w"))

def cache_save():
	json.dump(cache, open("cache.json", "w"), separators=(",", ":"))

def isint(n):
	try:
		int(n)
		return True
	except:
		return False

# }

# OTHER
# {

def play_vid(vurl):
	subprocess.run(["mpv", vurl])

def exit(exit_code=0):
	notify("Exiting DYT", "Exiting..." if exit_code == 0 else "There were a problem in DYT, submit it to Issues, or try to debug it, by running it in console emulator.")
	sys.exit(exit_code)

def check_instance(inst):
	try: req = requests.get(f"https://{inst}/api/v1/stats")
	except: bad = True
	else: bad = not req.ok
	if bad:
		notify("Error", "Selected instance isn't available or has no api OR no internet.")
		return True
	return False

# }

try:

	if __name__ == "__main__":
		configs = {
			"dmenu": {
				"ask": ask_dmenu,
				"text": text_dmenu,
				"notify": notify_send
			},
			"rofi": {
				"ask": ask_rofi,
				"text": text_rofi,
				"notify": notify_send
			},
			"cmd": {
				"ask": ask_cmd,
				"text": text_cmd,
				"notify": print
			},
		}

		os.chdir(os.path.dirname(__file__))

		if not os.path.isfile("settings.json"): json.dump({"subscribed": [], "instance": "vid.priv.au", "mode": "rofi", "debug": False}, open("settings.json", "w"))
		settings = json.load(open("settings.json"))

		if settings["debug"]:
			print = lambda *x: notify("Debug", " ".join(x))

		if not os.path.isfile("cache.json"): json.dump({"c": {}, "s": {}}, open("cache.json", "w"), separators=(",", ":"))
		cache = json.load(open("cache.json"))

		config = settings["mode"]

		ask = configs[config]["ask"]
		text = configs[config]["text"]
		notify = configs[config]["notify"]

		notify("Started", "Started DYT, wait while it is starting")

		a = check_instance(settings["instance"])
		if a: exit()

		sel = ask(
			*[f"{k}. {get_channel_name(i)}" for k, i in enumerate(settings["subscribed"], start=1)],
			"Subscribe",
			"Unsubscribe",
			"Search",
			"Settings",

			"Quit",
			"Disable debugging" if settings["debug"] else "Enable debugging",
			prefix="Menu",
		)

		if "debugging" in sel:
			settings["debug"] = not settings["debug"]
			settings_save()
			exit()

		fetch_videos = None

		if sel == "Settings":
			change = ask("Invidous instance", "Mode", prefix="Select setting")

			if change == "Invidous instance":
				new_inst = ask(settings["instance"], prefix="Newly selected instance")
				a = check_instance(new_inst)
				if not a: settings["instance"] = new_inst

			elif change == "Mode":
				settings["mode"] = ask(*configs.keys(), prefix="Select mode")

			settings_save()

		elif sel == "Subscribe":
			handle = text("Enter YT Handle: @")
			
			cid = handle_to_id(handle)

			if cid is None:
				notify("Error", f"Channel @{handle} does not exist!")
			else:
				notify("Subscribed", f"Subscribed to {get_channel_name(cid)}")

				settings["subscribed"].append(cid)
				settings_save()

		elif sel == "Unsubscribe":
			channel = ask("Back", *[f"{k}. {get_channel_name(i)}" for k, i in enumerate(settings["subscribed"], start=1)], prefix="Select channel")

			if channel != "Back":
				cnum, cname = channel.split(". ")
				cnum = int(cnum) - 1

				notify("Unsubscribed", f"Unsubscribed from {cname}")
				settings["subscribed"] = settings["subscribed"][:cnum] + settings["subscribed"][cnum + 1:]
				settings_save()

		elif sel == "Search":
			stype = ask("Channels", "Videos", prefix="Search for")

			if stype == "Channels":
				q = text("Query")
				channels = search_for_channels(q)
				channel = ask("Back", *[f"{k}. {get_channel_name(i)} ({get_channel_subs(i)})" for k, i in enumerate(channels, start=1)], prefix="Select channel")
				if channel == "Back": exit()
				channel = channels[int(channel.split(". ")[0]) - 1]
				
				thing = ask("Subscribe", "List videos", prefix="What to do?")

				if thing == "Subscribe":
					notify("Subscribed", f"Subscribed to {get_channel_name(channel)}")
					settings["subscirbed"].append(channel)
					settings_save()

				elif thing == "List videos":
					fetch_videos = channel

			else:
				q = text("Query")
				videos = search_videos(q)
				page = 1	

				while True:
					video = ask("Back", *[f"{k}. {i[1]}" for k, i in enumerate(videos, start=1)], "More", prefix="Select video")
					
					if video == "Back": exit()
					elif video == "More":
						page += 1
						videos += search_videos(q, page)
					else:
						vid = int(video.split(". ")[0]) - 1
						break

				play_vid(vid)

		elif sel in ("Quit", "q", "Exit", "e"):
			exit()

		else:
			if isint(sel):
				fetch_videos = settings['subscribed'][int(sel) - 1]

			elif ". " in sel:
				fetch_videos = settings['subscribed'][int(sel.split('. ')[0]) - 1]
				
			elif sel == "": exit()

			else: notify("Error", "What did ya select?")

		if fetch_videos:
			videos, continuation = fetch_channel(fetch_videos)

			while True:
				sel = [
					"Back",
					*[f"{k}. {i[1]}" for k, i in enumerate(videos, start=1)],
				]
					
				if continuation is not None: sel.append("More")

				vsel = ask(*sel, prefix="Select video")

				back = False

				if vsel == "Back":
					back = True
					break
				elif vsel == "More":
					new_videos, continuation = fetch_channel(fetch_videos, continuation)
					videos += new_videos
					continue
				else:
					vid = None
				
					if ". " in vsel: vid = int(vsel.split(". ")[0]) - 1
					elif isint(vsel): vid = int(vsel) - 1
					break
				
			if not back:
				play_vid(videos[vid][0])

		exit()

except Exception as err:
	print(f"Got {err}. Thats bad.")
	print(traceback.format_exc())

