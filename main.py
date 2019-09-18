import logging
from flask import Flask, jsonify
from flask_restful import Api

import firebase_admin
from firebase_admin import credentials

from matrix import Matrix, MatrixRow
from painter import PainterCell, PainterFill, PainterConcurrentPaint, PainterTask

import constants
import utils


cred = credentials.Certificate("./firebase_service_account.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = constants.MAX_CONTENT_LENGTH_MB * 1024 * 1024
api = Api(app)

#   getters
api.add_resource(Matrix, '/matrix')
#   setters
api.add_resource(PainterConcurrentPaint, '/matrix/concurrent')
api.add_resource(PainterTask, '/matrix/delayedtask/<int:delay>', '/matrix/task')


@app.route('/')
def root():
    millis, ts = utils.get_utc_timestamp()

    msgs = []
    success = False
    return_code = 403

    msgs.append('forbidden')

    response_obj = {'timestamp': millis,
                    'msgs': msgs,
                    'success': success}

    response = jsonify(response_obj)
    return response, return_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
