import logging
from flask import request
from flask_restful import Resource

import firestore as fs
import constants
import utils

import json
import time


class PainterConcurrentPaint(Resource):
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
                utils.postCloudTask(constants.PAINTER_QUEUE, '/matrix/task', payload=payload, start_in=0)

            cells = body['paint']
            for row, cols in enumerate(cells):
                for col, value in enumerate(cols):
                    colors.append(value)

                    delay = 5

                    payload = {
                        'action': 'paint',
                        'row': row,
                        'col': col,
                        'value': value
                    }
                    utils.postCloudTask(constants.PAINTER_QUEUE, '/matrix/delayedtask/{}'.format(delay), payload=payload, start_in=0)

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
    def post(self, **kwargs):
        millis, ts = utils.get_utc_timestamp()

        msgs = []
        success = False
        return_code = 403

        if 'delay' in kwargs:
            delay = kwargs['delay']
            msg = 'applying a delay of {}s'.format(delay)
            logging.warning(msg)
            msgs.append(msg)
            time.sleep(delay)

        payload = request.get_data(as_text=True) or None
        if payload is not None:
            payload = json.loads(payload)

            # print(payload)

            action = payload['action']

            if action == 'invert_fill':
                dim = 5
                matrix = fs.getMatrixAll()
                if matrix is not None:
                    batch = fs.initializeBatch()
                    cells = []
                    for row in range(dim):
                        for col in range(dim):
                            #   TODO: use position!
                            color = matrix[dim*row + col]['value']
                            color = constants.LUT_LENGTH - color

                            cell_id = 'row{}col{}'.format(row, col)
                            cell_data = {
                                'updated': millis,
                                'value': color
                            }

                            fs.updateMatrixCellBatched(batch, cell_id, cell_data)
                            cells.append(cell_data)
                    fs.commitBatch(batch)

                    success = True
                else:
                    msg = 'matrix is null'
                    logging.error(msg)
                    msgs.append(msg)

            if action == 'fill':
                color = payload['value']

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

            if action == 'paint':
                color = payload['value']

                row = payload['row']
                col = payload['col']

                cell_id = 'row{}col{}'.format(row, col)
                cell_data = {
                    'updated': millis,
                    'value': color
                }
                fs.updateMatrixCell(cell_id, cell_data)

                success = True

            if action == 'invert':
                row = payload['row']
                col = payload['col']

                cell = fs.getMatrixByCoords(row, col)
                if cell is not None:
                    color = cell[0]['value']
                    color = constants.LUT_LENGTH - color

                    cell_id = 'row{}col{}'.format(row, col)
                    cell_data = {
                        'updated': millis,
                        'value': color
                    }
                    fs.updateMatrixCell(cell_id, cell_data)

                    success = True

                else:
                    msg = 'unable to read cell at {},{}'.format(row, col)
                    logging.error(msg)
                    msgs.append(msg)

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
