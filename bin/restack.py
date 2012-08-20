#!/usr/bin/python
import gdata.spreadsheet.service
import gdata.spreadsheet
import gdata.service
import getopt
import sys
import string
import httplib
import urllib
import argparse

class ACRAReader:
	def __init__(self, user, password, archive, dest_host):
		self.client = gdata.spreadsheet.service.SpreadsheetsService()
		self.client.email = user
		self.client.password = password
		self.client.source = 'ACRA Importer'
		self.client.ProgrammaticLogin()
		self.client.curr_key = ''
		self.client.curr_worksheet_id = ''
		self.client.archive_worksheet_id = ''
		self.list_feed = None
		self.archive = archive

		self._KEY_RENAME = dict({'androidversion': 'android_version',
			'applicationlog': 'application_log',
			'appversioncode': 'app_version_code',
			'appversionname': 'app_version_name',
			'availablememsize': 'available_mem_size',
			'crashconfiguration': 'crash_configuration',
			'customdata': 'custom_data',
			'devicefeatures': 'device_features',
			'deviceid': 'device_id',
			'dumpsysmeminfo': 'dumpsys_meminfo',
			'filepath': 'file_path',
			'initialconfiguration': 'initial_configuration',
			'installationid': 'installation_id',
			'issilent': 'is_silent',
			'mediacodeclist': 'media_codec_list',
			'packagename': 'package_name',
			'phonemodel': 'phone_model',
			'reportid': 'report_id',
			'settingssecure': 'settings_secure',
			'settingssystem': 'settings_system',
			'sharedpreferences': 'shared_preferences',
			'stacktrace': 'stack_trace',
			'threaddetails': 'thread_details',
			'totalmemsize': 'total_mem_size',
			'userappstartdate': 'user_app_start_date',
			'usercomment': 'user_comment',
			'usercrashdate': 'user_crash_date',
			'useremail': 'user_email'})

		self._http_headers = {"Content-type": "application/x-www-form-urlencoded",
			"Accept": "text/plain"}
		self._dest_host = dest_host
	
	def _PromptForSpreadsheet(self):
		# Get the list of spreadsheets
		feed = self.client.GetSpreadsheetsFeed()
		self._PrintFeed(feed)
		input = raw_input('\nSelection: ')
		id_parts = feed.entry[string.atoi(input)].id.text.split('/')
		self.curr_key = id_parts[len(id_parts) - 1]

	def _PromptForWorksheet(self, prompt = "Selection: "):
		# Get the list of worksheets
		feed = self.client.GetWorksheetsFeed(self.curr_key)
		if len(feed.entry) > 1:
			self._PrintFeed(feed)
			input = raw_input(prompt)
		else:
			input = '0'
		id_parts = feed.entry[string.atoi(input)].id.text.split('/')
		return id_parts[len(id_parts) - 1]

	def _DumpRows(self):
		self.list_feed = self.client.GetListFeed(self.curr_key, self.client.curr_worksheet_id)
	
	def _ProcessRows(self):
		for i, row in enumerate(self.list_feed.entry):
			print "Processing row: %i\n" % i
			self._PostData(row)

	def _PostData(self, row):
		row_data = self._MungeKeys(row.custom)

		params = urllib.urlencode(row_data)
		headers = self._http_headers
		conn = httplib.HTTPConnection(self._dest_host)
		conn.request("POST", "/event", params, headers)
		response = conn.getresponse()
		data = response.read()
		conn.close()

		if response.status < 200 or response.status > 299:
			print response.status, response.reason
			print data
		else:
			if (self.archive and self._ArchiveRow(row_data)):
				self._DeleteRow(row)

	def _ArchiveRow(self, row):
		"""Toss the row into another tab in the spreadsheet"""
		try:
			self.client.InsertRow(row, self.curr_key, self.client.archive_worksheet_id)
		except:
			return False
		return True
	
	def _DeleteRow(self, row):
		"""Delete the data from the source tab"""
		print "Deleting stuff!"
		self.client.DeleteRow(row)


	def _MungeKeys(self, row):
		"""Rewrite the dict to use keys that ACRA uses instead of the dumbed down ones
		out of the gdata api"""

		result = {}

		for key in row:
			if row[key].text:
				value = row[key].text.encode('utf-8')
			else:
				value = ''

			if self._KEY_RENAME.has_key(key):
				result[self._KEY_RENAME[key]] = value
			else:
				result[key] = value

		return result
		

	def _PrintFeed(self, feed):
		for i, entry in enumerate(feed.entry):
			if isinstance(feed, gdata.spreadsheet.SpreadsheetsCellsFeed):
				print '%s %s\n' % (entry.title.text, entry.content.text)
			elif isinstance(feed, gdata.spreadsheet.SpreadsheetsListFeed):
				print '%s %s %s' % (i, entry.title.text, entry.content.text)
				print 'Contents:'
				for key in entry.custom:  
					print '  %s: %s' % (key, entry.custom[key].text) 
				print '\n',
			else:
				print '%s %s\n' % (i, entry.title.text)

	def Run(self):
		self._PromptForSpreadsheet()
		self.client.curr_worksheet_id = self._PromptForWorksheet(
				"Source worksheet: ")
		if self.archive:
			self.client.archive_worksheet_id = self._PromptForWorksheet(
					"Target worksheet: ")

		self._DumpRows()
		self._ProcessRows()

def main(user, password, archive, dest_host):
	reader = ACRAReader(user, password, archive, dest_host)
	reader.Run()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
			description = 'Process ACRA spreadsheet to migrate lines into Stackable')
	parser.add_argument('-u', '--user', required=True,
			help='Google account username')
	parser.add_argument('-p', '--password', required=True,
			help='Google account password')
	parser.add_argument('-a', '--archive', action='store_true', default=True,
			help='Archive rows and delete them from the source sheet')
	parser.add_argument('-d', '--dest_host', default="127.0.0.1:8080",
			help='Host running Stackable. Default: 127.0.0.1:8080')
	
	options = parser.parse_args()

	main(options.user, options.password, options.archive, options.dest_host)
