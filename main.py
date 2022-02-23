import datetime
import time
import statistics

import argh
import flask
import flask_mongoengine
import humanize

app = flask.Flask(__name__)
app.secret_key = "secret"
app.config["MONGODB_DB"] = "catfood-1"
db = flask_mongoengine.MongoEngine(app)


class CalorieRecord(db.Document):
    d = db.IntField()  # yyyymmdd
    t = db.IntField()  # MMSS
    e = db.IntField()  # epochtime
    calories = db.IntField()


@app.route("/")
def index():
    today = datetime.datetime.today()
    today_db_str = today.strftime("%Y%m%d")

    yesterday = today - datetime.timedelta(days=1)
    yesterday_db_str = yesterday.strftime("%Y%m%d")

    hours_ago = int(flask.request.args.get("hours", 24))
    epochtime_now = int(today.timestamp())
    epochtime_hours_ago = epochtime_now - (hours_ago * 60 * 60)

    records_hours = list(
        CalorieRecord.objects.filter(e__gt=epochtime_hours_ago).order_by("-e").all()
    )
    records_today = list(
        CalorieRecord.objects.filter(d=today_db_str).order_by("-e").all()
    )
    records_yesterday = list(
        CalorieRecord.objects.filter(d=yesterday_db_str).order_by("-e").all()
    )

    records_hours_sum = sum([r.calories for r in records_hours])
    records_today_sum = sum([r.calories for r in records_today])
    records_yesterday_sum = sum([r.calories for r in records_yesterday])

    last7days_db = CalorieRecord.objects.filter(
        d__gt=(int(yesterday_db_str) - 7)
    ).aggregate([{"$group": {"_id": "$d", "calories": {"$push": "$calories"}}}])

    last7days = list()
    last7days_sums = list()
    for r in last7days_db:
        d = str(r["_id"])
        cs = r["calories"]
        s = sum(cs)
        d_fmt = f"{d[0:4]}/{d[4:6]}/{d[6:8]}"
        last7days.append([d_fmt, s])
        last7days_sums.append(s)

    def nice_time(t2):
        return humanize.naturaltime(
            datetime.timedelta(seconds=(epochtime_now - t2))
        ).capitalize()

    return flask.render_template(
        "index.jinja2",
        title="catfood",
        page_title=f"Overview",
        hours_ago=hours_ago,
        records_hours=records_hours,
        records_hours_sum=records_hours_sum,
        records_today=records_today,
        records_today_sum=records_today_sum,
        records_yesterday=records_yesterday,
        records_yesterday_sum=records_yesterday_sum,
        nice_time=nice_time,
        last7days=list(last7days),
        last7days_sums=last7days_sums,
        statistics=statistics,
    )


@app.route("/new")
def new():
    return flask.render_template("add.jinja2", title="Cat food", page_title="Add")


@app.route("/delete/<record_id>")
def delete(record_id):
    record = CalorieRecord.objects(id=record_id).first_or_404()
    record.delete()
    return flask.redirect(flask.url_for("index"))


@app.route("/edit/<record_id>")
def edit(record_id):
    record = CalorieRecord.objects(id=record_id).first_or_404()
    return flask.render_template(
        "edit.jinja2", title="Cat food", page_title="Edit", record=record
    )


@app.route("/add/<new_calories>")
def add(new_calories):
    today = datetime.datetime.today()
    date_now = int(today.strftime("%Y%m%d"))
    time_now = int(today.strftime("%M%S"))
    epochtime_now = int(today.timestamp())

    CalorieRecord(
        d=date_now,
        t=time_now,
        e=epochtime_now,
        calories=new_calories,
    ).save()

    return flask.redirect(flask.url_for("index"))


def run_server():
    app.run(port=9696, debug=True)


if __name__ == "__main__":
    argh.dispatch_commands([run_server])
