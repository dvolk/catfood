import flask_mongoengine
import argh
import flask
import humanize
import datetime
import time


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
    date_now = int(today.strftime("%Y%m%d"))
    time_now = int(today.strftime("%M%S"))
    epochtime_now = int(today.timestamp())
    epochtime_24h_ago = epochtime_now - (24 * 60 * 60)

    def nice_time(t2):
        return humanize.naturaltime(
            datetime.timedelta(seconds=(epochtime_now - t2))
        ).capitalize()

    records_24 = list(
        CalorieRecord.objects.filter(e__gt=epochtime_24h_ago).order_by("-e").all()
    )
    records_24_sum = sum([r.calories for r in records_24])
    return flask.render_template(
        "index.jinja2",
        title="catfood",
        page_title="Last 24 hours",
        records_24=records_24,
        records_24_sum=records_24_sum,
        nice_time=nice_time,
    )


@app.route("/add/<new_calories>")
def add(new_calories):
    today = datetime.datetime.today()
    date_now = int(today.strftime("%Y%m%d"))
    time_now = int(today.strftime("%M%S"))
    epochtime_now = int(today.timestamp())
    epochtime_24h_ago = epochtime_now - (24 * 60 * 60)

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
