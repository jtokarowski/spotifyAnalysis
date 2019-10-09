from bs4 import BeautifulSoup as bs
import requests

#building a web scraper to get songs in a tracklist


#then will send names to spotify API to find and add to playlist

url = 'https://www.mixesdb.com/w/2019-10-07_-_Nora_En_Pure_-_Purified_163'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
response = requests.get(url, headers=headers)

#print(response)

soup = bs(response.content, "html.parser")

result = soup.findAll('script')

script = result[1]

string = str(script)

listedElements = string.split('data-keywordsartist=')

for element in listedElements:
	print(element)

#for i in range(len(string)):
#	print(string[i])



#result[data-keywordsartist]

#for key, val in result:


#print(result)