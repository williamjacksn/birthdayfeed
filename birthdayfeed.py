import calendar
import csv
import datetime
import flask
import html
import icalendar
import os
import requests

app = flask.Flask(__name__)


@app.route('/favicon.ico')
def favicon():
    static_path = os.path.join(app.root_path, 'static')
    return flask.send_from_directory(static_path, 'birthdayfeed.png')


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

    template_vars = {}

    home = flask.url_for('index', _external=True)
    template_vars['home'] = home

    template_vars['link_self'] = flask.request.url
    template_vars['author'] = flask.request.args.get('a', 'birthdayfeed')

    today = datetime.date.today()
    template_vars['today_atom'] = '{}T00:00:00Z'.format(today.isoformat())

    icon = flask.url_for('static', filename='birthdayfeed.png', _external=True)
    template_vars['icon_url'] = icon

    logo = flask.url_for('static', filename='birthday+feed.png', _external=True)
    template_vars['logo_url'] = logo

    birthdays = []
    seven_days = datetime.timedelta(days=7)
    data_location = flask.request.args.get('d', '')
    template_vars['escaped_location'] = html.escape(data_location)
    response = requests.get(data_location)
    for row in csv.reader(response.content.decode().splitlines()):
        if not row_is_valid(row):
            continue

        app.logger.debug(row)
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
        if next_birthday - today <= seven_days:
            if year == 1:
                bd_orig = birthday.replace(year=1900).strftime('%B %d')
                bd_next = next_birthday.strftime('%A, %B %d, %Y')
                title = '{}, born {}, will celebrate a birthday on {}'
                title = title.format(name, bd_orig, bd_next)
            else:
                age = next_birthday.year - birthday.year
                bd_orig = birthday.strftime('%B %d, %Y')
                bd_next = next_birthday.strftime('%A, %B %d, %Y')
                title = '{}, born {}, will turn {} on {}'
                title = title.format(name, bd_orig, age, bd_next)
            update_date = next_birthday - seven_days
            update_string = '{}T00:00:00Z'.format(update_date.isoformat())
            id_name = name.replace(' ', '-')
            id_s = '{}{}/{}'.format(home, id_name, next_birthday.year)
            birthdays.append({'title': title, 'updated': update_string,
                              'id': id_s})
    template_vars['birthdays'] = birthdays

    template = flask.render_template('birthdayfeed.atom', **template_vars)
    resp = flask.make_response(template)
    resp.mimetype = 'application/atom+xml'
    return resp


@app.route('/birthdayfeed.ics')
def ics():
    if 'icsd' not in flask.request.args:
        return flask.redirect(flask.url_for('index'), 303)

    cal = icalendar.Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '-//birthdayfeed.subtlecoolness.com')
    cal.add('calscale', 'GREGORIAN')
    cal.add('x-wr-calname', 'birthdayfeed')
    cal.add('x-wr-timezone', 'UTC')
    cal.add('x-wr-caldesc', ('Birthday calendar provided by '
                             'http://birthdayfeed.subtlecoolness.com/'))

    today = datetime.date.today()
    dtstamp = datetime.datetime.combine(today, datetime.time())

    data_location = flask.request.args.get('icsd', '')
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
            summary = '{}\'s birthday'.format(name)
            bd_orig = birthday.replace(year=1900).strftime('%B %d')
            bd_next = next_birthday.strftime('%A, %B %d, %Y')
            desc = '{}, born {}, will celebrate a birthday on {}'
            desc = desc.format(name, bd_orig, bd_next)
        else:
            age = next_birthday.year - birthday.year
            summary = '{} turns {}'.format(name, age)
            bd_orig = birthday.strftime('%B %d, %Y')
            bd_next = next_birthday.strftime('%A, %B %d, %Y')
            desc = '{}, born {}, will turn {} on {}'
            desc = desc.format(name, bd_orig, age, bd_next)
        day_after = next_birthday + datetime.timedelta(days=1)
        uid_name = name.replace(' ', '')
        uid = '{}{}'.format(uid_name, next_birthday.year)
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
    app.run(host='0.0.0.0', debug=True)

if __name__ == u'__main__':
    main()
