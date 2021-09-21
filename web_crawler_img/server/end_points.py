from web_crawler import app
from flask import request
from job_processing import create_job

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/jobs", methods=['POST'])
def post_job():
    parse_json = request.get_json(force=True, silent=True, cache=True)
    print(parse_json)
    if parse_json is None:
        return ("", 400)
    response_json = parse_json
    response_json['job_id'] = create_job(**parse_json)
    return (response_json, 200)

application = app
