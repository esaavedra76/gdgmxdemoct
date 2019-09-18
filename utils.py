import json
from datetime import datetime, timedelta

from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

import constants


def unix_time_millis(dt):
    epoch = datetime.utcfromtimestamp(0)
    return int((dt - epoch).total_seconds() * 1000.0)


def get_utc_timestamp():
    ts = datetime.utcnow()
    return unix_time_millis(ts), ts


def postCloudTask(queue_name, relative_uri, payload, start_in):
    project = constants.GCP_PROJECT_NAME
    location = constants.GCP_PROJECT_LOCATION

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, location, queue_name)

    task = {
        'app_engine_http_request': {
            'http_method': 'POST',
            'relative_uri': relative_uri
        }
    }

    if payload is not None:
        payload = json.dumps(payload)

        # The API expects a payload of type bytes.
        converted_payload = payload.encode()

        # Add the payload to the request.
        task['app_engine_http_request']['body'] = converted_payload

    if start_in is not None:
        # Convert "seconds from now" into an rfc3339 datetime string.
        d = datetime.utcnow() + timedelta(seconds=start_in)

        # Create Timestamp protobuf.
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(d)

        # Add the timestamp to the tasks.
        task['schedule_time'] = timestamp

    response = client.create_task(parent, task)
    print('Created task {}'.format(response.name))

    return response
