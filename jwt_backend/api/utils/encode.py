import gzip
import base64
import json
from datetime import datetime
from .messages_pb2 import GenericResponse

def bytes_to_number_stream(data: bytes) -> str:
    return " ".join(str(b) for b in data)

def encode_response(data):
    def default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Type {type(o)} not serializable")

    json_str = json.dumps(
        data,
        separators=(',', ':'),
        default=default
    )

    msg = GenericResponse()
    msg.payload = json_str
    proto_bytes = msg.SerializeToString()

    gzipped = gzip.compress(proto_bytes)
    b64_encoded = base64.b64encode(gzipped)
    res = bytes_to_number_stream(b64_encoded)

    return res
