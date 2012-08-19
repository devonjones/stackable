import cgi
import webapp2
import datetime
import sys
import re
from google.appengine.ext import db

class Defect(db.Model):
	defect_started = db.DateTimeProperty()
	comments = db.TextProperty()
	link = db.LinkProperty()

class AcraApplication(db.Model):
	package_name = db.StringProperty()

class AcraEventGroup(db.Model):
	defect = db.ReferenceProperty(Defect)
	app_version_codes = db.ListProperty(long)
	app_version_names = db.StringListProperty()
	android_versions = db.StringListProperty()
	phone_models = db.StringListProperty()
	brands = db.StringListProperty()
	products = db.StringListProperty()
	stack_trace = db.TextProperty()
	compare_stack_trace = db.TextProperty()

class AcraEvent(db.Model):
	timestamp = db.DateTimeProperty()
	report_id = db.StringProperty()
	app_version_code = db.IntegerProperty()
	app_version_name = db.StringProperty()
	package_name = db.StringProperty()
	file_path = db.StringProperty()
	android_version = db.StringProperty()
	phone_model = db.StringProperty()
	brand = db.StringProperty()
	product = db.StringProperty()
	build = db.TextProperty()
	total_mem_size = db.IntegerProperty()
	available_mem_size = db.IntegerProperty()
	custom_data = db.TextProperty()
	stack_trace = db.TextProperty()
	initial_configuration = db.TextProperty()
	crash_configuration = db.TextProperty()
	display = db.StringProperty(multiline=True)
	user_comment = db.TextProperty()
	user_app_start_date = db.DateTimeProperty()
	user_crash_date = db.DateTimeProperty()
	dumpsys_meminfo = db.TextProperty()
	dropbox = db.TextProperty()
	logcat = db.TextProperty()
	eventslog = db.TextProperty()
	radiolog = db.TextProperty()
	is_silent = db.StringProperty()
	device_id = db.StringProperty()
	installation_id = db.StringProperty()
	user_email = db.EmailProperty()
	device_features = db.TextProperty()
	environment = db.TextProperty()
	settings_system = db.TextProperty()
	settings_secure = db.TextProperty()
	shared_preferences = db.StringProperty(multiline=True)
	application_log = db.TextProperty()
	media_codec_list = db.TextProperty()
	thread_details = db.TextProperty()

class AcraEventHandler(webapp2.RequestHandler):
	def get(self, event_id):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.out.write("Placeholder: " + event_id)

class AcraEventGroupsHandler(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.out.write("Placeholder")

class AcraEventGroupHandler(webapp2.RequestHandler):
	def get(self, group_id):
		group = AcraEventGroup.get(group_id)
		lines = ["<html><head></head><body><H1>Group</H1><table>"]
		lines.append("<tr><th>App version codes</th><td>%s</td></tr>" % ', '.join([str(i) for i in group.app_version_codes]))
		lines.append("<tr><th>App Version Names</th><td>%s</td></tr>" % ', '.join(group.app_version_names))
		lines.append("<tr><th>Android Versions</th><td>%s</td></tr>" % ', '.join(group.android_versions))
		lines.append("<tr><th>Phone Models</th><td>%s</td></tr>" % ', '.join(group.phone_models))
		lines.append("<tr><th>Brands</th><td>%s</td></tr>" % ', '.join(group.brands))
		lines.append("<tr><th>Products</th><td>%s</td></tr>" % ', '.join(group.products))
		lines.append("</table>")
		lines.append("<pre>")
		lines.append(group.stack_trace)
		lines.append("</pre>")
		events = db.GqlQuery('SELECT * FROM AcraEvent WHERE ANCESTOR IS :1', group.key())
		count = 0
		for event in events:
			count += 1
			st = group.stack_trace
			sts = st.split('\n')
			lines.append("<li><a href='/event/" + str(event.key()) + "'>" + sts[0][:30] + "...</a>")
			lines.append("App version code: %s, " % event.app_version_code)
			lines.append("App Version Name: %s, " % event.app_version_name)
			lines.append("Android Version: %s, " % event.android_version)
			lines.append("Phone Model: %s, " % event.phone_model)
			lines.append("Brand: %s, " % event.brand)
			lines.append("Product: %s</li>" % event.product)
		lines.append("</ul>")
		lines.append("Count: %s" % count)
		lines.append("</html>")
		self.response.out.write('\n'.join(lines))

class ApplicationsHandler(webapp2.RequestHandler):
	def get(self):
		apps = AcraApplication.all()
		lines = ["<html><head></head><body><H1>Applications</H1><ul>"]
		for app in apps:
			lines.append("<li><a href='/application/" + app.package_name + "'>" + app.package_name + "</a></li>")
		lines.append("</html>")
		self.response.out.write('\n'.join(lines))

class ApplicationHandler(webapp2.RequestHandler):
	def get(self, app_id):
		app = AcraApplication.get_by_key_name(app_id)
		lines = ["<html><head></head><body><H1>Application: " + app.package_name + "</H1><ul>"]
		groups = db.GqlQuery('SELECT * FROM AcraEventGroup WHERE ANCESTOR IS :1', app.key())
		count = 0
		for group in groups:
			count += 1
			st = group.stack_trace
			sts = st.split('\n')
			lines.append("<li><a href='/group/" + str(group.key()) + "'>" + sts[0][:30] + "...</a>")
			lines.append("App version codes: %s, " % group.app_version_codes)
			lines.append("App Version Names: %s, " % group.app_version_names)
			lines.append("Android Versions: %s, " % group.android_versions)
			lines.append("Phone Models: %s, " % group.phone_models)
			lines.append("Brands: %s, " % group.brands)
			lines.append("Products: %s</li>" % group.products)
		lines.append("</ul>")
		lines.append("Count: %s" % count)
		lines.append("</html>")
		self.response.out.write('\n'.join(lines))

class AcraEventsHandler(webapp2.RequestHandler):
	def post(self):
		acceptable = ['timestamp', 'report_id', 'app_version_code',
			'app_version_name', 'package_name', 'file_path', 'phone_model',
			'android_version', 'build', 'brand', 'product', 'total_mem_size',
			'available_mem_size', 'custom_data', 'stack_trace',
			'initial_configuration', 'crash_configuration', 'display',
			'user_comment', 'user_app_start_date', 'user_crash_date',
			'dumpsys_meminfo', 'dropbox', 'logcat', 'eventslog', 'radiolog',
			'is_silent', 'device_id', 'installation_id', 'user_email',
			'device_features', 'environment', 'settings_system',
			'settings_secure', 'shared_preferences', 'application_log',
			'media_codec_list', 'thread_details']
		args = {k.lower(): v for k, v in self.request.POST.iteritems() if k.lower() in acceptable}
		if AcraEvent.get_by_key_name(args['report_id']):
			self.response.status = 409
			return
		if args['timestamp']:
			args['timestamp'] = datetime.datetime.strptime(
				args['timestamp'], '%m/%d/%Y %H:%M:%S')
		else:
			args['timestamp'] = datetime.datetime.now()
		if args['app_version_code']:
			args['app_version_code'] = int(args['app_version_code'])
		if args['total_mem_size']:
			args['total_mem_size'] = long(args['total_mem_size'])
		if args['available_mem_size']:
			args['available_mem_size'] = long(args['available_mem_size'])
		if args['user_app_start_date']:
			args['user_app_start_date'] = self.parse_user_date(
				args['user_app_start_date'])
		if args['user_crash_date']:
			args['user_crash_date'] = self.parse_user_date(args['user_crash_date'])
		if args['app_version_name'] and args['app_version_name'][0] == "'":
			args['app_version_name'] = args['app_version_name'][1:]
		if args['android_version'] and args['android_version'][0] == "'":
			args['android_version'] = args['android_version'][1:]
		group = self.get_group( args['app_version_code'],
			args['app_version_name'], args['android_version'],
			args['phone_model'], args['brand'], args['product'],
			args['stack_trace'], args['package_name'])
		event = AcraEvent(key_name=args['report_id'], parent=group, **args)
		event.put()
		self.response.status = 201

	def parse_user_date(self, date):
		parts = date.split(".")
		return datetime.datetime.strptime(parts[0], "%Y-%m-%dT%H:%M:%S")

	def get_group(self, app_version_code, app_version_name, android_version,
			phone_model, brand, product, stack_trace, package_name):
		groups = db.GqlQuery("SELECT * "
			"FROM AcraEventGroup")
		comp_st = munge_stack_trace(stack_trace)
		for group in groups:
			if group.compare_stack_trace == comp_st:
				self.add_group_filters(
					group, app_version_code, app_version_name,
					android_version, phone_model, brand, product)
				return group
		app = self.get_application(package_name)
		group = AcraEventGroup(parent=app, stack_trace=stack_trace, compare_stack_trace=comp_st)
		group.app_version_codes = [app_version_code]
		group.app_version_names = [app_version_name]
		group.android_versions = [android_version]
		group.phone_models = [phone_model]
		group.brands = [brand]
		group.products = [product]
		group.put()
		return group

	def add_group_filters(self, group, app_version_code, app_version_name,
			android_version, phone_model, brand, product):
		change = False
		if not app_version_code in group.app_version_codes:
			group.app_version_codes.append(app_version_code)
			change = True
		if not app_version_name in group.app_version_names:
			group.app_version_names.append(app_version_name)
			change = True
		if not android_version in group.android_versions:
			group.android_versions.append(android_version)
			change = True
		if not phone_model in group.phone_models:
			group.phone_models.append(phone_model)
			change = True
		if not brand in group.brands:
			group.brands.append(brand)
			change = True
		if not product in group.products:
			group.products.append(product)
			change = True
		if change:
			group.put()

	def get_application(self, package_name):
		app = AcraApplication.get_by_key_name(package_name)
		if app:
			return app
		app = AcraApplication(key_name=package_name, package_name=package_name)
		app.put()
		return app

def munge_stack_trace(stack_trace):
	testlines = stack_trace.split('\n')
	results = []
	for test in testlines:
		results.append(munge_row(test))
	return '\n'.join(results)

def munge_row(row):
	if row.strip().startswith('at android.'):
		return re.sub(r'java:\d+', 'java:-', row)
	if row.strip().startswith('at java.'):
		return re.sub(r'java:\d+', 'java:-', row)
	if row.strip().startswith('at com.android.'):
		return re.sub(r'java:\d+', 'java:-', row)
	if row.strip().startswith('at dalvik.'):
		return re.sub(r'java:\d+', 'java:-', row)
	return row

app = webapp2.WSGIApplication([
	('/event', AcraEventsHandler),
	(r'/event/(\d+)', AcraEventHandler),
	('/group', AcraEventGroupsHandler),
	(r'/group/([a-zA-Z0-9-]+)', AcraEventGroupHandler),
	('/application', ApplicationsHandler),
	(r'/application/([a-zA-Z.]+)', ApplicationHandler)
], debug=True)
