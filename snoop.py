#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Small tool to take in a list of domains and spit out emails and potential issues
Work smarter, not harder

Chris Maddalena
"""

import sys
import os
#from lib import *
import pwnedcheck
import urllib2

sys.path.append('lib/theharvester/')
from theHarvester import *

def main():
	# Clear the terminal window
	os.system('cls' if os.name == 'nt' else 'clear')
	# Main menu display
	try:
		domainList = sys.argv[1]
	except Exception as e:
		print "ERROR: You must supply only an input text file!"
		print "ERROR: %s" % e

	print "[+] Trying to read %s" % domainList
	try:
		with open(domainList, 'r') as domains:
			for domain in domains:
				print "[+] Checking %s" % domain.rstrip()
				harvest(domain)
	except Exception as e:
		print "[!] Could not open your file, %s" % domainList
		print "ERROR: %s" % e

# Number of commands
total = 2 # Tests
harvesterDomains = 6 # Search engines used with theHarvester
# Headers for use with urllib2
user_agent = "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)"
headers = { 'User-Agent' : user_agent }

def harvest(domain):

	domain = domain.rstrip()
	harvestLimit = 100
	harvestStart = 0
	# Create drectory for client reports and report
	if not os.path.exists("reports/%s" % domain):
		try:
			os.makedirs("reports/%s" % domain)
		except Exception as e:
			print "[!] Could not create reports directory!"
			print "ERROR: %s" % e

	file = "reports/%s/%s" % (domain, domain + ".txt")

	print "[+] Running The Harvester (1/%s)" % total
	# Search through most of Harvester's supported engines
	# No Baidu because it always seems to hang or take way too long
	print "[-] Harvesting Google (1/%s)" % harvesterDomains
	search = googlesearch.search_google(domain,harvestLimit,harvestStart)
	search.process()
	googleHarvest = search.get_emails()
	print "[-] Harvesting LinkedIn (2/%s)" % harvesterDomains
	search = linkedinsearch.search_linkedin(domain,harvestLimit)
	search.process()
	linkHarvest = search.get_people()
	print "[-] Harvesting Twitter (3/%s)" % harvesterDomains
	search = twittersearch.search_twitter(domain,harvestLimit)
	search.process()
	twitHarvest = search.get_people()
	print "[-] Harvesting Yahoo (4/%s)" % harvesterDomains
	search = yahoosearch.search_yahoo(domain,harvestLimit)
	search.process()
	yahooHarvest = search.get_emails()
	print "[-] Harvesting Bing (5/%s)" % harvesterDomains
	search = bingsearch.search_bing(domain,harvestLimit,#harvestStart)
	search.process('no')
	bingHarvest = search.get_emails()
	print "[-] Harvesting Jigsaw (6/%s)" % harvesterDomains
	search = jigsaw.search_jigsaw(domain,harvestLimit)
	search.process()
	jigsawHarvest = search.get_people()

	# Combine lists and strip out duplicate findings for unique lists
	totalEmails = googleHarvest #+ bingHarvest + yahooHarvest
	temp = []
	for email in totalEmails:
		email = email.lower()
		temp.append(email)
	unique = set(temp)
	uniqueEmails = list(unique)
	# Do the same with people, but keep Twitter handles separate
	totalPeople = linkHarvest + jigsawHarvest
	unique = set(totalPeople)
	uniquePeople = list(unique)
	# Process Twitter handles to kill duplicates
	handles = []
	for twit in twitHarvest:
		# Split handle from account description and strip rogue periods
		handle = twit.split(' ')[0]
		handle = handle.rstrip('.')
		handles.append(handle.lower())
	unique = set(handles)
	uniqueTwitter = list(unique)

	print "[+] Harvester found a total of %s emails and %s names across all engines" % (len(uniqueEmails),len(uniquePeople) + len(uniqueTwitter))
	print "[+] Running emails through HaveIBeenPwned and writing report (2/%s)" % total
	with open(file, 'w') as report:
		report.write("### Email & People Report for %s ###\n" % domain)
		report.write("---THEHARVESTER Results---\n")
		report.write("Emails checked with HaveIBeenPwned for breaches and pastes\n")
		for email in uniqueEmails:
			# Make sure we drop that @domain.com result Harvester always includes
			if email == '@' + domain:
				pass
			else:
				report.write('\n' + 'Email: ' + email + '\n')
				report.write('Pwned: ')
				# Check haveibeenpwned data breaches
				try:
					pwned = pwnedcheck.check(email)
				except:
					print "[!] Could not parse JSON. Moving on..."
				# If no results for breaches we return None
				if not pwned:
					report.write('None' + '\n')
				else:
					report.write('\n')
					for pwn in pwned:
						report.write('+ ' + pwn + '\n')
				# Check haveibeenpwned for pastes from Pastebin, Pastie, Slexy, Ghostbin, QuickLeak, JustPaste, and AdHocUrl
				url = "https://haveibeenpwned.com/api/v2/pasteaccount/" + email
				page = urllib2.Request(url, None, headers)
				# We must use Try because an empty result is like a 404 and causes an error
				try:
					source = urllib2.urlopen(page).read()
					report.write("Pastes: " + source + "\n")
				except:
					report.write("Pastes: No pastes\n")

		report.write("\n---PEOPLE Results---\n")
		report.write("Names and social media accounts (Twitter and LinkedIn)\n\n")
		for person in uniquePeople:
			report.write('Name: ' + person + '\n')
		for twit in uniqueTwitter:
			# Drop the lonely @ Harvester often includes
			if twit == '@':
				pass
			else:
				report.write('Twitter: ' + twit + '\n')

	report.close()


if __name__ == "__main__":
	main()
