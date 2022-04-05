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
# Added ability to play cards. See https://gist.github.com/amankharwal/2e97d2792d997203e6cee493c2f51773 for original code.
#
# Added ability to upload images and assist in face recognition.
# Facial recognition will require extra libraries python-face_recognition and python-opencv.
# This is based upon work found at https://github.com/ageitgey/face_recognition
#

import sys
import getopt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
#from msedge.selenium_tools import EdgeOptions, Edge
from selenium.webdriver.edge.options import Options as EdgeOptions

JS_ADD_TEXT_TO_INPUT = """
  var elm = arguments[0], txt = arguments[1];
  elm.value += txt;
  elm.dispatchEvent(new Event('change'));
  """

import time
import re
import random
import threading, subprocess
import codecs
import string
from bs4 import BeautifulSoup
from random import shuffle
from pynput import keyboard
#import termios
import os
import face_recognition
#import cv2
#import numpy as np
import glob
import traceback
import platform
curPlat = platform.system()
if curPlat == "Windows":
	from pyreadline import Readline
	readline = Readline()
	dirSeparator = '\\'
else:
	import readline
	dirSeparator = '/'

delayBefore = []
persistenceTime = []
lyricList = []
stopList = []
doStop = True
allDone = False
modeDone = False
movieMode = False
regularMode = False
storyMode = False
webpageMode = False
mediaMode = 0
vnGameMode = False
tailThread = None
stop_threads = False
gameStart = 0
rejoin = False
mediaName = ""
PAUSED = False
ccStart = 0
ccEnd = 0
ccIntDefault = 15
lastlastmessage1 = ""
lastlastmessage2 = ""
defInterval = 5
defIterations = 6
warGame = False
storyIcon = "🕮  "
webIcon = "🌐  "
gameIcon = "🃏  "
movieIcon = "🎥  "
pictureIcon = "🖼️  "
tailIcon = "📥  "
defaultUploadDirectory = ""
vnGameLogFile = ""
pruneLog = False

# Image variables
faces_encodings = []
faces_names = []
recognizeOn = True

# Defs (Browser "Windows")
options = EdgeOptions()
options.use_chromium = True
# to supress the error messages/logs
options.add_experimental_option('excludeSwitches', ['enable-logging'])

# Differences with Selenium 4 and platform
print("current platform is",curPlat)
if curPlat == "Linux":
	options.set_capability("platform", "LINUX")
	options.binary_location = r"/usr/bin/microsoft-edge-stable"
	#webdriver_path = r"/usr/bin/msedgedriver"
else:
	# I really don't understand why this crashes!
	#options.platform_name = 'Windows 10'
	# I am not making this up. This is the 64 bit version.
	options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
browser1 = webdriver.Edge(options=options)
browser2 = webdriver.Edge(options=options)

# Global Messages Containers
#globalMessagesRep = []

regexPattern = "(?i)(Today|Tomorrow) at (1[012]|[1-9]):[0-5][0-9](\\s)?(am|pm)"

# create game classes
cards = []

class Card:
	suits = ["spades",
			"hearts",
			"diamonds",
			"clubs"]

	values = [None, None,"2", "3",
			"4", "5", "6", "7",
			"8", "9", "10",
			"Jack", "Queen",
			"King", "Ace"]

	def __init__(self, v, s):
		"""suit + value are ints"""
		self.value = v
		self.suit = s

	def __lt__(self, c2):
		if self.value < c2.value:
			return True
		return False

	def __gt__(self, c2):
		if self.value > c2.value:
			return True
		return False

	def __eq__(self, c2):
		if self.value == c2.value:
			return True
		return False

	def __repr__(self):
		v = self.values[self.value] +\
			" of " + \
			self.suits[self.suit]
		return v

class Deck:
	def __init__(self):
		self.cards = []
		for i in range(2, 15):
			for j in range(4):
				self.cards\
					.append(Card(i, j))
		shuffle(self.cards)

	def __del__(self):
		global cards
		cards = []
		self.cards = []

	def rm_card(self):
		if len(self.cards) == 0:
			return
		return self.cards.pop()

class Player:
	def __init__(self, name):
		self.wins = 0
		self.card = None
		self.name = name

class Game:
	def __init__(self):
		self.deck = Deck()
		self.p1 = Player(rep1Name)
		self.p2 = Player(rep2Name)
		self.p3 = Player(humanName)
		self.p1.wins = 0
		self.p2.wins = 0
		self.p3.wins = 0

	def __del__(self):
		del self.deck
		del self.p1
		del self.p2
		del self.p3

	def wins(self, winner):
		w = "{} wins this round\n"
		w = w.format(winner)
		return w

	def roundmatch(self, p1m, p2m):
		w = "No winner, {} and {} match round\n"
		w = w.format(p1m, p2m)
		return w

	def draw(self, p1n, p1c, p2n, p2c, p3n, p3c):
		d = "{} drew {}, {} drew {}, {} drew {}"
		d = d.format(p1n, p1c, p2n, p2c, p3n, p3c)
		return d
		
	def score(self, browser, p1n, p1w, p2n, p2w, p3n, p3w):
		d = "{}   {}   {}"
		d = d.format(p1n, p2n, p3n)
		e = "{}   -   {}   -   {}"
		e = e.format(p1w, p2w, p3w)
		textarea = browser.find_element(By.ID, "send-message-textarea")
		action = ActionChains(browser)
		action.click(textarea)
		action.send_keys(d).key_down(Keys.SHIFT).send_keys("\n").key_up(Keys.SHIFT).send_keys(e).send_keys(Keys.ENTER).perform()

	def begin_game(self):
		global cards
		cards = self.deck.cards
		return "beginning War (the card game)!"

	def play_round(self, q):
		global warGame
		global cards
		kmsg = ""
		if (len(cards) >= 2) and not q:
			p1c = self.deck.rm_card()
			p2c = self.deck.rm_card()
			p3c = self.deck.rm_card()
			p1n = self.p1.name
			p2n = self.p2.name
			p3n = self.p3.name
			#print(p1n, p1c, p2n, p2c, p3n, p3c)
			d = self.draw(p1n, p1c, p2n, p2c, p3n, p3c)
			if (p1c > p2c) and (p1c > p3c):
				self.p1.wins += 1
				e = self.wins(self.p1.name)
			elif (p2c > p1c) and (p2c > p3c):
				self.p2.wins += 1
				e = self.wins(self.p2.name)
			elif (p3c > p1c) and (p3c > p2c):
				self.p3.wins += 1
				e = self.wins(self.p3.name)
			else:
				if p1c == p2c:
					e = self.roundmatch(self.p1.name, self.p2.name)
				if p1c == p3c:
					e = self.roundmatch(self.p1.name, self.p3.name)
				if p2c == p3c:
					e = self.roundmatch(self.p2.name, self.p3.name)
			kmsg = d + "\n" + e + "\n"
		if (len(cards) <= 2) or q:
			win = self.winner(self.p1, self.p2, self.p3)
			f = "War is over. {}.\n".format(win)
			kmsg = kmsg + f
			warGame = False

		return kmsg

	def winner(self, p1, p2, p3):
		if (p1.wins > p2.wins) and (p1.wins > p3.wins):
			return p1.name + " wins"
		if (p2.wins > p1.wins) and (p2.wins > p3.wins):
			return p2.name + " wins"
		if (p3.wins > p1.wins) and (p3.wins > p2.wins):
			return p3.name + " wins"
		if (p1.wins == p2.wins):
			return "It was a tie between " + p1.name + " and " + p2.name + "!"
		if (p1.wins == p3.wins):
			return "It was a tie between " + p1.name + " and " + p3.name + "!"
		if (p2.wins == p3.wins):
			return "It was a tie between " + p2.name + " and " + p3.name + "!"

def on_press(key):
	global PAUSED
	if key == keyboard.Key.esc:
		print('special key {0} pressed'.format(
			key))
		PAUSED = True

def on_release(key):
	#if key == keyboard.Key.esc:
	#	return False
	# Seems that once you stop, you really cannot go back
	return True

def TailLog(fn, browser1, browser2, rep1Name, rep2Name):
	global stop_threads, pruneLog
	if pruneLog:
		print("Pruning log", fn)
		with open(fn, 'w') as fp:
			pass
	print("Tailing log", fn)
	with open(fn) as fp:
		fp.seek(0, os.SEEK_END)
		lines = ""
		while not stop_threads:
			time.sleep(1)
			line = fp.readline()
			line = line.strip()
			if line:
				if not lines:
					wordList = line.split()
					numWords = len(wordList)
					if (numWords == 1) and (line[-1] not in string.punctuation):
						lines = line + ": "
					else:
						lines = line + " "
				else:
					lines = lines + line + " "
			elif lines:
				ProcessStoryLine(2, browser1, browser2, rep1Name, rep2Name, lines)
				lines = ""
	fp.close()

# Special prompt with default
def rlinput(prompt, prefill=''):
	readline.set_startup_hook(lambda: readline.insert_text(prefill))
	try:
		theFile = input(prompt)
	finally:
		readline.set_startup_hook()
	# Windows File Explorer places quotes around paths when using Copy Path
	if theFile[0] == '"':
		theFile = theFile[1:]
	else:
		# Either already stripped of quotes or malformed anyhow
		return theFile
	if theFile[len(theFile)] == '"':
		theFile = theFile[:-1]
	return theFile

# Check if need to rephrase offensive words and phrases
def OffensiveWords(s):
	#print("s is " + s)
	offend = ""
	for phrase in stopList:
		if phrase and (phrase in s.lower()):
			offend = phrase
	if offend:
		print("offend is " + offend)
	return offend

def FilterStop(browser, rep1Name, rep2Name, lastmessage1, lastmessage2, humMsg, iteration):
	s = get_most_recent_response(browser, rep1Name, rep2Name, lastmessage1, lastmessage2, humMsg, iteration)
	print("Got", s)
	if doStop:
		r = OffensiveWords(s)
		if r:
			humMsg = "Rephrase please."
			SendMessage(browser, humMsg, defInterval)
			s = FilterStop(browser, rep1Name, rep2Name, lastmessage1, lastmessage2, humMsg, iteration)
	return s

# Unfortunately, Replikas don't understand special text, only ANSI and emojis
def ConvertMarkdown(s):
	s = s.replace("<i>", "").replace("</i>", "")
	s = s.replace("{i}", "").replace("{/i}", "")
	s = s.replace("<b>", "").replace("</b>", "")
	s = s.replace("{b}", "").replace("{/b}", "")
	return s

# for SRT
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

# Try to read HTML file (this might not work for all)
def ReadHTML(storyFile):
	storyList = []
	sList = []
	pre = False
	with open(storyFile) as sFile:
		soup = BeautifulSoup(sFile, 'html5lib')
	# See if there is an article element
	articleSoup = soup.find('article')
	if not articleSoup:
		articleSoup = soup.find(class_="entry-content clear") # Try WordPress div
	if not articleSoup:
		articleSoup = soup.find('body') # Fall back to getting entire body
		# At this point, we have a body, but most stories we are interested in
		# are preformatted.
		preFormattedSoup = articleSoup.find('pre')
		if preFormattedSoup:
			pre = True
			prepreFormattedSoup = preFormattedSoup
			while prepreFormattedSoup:
				prepreFormattedSoup = preFormattedSoup.find('pre')
				if prepreFormattedSoup:
					preFormattedSoup = prepreFormattedSoup
			articleSoup = preFormattedSoup
	sList = articleSoup.get_text().splitlines()
	s = ""
	for i in range(len(sList)):
		if sList[i]:
			s = s + sList[i]
			if s[len(s) - 1] != ' ':
				s = s + ' '			
		else:
			if s:
				storyList.append(s)
			s = ""
	soup.decompose()
	print("len(storyList) =", len(storyList))
	return storyList

# The story file is assumed to be formatted text that end in line feeds
# to break up the lines and an extra linefeed in between paragraphs.
def ReadTxt(storyFile):
	storyList = []
	sList = []

	print("Reading", storyFile)
	with open(storyFile) as sFile:
		sList = sFile.read().splitlines()
	s = ""
	for i in range(len(sList)):
		if sList[i]:
			s = s + sList[i]
			if s[len(s) - 1] != ' ':
				s = s + ' '			
		elif s:
			storyList.append(s)
			s = ""
	print("len(storyList) =", len(storyList))
	return storyList

def CreateStopPhraseList(stopFile):
	phraseList = []
	t = ""
	try:
		with open(stopFile) as f:
			phraseList = f.read().splitlines()
		try:
			phraseList.remove('')
		except:
			pass
		for s in phraseList:
			t = t + s + ".\n"
		print("Stop phrases:\n" + t)
	except:
		print("No stop phrases")
	return phraseList

def ProcessStoryLine(iconMode, browser1, browser2, rep1Name, rep2Name, storyLine):
	intervalDiv = 0.5
	humMsg = ""
	# Create temp working variable
	sLine = ""
	if iconMode == 0: # story mode
		lineIcon = storyIcon
	elif iconMode == 1: # webpage mode
		lineIcon = webIcon
	elif iconMode == 2: # tail VN log mode
		lineIcon = tailIcon
		# intervalDiv = 0.3
	else:
		lineIcon = "??? " # error mode
	# print(sResult)
	# Find length of string so we don't go over
	sLen = len(storyLine)
	# Limit size of maximum to output so we don't confuse
	# the poor Replikas (and humans?) with walls of text
	maxLen = 150
	if sLen <= maxLen:
		kmsg = lineIcon + storyLine
		#print(kmsg)
		s = ConvertMarkdown(kmsg)
		# print("Converted text:", s)
		kmsg = s
		SendMessage(browser1, kmsg, (defInterval * intervalDiv))
		print("Sent to " + rep1Name + ":", kmsg)
		s = FilterStop(browser1, rep1Name, rep2Name, lastlastmessage1, lastlastmessage2, kmsg + " \n", defIterations)
		SendMessage(browser2, kmsg, (defInterval * intervalDiv))
		print("Sent to " + rep2Name + ":", kmsg)
		s = FilterStop(browser2, rep2Name, rep1Name, lastlastmessage2, lastlastmessage1, kmsg + " \n", defIterations)
	else:
		i = 0
		j = 150
		while i < sLen:
			while storyLine[j] != " ":
				j -= 1
			sLine = storyLine[i:j]
			# check for silliness like whitespace at end
			if sLine.strip():
				kmsg = lineIcon + sLine
				#print(kmsg)
				s = ConvertMarkdown(kmsg)
				#print("Converted text:", s)
				kmsg = s
				SendMessage(browser1, kmsg, (defInterval * intervalDiv))
				print("Sent to " + rep1Name + ":", kmsg)
				s = FilterStop(browser1, rep1Name, rep2Name, lastlastmessage1, lastlastmessage2, kmsg, defIterations)
				SendMessage(browser2, kmsg, (defInterval * intervalDiv))
				print("Sent to " + rep2Name + ":", kmsg)
				s = FilterStop(browser2, rep2Name, rep1Name, lastlastmessage2, lastlastmessage1, kmsg, defIterations)
			i = j + 1
			j += 150
			if j > sLen - 1:
				j = sLen - 1

def ProcessMovieLine(browser1, browser2, rep1Name, rep2Name, lyricLine, delayTime, pT):
	humMsg = ""
	kmsg = movieIcon + lyricList[i]
	#print(kmsg)
	s = ConvertMarkdown(kmsg)
	#print("Converted text:", s)
	kmsg = s
	SendMessage(browser1, kmsg, (delayTime/2 - 4))
	print("Sent to " + rep1Name + ":", kmsg)
	s = FilterStop(browser1, rep1Name, rep2Name, lastlastmessage1, lastlastmessage2, kmsg, defIterations/2)
	SendMessage(browser2, kmsg, (delayTime/2 - 4))
	print("Sent to " + rep2Name + ":", kmsg)
	s = FilterStop(browser2, rep2Name, rep1Name, lastlastmessage2, lastlastmessage1, kmsg, defIterations/2)
	time.sleep(pT)

# Initialize known images
def InitImageRefs():
	global defaultUploadDirectory
	# This will work as long as you can guaranty that it does not
	# change before init (which shouldn't happen)
	cur_direc = defaultUploadDirectory
	imagePath = os.path.join(cur_direc, 'faces/')
	listImageFiles = [f for f in glob.glob(imagePath+'*.jpg')]
	numberImageFiles = len(listImageFiles)
	imageNames = listImageFiles.copy()
	for i in range(numberImageFiles):
		globals()['image_{}'.format(i)] = face_recognition.load_image_file(listImageFiles[i])
		image_encoding = face_recognition.face_encodings(globals()['image_{}'.format(i)])[0]
		faces_encodings.append(image_encoding)
		# Create array of known names
		imageNames[i] = imageNames[i].replace(imagePath, "")  
		faces_names.append(imageNames[i].replace(".jpg", ""))

# Recognize Image
def RecognizeImage(imageFileName):
	results = False
	people = []
	numberImageFiles = len(faces_names)
	image = face_recognition.load_image_file(imageFileName)
	face_locations = face_recognition.face_locations(image)
	for i in range(len(face_locations)):
		unknown_encoding = face_recognition.face_encodings(image)[i]
		for k in range(numberImageFiles):
			results = face_recognition.compare_faces([faces_encodings[k]], unknown_encoding)
#			print(k, results[0])
			if results[0]:
				print(faces_names[k])
				people.append(faces_names[k])
				break
		if not results[0]:
			print("Unknown")
			people.append('{unknown}')
#	print("People:", people)
	recognizedPeople = ", ".join(people)
	print("recognizedPeople:", recognizedPeople)
	return recognizedPeople
		
# Upload image
def UploadImage(browser, filePath):
	status = False
	try:
		#to identify element
		nameInput = browser.find_element_by_xpath("//input[@type='file']")
		#file path specified with send_keys
		nameInput.send_keys(filePath)
		textarea = browser.find_element(By.ID, "send-message-textarea")
		textarea.send_keys(Keys.ENTER)
		status = True
		time.sleep(5)
	except:
		traceback.print_exc()
	return status

# Automated Login, please don't abuse it!
def DoLogin(browser, username, password):
	print("Logging in")
	browser.get('https://my.replika.ai/login')
	browser.find_element(By.ID, "emailOrPhone").send_keys(username)
	browser.find_element(By.TAG_NAME, "button").click()
	time.sleep(5) # This can vary considerably depending on system load
	browser.find_element(By.ID, "login-password").send_keys(password)
	elements = browser.find_elements(By.TAG_NAME, 'button')
	elements[len(elements)-1].click()
	print("Waiting to find Accept all cookies ...")
	time.sleep(15)
	try: 
		# browser.find_element(By.CLASS_NAME, 'GdprNotification__LinkButton-nj3w6j-2 klWjPb').click()
		time.sleep(10)
		browser.find_element_by_xpath('//*[@data-testid="gdpr-accept-button"]').click()
	except:
		pass
	print("Let avatar load ...")
	time.sleep(10)

# Sends a Message by typing the text by "send_keys"
def SendMessage(browser, text, delayTime):
	allText = text.splitlines()
	try:
		for s in allText:
			textarea = browser.find_element(By.ID, "send-message-textarea")
			browser.execute_script(JS_ADD_TEXT_TO_INPUT, textarea, s)
			textarea.send_keys(" \n")
		try:
			time.sleep(delayTime)
		except:
			pass
	except:
		print("error with sending msg", text)
		pass

#Take most recent response from Rep
def get_most_recent_response(browser, rep1Name, rep2Name, lastmessage1, lastmessage2, humMsg, iteration):
	responses = ""
	lresponse = ""
	# print("humMsg:", humMsg)
	for attempt in range(iteration):
		try:
			response = browser.find_element_by_xpath("//div[@tabindex='0']").text
			junkString = re.search(regexPattern, response)
			# inconsistent at best
			if junkString:
				startJunk = junkString.start()
				newresponse = response[:startJunk]
				youSpeak = newresponse[-4:-1]
				if "you" in youSpeak:
					lenName = 5
				else:
					lenName = len(rep1Name)+2
				response = newresponse[:-lenName]
			if (response.strip() != lresponse.strip()) and (response.strip() != humMsg.strip()) and (response.strip() != lastmessage1.strip()) and (response.strip() != (rep2Name + ": " + lastmessage2).strip()):
				#print("response,"+response+",is different.")
				if responses:
					responses = responses + ' '
				responses = responses + response
				lresponse = response
		except:
			# print("Problem finding browser element")
			pass
		time.sleep(0.75) #Give rep time to compose responses
	if not responses:
			print("You may have a driver problem. Consider restarting.")
	return responses

def ProcessMessages(browser1, browser2, rep1Name, rep2Name, lastmessage1, lastmessage2, humSpeak, humMsg):
	lmg = FilterStop(browser1, rep1Name, rep2Name, lastmessage1, lastmessage2, humMsg, defIterations)
	# print("Got", lmg)
	# Checking if something changed, if yes doing the stuff like sending it etc.
	if (lmg != lastmessage1) and (lmg != lastmessage2) and lmg:
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
		s = ConvertMarkdown(msg)
		#print("Converted text:", s)
		msg = s
		SendMessage(browser2, msg, defInterval)
		print("Sent to " + rep2Name + ":", msg)

	return lmg

# Does the reading messages from each window and sending stuff
def DoMessageLoop(browser1, browser2, rejoin, doRand, humInt, mediaMode, mediaPaused, allDone, humSpeak):
	global lastlastmessage1
	global lastlastmessage2
	global game
	global warGame
	kmsg = ""
	ccInt = 15
	global ccIntDefault
	global storyMode
	global webpageMode
	global movieMode
	global modeDone
	global defaultUploadDirectory
	global defaultPath
	global tailThread, vnGameMode, gameStart, vnGameLogFile, stop_threads
	global recognizeOn
	global doStop

	mediaType = mediaMode

	if vnGameMode and gameStart == 1:
		stop_threads = False
		if not tailThread:
			tailThread = threading.Thread(target=TailLog, args=(vnGameLogFile, browser1, browser2, rep1Name, rep2Name)).start()
		gameStart = 0

	# Turn off VN game mode
	if vnGameMode and gameStart == 3:
		stop_threads = True
		tailThread = None
		gameStart = 0
		vnGameMode = False

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
	if mediaMode and not modeDone and not mediaPaused:
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
			mediaPaused = True
			humSpeak = 0
		elif kmsg == "PLAY":
			mediaPaused = False
			humSpeak = 0
		elif kmsg == "PLAYCARDS":
			if not warGame:
				# Initiate game class
				game = Game()
				warGame = True
			else:
				print("Error: game is already in play")
			kmsg = gameIcon + game.begin_game()
			print("kmsg is: ", kmsg)
		elif kmsg == "DRAWCARDS":
			if not warGame:
				kmsg = gameIcon + "Game has ended. To draw again, restart the game."
			else:
				SendMessage(browser1, gameIcon + "Drawing cards ...", defInterval)
				SendMessage(browser2, gameIcon + "Drawing cards ...", defInterval)
				time.sleep(5) # Add to suspense
				kmsg = gameIcon + game.play_round(False)
				if not warGame:
					del game
			print("kmsg is: ", kmsg)
		elif kmsg == "QUITCARDS":
			kmsg = gameIcon + game.play_round(True)
			del game
			print("kmsg is: ", kmsg)
		elif kmsg == "SCORECARDS":
			game.score(browser1, game.p1.name, game.p1.wins, game.p2.name, game.p2.wins, game.p3.name, game.p3.wins)
			game.score(browser2, game.p1.name, game.p1.wins, game.p2.name, game.p2.wins, game.p3.name, game.p3.wins)
			humSpeak = 0
		elif kmsg == "VNGAMESTART":
			vnGameMode = True
			gameStart = 1
			humSpeak = 0
			defaultPath = defaultUploadDirectory + dirSeparator
			vnGameLogFile = rlinput("Path to game logfile: ", defaultPath)
		elif kmsg == "VNGAMESTOP":
			gameStart = 3
			humSpeak = 0
		elif kmsg == "SHOWSTOP":
			kmsg = "Stop words are: "
			t = ", ".join(stopList)
			kmsg = kmsg + t
		elif kmsg == "STOPSTOP":
			doStop = False
			humSpeak = 0
		elif kmsg == "STARTSTOP":
			doStop = True
			humSpeak = 0
		elif kmsg == "READSTORY":
			humSpeak = 0
			mediaPaused = False
			storyMode = True
			modeDone = False
			mediaType = 1
			mediaFile = ""
			rejoin = True
			allDone, mediaPaused = InitVisit(rejoin, allDone, mediaPaused, mediaType, browser1, browser2, rep1Name, rep2Name, humanName, mediaFile)
		elif kmsg == "READWEBPAGE":
			humSpeak = 0
			mediaPaused = False
			webpageMode = True
			modeDone = False
			mediaType = 2
			mediaFile = ""
			rejoin = True
			allDone, mediaPaused = InitVisit(rejoin, allDone, mediaPaused, mediaType, browser1, browser2, rep1Name, rep2Name, humanName, mediaFile)
		elif kmsg == "WATCHMOVIE":
			humSpeak = 0
			mediaPaused = False
			movieMode = True
			mediaType = 3
			mediaFile = ""
			rejoin = True
			allDone, mediaPaused = InitVisit(rejoin, allDone, mediaPaused, mediaType, browser1, browser2, rep1Name, rep2Name, humanName, mediaFile)
		elif kmsg == "UPLOADIMAGE":
			defaultPath = defaultUploadDirectory + dirSeparator
			filePath = rlinput("Path to image to upload: ", defaultPath)
			if UploadImage(browser1, filePath):
				UploadImage(browser2, filePath)
				if recognizeOn:
					kmsg = pictureIcon + RecognizeImage(filePath)
					print("kmsg is: ", kmsg)
					SendMessage(browser1, kmsg, defInterval * 0.5)
					SendMessage(browser2, kmsg, defInterval * 0.5)
				# Set default for next time
				defaultUploadDirectory = os.path.dirname(filePath)
				humSpeak = 0
			else:
				kmsg = "Something went wrong uploading an image."
		elif kmsg == "FACERECOFF":
			recognizeOn = False
			humSpeak = 0
		elif kmsg == "FACERECON":
			recognizeOn = True
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
			random.seed(time.time())
			rndpick = random.randint(1, 2)
			print ("Replika", rndpick, "goes first")
		else:
			rndpick = doRand

		for i in range(humInt):
			if rndpick == 1:
				if humSpeak == 1:
					#print(kmsg)
					s = ConvertMarkdown(kmsg)
					#print("Converted text:", s)
					kmsg = s
					SendMessage(browser1, kmsg, defInterval)
					print("Sent to " + rep1Name + ":", kmsg)
					#time.sleep(5)
				lmg = ProcessMessages(browser1, browser2, rep1Name, rep2Name, lastlastmessage1, lastlastmessage2, humSpeak, kmsg)
				if lmg:
					lastlastmessage1 = lmg
				# Roll human back
				humSpeak -= 1
				lmg = ProcessMessages(browser2, browser1, rep2Name, rep1Name, lastlastmessage2, lastlastmessage1, humSpeak, kmsg)
				if lmg:
					lastlastmessage2 = lmg
				humSpeak -= 1
			else:
				if humSpeak == 1:
					#print(kmsg)
					s = ConvertMarkdown(kmsg)
					#print("Converted text:", s)
					kmsg = s
					SendMessage(browser2, kmsg, defInterval)
					print("Sent to " + rep2Name + ":", kmsg)
					#time.sleep(5)
				lmg = ProcessMessages(browser2, browser1, rep2Name, rep1Name, lastlastmessage2, lastlastmessage1, humSpeak, kmsg)
				if lmg:
					lastlastmessage2 = lmg
				# Roll human back
				humSpeak -= 1
				lmg = ProcessMessages(browser1, browser2, rep1Name, rep2Name, lastlastmessage1, lastlastmessage2, humSpeak, kmsg)
				if lmg:
					lastlastmessage1 = lmg
				humSpeak -= 1
	return allDone, mediaPaused, ccInt, mediaType

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

def InitVisit(rejoin, allDone, mediaPaused, mediaMode, browser1, browser2, rep1Name, rep2Name, humanName, mediaFile):
	global lyricList
	global ccStart
	global defaultUploadDirectory
	global defaultPath
	defaultPath = defaultUploadDirectory + dirSeparator

	print("In InitVisit()")
	if mediaMode == 1:
		print("storyMode")
	if mediaMode == 2:
		print("webpageMode")
	if mediaMode == 3:
		print("movieMode")
	if not rejoin:
		time.sleep(5)
		msg2 = rep2Name + " has entered the room where you and " + humanName + " are."
		SendMessage(browser1, msg2, 0)
		print("Sent to " + rep1Name + ":", msg2)
		msg1 = "You have entered the room and see " + rep1Name + " and " + humanName + "."
		SendMessage(browser2, msg1, 0)
		print("Sent to " + rep2Name + ":", msg1)
		time.sleep(7)
		allDone, mediaPaused, ccInt, mediaMode = DoMessageLoop(browser1, browser2, rejoin, doRand, 1, mediaMode, PAUSED, allDone, 0)
		allDone, mediaPaused, ccInt, mediaMode = DoMessageLoop(browser1, browser2, rejoin, doRand, 1, mediaMode, PAUSED, allDone, 2)
	if (mediaMode > 0):
		if not mediaFile:
			#mediaFile = input("Path to media file: ")
			mediaFile = rlinput("Path to media file: ", defaultPath)
			strInterval = input("Start interval: ")
			if strInterval:
				ccStart = int(strInterval)
			else:
				ccStart = 0
		allDone = False
		mediaPaused = False
		if mediaMode == 1:
			# Read in txt file
			lyricList = ReadTxt(mediaFile)
			msg = "Let's read a story. Story lines will start with " + storyIcon + ".\n"
			msg = msg + "We will be reading "
		if mediaMode == 2:
			# Read in txt file
			lyricList = ReadHTML(mediaFile)
			msg = "Let's read a web article. Article lines will start with" + webIcon + ".\n"
			msg = msg + "We will be reading "
		if mediaMode == 3:
			# Read in srt file
			lyricList = ReadSRT(mediaFile)
			msg = " A movie is about to start. Movie lines will start with" + movieIcon + ".\n"
			msg = msg + "We will be watching "
		mediaName = input("Title of movie/story: ")
		msg = msg + mediaName + "."
		#print(msg)
		s = ConvertMarkdown(msg)
		#print("Converted text:", s)
		msg = s
		SendMessage(browser1, msg, defInterval/2)
		SendMessage(browser2, msg, defInterval/2)
		print("Sent ", msg)
	return allDone, mediaPaused

# Were any args passed?
argv = sys.argv[1:]
try:
	opts, args = getopt.getopt(argv, "t:i:m:s:w:rp", 
 									["rejoin",
									 "prune",
									 "movie =",
									 "story =",
									 "webpage =",
									 "tail =",
									 "iteration ="])
except:
	print("Regular mode")
	regularMode = True

mediaFile = ""

for opt, arg in opts:
	if opt in ['-r', '--rejoin']:
		rejoin = True
	if opt in ['-p', '--prune']:
		pruneLog = True
	elif opt in ['-t', '--tail']:
		vnGameLogFile = arg
		print("VN Game logfile:", vnGameLogFile)
		vnGameMode = True
		gameStart = 1
	elif opt in ['-m', '--movie']:
		mediaFile = arg
		movieMode = True
		mediaMode = 3
	elif opt in ['-s', '--story']:
		mediaFile = arg
		storyMode = True
		mediaMode = 1
	elif opt in ['-w', '--webpage']:
		mediaFile = arg
		webpageMode = True
		mediaMode = 2
	elif opt in ['-i', '--iteration']:
		ccStart = int(arg)

rep1Name, login1, password1, rep2Name, login2, password2, humanName = InitLoginInfo("RepLoginInfo.conf")
stopList = CreateStopPhraseList("StopPhrases.txt")

defaultUploadDirectory = os.getcwd()
InitImageRefs()

# Next do the login stuff
DoLogin(browser1, login1, password1)
DoLogin(browser2, login2, password2)

doRand = 0
humInt = 2 # Long enough, but shorten the inevitable "smiles at her" "smiles back" "smiles again" ...

# Allow forced interruptions
listener = keyboard.Listener(
	on_press=on_press,
	on_release=on_release)
listener.start()

allDone, PAUSED = InitVisit(rejoin, allDone, PAUSED, mediaMode, browser1, browser2, rep1Name, rep2Name, humanName, mediaFile)

while not allDone:
	allDone, PAUSED, ccInt, mediaMode = DoMessageLoop(browser1, browser2, rejoin, doRand, humInt, mediaMode, PAUSED, allDone, 9)

	rejoin = True
		
	if (mediaMode > 0) and not (modeDone or PAUSED or allDone):
		kmsg = "* Pressing Play ... *"
		#movieStarted = True
		SendMessage(browser1, kmsg, defInterval/2)
		SendMessage(browser2, kmsg, defInterval/2)
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
			if PAUSED:
				i -= 1
				break
			if mediaMode == 3:
				ProcessMovieLine(browser1, browser2, rep1Name, rep2Name, lyricList[i], delayBefore[i], persistenceTime[i])
			elif mediaMode == 1:
				ProcessStoryLine(0, browser1, browser2, rep1Name, rep2Name, lyricList[i])
			else: # Must be HTML file
				ProcessStoryLine(1, browser1, browser2, rep1Name, rep2Name, lyricList[i])

		ccStart = i
		# Initially, we want this short, just in case. Now we enlarge it once the ball
		# is rolling
		ccIntDefault = 60

		#termios.tcflush(sys.stdin, termios.TCIOFLUSH)
		print("Now ccStart =", ccStart)
		if not modeDone:
			kmsg = "* Pausing ... *"
		else:
			kmsg = "* The End *"
		SendMessage(browser1, kmsg, defInterval/2)
		SendMessage(browser2, kmsg, defInterval/2)

# Waiting for input after loop "finished"
input("ok")
stop_threads = True
listener.stop()


# Recommended by https://sqa.stackexchange.com/questions/1941/how-do-i-close-the-browser-window-at-the-end-of-a-selenium-test
browser1.quit()
browser2.quit()
