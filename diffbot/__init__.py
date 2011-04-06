"""
Extract Story Source using diffbot API

http://www.diffbot.com/docs/api/article

"""

GAE = True

try:
	from google.appengine.api import urlfetch
except ImportError:
	GAE = False
import urllib2
import urllib
import logging
import simplejson as json

class ReqCacheHandler(object):
	
	def __init__(self):
		"""docstring for __init__"""
		pass
		
	def fname(self):
		"""docstring for fname"""
		pass
		
class MemcacheHandler(ReqCacheHandler):
	
	def fname(self):
		"""docstring for fname"""
		pass
		
	def fname(self):
		"""docstring for fname"""
		pass
		

class DiffBot():
	
	api_endpoint = "http://www.diffbot.com/api/article"
	dev_token = "9b86226d9a3306f32bf80fa733692582"
	request_attempts = 3
	
	def __init__(self, cache_handler = None, url_handler = None, dev_token = None):
		if not dev_token and not self.dev_token:
			raise "Pleae provide a dev token"

	def get_req_args(self, url, format = 'json', comments = False, stats = False):
		api_arguments = {
			"token": self.dev_token,
			"url": url,
			"tags": '1'
		}
		if format != 'json':
			api_arguments['format'] = format
		if comments:
			api_arguments['comments'] = True
		if stats:
			api_arguments['stats'] = True
			
		query_string = urllib.urlencode(api_arguments)
		# query_string = '&'.join([k+'='+urllib.quote(str(v)) for (k,v) in api_arguments.items()])
		
		return query_string

	def req_urllib(self, url):
		try:
			request = urllib2.Request(
					url,
					# api_args,
					# headers
				)
			handle = urllib2.urlopen(request)
			response = handle.read()
			return response

		except urllib2.URLError, e:
			logging.exception(e)
			return False

	def req_urlfetch(self, url, attempt = 1):
		logging.info("Running req_urlfetch with url %s and attempt %d" % (url, attempt))
		
		headers = {}		
		headers['Connection'] = 'Close'
		result = None
		
		# @TODO - make async http://code.google.com/appengine/docs/python/urlfetch/asynchronousrequests.html
		try:
			result = urlfetch.fetch(
				url, 
				# payload = urllib.urlencode(arg), 
				method = urlfetch.GET, 
				headers = headers,
				deadline = 20
			)
		except urlfetch.DownloadError, e:
			logging.exception("DiffBot: (Download Attempt [%d/%d]) DownloadError: Download timed out" 
				% (attempt, self.request_attempts))
			if attempt <= self.request_attempts:
				logging.info("Diffbot: Attempting Download Again")
				attempt += 1
				return self.req_urlfetch(url, attempt)
		except Exception, e:
			logging.exception("Diffbot: Exception: %s" % e.message)
			logging.exception("Diffbot: Exceeded number of attempts allowed")
			return False
			# raise
			# raise Exception("File Not found")
			# return False
			
		if result:
			if result.status_code == 200:
				return result.content.decode('UTF-8')
		
		return False
		
	def get(self, article_url, format = 'json', comments = False, stats = False):
		api_args = self.get_req_args(article_url)
		headers = {
			"User-Agent": "Evergreen v1.0 <+http://evergreen-proto.appspot.com>",
		}
		url = self.api_endpoint + '?' + api_args
		response = self.req_urlfetch(url)
		
		if response:
			de = json.loads(response)
			de['raw_response'] = response
			return de
			
		return False

def diffbot():
	import sys
	from optparse import OptionParser
	parser = OptionParser(usage="%prog: [options] [file]")
	parser.add_option('-v', '--verbose', action='store_true')
	parser.add_option('-u', '--url', help="use URL instead of a local file")
	(options, args) = parser.parse_args()
	
	if not (len(args) == 1 or options.url):
		parser.print_help()
		sys.exit(1)
	logging.basicConfig(level=logging.DEBUG)

	file = None
	if options.url:
		import urllib
		file = urllib.urlopen(options.url)
	else:
		file = open(args[0])
	try:
		print Document(file.read(), debug=options.verbose).summary().encode('ascii','ignore')
	finally:
		file.close()
	
if __name__ == "__main__":
	diffbot()
		
	