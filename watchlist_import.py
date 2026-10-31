"""Validate a private PreDash export; never publish the uploaded list."""
import json
import re


def parse_watchlist(raw):
    try:
        bundle = json.loads(raw)
    except (ValueError, UnicodeError, TypeError):
        raise ValueError('유효한 JSON 파일을 선택하세요.') from None
    if not isinstance(bundle, dict) or type(bundle.get('version')) is not int or bundle['version'] != 1:
        raise ValueError('지원하는 관심종목 파일 버전은 1입니다.')
    codes, names = bundle.get('codes'), bundle.get('names')
    if not isinstance(codes, list) or not codes or len(codes) > 500 or not isinstance(names, dict):
        raise ValueError('종목코드 목록과 기업명이 필요합니다. 최대 500개를 지원합니다.')
    result, seen = [], set()
    for code in codes:
        if not isinstance(code, str) or not re.fullmatch(r'[0-9]{6}', code):
            raise ValueError('종목코드는 숫자 6자리 문자열이어야 합니다.')
        name = names.get(code)
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
            raise ValueError('각 종목코드에 유효한 기업명이 필요합니다.')
        if code not in seen:
            result.append({'code': code, 'name': name.strip()})
            seen.add(code)
    return result


def add_watchlist(data, incoming):
    stocks = data.setdefault('stocks', [])
    existing = {stock['code'] for stock in stocks}
    for stock in incoming:
        if stock['code'] not in existing:
            stocks.append({**stock, 'kind': '관심'})
            existing.add(stock['code'])
