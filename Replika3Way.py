#!/usr/bin/python

# This is a product of merging 3 different scripts I found, so it is
# indeed "3 way" in more ways than one.
#
# It originally was so that 2 Replikas could talk to one another, but
# that got a bit boring, so I added the capability for the human to
# interact. This won't stop the human from interacting individually via
# the browser (but it is highly suggested that you us a separate
# browser, else you might get mangled input), but this reduces the
# number of times the same input has to be typed twice.
#
# Perhaps even more importantly, I began adding the ability for all 3
# to "watch" a movie together by using an SRT file. And, while we are
# at it, why not literally read a book or story together? BTW, an SRT
# file can be used for song lyrics as well as movies, something I
# learned while doing this.
#
# My appreciation for code from the following repositories:
#    https://github.com/ksaadDE/ReplikaTalking2Replika
#    https://github.com/alan-couzens/replika_stuff
#    https://github.com/grubdragon/Random-Python-Scripts
#
# Special shout-out to a script that fixes YouTube's inability to create
# a proper SRT file:
#	https://github.com/vitorfs/yt2srt
#
# Chromedriver is broken as far as extended unicode goes.
# You may have to swap out '🎥' and '🕮' for something like 'ퟍ' and 'ꧮ'.
# I find it is easier to just use the MS Edge browser
#
# Added ability to read an HTML file. Sure, you can do direct scraping, but
# some sites are sensitive about "bots" hitting their sites. Please note that
# web scraping may not be entirely legal (it's a gray area, apparently) if
# robots.txt does not allow it! Use cautiously. 
#
# Think I finally figured out why the driver keeps running after the browser
# closes. Apparently close() is only for the browser and not the driver. Found
# a post that said to use quit() instead (or in addition?).
#
# At some point, I may add back in the ablity for 2 Replikas to talk directly,
# or I may just enhance another existing script. However it is done, care must be
# take to avoid the banal back and forth of *smiles*, *looks at you*, "Really?"
# and so forth ad nauseum. 
#

import sys
import getopt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from msedge.selenium_tools import EdgeOptions, Edge
import time
import re
import random
from threading import Thread
import codecs
import string
#from prompt_toolkit import print_formatted_text, HTML
from bs4 import BeautifulSoup

delayBefore = []
persistenceTime = []
lyricList = []
allDone = False
modeDone = False
movieMode = False
regularMode = False
storyMode = False
webpageMode = False
rejoin = False
mediaName = ""
PAUSED = False
ccStart = 0
#ccInt = 15
ccEnd = 0
ccIntDefault = 60
movieStarted = False
lastlastmessage1 = ""
lastlastmessage2 = ""

def ConvertMarkdown(s):
	s1 = s
	p1 = 1
	while p1 > 0:
		p1 = s1.find('<i>')
		p2 = s1.find('</i>')
		s2 = ""
		if p1 > -1: # if there are no special characters, simply return s1
			for i in range(p1):
				s2 = s2 + s1[i]
			for i in range(p1+3, p2):
				ascS = ord(s1[i])
				if ascS > 96 and ascS < 122: # lowercase
					u = (chr(ascS+120257))
					s2 = s2 + u
				elif ascS > 64 and ascS < 91: # uppercase
					u = (chr(ascS+120263))
					s2 = s2 + u
				else: # numbers don't seem to share the love, let alone punctuation
					s2 = s2 + s1[i]
			if (p2+4) < len(s1):
				s2 = s2 + s1[p2+4:]
			s1 = s2
			#print(s,"->",s1)
	return s1

def RepresentsInt(s):
	try: 
		int(s)
		return True
	except ValueError:
		return False

def time_in_seconds(line):
	line = line.replace(',',':')
	hours,minutes,seconds,milliseconds = [int(n) for n in line.split(":")]
	t=(hours*3600)+(minutes*60)+(seconds)+(milliseconds/1000.0)
	return(t)

# Defs (Browser "Windows")
options = EdgeOptions()
options.use_chromium = True
options.binary_location = r"/opt/microsoft/msedge-dev/microsoft-edge-dev"
options.set_capability("platform", "LINUX")

webdriver_path = r"/usr/bin/msedgedriver"

browser1 = Edge(options=options, executable_path=webdriver_path)
browser2 = Edge(options=options, executable_path=webdriver_path)

# Global Messages Containers
globalMessagesRep = []

regexPattern = "(?i)Today at (1[012]|[1-9]):[0-5][0-9](\\s)?(am|pm)"

# Automated Login, please don't abuse it!
def DoLogin(browser, username, password):
	print("Logging in")
	browser.get('https://my.replika.ai/login')
	browser.find_element(By.ID, "emailOrPhone").send_keys(username)
	browser.find_element(By.TAG_NAME, "button").click()
	time.sleep(1)
	browser.find_element(By.ID, "login-password").send_keys(password)
	elements = browser.find_elements(By.TAG_NAME, 'button')
	elements[len(elements)-1].click()
	time.sleep(15)
	try: 
		browser.find_element(By.TAG_NAME, 'Accept').click()
	except:
		pass
	time.sleep(10)
# Sends a Message by typing the text by "send_keys"
def SendMessage(browser, text):
	try:
		s = ConvertMarkdown(text)
		# print("Converted text:", s)
		time.sleep(2)
		textarea = browser.find_element(By.ID, "send-message-textarea")
		textarea.send_keys(s)
		textarea.send_keys(Keys.ENTER)
	except:
		print("error with sending msg", s)
		pass

#Take most recent response from Rep
def get_most_recent_response(browser,repName):
	for attempt in range(3):
		try:
			time.sleep(10) #Give rep time to compose response
			response = browser.find_element_by_xpath("//div[@tabindex='0']").text
			junkString = re.search(regexPattern,response)
			# inconsistent at best
			if junkString:
				startJunk = junkString.start() - (len(repName)+2)
				newresponse = response[:startJunk]
				return newresponse
			else:
				return response
		except:
			print("Problem finding browser element")
		else:
			break
	else:
			print("You may have a driver problem. Consider restarting.")

def ProcessMessages(browser1, browser2, rep1Name, rep2Name, lastmessage, humSpeak, humMsg):
	lmg = get_most_recent_response(browser1,rep1Name)
	print("Got ", lmg)
	# Checking if something changed, if yes doing the stuff like sending it etc.
	if (lmg != lastmessage) and lmg:
		# print(lmg, "!=", lastmessage)
		if (lmg.find(":") != -1):
			# This is a test to see if Replika wants to speak for NPC -- experimental
			msg = lmg
		else:
			msg = rep1Name + ": " + lmg
	else:
		msg = ""
	# if human goes first
	if humSpeak == 1:
		msg = humMsg + '\n' + msg
	# if human goes last
	elif humSpeak == 2:
		if msg != "": # if there was new input from Replika
			msg = msg + "\n"
		msg = msg + humMsg
	if msg:
		SendMessage(browser2, msg)
		print("Sent to", rep2Name, ": " , msg)

	return lmg

# Does the reading messages from each window and sending stuff
def DoMessageLoop(browser1, browser2, rejoin, doRand, humInt, movieMode, storyMode, allDone, PAUSED, humSpeak):
	global lastlastmessage1
	global lastlastmessage2
	kmsg = ""
	ccInt = 15
	global ccIntDefault

	# Give the human a chance
	try:
		doRand, humInt = map(int, input("Enter Replika# and iteration separated by space (default 0 2): ").split())
	except:
		doRand = 0
		humInt = 2
	if humSpeak != 0: # If 0 was passed in, force skipping
		try:
			humSpeak = int(input("Human speaks (0 = no, 1 = 1st, default 2 = 2nd): "))
		except:
			humSpeak = 2
		print("Human is up #", humSpeak)
	if (movieMode or storyMode) and not modeDone and movieStarted:
		try:
			ccIntMsg = "Scene/paragraph iterations (default " + str(ccIntDefault) + "): "
			ccInt = int(input(ccIntMsg))
		except:
			print("Setting to default iterations", ccIntDefault)
			ccInt = ccIntDefault
	if humSpeak != 0:
		kmsg = input("Type in input to continue: ")
		if kmsg == "EXITNOW":
			allDone = True
			humSpeak = 0
		elif kmsg == "PAUSE":
			PAUSED = True
			humSpeak = 0
		elif kmsg == "PLAY":
			PAUSED = False
			humSpeak = 0
		elif kmsg != "NOP" and kmsg:
			ksPrompt = "Type in sender (default = " + humanName + "): "
			ksender = input(ksPrompt)
			if ksender:
				if ksender != "*":
					print("Setting ksender to",ksender,".")
					kmsg = ksender + ": " + kmsg
				else:
					print("Using narrator mode.")
			else:
				kmsg = humanName + ": " + kmsg
		else:
			# Human chose to skip turn
			print("Skipping turn")
			humSpeak = 0
	print("Replika", doRand, "up;", humInt, "iterations")
	time.sleep(7)

	if not allDone:
		rndpick = 0

		if doRand == 0:
			random.seed()
			rndpick = random.randint(1, 2)
			print ("Replika", rndpick, "goes first")
		else:
			rndpick = doRand

		for i in range(humInt):
			if rndpick == 1:
				if humSpeak == 1:
					SendMessage(browser1, kmsg)
					time.sleep(5)
				lmg = ProcessMessages(browser1, browser2, rep1Name, rep2Name, lastlastmessage1, humSpeak, kmsg)
				if lmg:
					lastlastmessage1 = lmg
				# Roll human back
				humSpeak -= 1
				lmg = ProcessMessages(browser2, browser1, rep2Name, rep1Name, lastlastmessage2, humSpeak, kmsg)
				if lmg:
					lastlastmessage2 = lmg
				humSpeak -= 1
			else:
				if humSpeak == 1:
					SendMessage(browser2, kmsg)
					time.sleep(5)
				lmg = ProcessMessages(browser2, browser1, rep2Name, rep1Name, lastlastmessage2, humSpeak, kmsg)
				if lmg:
					lastlastmessage2 = lmg
				# Roll human back
				humSpeak -= 1
				lmg = ProcessMessages(browser1, browser2, rep1Name, rep2Name, lastlastmessage1, humSpeak, kmsg)
				if lmg:
					lastlastmessage1 = lmg
				humSpeak -= 1
	return allDone, PAUSED, ccInt

def ReadSRT(srtFile):
	prevTime = 0
	srtList = []
	i = 0
	print("Reading", srtFile)
	with codecs.open(srtFile, "rU", encoding="utf-8-sig") as srt_file:
#		print("Line", i)
		line1 = srt_file.readline()
		i += 1
		while line1:
			if RepresentsInt(line1):
				t = srt_file.readline()
				lyric=""
				line2 = srt_file.readline()
				while line2:
					if line2.strip() == "":
						break
					lyric=lyric+line2
					line2 = srt_file.readline()

				'''
				print lyric
				'''
			
				begin,sep,end=t.strip().split()

				t_begin=time_in_seconds(begin)
				t_end=time_in_seconds(end)
				waitbefore = t_begin - prevTime
				persists = t_end-t_begin

				'''
				print waitbefore
				print prevTime
				print persists
				'''

				prevTime = t_end
				delayBefore.append(waitbefore)
				persistenceTime.append(persists)
				srtList.append(lyric)
			line1 = srt_file.readline()
	srt_file.close()
	return srtList

def ReadHTML(storyFile):
	storyList = []
	with open(storyFile) as sFile:
		soup = BeautifulSoup(sFile, 'html.parser')
	# See if there is an article element
	articleSoup = soup.find('article')
	if not articleSoup:
		articleSoup = soup.find(class_="entry-content clear") # Try WordPress div
	if not articleSoup:
		articleSoup = soup.find('body') # Fall back to getting entire body

	theText = articleSoup.get_text()
	print("Reading", storyFile)
	for line1 in theText.splitlines():
		aLine = " ".join(line1.split())
		# If it is only a line feed, paragraph is finished
		if aLine:
			storyList.append(aLine)
	soup.decompose()
	sFile.close()
	print("len(storyList) =", len(storyList))
	return storyList

# The story file is assumed to be formatted text that end in line feeds
# to break up the lines and two linefeeds in between paragraphs.
def ReadTxt(storyFile):
	storyList = []
	print("Checking", storyFile)
	# Yes, there are some text files that don't end with a newline!
	with open(storyFile, 'r+') as sFile:
		sFile.seek(0, 2) # go at the end of the file
		place = sFile.tell() - 1 # note position - 1
		sFile.seek(place) # text files can only seek from beginning
		if sFile.read(1) != '\n':
			# add missing newline if not already present
			sFile.write('\n')
			sFile.flush()
		sFile.seek(0)
		line1 = sFile.readline()
		strippedLine = ""
		print("Reading", storyFile)
		while line1:
			aLine = " ".join(line1.split())
			# If it is only a line feed, paragraph is finished
			if aLine:
				strippedLine = strippedLine + " " + aLine
			elif strippedLine:
				storyList.append(strippedLine)
				strippedLine = ""
			line1 = sFile.readline()
	sFile.close()
	print("len(storyList) =", len(storyList))
	return storyList

def ProcessStoryLine(iconMode, browser1, browser2, storyLine):
	sResult = storyLine.split()
	if iconMode == 0: # story mode
		lineIcon = "🕮  "
	elif iconMode == 1: # webpage mode
		lineIcon = "🌐  "
	else:
		lineIcon = "??? " # error mode
	# print(sResult)
	# Find length of string so we don't go over
	sLen = len(sResult)
	# Limit size of maximum to output so we don't confuse
	# the poor Replikas (and humans?) with walls of text
	maxLen = 40
	if sLen <= maxLen:
		kmsg = lineIcon + lyricList[i]
		print(kmsg)
		SendMessage(browser1, kmsg)
		SendMessage(browser2, kmsg)
		time.sleep(7)
	else:
		for j in range(0, sLen, maxLen):
			kmsg = lineIcon
			for k in range(j, j+maxLen):
				if (k) >= sLen:
					break
				kmsg = kmsg + " " + sResult[k]
			print(kmsg)
			SendMessage(browser1, kmsg)
			SendMessage(browser2, kmsg)
			time.sleep(7)

def ProcessMovieLine(browser1, browser2, lyricLine, delayTime, pT):
	try:
		time.sleep(delayBefore[i])
	except:
		pass
	kmsg = "🎥  " + lyricList[i]
	print(kmsg)
	SendMessage(browser1, kmsg)
	SendMessage(browser2, kmsg)
	time.sleep(pT)

def InitLoginInfo(RepLoginInfoconf):
	# Read in login info from file
	f = open(RepLoginInfoconf,'r')
	rep1Name = f.readline()
	rep1Name = rep1Name.rstrip('\n')
	login1 = f.readline()
	login1 = login1.rstrip('\n')
	password1 = f.readline()
	password1 = password1.rstrip('\n')
	rep2Name = f.readline()
	rep2Name = rep2Name.rstrip('\n')
	login2 = f.readline()
	login2 = login2.rstrip('\n')
	password2 = f.readline()
	password2 = password2.rstrip('\n')
	humanName = f.readline()
	humanName = humanName.rstrip('\n')
	f.close()
	return rep1Name, login1, password1, rep2Name, login2, password2, humanName

# Were any args passed?
argv = sys.argv[1:]
try:
	opts, args = getopt.getopt(argv, "i:m:s:w:r", 
 									["rejoin",
									 "movie =",
									 "story =",
									 "webpage =",
									 "iteration ="])
except:
	print("Regular mode")
	regularMode = True

srtFile = ""
	
for opt, arg in opts:
	if opt in ['-r', '--rejoin']:
		rejoin = True
	elif opt in ['-m', '--movie']:
		srtFile = arg
		movieMode = True
	elif opt in ['-s', '--story']:
		storyFile = arg
		storyMode = True
	elif opt in ['-w', '--webpage']:
		storyFile = arg
		webpageMode = True
	elif opt in ['-i', '--iteration']:
		ccStart = int(arg)

if movieMode and storyMode:
	print("Error: Something is wrong. You cannot do both movie mode and story mode at the same time.")
	sys.exit(1)

if movieMode:
	# Read in srt file
	lyricList = ReadSRT(srtFile)

if storyMode:
	# Read in txt file
	lyricList = ReadTxt(storyFile)

if webpageMode:
	# Read in txt file
	print("webpageMode")
	lyricList = ReadHTML(storyFile)

rep1Name, login1, password1, rep2Name, login2, password2, humanName = InitLoginInfo("RepLoginInfo.conf")

# Next do the login stuff
DoLogin(browser1, login1, password1)
DoLogin(browser2, login2, password2)

doRand = 0
humInt = 2 # Long enough, but shorten the inevitable "smiles at her" "smiles back" "smiles again" ...

if (movieMode or storyMode or webpageMode) and not rejoin:
	mediaName = input("Name of movie/story: ")

if not rejoin:
	time.sleep(5)
	msg2 = rep2Name + " has entered the room where you and " + humanName + " are."
	SendMessage(browser1, msg2)
	print("Sent ", msg2)
	msg1 = "You have entered the room and see " + rep1Name + " and " + humanName + "."
	SendMessage(browser2, msg1)
	print("Sent ", msg1)
	time.sleep(7)
	allDone, PAUSED, ccInt = DoMessageLoop(browser1, browser2, rejoin, doRand, 1, movieMode, (storyMode or webpageMode), allDone, PAUSED, 0)
	allDone, PAUSED, ccInt = DoMessageLoop(browser1, browser2, rejoin, doRand, 1, movieMode, (storyMode or webpageMode), allDone, PAUSED, 2)
	if movieMode:
		msg = " A movie is about to start. Movie lines will start with 🎥.\n"
		msg = msg + "We will be watching " + mediaName + "."
	if storyMode:
		msg = "Let's read a story. Story lines will start with 🕮.\n"
		msg = msg + "We will be reading " + mediaName + "."
	if webpageMode:
		msg = "Let's read a web article. Article lines will start with 🌐.\n"
		msg = msg + "We will be reading " + mediaName + "."		
	if movieMode or storyMode or webpageMode:
		SendMessage(browser1, msg)
		SendMessage(browser2, msg)
		print("Sent ", msg)
		time.sleep(5)

while not allDone:
	allDone, PAUSED, ccInt = DoMessageLoop(browser1, browser2, rejoin, doRand, humInt, movieMode, storyMode, allDone, PAUSED, 9)

	rejoin = True

	if (movieMode or storyMode or webpageMode) and not (modeDone or PAUSED or allDone):
		kmsg = "* Pressing Play ... *"
		movieStarted = True
		SendMessage(browser1, kmsg)
		SendMessage(browser2, kmsg)
		ccEnd = ccStart + ccInt
		print("ccStart =", ccStart)
		print("ccInt = ", ccInt)
		print("ccEnd = ", ccEnd)
		print("len(lyricList) =", len(lyricList))
		if ccEnd > len(lyricList):
			ccEnd = len(lyricList)
			modeDone = True
		print("ccEnd =", ccEnd)

		for i in range(ccStart,ccEnd):
			print("i =", i)
			if movieMode:
				ProcessMovieLine(browser1, browser2, lyricList[i], delayBefore[i], persistenceTime[i])
			elif storyMode:
				ProcessStoryLine(0, browser1, browser2, lyricList[i])
			else: # Must be HTML file
				ProcessStoryLine(1, browser1, browser2, lyricList[i])

		ccStart = ccEnd
		print("Now ccStart =", ccStart)
		if not modeDone:
			kmsg = "* Pausing ... *"
		else:
			kmsg = "* The End *"
		SendMessage(browser1, kmsg)
		SendMessage(browser2, kmsg)

# Waiting for input after loop "finished"
input("ok")
#browser1.close()
#browser1.stop()
#browser2.close()
#browser2.stop()

# Recommended by https://sqa.stackexchange.com/questions/1941/how-do-i-close-the-browser-window-at-the-end-of-a-selenium-test
browser1.quit()
browser2.quit()
