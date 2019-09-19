import logging
from flask import request
from flask_restful import Resource

import firestore as fs
import constants
import utils

import random
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

            start_painting_at = body['start_painting_at'] if 'start_painting_at' in body else 0
            start_posteffects_at = body['start_posteffects_at'] if 'start_posteffects_at' in body else 0
            next_posteffect_at = body['next_posteffect_at'] if 'next_posteffect_at' in body else 0
            unreliable = body['unreliable'] if 'unreliable' in body else None
            unreliable_prob = body['unreliable_probability'] if 'unreliable_probability' in body else None
            unreliable_fill = body['unreliable_fill'] if 'unreliable_fill' in body else None

            if 'fill' in body:
                payload = {
                    'action': 'fill',
                    'value': body['fill']
                }
                if unreliable_fill is not None:
                    payload.update({
                        'unreliable': unreliable_fill,
                        'probability': unreliable_prob
                    })
                utils.postCloudTask(constants.PAINTER_QUEUE, '/matrix/task', payload=payload, start_in=0)

            cells = body['paint']
            for row, cols in enumerate(cells):
                for col, value in enumerate(cols):
                    colors.append(value)

                    if 'delay' in body:
                        delay = body['delay']
                    else:
                        delay = constants.DELAY_IN_SECS

                    payload = {
                        'action': 'paint',
                        'row': row,
                        'col': col,
                        'value': value
                    }
                    if unreliable is not None:
                        payload.update({
                            'unreliable': unreliable,
                            'probability': unreliable_prob
                        })
                    if delay > 0:
                        utils.postCloudTask(constants.PAINTER_QUEUE, '/matrix/delayedtask/{}'.format(delay), payload=payload, start_in=start_painting_at)
                    else:
                        utils.postCloudTask(constants.PAINTER_QUEUE, '/matrix/task', payload=payload, start_in=start_painting_at)

            if 'posteffects' in body:
                start_at = start_posteffects_at
                posteffects = body['posteffects']
                for effect in posteffects:
                    payload = {
                        'action': 'posteffect',
                        'effect': effect
                    }
                    utils.postCloudTask(constants.PAINTER_QUEUE, '/matrix/task', payload=payload, start_in=start_at)

                    start_at += next_posteffect_at

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
            probability = 100 - payload['probability'] if 'probability' in payload else constants.DEFAULT_PROBABILITY
            if probability > 100:
                probability = 100
            if probability < 0:
                probability = 0
            unreliable = random.randint(0, 100) > probability if 'unreliable' in payload and payload['unreliable'] else False
            label = '?' if unreliable else ''

            if unreliable:
                msg = '{} UNRELIABLE'.format(action)
                logging.warning(msg)
                msgs.append(msg)

            if action == 'posteffect' and payload['effect'] == 'b&w':
                dim = constants.CANVAS_DIMENSION
                matrix = fs.getMatrixAll()
                if matrix is not None:
                    batch = fs.initializeBatch()
                    cells = []
                    for row in range(dim):
                        for col in range(dim):
                            #   TODO: use position!
                            color = matrix[dim*row + col]['value']

                            if color >= 0:
                                if unreliable:
                                    color = constants.LUT_LENGTH - color
                                    if color == 5:
                                        color = 4   #   due to inverse of 5 being 5
                                color += 100

                                cell_id = 'row{}col{}'.format(row, col)
                                cell_data = {
                                    'updated': millis,
                                    'label': label,
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

            if (action == 'invert_fill') or (action == 'posteffect' and payload['effect'] == 'invert'):
                dim = constants.CANVAS_DIMENSION
                matrix = fs.getMatrixAll()
                if matrix is not None:
                    batch = fs.initializeBatch()
                    cells = []
                    for row in range(dim):
                        for col in range(dim):
                            #   TODO: use position!
                            color = matrix[dim*row + col]['value']

                            if color >= 0:
                                color = constants.LUT_LENGTH - color
                                if unreliable:
                                    color = constants.LUT_LENGTH - color
                                    if color == 5:
                                        color = 4   #   due to inverse of 5 being 5

                                cell_id = 'row{}col{}'.format(row, col)
                                cell_data = {
                                    'updated': millis,
                                    'label': label,
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
                if color >= 0 and unreliable:
                    color = constants.LUT_LENGTH - color
                    if color == 5:
                        color = 4   #   due to inverse of 5 being 5

                dim = constants.CANVAS_DIMENSION
                batch = fs.initializeBatch()
                cells = []
                for row in range(dim):
                    for col in range(dim):
                        if color >= 0:
                            cell_id = 'row{}col{}'.format(row, col)
                            cell_data = {
                                'updated': millis,
                                'label': label,
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

                if color >= 0:
                    if unreliable:
                        color = constants.LUT_LENGTH - color
                        if color == 5:
                            color = 4   #   due to inverse of 5 being 5

                    cell_id = 'row{}col{}'.format(row, col)
                    cell_data = {
                        'updated': millis,
                        'label': label,
                        'value': color
                    }
                    fs.updateMatrixCell(cell_id, cell_data)

                    print('{} -> {}'.format(cell_id, color))

                success = True

            if action == 'invert':
                row = payload['row']
                col = payload['col']

                cell = fs.getMatrixByCoords(row, col)
                if cell is not None:
                    color = cell[0]['value']

                    if color >= 0:
                        color = constants.LUT_LENGTH - color
                        if unreliable:
                            color = constants.LUT_LENGTH - color

                        cell_id = 'row{}col{}'.format(row, col)
                        cell_data = {
                            'updated': millis,
                            'label': label,
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

            if unreliable:
                return_code = 404

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

        dim = constants.CANVAS_DIMENSION

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
