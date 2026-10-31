import unittest
from mutex_probe import verify


def rows():
    return [
        {'name': 'r17', 'lock': 'shared', 'start_ns': 1, 'end_ns': 4},
        {'name': 'r18', 'lock': 'shared', 'start_ns': 5, 'end_ns': 8},
        {'name': 'third-pending', 'lock': 'shared', 'start_ns': 9, 'end_ns': 12},
        {'name': 'independent', 'lock': 'independent', 'start_ns': 2, 'end_ns': 10},
    ]


class ProbeTests(unittest.TestCase):
    def test_serialized_shared_and_parallel_unrelated(self):
        self.assertTrue(verify(rows()))

    def test_overlap_rejected(self):
        data = rows()
        data[1]['start_ns'] = 3
        with self.assertRaisesRegex(ValueError, 'overlapped'):
            verify(data)

    def test_canceled_pending_job_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing/duplicate'):
            verify([r for r in rows() if r['name'] != 'third-pending'])

    def test_wrong_group_membership_rejected(self):
        data = rows()
        data[-1]['lock'] = 'shared'
        with self.assertRaisesRegex(ValueError, 'membership'):
            verify(data)


if __name__ == '__main__':
    unittest.main()
