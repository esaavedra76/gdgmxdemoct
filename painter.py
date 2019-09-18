import logging
from flask_restful import Resource

import firestore as fs
import constants
import utils

import time


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
