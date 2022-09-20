import birthdayfeed.config
import birthdayfeed.lang
import calendar
import csv
import datetime
import flask
import html
import icalendar
import os
import random
import requests
import resource
import waitress
import werkzeug.middleware.proxy_fix

config = birthdayfeed.config.Config()
app = flask.Flask(__name__)
app.wsgi_app = werkzeug.middleware.proxy_fix.ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_port=1)


def date_is_valid(year, month, day):
    try:
        datetime.date(year, month, day)
    except ValueError:
        return False
    return True


def get_all_birthdays(origin: datetime.date) -> list[datetime.date]:
    """Given a `datetime.date` object representing a date of birth, return a list of `datetime.date` objects
    representing all birthdays from birth to the next birthday from today or 85 years after the date of birth, whichever
    is greater."""

    if origin.year == 1:
        return [get_next_birthday(origin)]

    birthdays = [origin]
    today = datetime.date.today()
    next_year = today.year + 1

    offset = 0
    this_bd = origin
    while this_bd.year < next_year or offset < 85:
        offset = offset + 1
        try:
            this_bd = origin.replace(year=origin.year + offset)
        except ValueError:
            this_bd = datetime.date(origin.year + offset, 3, 1)
        birthdays.append(this_bd)

    return birthdays


def get_lang_class(key: str):
    lang_class_map = {
        'en-an': birthdayfeed.lang.EnglishAnniversaryTranslator,
        'en-bd': birthdayfeed.lang.EnglishBirthdayTranslator,
    }
    lang_class = lang_class_map.get(key, birthdayfeed.lang.EnglishBirthdayTranslator)
    app.logger.debug(f'Translation class is {lang_class}')
    return lang_class


def get_next_birthday(bd):
    """Given a datetime.date object representing a date of birth, return a datetime.date object representing the next
    time this birthday will be celebrated."""

    today = datetime.date.today()
    this_year = today.year
    next_year = today.year + 1

    if is_leap_day(bd) and not calendar.isleap(this_year):
        birthday_this_year = datetime.date(this_year, 3, 1)
    else:
        birthday_this_year = bd.replace(year=this_year)

    if today <= birthday_this_year:
        return birthday_this_year
    else:
        if is_leap_day(bd) and not calendar.isleap(next_year):
            return datetime.date(next_year, 3, 1)
        else:
            return birthday_this_year.replace(year=next_year)


def is_leap_day(d):
    return d.month == 2 and d.day == 29


def parse_row(row):
    year = int(row[1])
    if year == 0:
        year = 1
    month = int(row[2])
    day = int(row[3])
    return year, month, day


def row_is_valid(row):
    if len(row) < 4:
        return False
    return row[1].isdigit() and row[2].isdigit() and row[3].isdigit()


@app.before_request
def before_request():
    flask.g.request_id = random.randbytes(4).hex()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    app.logger.info(f'{flask.g.request_id} - before maxrss: {usage.ru_maxrss}')
    user_agent = flask.request.headers.get('user-agent')
    app.logger.info(f'{flask.g.request_id} ---- user-agent: {user_agent}')


@app.teardown_request
def teardown_request(response):
    usage = resource.getrusage(resource.RUSAGE_SELF)
    app.logger.info(f'{flask.g.request_id} teardown maxrss: {usage.ru_maxrss}')
    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    return flask.render_template('index.html')


@app.route('/birthdayfeed.atom')
def atom():
    if 'd' not in flask.request.args:
        return flask.redirect(flask.url_for('index'), 303)
    notification_days = int(flask.request.args.get('notification_days', '7'))

    lang_class = get_lang_class(flask.request.args.get('l', 'en-bd'))

    c = {}

    today = datetime.date.today()
    c['today_atom'] = f'{today.isoformat()}T00:00:00Z'

    c['birthdays'] = []
    notification_interval = datetime.timedelta(days=notification_days)
    data_location = flask.request.args.get('d')
    app.logger.info(f'{flask.g.request_id} - building atom: {data_location}')
    c['escaped_location'] = html.escape(data_location)
    response = requests.get(data_location, stream=True)
    for row in csv.reader(response.iter_lines(decode_unicode=True)):
        if not row_is_valid(row):
            continue

        name = html.escape(row[0])
        year, month, day = parse_row(row)

        if date_is_valid(year, month, day):
            birthday = datetime.date(year, month, day)
        else:
            continue

        next_birthday = get_next_birthday(birthday)
        if next_birthday - today <= notification_interval:
            t = lang_class(name, birthday, next_birthday)
            update_date = next_birthday - notification_interval
            update_string = f'{update_date.isoformat()}T00:00:00Z'
            id_name = name.replace(' ', '-')
            url = flask.url_for('index', _external=True)
            id_s = f'{url}{id_name}/{next_birthday.year}'
            c['birthdays'].append({'title': t.description, 'updated': update_string, 'id': id_s})

    resp = flask.make_response(flask.render_template('birthdayfeed.atom', c=c))
    resp.mimetype = 'application/atom+xml'
    return resp


@app.route('/birthdayfeed.ics')
def ics():
    if 'icsd' not in flask.request.args and 'd' not in flask.request.args:
        return flask.redirect(flask.url_for('index'), 303)

    lang_class = get_lang_class(flask.request.args.get('l', 'en-bd'))

    cal = icalendar.Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '-//birthdayfeed.subtlecoolness.com')
    cal.add('calscale', 'GREGORIAN')
    cal.add('x-wr-calname', 'birthdayfeed')
    cal.add('x-wr-timezone', 'UTC')
    cal.add('x-wr-caldesc', 'Birthday calendar provided by https://birthdayfeed.subtlecoolness.com/')

    today = datetime.date.today()
    dtstamp = datetime.datetime.combine(today, datetime.time())

    data_location = flask.request.args.get('icsd', flask.request.args.get('d'))
    app.logger.info(f'{flask.g.request_id} -- building ics: {data_location}')

    response = requests.get(data_location, stream=True)
    row_count = 0
    for row in csv.reader(response.iter_lines(decode_unicode=True)):
        if not row_is_valid(row):
            continue

        name = row[0]
        year, month, day = parse_row(row)

        if date_is_valid(year, month, day):
            birthday = datetime.date(year, month, day)
        else:
            continue

        if row_count < 10:
            for next_birthday in get_all_birthdays(birthday):
                t = lang_class(name, birthday, next_birthday)
                event = icalendar.Event()
                day_after = next_birthday + datetime.timedelta(days=1)
                uid_name = name.replace(' ', '')
                uid = f'{uid_name}{next_birthday.year}'
                event.add('summary', t.summary)
                event.add('dtstart', next_birthday)
                event.add('dtend', day_after)
                event.add('dtstamp', dtstamp)
                event.add('uid', f'{uid}@birthdayfeed.subtlecoolness.com')
                event.add('created', dtstamp)
                event.add('description', t.description)
                event.add('last-modified', dtstamp)
                event.add('transp', 'TRANSPARENT')
                cal.add_component(event)
            app.logger.info(f'{flask.g.request_id} ---- ics events: {len(cal.subcomponents)}')
            row_count += 1
        else:
            app.logger.info(f'{flask.g.request_id} max rows reached')
            event = icalendar.Event()
            event.add('summary', 'Thank you for using birthdayfeed')
            event.add('dtstart', today)
            event.add('dtend', dtstamp + datetime.timedelta(days=1))
            event.add('dtstamp', dtstamp)
            event.add('uid', f'thanks@birthdayfeed.subtlecoolness.com')
            event.add('created', dtstamp)
            event.add('description', 'The free version of birthdayfeed only supports 10 rows in a source file')
            event.add('last-modified', dtstamp)
            event.add('transp', 'TRANSPARENT')
            cal.add_component(event)
            response.close()
            break

    resp = flask.make_response(cal.to_ical())
    resp.mimetype = 'text/calendar'
    return resp


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'), 'birthdayfeed.png')


def main():
    app.logger.info(f'birthdayfeed {config.version}')
    waitress.serve(app, threads=config.web_server_threads)
