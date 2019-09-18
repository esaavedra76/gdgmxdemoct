import logging
from flask import Flask, request, jsonify, make_response
from flask_restful import Api

import firebase_admin
from firebase_admin import credentials

from matrix import Matrix, MatrixRow
from painter import PainterCell, PainterFill, PainterPaint, PainterTask

import constants
import utils


cred = credentials.Certificate("./firebase_service_account.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = constants.MAX_CONTENT_LENGTH_MB * 1024 * 1024
api = Api(app)

api.add_resource(Matrix, '/matrix')
api.add_resource(MatrixRow, '/matrix/<int:row>')
api.add_resource(PainterCell, '/matrix/<int:row>/<int:col>/<int:color>')
api.add_resource(PainterFill, '/matrix/fill/<int:color>')
api.add_resource(PainterPaint, '/matrix/paint')
api.add_resource(PainterTask, '/matrix/task')


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
