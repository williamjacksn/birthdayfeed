import birthdayfeed.config
import calendar
import csv
import datetime
import flask
import html
import icalendar
import logging
import os
import requests
import sys
import waitress
import werkzeug.middleware.proxy_fix

from typing import List

config = birthdayfeed.config.Config()
app = flask.Flask(__name__)
app.wsgi_app = werkzeug.middleware.proxy_fix.ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_port=1)


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'), 'birthdayfeed.png')


@app.route('/', methods=['GET', 'POST'])
def index():
    return flask.render_template('index.html')


def row_is_valid(row):
    if len(row) < 4:
        return False
    return row[1].isdigit() and row[2].isdigit() and row[3].isdigit()


def date_is_valid(year, month, day):
    try:
        datetime.date(year, month, day)
    except ValueError:
        return False
    return True


def is_leap_day(d):
    return d.month == 2 and d.day == 29


def get_all_birthdays(bd: datetime.date) -> List[datetime.date]:
    """Given a datetime.date object representing a date of birth, return a list of datetime.date objects representing
    all birthdays from birth to the next birthday from today or 85 years after the date of birth, whichever is
    greater."""

    if bd.year == 1:
        return [get_next_birthday(bd)]

    birthdays = [bd]
    today = datetime.date.today()
    next_year = today.year + 1

    offset = 0
    this_bd = bd
    while this_bd.year < next_year or offset < 85:
        offset = offset + 1
        try:
            this_bd = bd.replace(year=bd.year + offset)
        except ValueError:
            this_bd = datetime.date(bd.year + offset, 3, 1)
        birthdays.append(this_bd)

    return birthdays


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


@app.route('/birthdayfeed.atom')
def atom():
    if 'd' not in flask.request.args:
        return flask.redirect(flask.url_for('index'), 303)
    notification_days = 7
    if 'notification_days' in flask.request.args:
        notification_days = int(flask.request.args['notification_days'])

    c = {}

    today = datetime.date.today()
    c['today_atom'] = f'{today.isoformat()}T00:00:00Z'

    c['birthdays'] = []
    notification_interval = datetime.timedelta(days=notification_days)
    data_location = flask.request.args.get('d')
    c['escaped_location'] = html.escape(data_location)
    response = requests.get(data_location)
    for row in csv.reader(response.content.decode().splitlines()):
        if not row_is_valid(row):
            continue

        name = html.escape(row[0])
        year = int(row[1])
        if year == 0:
            year = 1
        month = int(row[2])
        day = int(row[3])

        if date_is_valid(year, month, day):
            birthday = datetime.date(year, month, day)
        else:
            continue

        next_birthday = get_next_birthday(birthday)
        bd_next = f'{next_birthday:%A, %B} {next_birthday.day}, {next_birthday.year}'
        if next_birthday - today <= notification_interval:
            if year == 1:
                title = f'{name}, born {birthday:%B} {birthday.day}, will celebrate a birthday on {bd_next}'
            else:
                age = next_birthday.year - birthday.year
                title = f'{name}, born {birthday:%B} {birthday.day}, {birthday.year}, will turn {age} on {bd_next}'
            update_date = next_birthday - notification_interval
            update_string = f'{update_date.isoformat()}T00:00:00Z'
            id_name = name.replace(' ', '-')
            url = flask.url_for('index', _external=True)
            id_s = f'{url}{id_name}/{next_birthday.year}'
            c['birthdays'].append({'title': title, 'updated': update_string, 'id': id_s})

    resp = flask.make_response(flask.render_template('birthdayfeed.atom', c=c))
    resp.mimetype = 'application/atom+xml'
    return resp


@app.route('/birthdayfeed.ics')
def ics():
    if 'icsd' not in flask.request.args and 'd' not in flask.request.args:
        return flask.redirect(flask.url_for('index'), 303)

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
    response = requests.get(data_location)
    for row in csv.reader(response.content.decode().splitlines()):
        if not row_is_valid(row):
            continue

        name = row[0]
        year = int(row[1])
        if year == 0:
            year = 1
        month = int(row[2])
        day = int(row[3])

        if date_is_valid(year, month, day):
            birthday = datetime.date(year, month, day)
        else:
            continue

        for next_birthday in get_all_birthdays(birthday):
            event = icalendar.Event()
            bd_next = f'{next_birthday:%A, %B} {next_birthday.day}, {next_birthday.year}'
            if year == 1:
                summary = f"{name}'s birthday"
                desc = f'{name}, born {birthday:%B} {birthday.day}, will celebrate a birthday on {bd_next}'
            else:
                age = next_birthday.year - birthday.year
                if age == 0:
                    summary = f'{name} is born'
                    desc = f'{name} was born on {bd_next}'
                else:
                    summary = f'{name} turns {age}'
                    desc = f'{name}, born {birthday:%B} {birthday.day}, {birthday.year}, will turn {age} on {bd_next}'
            day_after = next_birthday + datetime.timedelta(days=1)
            uid_name = name.replace(' ', '')
            uid = f'{uid_name}{next_birthday.year}'
            event.add('summary', summary)
            event.add('dtstart', next_birthday)
            event.add('dtend', day_after)
            event.add('dtstamp', dtstamp)
            event.add('uid', f'{uid}@birthdayfeed.subtlecoolness.com')
            event.add('created', dtstamp)
            event.add('description', desc)
            event.add('last-modified', dtstamp)
            event.add('transp', 'TRANSPARENT')
            cal.add_component(event)

    resp = flask.make_response(cal.to_ical())
    resp.mimetype = 'text/calendar'
    return resp


def main():
    logging.basicConfig(format=config.log_format, level='DEBUG', stream=sys.stdout)
    app.logger.debug(f'birthdayfeed {config.version}')
    app.logger.debug(f'Changing log level to {config.log_level}')
    logging.getLogger().setLevel(config.log_level)
    waitress.serve(app)
