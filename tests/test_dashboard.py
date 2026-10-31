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

class ReviewTest(unittest.TestCase):
    def test_latest_note_supersedes_old_due_date(self):
        from dashboard import latest_notes
        state = {'journal': [
            {'code': '005930', 'kind': 'note', 'at': '2026-10-01', 'next_review': '2026-10-02'},
            {'code': '005930', 'kind': 'note', 'at': '2026-10-31', 'next_review': '2026-12-01'}]}
        self.assertEqual(latest_notes(state)['005930']['next_review'], '2026-12-01')

    def test_freshness_missing_future_and_boundary(self):
        from datetime import date
        from dashboard import freshness
        today = date(2026, 10, 31)
        self.assertEqual(freshness(None, today, 7), '확인 필요')
        self.assertEqual(freshness('2026-11-01', today, 7), '날짜 확인 필요')
        self.assertEqual(freshness('2026-10-24', today, 7), '7일 경과')
        self.assertIn('갱신 점검', freshness('2026-10-23', today, 7))
