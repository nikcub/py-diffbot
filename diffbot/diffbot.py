#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:expandtab
"""
  py-diffbot - diffbot.py

  Python client and library for the Diffbot article API and others.

  This source file is subject to the new BSD license that is bundled with this 
  package in the file LICENSE.txt. The license is also available online at the 
  URL: <http://nikcub.appspot.com/bsd-license.txt>

  :copyright: Copyright (C) 2011 Nik Cubrilovic and others, see AUTHORS
  :license: new BSD, see LICENSE for more details.
"""

__version__ = '0.0.1'
__author__ = 'Nik Cubrilovic <nikcub@gmail.com>'

import os, sys, logging, urlparse, urllib

try:
  import json
except ImportError:
  try:
    import simplejson as json
  except ImportError:
    _JSON = False

class DiffBot():
  
  api_endpoint = "http://www.diffbot.com/api/article"
  dev_token = "9b86226d9a3306f32bf80fa733692582"
  request_attempts = 3

  def __init__(self, cache_options = None, url_handler = None, dev_token = None):
    if not dev_token and not self.dev_token:
      raise "Pleae provide a dev token"
    
    from handlers import handler
    
    self._http_handler_class = handler()
    self._http_handle = self._http_handler_class(cache_options)

  def http_handler(self):
    return self._http_handle

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

    
  def get_article(self, article_url, format = 'json', comments = False, stats = False, dirty_hack = False):
    api_args = self.get_req_args(article_url)
    url = self.api_endpoint + '?' + api_args
    
    response = self.http_handler().fetch(url)
    
    if response:
      de = json.loads(response)
      if not de.has_key('tags'):
        de['tags'] = []
      if dirty_hack:
        de['raw_response'] = response
      else:
        de['raw_response'] = ''
      return de
    
    # logging.info(response)
    logging.info('DONE!')  
    return False

#---------------------------------------------------------------------------
#   Helper Functions
#---------------------------------------------------------------------------

def init_logger(level, debug = False):
  """Sets the logging level for both the command line client and the 
  client library
  """
  if debug:
    log_level = logging.DEBUG
  elif level:
    log_level = level
  else:
    log_level = logging.WARNING
  
  try:
    return logging.basicConfig(level=log_level)
  except Exception:
    return False

def unset_gae():
  # sys.path = [path for path in sys.path if 'site-packages' not in path]
  pass
  # for x in sys.path:
    # logging.info(x)

def set_gae():
  a = "/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEn" \
       + "gine-default.bundle/Contents/Resources/google_appengine"
  sys.path = sys.path + [os.path.abspath(os.path.realpath(a))]


#---------------------------------------------------------------------------
#   Main command line application function
#---------------------------------------------------------------------------

def main(debug = False):
  import sys
  from optparse import OptionParser, SUPPRESS_HELP
  
  parser = OptionParser(usage="%prog: [options] [url]")
  parser.add_option('-d', '--debug', action='store_const', 
                    const=logging.DEBUG, dest='log_level')
  parser.add_option('-v', '--verbose', action='store_const', 
                    const=logging.INFO, dest='log_level')
  parser.add_option('-q', '--quiet', action='store_const', 
                    const=logging.CRITICAL, dest='log_level')
  parser.add_option('-o', '--output', choices=['html', 'raw', 'json', 'pretty'], 
                    dest='oformat', help="Ouput format (html, raw, json, pretty)")
  parser.add_option('-k', dest='key', help="Diffbot developer API key")
  # Tests
  # h = http, m = memcache, f = filecache
  parser.add_option('-t', '--test', 
              choices=["gae", "nogae", "http", "memcache", "filecache", "h", "m", "f"], 
              help=SUPPRESS_HELP)
  
  (options, args) = parser.parse_args()
  init_logger(options.log_level, debug)
  
  # logging.info("Got arguments:")
  # logging.info(options)
  # logging.info(args)
  # logging.info(len(args))
  
  if len(args) != 1:
    parser.print_help()
    sys.exit(-1)

  _url_parsed = urlparse.urlparse(args[0])
  _url = urlparse.urlunparse(_url_parsed)
  
  if not _url_parsed.netloc or not _url_parsed.scheme:
    print "Error: Please enter a valid url (%s)" % _url
    sys.exit(-1)

  if options.test == 'gae':
    set_gae()
  elif options.test == 'nogae':
    unset_gae()
  elif options.test == 'http' or options.test == 'h':
    logging.info("Testing http client")
    # http_client = httpclient.HttpClient(_url)
  elif options.test == 'memcache' or options.test == 'm':
    logging.info("Testing memcache")
  
  cache_options = {'handler': 'file'}
  db = DiffBot(cache_options)
  article = db.get_article(_url)

  from pprint import pprint
  pprint(article)
  
  # for (k, v) in article:
    # if 
  


if __name__ == "__main__":
  main(os.environ.get('DIFFBOT_DEBUG', False))

  