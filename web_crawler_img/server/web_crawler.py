from flask import Flask, request
from flask import request
from .job_processing import create_job, check_job_status, get_job_result

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/jobs", methods=['POST'])
def post_job():
    request_json = request.get_json(force=True, silent=True, cache=True)
    if request_json is None:
        return ("", 400)
    if 'urls' not in request_json.keys():
        return ("", 400)
    if 'workers' not in request_json.keys():
        request_json['workers'] = 1
    response_json = request_json
    response_json['job_id'] = create_job(**request_json)
    return (response_json, 200)

@app.route("/jobs/<job_id>/status", methods = ['GET'])
def check_status(job_id):
    response_json = check_job_status(job_id)
    return (response_json, 200)

@app.route("/jobs/<job_id>/result", methods = ['GET'])
def get_result(job_id):
    response_json = get_job_result(job_id)
    return (response_json, 200)

application = app
