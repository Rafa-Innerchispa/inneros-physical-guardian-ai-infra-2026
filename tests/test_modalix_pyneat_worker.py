from __future__ import annotations

import io
import json
import struct
import unittest
from guardian_demo.modalix_pyneat_worker import (
    WORKER_SCHEMA,
    WIRE_PROTOCOL,
    _read_envelope,
    _write_response,
)
from guardian_demo.sima_adapter import ModalixSshPyNeatBackend

class TestModalixPyNeatWorkerProtocol(unittest.TestCase):
    def test_length_prefixed_multi_request_single_session(self):
        stream = io.BytesIO()

        # Request 1
        req1 = {'operation': 'infer', 'frame_id': 'frame_001', 'source_id': 'camera_01', 'request_nonce': 'nonce_001'}
        img1 = b'FAKE_JPEG_BYTES_1'
        packet1 = ModalixSshPyNeatBackend._encode_envelope(req1, img1)
        stream.write(packet1)

        # Request 2
        req2 = {'operation': 'infer', 'frame_id': 'frame_002', 'source_id': 'camera_01', 'request_nonce': 'nonce_002'}
        img2 = b'FAKE_JPEG_BYTES_2'
        packet2 = ModalixSshPyNeatBackend._encode_envelope(req2, img2)
        stream.write(packet2)

        # Signal graceful shutdown at end
        stream.write(struct.pack('>I', 0))
        stream.seek(0)

        # Read envelope 1
        env1 = _read_envelope(stream, json, struct)
        self.assertIsNotNone(env1)
        r1, b1 = env1
        self.assertEqual(r1['frame_id'], 'frame_001')
        self.assertEqual(r1['request_nonce'], 'nonce_001')
        self.assertEqual(b1, img1)

        # Read envelope 2 from SAME persistent stream without closing
        env2 = _read_envelope(stream, json, struct)
        self.assertIsNotNone(env2)
        r2, b2 = env2
        self.assertEqual(r2['frame_id'], 'frame_002')
        self.assertEqual(r2['request_nonce'], 'nonce_002')
        self.assertEqual(b2, img2)

        # Graceful shutdown returns None
        env3 = _read_envelope(stream, json, struct)
        self.assertIsNone(env3)

    def test_ndjson_response_formatting_and_no_stale_response(self):
        out_stream = io.BytesIO()
        resp1 = {
            'worker_schema': WORKER_SCHEMA,
            'operation': 'infer',
            'execution_status': 'REAL_TARGET_MLA_SUCCESS',
            'request_sequence': 1,
            'request_nonce': 'nonce_101',
            'frame_id': 'frame_101'
        }
        resp2 = {
            'worker_schema': WORKER_SCHEMA,
            'operation': 'infer',
            'execution_status': 'REAL_TARGET_MLA_SUCCESS',
            'request_sequence': 2,
            'request_nonce': 'nonce_102',
            'frame_id': 'frame_102'
        }

        _write_response(out_stream, json, resp1)
        _write_response(out_stream, json, resp2)

        out_stream.seek(0)
        lines = out_stream.getvalue().decode('utf-8').strip().split('\n')
        self.assertEqual(len(lines), 2)
        
        parsed1 = json.loads(lines[0])
        parsed2 = json.loads(lines[1])
        self.assertEqual(parsed1['request_sequence'], 1)
        self.assertEqual(parsed1['request_nonce'], 'nonce_101')
        self.assertEqual(parsed2['request_sequence'], 2)
        self.assertEqual(parsed2['request_nonce'], 'nonce_102')
        self.assertNotEqual(parsed1['frame_id'], parsed2['frame_id'])

    def test_corrupt_frame_fail_closed_and_recovery_sequence(self):
        # Build stream: corrupt packet followed immediately by valid packet
        stream = io.BytesIO()

        # Packet A: Valid request with corrupt image payload
        req_corrupt = {'operation': 'infer', 'frame_id': 'frame_corrupt', 'source_id': 'camera_01', 'request_nonce': 'nonce_err'}
        img_corrupt = b'NOT_A_JPEG'
        stream.write(ModalixSshPyNeatBackend._encode_envelope(req_corrupt, img_corrupt))

        # Packet B: Valid request with valid image payload in same session
        req_valid = {'operation': 'infer', 'frame_id': 'frame_valid', 'source_id': 'camera_01', 'request_nonce': 'nonce_ok'}
        img_valid = b'VALID_JPEG_BYTES'
        stream.write(ModalixSshPyNeatBackend._encode_envelope(req_valid, img_valid))

        stream.seek(0)

        env_a = _read_envelope(stream, json, struct)
        self.assertIsNotNone(env_a)
        self.assertEqual(env_a[0]['frame_id'], 'frame_corrupt')
        self.assertEqual(env_a[1], img_corrupt)

        env_b = _read_envelope(stream, json, struct)
        self.assertIsNotNone(env_b)
        self.assertEqual(env_b[0]['frame_id'], 'frame_valid')
        self.assertEqual(env_b[1], img_valid)

    def test_malformed_envelope_handling(self):
        stream = io.BytesIO(b'BAD')
        with self.assertRaises(Exception):
            _read_envelope(stream, json, struct)

    def test_mismatched_image_size_raises(self):
        stream = io.BytesIO()
        header = {'operation': 'infer', 'image_size': 999}
        enc_hdr = json.dumps(header).encode('utf-8')
        img = b'123'
        env_size = 4 + len(enc_hdr) + len(img)
        packet = struct.pack('>I', env_size) + struct.pack('>I', len(enc_hdr)) + enc_hdr + img
        stream.write(packet)
        stream.seek(0)

        with self.assertRaises(ValueError):
            _read_envelope(stream, json, struct)

if __name__ == '__main__':
    unittest.main()
