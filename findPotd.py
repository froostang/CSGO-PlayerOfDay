import schedule
import time
import pymongo
from pymongo import MongoClient
import datetime
import json, urllib
import re


def findPotd():

	client = MongoClient('localhost', 27017)
	db = client['csgoPotd']
	potd = db.potds
	pStats = db.pStats
	c = pStats.find()
	potd_ref = { "h":0, "steamId":0 }
	t_d = datetime.datetime.utcnow().strftime('%B %d %Y')
	
	for document in c:
		
		a = document['steamId']

		url = "http://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=730&key=D4FCE4EAED4E74A61D7130D5862616DB&steamid=%s" % a
		url_summaries = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=D4FCE4EAED4E74A61D7130D5862616DB&steamids=%s" %a

		response = urllib.urlopen(url)
		response_summaries = urllib.urlopen(url_summaries)
		
		if response and response_summaries:

			parsed_json = json.loads(response.read())
			parsed_json2 = json.loads(response_summaries.read())

			if (parsed_json2 
				and 'response' in parsed_json2 
				and 'players' in parsed_json2['response'] 
				and parsed_json 
				and 'playerstats' in parsed_json 
				and 'stats' in parsed_json['playerstats']):
				
				statsReformat = {}
				playerInfo = parsed_json2['response']['players'][0]
				stats = parsed_json['playerstats']['stats']
				
				#reform stats json
				kills = 0
				killsToday = 0
				for item in stats:
					name = item['name']
					if isinstance(name, basestring):
						name = name.replace(".","_")
					value = item['value']
					statsReformat[name] = value

					if name == "total_kills":
						kills = value
						print(value)
						killsToday = kills - document['stats']['total_kills']
						print(killsToday)
						
				r = pStats.update_one( {"steamId":document['steamId']},
		                       		   { "$set": 
		                       		       { 
		                       		       "h":killsToday, 
		                                   "stats":statsReformat,
		                                   "pi": playerInfo,
		                                   }
		                               },
		                               upsert=True)
				print(r)

				if killsToday > potd_ref['h']:
					potd_ref['h'] = killsToday
					potd_ref['steamId'] = document['steamId']

	_potd = potd.insert({"steamId":potd_ref['steamId'], "h":potd_ref['h'], 
		                 "date":datetime.datetime.utcnow().strftime('%B %d %Y') })
	client.close()

findPotd()

#schedule.every().hour.do(job)
#schedule.every(1).day.at("10:30").do(findPotd)

#while True:
#    schedule.run_pending()
#    time.sleep(1)