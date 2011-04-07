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
  """DiffBot API Client

  Make requests to the DiffBot API. Client library has built-in support for
  multiple http client libraries, caching with a local file cache and memcache
  and Google App Engine (defaults to urlfetch and memcache).

  Initialization options are caching options and developer token, which is
  required for all requests.

  Usage:

  >>> import diffbot
  >>> db = diffbot.DiffBot(dev_token="mydevtoken")
  >>> db.get_article("http://www.newssite.com/newsarticle.html")
  [parsed article here]

  :since: v0.1
  """

  api_endpoint = "http://www.diffbot.com/api/article"
  request_attempts = 3

  def __init__(self, cache_options = None, dev_token = None, attempts = 3):
    """Initialize the DiffBot API client. Parameters are cache options and the
    required developer token.

    Cache options as a dict with key:
      handler:              memcache or file
      cache_dir:            if file cache, use cache folder (default tmp)
      memcache_server:      memcache server IP address
      memcache_user:        memcache username

    dev_token is a required developer token

    attempts is the number of http request attempts to make on failure
    """
    if not dev_token:
      dev_token = os.environ.get('DIFFBOT_TOKEN', False)

    if not dev_token:
      raise Exception("Please provide a dev token")

    self.dev_token = dev_token

    from handlers import handler

    self._http_handler_class = handler()
    self._http_handle = self._http_handler_class(cache_options)

  def http_handler(self):
    """Returns the http handler object, which implements handlers.HttpHandler.
    Implements a single function, fetch, which has a single argument, the url.
    Handler classes wrap Google App Engine urlfetch library and the various
    options and exceptions, as well as urllib and urllib2, which will be selected
    automatically depending on Python version and environment.
    """
    return self._http_handle

  def get_req_args(self, url, format = 'json', comments = False, stats = False):
    """Build request arguments for query string in API request. Defaults are
    to request JSON output format."""
    # TODO some of these are not implemented. can we order the dict?
    api_arguments = {
      "token": self.dev_token,
      "url": url,
      # "tags": '1'
    }
    if format != 'json':
      api_arguments['format'] = format
    if comments:
      api_arguments['comments'] = True
    if stats:
      api_arguments['stats'] = True

    query_string = urllib.urlencode(api_arguments)

    return query_string

  def get_article(self, article_url, format = 'json', comments = False,
                  stats = False, dirty_hack = False):
    """Make an API request to the DiffBot server to retrieve an article.

    Requires article_url
    """
    api_args = self.get_req_args(article_url)
    url = self.api_endpoint + '?' + api_args

    response = self.http_handler().fetch(url)

    if response:
      try:
        de = json.loads(response)
      except Exception, e:
        logging.exception(e)
        return False
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
  parser.add_option('-c', '--cache', choices=['memcache', 'file', 'm', 'f'],
                    dest='cache', help="Cache (memcache or file)")
  parser.add_option('-o', '--output', choices=['html', 'raw', 'json', 'pretty'],
                    dest='oformat', help="Ouput format (html, raw, json, pretty)")
  parser.add_option('-k', dest='key', help="Diffbot developer API key")

  parser.add_option('-t', '--test',
              choices=["gae", "nogae", "http", "memcache", "filecache", "h", "m", "f"],
              help=SUPPRESS_HELP)

  (options, args) = parser.parse_args()
  init_logger(options.log_level, debug)

  if len(args) != 1:
    parser.print_help()
    sys.exit(-1)

  _url_parsed = urlparse.urlparse(args[0])
  _url = urlparse.urlunparse(_url_parsed)

  if not _url_parsed.netloc or not _url_parsed.scheme:
    print "Error: Please enter a valid url (%s)" % _url
    sys.exit(-1)

  cache_options = {}

  if options.test == 'gae':
    set_gae()
  elif options.test == 'nogae':
    unset_gae()
  elif options.test == 'memcache' or options.test == 'm':
    logging.info("Testing memcache")

  if options.cache == 'm' or options.cache == 'memcache':
    cache_options['handler'] = 'memcache'
  elif options.cache == 'f' or options.cache == 'file':
    cache_options['handler'] = 'file'
  # cache_options = {'handler': 'memcache'}

  try:
    db = DiffBot(cache_options)
    article = db.get_article(_url)
  except Exception, e:
    print "Error: ", e
    exit(-1)

  # Output document based on options
  if options.output == 'raw':
    print article
  elif options.output = 'json':
    from pprint import pprint
    pprint(article)
  else:
    print article

if __name__ == "__main__":
  main(os.environ.get('DIFFBOT_DEBUG', False))

