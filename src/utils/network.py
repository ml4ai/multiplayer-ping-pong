import json
from config import HEADER


def send(connection, payload):
    # Convert payload into json string and encode it
    payload_msg = json.dumps(payload).encode('utf-8')

    # Pad the json string to specific data length
    payload_msg += b' ' * (HEADER - len(payload_msg))

    # Send payload
    connection.send(payload_msg)
