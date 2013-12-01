# -*- coding: utf-8 -*-

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import cgi
import os
import urllib2
import csv
from datetime import date, timedelta

class birthdayfeed(webapp.RequestHandler):
	def get(self):
		bf_tmpl = {}
		bf_tmpl['bf_home'] = 'http://birthdayfeed.subtlecoolness.com/'
		bf_tmpl['bf_d_loc'] = self.request.get('d')
		bf_tmpl['bf_d_loc_escaped'] = cgi.escape(bf_tmpl['bf_d_loc'])
		if bf_tmpl['bf_d_loc']:
			bf_tmpl['bf_self'] = self.request.url
			bf_birthdays = []
			bf_today = date.today()
			bf_tmpl['bf_today_atom'] = bf_today.strftime('%Y-%m-%dT00:00:00Z')
			if self.request.get('a'):
				bf_tmpl['bf_author'] = self.request.get('a')
			else:
				bf_tmpl['bf_author'] = 'birthdayfeed'
			bf_seven_days = timedelta(days=7)
			bf_data_file = urllib2.urlopen(bf_tmpl['bf_d_loc'])
			bf_csv = csv.reader(bf_data_file)
			for bf_data_entry in bf_csv:
				if len(bf_data_entry) > 3:
					bf_bd_name = bf_data_entry[0]
					bf_bd_year = int(bf_data_entry[1])
					if bf_bd_year == 0:
						bf_bd_year = 1
					bf_bd_month = int(bf_data_entry[2])
					bf_bd_day = int(bf_data_entry[3])
					try:
						bf_bd = date(bf_bd_year, bf_bd_month, bf_bd_day)
					except ValueError:
						continue
					try:
						bf_bd_this_year = date(bf_today.year, bf_bd_month, bf_bd_day)
					except ValueError:
						if bf_bd_month == 2 and bf_bd_day == 29:
							bf_bd_this_year = date(bf_today.year, 3, 1)
					if bf_today <= bf_bd_this_year:
						bf_bd_next = bf_bd_this_year
					else:
						try:
							bf_bd_next = date(bf_today.year + 1, bf_bd_month, bf_bd_day)
						except ValueError:
							if bf_bd_month == 2 and bf_bd_day == 29:
								bf_bd_next = date(bf_today.year + 1, 3, 1)
					if bf_bd_next - bf_today <= bf_seven_days:
						if bf_bd.year == 1:
							bf_t = bf_bd_name + ', born ' + bf_bd.strftime('%B %d') + ', will celebrate a birthday on ' + bf_bd_next.strftime('%A, %B %d, %Y')
						else:
							bf_age = bf_bd_next.year - bf_bd.year
							bf_t = bf_bd_name + ', born ' + bf_bd.strftime('%B %d, %Y') + ', will turn ' + str(bf_age) + ' on ' + bf_bd_next.strftime('%A, %B %d, %Y')
						bf_updated = (bf_bd_next - bf_seven_days).strftime('%Y-%m-%dT00:00:00Z')
						bf_id = bf_tmpl['bf_home'] + bf_bd_name.replace(' ','-') + '/' + str(bf_bd_next.year)
						bf_birthdays.append({'bf_t': bf_t, 'bf_updated': bf_updated, 'bf_id': bf_id})
			bf_tmpl['bf_birthdays'] = bf_birthdays
			path = os.path.join(os.path.dirname(__file__), 'birthdayfeed.atom')
			self.response.headers['Content-Type'] = 'application/atom+xml'
			self.response.out.write(template.render(path, bf_tmpl))
		else:
			self.response.set_status(303)
			self.response.headers['Location'] = bf_tmpl['bf_home']

application = webapp.WSGIApplication([('/birthdayfeed.atom', birthdayfeed)], debug = True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
