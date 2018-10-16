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

config = birthdayfeed.config.Config()
app = flask.Flask(__name__)


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'), 'birthdayfeed.png')


@app.route('/')
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


def get_next_birthday(bd):
    """Given a datetime.date object representing a date of birth, return a
    datetime.date object representing the next time this birthday will be
    celebrated."""

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

        next_birthday = get_next_birthday(birthday)
        bd_next = next_birthday.strftime('%A, %B %d, %Y')
        if next_birthday - today <= notification_interval:
            if year == 1:
                bd_orig = birthday.replace(year=1900).strftime('%B %d')
                title = f'{name}, born {bd_orig}, will celebrate a birthday on {bd_next}'
            else:
                age = next_birthday.year - birthday.year
                bd_orig = birthday.strftime('%B %d, %Y')
                title = f'{name}, born {bd_orig}, will turn {age} on {bd_next}'
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

        event = icalendar.Event()
        next_birthday = get_next_birthday(birthday)
        if year == 1:
            summary = f"{name}'s birthday"
            bd_orig = birthday.replace(year=1900).strftime('%B %d')
            bd_next = next_birthday.strftime('%A, %B %d, %Y')
            desc = f'{name}, born {bd_orig}, will celebrate a birthday on {bd_next}'
        else:
            age = next_birthday.year - birthday.year
            summary = f'{name} turns {age}'
            bd_orig = birthday.strftime('%B %d, %Y')
            bd_next = next_birthday.strftime('%A, %B %d, %Y')
            desc = f'{name}, born {bd_orig}, will turn {age} on {bd_next}'
        day_after = next_birthday + datetime.timedelta(days=1)
        uid_name = name.replace(' ', '')
        uid = f'{uid_name}{next_birthday.year}'
        event.add('summary', summary)
        event.add('dtstart', next_birthday)
        event.add('dtend', day_after)
        event.add('dtstamp', dtstamp)
        event.add('uid', uid + '@birthdayfeed.subtlecoolness.com')
        event.add('created', dtstamp)
        event.add('description', desc)
        event.add('last-modified', dtstamp)
        event.add('transp', 'TRANSPARENT')
        cal.add_component(event)

    resp = flask.make_response(cal.to_ical())
    resp.mimetype = 'text/plain'
    return resp


def main():
    logging.basicConfig(format=config.log_format, level='DEBUG', stream=sys.stdout)
    app.logger.debug(f'birthdayfeed {config.version}')
    app.logger.debug(f'Changing log level to {config.log_level}')
    logging.getLogger().setLevel(config.log_level)
    waitress.serve(app)
