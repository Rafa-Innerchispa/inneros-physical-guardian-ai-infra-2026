"""Offline deterministic tests for the hackathon-specific Guardian sandbox."""
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from inneros_meta_guardian.engine import Guardian, LifecycleError
from inneros_meta_guardian.evidence import Store
from inneros_meta_guardian.fixtures import SCENARIOS
from inneros_meta_guardian.models import ModelUnavailable, _extract_meta, _local_url, narrate
from inneros_meta_guardian.policy import FORBIDDEN_ACTIONS


class GuardianLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.guardian = Guardian()

    def test_each_scenario_happy_path(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                row = self.guardian.ingest(scenario)
                self.assertEqual('SIMULATED_FIXTURE', row['truth'])
                row = self.guardian.analyze(row['id'])
                self.assertTrue(row['policy']['allowed'])
                self.assertEqual('deterministic', row['narration']['provider'])
                row = self.guardian.approve(row['id'], 'Operator A', row['recommended_action'])
                row = self.guardian.execute(row['id'])
                self.assertEqual('SIMULATED_REFERENCE_IO', row['execution']['truth'])
                row = self.guardian.verify(row['id'])
                self.assertEqual('verified', row['status'])
                result = self.guardian.evidence(row['id'])
                self.assertTrue(result['global_chain_validation']['valid'])
                self.assertEqual(['OBSERVE', 'REASON', 'APPROVE', 'ACT', 'VERIFY'], [e['event'] for e in result['audit']])

    def test_denied_unsafe_action_does_not_allow_execution(self):
        row = self.guardian.ingest()
        row = self.guardian.analyze(row['id'])
        for action in FORBIDDEN_ACTIONS:
            with self.subTest(action=action), self.assertRaises(LifecycleError):
                self.guardian.approve(row['id'], 'Operator A', action)
        self.assertEqual('analyzed', self.guardian.get(row['id'])['status'])
        with self.assertRaises(LifecycleError):
            self.guardian.execute(row['id'])
        self.assertTrue(self.guardian.store.verify()['valid'])

    def test_approval_required_and_strict_state_machine(self):
        id = self.guardian.ingest()['id']
        with self.assertRaises(LifecycleError):
            self.guardian.execute(id)
        with self.assertRaises(LifecycleError):
            self.guardian.approve(id, 'Operator', 'activate_beacon')
        self.guardian.analyze(id)
        with self.assertRaises(LifecycleError):
            self.guardian.verify(id)
        with self.assertRaises(LifecycleError):
            self.guardian.approve(id, '', 'activate_beacon')
        self.guardian.approve(id, 'Operator', 'activate_beacon')
        with self.assertRaises(LifecycleError):
            self.guardian.analyze(id)

    def test_verify_uses_virtual_readback_not_ack(self):
        row = self.guardian.ingest()
        row = self.guardian.analyze(row['id'])
        row = self.guardian.approve(row['id'], 'Operator', row['recommended_action'])
        self.guardian.execute(row['id'])
        self.guardian.reset_virtual_state(row['id'])
        verified = self.guardian.verify(row['id'])
        self.assertEqual('failed_safe', verified['status'])
        self.assertFalse(verified['verification']['passed'])
        self.assertTrue(self.guardian.evidence(row['id'])['global_chain_validation']['valid'])

    def test_unknown_scenario(self):
        with self.assertRaises(ValueError):
            self.guardian.ingest('production_camera_1')

    def test_audit_chain_detects_payload_tampering(self):
        row = self.guardian.ingest()
        self.assertTrue(self.guardian.store.verify()['valid'])
        self.guardian.store.db.execute("UPDATE audit SET payload=? WHERE incident_id=?", ('{"fake":true}', row['id']))
        self.guardian.store.db.commit()
        self.assertFalse(self.guardian.store.verify()['valid'])

    def test_persists_incidents_across_store_reopen(self):
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / 'db.sqlite3')
            g = Guardian(path)
            row = g.ingest()
            self.assertEqual(row['id'], Guardian(path).get(row['id'])['id'])
            self.assertTrue(Guardian(path).store.verify()['valid'])

    def test_after_restart_readback_must_fail_safe(self):
        # The virtual actuator has NOT persisted; this is intentionally not fake-proofed.
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / 'db.sqlite3')
            original = Guardian(path)
            row = original.ingest()
            row = original.analyze(row['id'])
            row = original.approve(row['id'], 'Operator', row['recommended_action'])
            original.execute(row['id'])
            restarted = Guardian(path)
            row = restarted.verify(row['id'])
            self.assertEqual('failed_safe', row['status'])


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.incident = Guardian().ingest()

    def test_meta_is_off_by_default_and_cannot_falsify_label(self):
        with patch.dict(os.environ, {'ALLOW_EXTERNAL_META':'false','MODEL_API_KEY':'test'}, clear=False):
            with self.assertRaises(ModelUnavailable):
                narrate('meta', self.incident)

    def test_meta_responses_parser_and_source_truth(self):
        payload = {'output':[{'type':'reasoning','summary':[]},{'type':'message','content':[{'type':'output_text','text':'Synthetic door left open.'}]}]}
        self.assertEqual('Synthetic door left open.', _extract_meta(payload))
        with patch.dict(os.environ, {'ALLOW_EXTERNAL_META':'true','MODEL_API_KEY':'dummy','META_BASE_URL':'https://api.meta.ai/v1'}, clear=False):
            with patch('inneros_meta_guardian.models._post', return_value=payload) as mock_call:
                result = narrate('meta', self.incident)
                self.assertEqual('MODEL_GENERATED_FROM_SIMULATED_SIGNALS', result['truth'])
                self.assertEqual('muse-spark-1.3', result['model'])
                args = mock_call.call_args.args
                self.assertEqual('https://api.meta.ai/v1/responses', args[0])
                self.assertFalse(args[1]['store'])
                self.assertEqual('dummy', args[2]['Authorization'].split(' ')[1])

    def test_meta_wrong_endpoint_blocked(self):
        with patch.dict(os.environ, {'ALLOW_EXTERNAL_META':'true','MODEL_API_KEY':'dummy','META_BASE_URL':'https://untrusted.test'}, clear=False):
            with self.assertRaises(ModelUnavailable):
                narrate('meta', self.incident)

    def test_ollama_loopback_only(self):
        with patch.dict(os.environ, {'OLLAMA_URL':'http://127.0.0.1:11434@external.example/api/chat'}):
            with self.assertRaises(ModelUnavailable):
                _local_url()
        with patch.dict(os.environ, {'OLLAMA_URL':'http://127.0.0.1:11434/api/chat'}):
            self.assertIn('127.0.0.1', _local_url())

    def test_ollama_fallback_without_remote(self):
        with patch('inneros_meta_guardian.models._post', side_effect=ModelUnavailable('No Ollama')):
            row = Guardian().ingest()
            guardian = Guardian()
            row = guardian.ingest()
            result = guardian.analyze(row['id'], 'ollama')
            self.assertEqual('deterministic', result['narration']['provider'])
            self.assertEqual('ollama', result['narration']['requested_provider'])
            self.assertIn('fallback_reason', result['narration'])

    def test_bad_meta_response_is_not_false_success(self):
        with self.assertRaises(ModelUnavailable):
            _extract_meta({'output':[]})


if __name__ == '__main__':
    unittest.main()
