import calendar
import cgi
import csv
import datetime
import os
import requests

from flask import (Flask, make_response, redirect, render_template, request,
    send_from_directory, url_for)

app = Flask(__name__)
app.debug = True

@app.route(u'/favicon.ico')
def favicon():
    static_path = os.path.join(app.root_path, u'static')
    return send_from_directory(static_path, u'birthdayfeed.png')

@app.route(u'/')
def index():
    return render_template(u'index.html')

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
    '''Given a datetime.date object representing a date of birth, return a
    datetime.date object representing the next time this birthday will be
    celebrated.'''

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

@app.route(u'/birthdayfeed.atom')
def atom():
    if u'd' not in request.args:
        return redirect(url_for(u'index'), 303)

    template_vars = dict()

    home = url_for(u'index', _external=True)
    template_vars[u'home'] = home

    template_vars[u'link_self'] = request.url
    template_vars[u'author'] = request.args.get(u'a', u'birthdayfeed')

    today = datetime.date.today()
    template_vars[u'today_atom'] = u'{}T00:00:00Z'.format(today.isoformat())

    icon = url_for(u'static', filename=u'birthdayfeed.png', _external=True)
    template_vars[u'icon_url'] = icon

    logo = url_for(u'static', filename=u'birthday+feed.png', _external=True)
    template_vars[u'logo_url'] = logo

    birthdays = list()
    seven_days = datetime.timedelta(days=7)
    data_location = request.args.get(u'd', u'')
    template_vars[u'escaped_location'] = cgi.escape(data_location)
    response = requests.get(data_location)
    for row in csv.reader(response.iter_lines()):
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
        if next_birthday - today <= seven_days:
            if year == 1:
                bd_orig = birthday.strftime(u'%B %d')
                bd_next = next_birthday.strftime(u'%A, %B %d, %Y')
                title = u'{}, born {}, will celebrate a birthday on {}'
                title = title.format(name, bd_orig, bd_next)
            else:
                age = next_birthday.year - birthday.year
                bd_orig = birthday.strftime(u'%B %d, %Y')
                bd_next = next_birthday.strftime(u'%A, %B %d, %Y')
                title = u'{}, born {}, will turn {} on {}'
                title = title.format(name, bd_orig, age, bd_next)
            update_date = next_birthday - seven_days
            update_string = u'{}T00:00:00Z'.format(update_date.isoformat())
            id_name = name.replace(u' ', u'-')
            id_s = u'{}{}/{}'
            id_s = id_s.format(home, id_name, next_birthday.year)
            birthdays.append({
                u'title': title,
                u'updated': update_string,
                u'id': id_s
            })
    template_vars[u'birthdays'] = birthdays

    template = render_template(u'birthdayfeed.atom', **template_vars)
    resp = make_response(template)
    resp.mimetype = u'application/atom+xml'
    return resp

@app.route(u'/birthdayfeed.ics')
def ics():
    if u'icsd' not in request.args:
        return redirect(url_for(u'index'), 303)

    template_vars = dict()

    today = datetime.date.today()
    template_vars[u'dtstamp'] = u'{}T00:00:00Z'.format(today.isoformat())

    birthdays = list()
    data_location = request.args.get(u'icsd', u'')
    response = requests.get(data_location)
    for row in csv.reader(response.iter_lines()):
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
        if year == 1:
            summary = u'{}\'s birthday'.format(name)
            bd_orig = birthday.strftime(u'%B %d')
            bd_next = next_birthday.strftime(u'%A\\, %B %d\\, %Y')
            desc = u'{}\\, \r\n born {}\\, \r\n will '.format(name, bd_orig)
            desc = u'{}celebrate a birthday on \r\n {}'.format(desc, bd_next)
        else:
            age = next_birthday.year - birthday.year
            summary = u'{} turns {}'.format(name, age)
            bd_orig = birthday.strftime(u'%B %d\\, %Y')
            bd_next = next_birthday.strftime(u'%A\\, %B %d\\, %Y')
            desc = '{}\\, \r\n born {}\\, \r\n will turn {} on \r\n {}'
            desc = desc.format(name, bd_orig, age, bd_next)
        dtstart = next_birthday.strftime(u'%Y%m%d')
        day_after = next_birthday + datetime.timedelta(days=1)
        dtend = day_after.strftime(u'%Y%m%d')
        uid_name = name.replace(u' ', u'')
        uid = u'{}{}'.format(uid_name, next_birthday.year)
        birthdays.append({
            u'dtstart': dtstart,
            u'dtend': dtend,
            u'uid': uid,
            u'summary': summary,
            u'description': desc
        })
    template_vars[u'birthdays'] = birthdays

    resp = make_response(render_template(u'birthdayfeed.ics', **template_vars))
    resp.mimetype = u'text/plain'
    return resp

if __name__ == u'__main__':
    app.run(host=u'0.0.0.0')
