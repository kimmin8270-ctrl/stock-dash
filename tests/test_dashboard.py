import unittest
from unittest.mock import patch
from dashboard import overview_data


class DashboardTest(unittest.TestCase):
    @patch('dashboard.published', return_value={})
    def test_missing_data_stays_missing(self, _):
        rows, notices = overview_data({'stocks': [{'code': '005930', 'name': '기업'}]})
        self.assertIsNone(rows[0]['기준 종가(원)'])
        self.assertIsNone(rows[0]['가격 평가'])
        self.assertEqual(rows[0]['누적 매출 성장'], '확인 필요')
        self.assertEqual(notices, [])

    @patch('dashboard.published', return_value={'005930': {'code': '005930', 'name': '기업', 'as_of': '2026-10-30'}})
    def test_older_upload_does_not_replace_newer_public_research(self, _):
        rows, _ = overview_data({'chat_research': [{'code': '005930', 'name': '기업', 'as_of': '2026-09-01'}]})
        self.assertEqual(rows[0]['조사일'], '2026-10-30')
