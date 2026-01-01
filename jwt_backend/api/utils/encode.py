import gzip
import base64
import json
from datetime import datetime
from .messages_pb2 import GenericResponse

def bytes_to_number_stream(data: bytes) -> str:
    """
    Converts a byte array into a space-separated string of decimal integers.
    
    :param data: The raw bytes to convert.
    :return: A string representation of the byte values (e.g., "65 66 67").
    """
    return " ".join(str(b) for b in data)

def encode_response(data: dict) -> str:
    """
    A multi-stage serialization and obfuscation pipeline for outgoing responses.

    @description
    This function processes a dictionary through a rigorous pipeline:
    1. JSON Serialization: Converts the dict to a minified string.
    2. Protobuf Wrapping: Embeds the string into a binary GenericResponse message.
    3. Compression: Compresses the binary data using Gzip to reduce size.
    4. Encoding: Converts compressed binary to a Base64 string.
    5. Obfuscation: Transforms the Base64 string into a decimal-integer stream string.

    @param data: The dictionary containing the response payload.
    :return: An obfuscated string representing the final processed data.

    @example
    # Input
    data = {"status": "success", "timestamp": datetime.now()}
    
    # Execution
    encoded_str = encode_response(data)
    
    # Output Example
    # "85 49 104 102 84 ... 61 61"

    @input_arguments
    - data: dict (Must be JSON-serializable, handles datetime objects).
    
    @possible_input_values
    - data: {"key": "value"}
    - data: {"items": [1, 2, 3], "meta": {"count": 3}}
    """
    def default(o):
        """Custom JSON serializer for non-standard objects."""
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Type {type(o)} not serializable")

    # Step 1: Minified JSON Serialization
    json_str = json.dumps(
        data,
        separators=(',', ':'),
        default=default
    )

    # Step 2: Protocol Buffer Encapsulation
    msg = GenericResponse()
    msg.payload = json_str
    proto_bytes = msg.SerializeToString()

    # Step 3: Gzip Compression
    gzipped = gzip.compress(proto_bytes)

    # Step 4: Base64 Encoding
    b64_encoded = base64.b64encode(gzipped)

    # Step 5: Final Transformation to Number Stream
    res = bytes_to_number_stream(b64_encoded)

    return res