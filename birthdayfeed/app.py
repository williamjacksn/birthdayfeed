import calendar
import csv
import datetime
import html
import os
import resource
import secrets
from collections.abc import Iterator

import flask
import icalendar
import requests
import waitress
import werkzeug.middleware.proxy_fix

import birthdayfeed.lang

__version__ = "2025.0"
__web_server_threads__ = int(os.getenv("WEB_SERVER_THREADS", 8))
__scheme__ = os.getenv("SCHEME", "https")

app = flask.Flask(__name__)
app.wsgi_app = werkzeug.middleware.proxy_fix.ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_port=1
)


def date_is_valid(year: int, month: int, day: int) -> bool:
    try:
        datetime.date(year, month, day)
    except ValueError:
        return False
    return True


def decoded_response(response: requests.Response) -> Iterator[str]:
    line: bytes
    for line in response.iter_lines():
        yield line.decode()


def get_all_birthdays(origin: datetime.date) -> list[datetime.date]:
    """Given a `datetime.date` object representing a date of birth, return a list of
    `datetime.date` objects representing all birthdays from birth to the next birthday
    from today or 85 years after the date of birth, whichever is greater."""

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


def get_lang_class(key: str) -> type[birthdayfeed.lang.DefaultTranslator]:
    lang_class_map = {
        "en-an": birthdayfeed.lang.EnglishAnniversaryTranslator,
        "en-bd": birthdayfeed.lang.EnglishBirthdayTranslator,
    }
    lang_class = lang_class_map.get(key, birthdayfeed.lang.EnglishBirthdayTranslator)
    app.logger.debug(f"Translation class is {lang_class}")
    return lang_class


def get_next_birthday(bd: datetime.date) -> datetime.date:
    """Given a `datetime.date` object representing a date of birth, return a
    `datetime.date` object representing the next time this birthday will be
    celebrated."""

    now = datetime.datetime.now(tz=datetime.UTC)
    today = now.date()
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


def is_leap_day(d: datetime.date) -> bool:
    return d.month == 2 and d.day == 29


def parse_row(row: list[str]) -> tuple[int, int, int]:
    year = int(row[1])
    if year == 0:
        year = 1
    month = int(row[2])
    day = int(row[3])
    return year, month, day


def row_is_valid(row: list[str]) -> bool:
    if len(row) < 4:
        return False
    return row[1].isdigit() and row[2].isdigit() and row[3].isdigit()


@app.before_request
def before_request() -> None:
    flask.g.request_id = secrets.token_hex(4)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    app.logger.info(f"{flask.g.request_id} - before maxrss: {usage.ru_maxrss}")
    user_agent = flask.request.headers.get("user-agent")
    app.logger.info(f"{flask.g.request_id} ---- user-agent: {user_agent}")


@app.teardown_request
def teardown_request(response: flask.Response) -> flask.Response:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    app.logger.info(f"{flask.g.request_id} teardown maxrss: {usage.ru_maxrss}")
    return response


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    flask.g.scheme = __scheme__
    return flask.render_template("index.html")


@app.route("/birthdayfeed.atom")
def atom() -> flask.Response:
    if "d" not in flask.request.args:
        return flask.redirect(flask.url_for("index"), 303)

    flask.g.index = flask.url_for("index", _external=True, _scheme=__scheme__)
    notification_days = int(flask.request.args.get("notification_days", "7"))

    lang_class = get_lang_class(flask.request.args.get("l", "en-bd"))

    c = {}

    today = datetime.date.today()
    c["today_atom"] = f"{today.isoformat()}T00:00:00Z"

    c["birthdays"] = []
    notification_interval = datetime.timedelta(days=notification_days)
    data_location = flask.request.args.get("d")
    app.logger.info(f"{flask.g.request_id} - building atom: {data_location}")
    c["escaped_location"] = html.escape(data_location)
    response = requests.get(data_location, stream=True, timeout=10)
    for row in csv.reader(decoded_response(response)):
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
            update_string = f"{update_date.isoformat()}T00:00:00Z"
            id_name = name.replace(" ", "-")
            id_s = f"{flask.g.index}{id_name}/{next_birthday.year}"
            c["birthdays"].append(
                {"title": t.description, "updated": update_string, "id": id_s}
            )

    flask.g.scheme = __scheme__
    resp = flask.make_response(flask.render_template("birthdayfeed.atom", c=c))
    resp.mimetype = "application/atom+xml"
    return resp


@app.route("/birthdayfeed.ics")
def ics() -> flask.Response:
    if "icsd" not in flask.request.args and "d" not in flask.request.args:
        return flask.redirect(flask.url_for("index"), 303)

    def generate(
        csv_url: str,
        lang_class: type[birthdayfeed.lang.DefaultTranslator],
        cal_type: str = "full",
    ) -> Iterator[bytes]:
        if cal_type not in ("next", "full"):
            cal_type = "full"
        cal = icalendar.Calendar()
        cal.add("version", "2.0")
        cal.add("prodid", "-//birthdayfeed.subtlecoolness.com")
        cal.add("calscale", "GREGORIAN")
        cal.add("x-wr-calname", "birthdayfeed")
        cal.add("x-wr-timezone", "UTC")
        cal.add(
            "x-wr-caldesc", f"Birthday calendar provided by {flask.request.host_url}"
        )
        for line in cal.to_ical().splitlines(keepends=True):
            if not line.startswith(b"END:"):
                yield line

        dtstamp = datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC)

        response = requests.get(csv_url, stream=True, timeout=10)
        for row in csv.reader(decoded_response(response)):
            if not row_is_valid(row):
                continue

            name = row[0]
            year, month, day = parse_row(row)

            if date_is_valid(year, month, day):
                birthday = datetime.date(year, month, day)
            else:
                continue

            if cal_type == "full":
                birthdays = get_all_birthdays(birthday)
            else:
                birthdays = [get_next_birthday(birthday)]
            for next_birthday in birthdays:
                t = lang_class(name, birthday, next_birthday)
                event = icalendar.Event()
                day_after = next_birthday + datetime.timedelta(days=1)
                uid_name = name.replace(" ", "")
                uid = f"{uid_name}{next_birthday.year}"
                event.add("summary", t.summary)
                event.add("dtstart", next_birthday)
                event.add("dtend", day_after)
                event.add("dtstamp", dtstamp)
                event.add("uid", f"{uid}@{flask.request.host}")
                event.add("created", dtstamp)
                event.add("description", t.description)
                event.add("last-modified", dtstamp)
                event.add("transp", "TRANSPARENT")
                yield event.to_ical()

        for line in cal.to_ical().splitlines(keepends=True):
            if line.startswith(b"END:"):
                yield line

    data_location = flask.request.args.get("icsd", flask.request.args.get("d"))
    app.logger.info(f"{flask.g.request_id} -- building ics: {data_location}")
    _lang_class = get_lang_class(flask.request.args.get("l", "en-bd"))
    _cal_type = flask.request.values.get("t", "full")

    resp = flask.make_response(
        flask.stream_with_context(generate(data_location, _lang_class, _cal_type))
    )
    resp.mimetype = "text/calendar"
    return resp


@app.route("/favicon.ico")
def favicon() -> flask.Response:
    return flask.send_from_directory(
        os.path.join(app.root_path, "static"), "birthdayfeed.png"
    )


def main() -> None:
    app.logger.info(f"birthdayfeed {__version__}")
    waitress.serve(app, threads=__web_server_threads__)
