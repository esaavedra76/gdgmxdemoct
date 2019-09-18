import logging
from flask_restful import Resource

import firestore as fs
import utils


class Matrix(Resource):
    def get(self):
        millis, ts = utils.get_utc_timestamp()

        msgs = []
        success = False
        return_code = 403

        matrix = fs.getMatrixAll()
        if matrix is not None:
            indicators = []
            for cell in matrix:
                indicators.append(cell)

            success = True

        response_obj = {'timestamp': millis,
                        'msgs': msgs,
                        'success': success}

        if success:
            return_code = 200
            response_obj.update({
                'matrix': indicators
            })

        return response_obj, return_code

    def post(self):
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
                    'created': millis,
                    'updated': millis,
                    'id': cell_id,
                    'row': row,
                    'col': col,
                    'value': 0
                }

                fs.setMatrixCellBatched(batch, cell_id, cell_data)
                cells.append(cell_data)

        fs.commitBatch(batch)

        success = True

        response_obj = {'timestamp': millis,
                        'msgs': msgs,
                        'success': success}

        if success:
            return_code = 200
            response_obj.update({
                'matrix': cells
            })

        return response_obj, return_code


class MatrixRow(Resource):
    def get(self, row: int):
        millis, ts = utils.get_utc_timestamp()

        msgs = []
        success = False
        return_code = 403

        matrix = fs.getMatrix(row)
        if matrix is not None:
            indicators = []
            for cell in matrix:
                indicators.append(cell)

            success = True

        response_obj = {'timestamp': millis,
                        'msgs': msgs,
                        'success': success}

        if success:
            return_code = 200
            response_obj.update({
                'matrix': indicators
            })

        return response_obj, return_code
