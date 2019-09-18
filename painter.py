import logging
from flask import request
from flask_restful import Resource

import firestore as fs
import constants
import utils

import json
import time


class PainterPaint(Resource):
    def post(self):
        millis, ts = utils.get_utc_timestamp()

        msgs = []
        success = False
        return_code = 403

        body = request.json
        if body is not None and 'paint' in body:
            colors = []

            if 'fill' in body:
                payload = {
                    'action': 'fill',
                    'value': body['fill']
                }
                utils.postCloudTask(constants.PAINTER_QUEUE, '/matrix/task', payload=payload, start_in=1)

            cells = body['paint']
            for row, cols in enumerate(cells):
                for col, value in enumerate(cols):
                    colors.append(value)

                    payload = {
                        'action': 'paint',
                        'row': row,
                        'col': col,
                        'value': value
                    }
                    utils.postCloudTask(constants.PAINTER_QUEUE, '/matrix/task', payload=payload, start_in=1)

            success = True

        response_obj = {'timestamp': millis,
                        'msgs': msgs,
                        'success': success}

        if success:
            return_code = 200
            response_obj.update({
                'colors': colors
            })

        return response_obj, return_code


class PainterTask(Resource):
    def post(self):
        millis, ts = utils.get_utc_timestamp()

        msgs = []
        success = False
        return_code = 403

        time.sleep(constants.DELAY_IN_SECS)

        payload = request.get_data(as_text=True) or None
        if payload is not None:
            payload = json.loads(payload)

            print(payload)

            action = payload['action']
            color = payload['value']

            if action == 'fill':
                dim = 5
                batch = fs.initializeBatch()
                cells = []
                for row in range(dim):
                    for col in range(dim):
                        cell_id = 'row{}col{}'.format(row, col)
                        cell_data = {
                            'updated': millis,
                            'value': color
                        }

                        fs.updateMatrixCellBatched(batch, cell_id, cell_data)
                        cells.append(cell_data)
                fs.commitBatch(batch)

            if action == 'paint':
                row = payload['row']
                col = payload['col']

                time.sleep(constants.DELAY_IN_SECS)

                cell_id = 'row{}col{}'.format(row, col)
                cell_data = {
                    'updated': millis,
                    'value': color
                }
                fs.updateMatrixCell(cell_id, cell_data)

            success = True

        response_obj = {'timestamp': millis,
                        'msgs': msgs,
                        'success': success}

        if success:
            return_code = 200

        return response_obj, return_code


class PainterCell(Resource):
    def post(self, row: int, col: int, color: int):
        millis, ts = utils.get_utc_timestamp()

        msgs = []
        success = False
        return_code = 403

        time.sleep(constants.DELAY_IN_SECS)

        cell_id = 'row{}col{}'.format(row, col)
        cell_data = {
            'updated': millis,
            'value': color
        }
        fs.updateMatrixCell(cell_id, cell_data)

        success = True

        response_obj = {'timestamp': millis,
                        'msgs': msgs,
                        'success': success}

        if success:
            return_code = 200

        return response_obj, return_code


class PainterFill(Resource):
    def post(self, color: int):
        millis, ts = utils.get_utc_timestamp()

        msgs = []
        success = False
        return_code = 403

        dim = 5

        batch = fs.initializeBatch()

        cells = []
        for row in range(dim):
            for col in range(dim):
                cell_id = 'row{}col{}'.format(row, col)
                cell_data = {
                    'updated': millis,
                    'value': color
                }

                fs.updateMatrixCellBatched(batch, cell_id, cell_data)
                cells.append(cell_data)

        fs.commitBatch(batch)

        success = True

        response_obj = {'timestamp': millis,
                        'msgs': msgs,
                        'success': success}

        if success:
            return_code = 200

        return response_obj, return_code
