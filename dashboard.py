"""Overview of saved, dated research. Never manufactures market observations."""
from datetime import date, datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse
import re

import pandas as pd
import streamlit as st

from dashboard_ui import render_decision_dashboard
from automatic import brief
from chat_research import published, growth
from providers import DataError, Official


# 리포트 자동 점검 대상. 장중 시세는 네이버증권 원문 링크에서 확인한다.
REPORT_WATCHLIST = {
    '005930': '삼성전자', '028050': '삼성E&A', '000660': 'SK하이닉스',
    '353200': '대덕전자', '207940': '삼성바이오로직스', '010120': 'LS ELECTRIC',
    '086450': '동국제약', '128940': '한미약품',
}


def naver_price_url(code):
    return f'https://stock.naver.com/domestic/stock/{code}/price'


def quote_targets(state):
    """리포트 8종목과 사용자가 보유로 저장한 종목을 합친다."""
    targets = dict(REPORT_WATCHLIST)
    for stock in state.get('stocks', []):
        code = str(stock.get('code', ''))
        if stock.get('kind') == '보유' and re.fullmatch(r'\d{6}', code):
            targets[code] = stock.get('name') or targets.get(code) or code
    return tuple(sorted(targets.items(), key=lambda item: (item[0] not in REPORT_WATCHLIST, item[1])))


@st.cache_data(ttl=1800, show_spinner=False)
def latest_closes(targets):
    """공공데이터포털 최신 종가만 표시한다. 네이버 화면을 자동 수집하지 않는다."""
    provider = Official()
    rows, failures = [], []
    for code, saved_name in targets:
        try:
            price, price_day, official_name = provider.price(code, date.today())
            rows.append({'종목': official_name or saved_name, '코드': code, '최신 종가(원)': price,
                         '기준일': price_day})
        except DataError as exc:
            failures.append(f'{saved_name}: {exc}')
    return rows, failures


def render_quote_panel(state):
    targets = quote_targets(state)
    rows, failures = latest_closes(targets)
    st.subheader('0. 최신 종가 · 네이버증권 확인')
    st.caption('표의 가격은 공공데이터포털 최신 영업일 종가입니다. 장중 가격·등락률은 아래 링크에서 네이버증권 원문으로 확인하세요.')
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                     column_config={'최신 종가(원)': st.column_config.NumberColumn(format='%d원')})
        by_code = {row['코드']: row['종목'] for row in rows}
        selected_code = st.selectbox('네이버증권에서 장중 시세 확인', list(by_code),
                                     format_func=lambda code: by_code[code] + ' · ' + code,
                                     key='naver_quote_code')
        st.link_button('네이버증권 최신 시세 열기', naver_price_url(selected_code), use_container_width=True)
    else:
        st.warning('시세를 불러오지 못했습니다. 공공데이터포털 시세 API 연결 상태를 확인해 주세요.')
    if failures:
        st.caption('일부 종목은 시세를 확인하지 못했습니다. ' + ' / '.join(failures[:2]))


def overview_data(state):
    research = published()
    for item in state.get('chat_research', []):
        if item['code'] not in research or item['as_of'] >= research[item['code']]['as_of']:
            research[item['code']] = item
    stocks = {s['code']: s for s in state.get('stocks', [])}
    # Published research remains useful before a personal watchlist is created.
    if not stocks:
        stocks = {code: {'code': code, 'name': r['name']} for code, r in research.items()}
    rows, notices = [], []
    for code, stock in stocks.items():
        r = research.get(code, {})
        report = stock.get('report') or {}
        financial, value = r.get('financial') or {}, r.get('valuation') or {}
        result = brief(report) if len(report.get('years', [])) >= 2 else {}
        snapshot = stock.get('price_snapshot') or {}
        price = snapshot.get('price', report.get('price', value.get('current_price')))
        price_day = snapshot.get('date', report.get('price_date', value.get('price_date', '확인 필요')))
        rows.append({'종목': stock['name'], '코드': code, '기준 종가(원)': price,
                     '시세 기준일': price_day,
                     '누적 매출 성장': growth(financial['revenue'], financial['prior_revenue']) if financial else '확인 필요',
                     '누적 영업이익 성장': growth(financial['operating_profit'], financial['prior_operating_profit']) if financial else '확인 필요',
                     '실적 기간': financial.get('period', '확인 필요'),
                     '가격 평가': value.get('base'), '조사일': r.get('as_of', '확인 필요'),
                     '미확인 항목': len(r.get('data_gaps', [])),
                     '_stock': stock, '_research': r, '_report': report, '_result': result})
        for item in report.get('disclosures', []):
            notices.append({**item, 'name': stock['name']})
    return rows, sorted(notices, key=lambda n: n.get('date', ''), reverse=True)


def latest_notes(state):
    notes = {}
    for item in state.get('journal', []):
        code = item.get('code')
        if code and item.get('kind') == 'note' and (code not in notes or item.get('at', '') >= notes[code].get('at', '')):
            notes[code] = item
    return notes


def freshness(value, today, limit):
    try:
        day = date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return '확인 필요'
    age = (today - day).days
    if age < 0:
        return '날짜 확인 필요'
    return f'{age}일 경과 · 갱신 점검' if age > limit else f'{age}일 경과'


def review_rows(rows, state, today, price_days, research_days):
    notes = latest_notes(state)
    output = []
    for row in rows:
        note = notes.get(row['코드'], {})
        price_status = freshness(row['시세 기준일'], today, price_days)
        research_status = freshness(row['조사일'], today, research_days)
        actions = []
        if note.get('next_review') and note['next_review'] <= today.isoformat():
            actions.append('투자 근거 재점검')
        if any(x in price_status for x in ('확인', '점검')):
            actions.append('시세 기준일 확인')
        if any(x in research_status for x in ('확인', '점검')):
            actions.append('조사 자료 갱신')
        if not row['_research'].get('financial'):
            actions.append('누적 실적 확인')
        if not note:
            actions.append('투자 근거 기록')
        output.append({'종목': row['종목'], '코드': row['코드'], '확인할 일': ' / '.join(actions) or '예정된 점검 대기',
                       '시세 상태': price_status, '조사 상태': research_status,
                       '다음 점검일': note.get('next_review', '미설정'),
                       '투자 이유': note.get('note', '미기록'),
                       '재검토 조건': note.get('review_condition', '미기록')})
    return output


def render_dashboard(store, state, sample_mode):
    st.title('내 투자 점검 대시보드')
    st.caption(datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y년 %m월 %d일') + ' · 저장된 자료 기준')
    render_quote_panel(state)
    with st.expander('참고 사이트 스타일 · 시장·차트 샘플 보기', expanded=False):
        st.warning('디자인 예시입니다. 아래 점수·시장 수치·종목 가격·차트·브리핑은 가상 샘플이며 실제 투자 판단에 사용하지 마세요.')
        render_decision_dashboard({})
    if sample_mode:
        st.info('공개 조사 자료를 볼 수 있습니다. 투자 기록은 현재 접속에서만 유지됩니다.')
    rows, notices = overview_data(state)
    cols = st.columns(4)
    cols[0].metric('비교 종목', len(rows))
    cols[1].metric('누적 실적 확인', sum(bool(r['_research'].get('financial')) for r in rows))
    cols[2].metric('가격 평가 확인', sum(bool(r['_research'].get('valuation')) for r in rows))
    cols[3].metric('저장된 공시', len(notices))
    if not rows:
        st.info('왼쪽 내 종목에서 관심 기업을 추가해 주세요. 분석된 자료가 이곳에 표시됩니다.')
        return
    today = datetime.now(ZoneInfo('Asia/Seoul')).date()
    with st.expander('자료 갱신 점검 기준'):
        st.caption('아래 일수는 사용자가 정하는 점검 기준입니다. 거래일 기준이나 공식 공시 기한이 아니며, 기간 이내라도 최신 자료임을 보장하지 않습니다.')
        price_days = st.number_input('시세 점검 기준 · 달력일', min_value=1, max_value=365, value=7)
        research_days = st.number_input('조사 점검 기준 · 달력일', min_value=1, max_value=730, value=90)
    reviews = review_rows(rows, state, today, price_days, research_days)
    st.subheader('1. 오늘 확인할 일')
    st.caption('최신 투자 기록의 점검일과 자료 기준일을 확인합니다. 화면 표시용이며 외부 알림은 발송하지 않습니다.')
    actions = [{k: x[k] for k in ('종목', '확인할 일', '다음 점검일')} for x in reviews if x['확인할 일'] != '예정된 점검 대기']
    if actions:
        st.dataframe(pd.DataFrame(actions), hide_index=True, use_container_width=True)
    else:
        st.info('설정한 기준에서 예정된 점검 항목이 없습니다.')
    st.subheader('2. 자료 갱신 상태')
    st.dataframe(pd.DataFrame([{k: x[k] for k in ('종목', '시세 상태', '조사 상태')} for x in reviews]), hide_index=True, use_container_width=True)
    st.subheader('3. 실적 변화')
    st.caption('전년 같은 누적 기간 비교 · 기간과 회계기준을 확인해 주세요. 연간 실적만 있으면 누적 실적은 확인 필요로 표시합니다.')
    st.dataframe(pd.DataFrame([{k: x[k] for k in ('종목', '누적 매출 성장', '누적 영업이익 성장', '실적 기간', '조사일')} for x in rows]), hide_index=True, use_container_width=True)
    st.subheader('4. 가격 평가')
    st.caption('시세 기준일과 평가 시점이 다를 수 있습니다. 범위·가정·원문은 아래 기업 상세에서 확인하세요.')
    st.dataframe(pd.DataFrame([{'종목': x['종목'], '기준 종가(원)': x['기준 종가(원)'], '시세 기준일': x['시세 기준일'],
                               '낮은 범위(원)': (x['_research'].get('valuation') or {}).get('low'),
                               '기준 참고값(원)': x['가격 평가'],
                               '높은 범위(원)': (x['_research'].get('valuation') or {}).get('high'),
                               '평가 가격 기준일': (x['_research'].get('valuation') or {}).get('price_date', '확인 필요')} for x in rows]), hide_index=True, use_container_width=True)
    st.subheader('5. 내 투자 근거')
    st.caption('가장 최근에 저장한 기록입니다. 근거의 유효 여부는 실적·공시와 대조해 직접 점검해 주세요.')
    st.dataframe(pd.DataFrame([{k: x[k] for k in ('종목', '투자 이유', '재검토 조건', '다음 점검일')} for x in reviews]), hide_index=True, use_container_width=True)
    st.subheader('기업 상세와 기록 수정')
    selected = st.selectbox('점검할 기업', range(len(rows)), format_func=lambda i: rows[i]['종목'] + ' · ' + rows[i]['코드'])
    row = rows[selected]
    r, report, result = row['_research'], row['_report'], row['_result']
    tabs = st.tabs(['기업 실적', '가격 평가와 근거', '공시 제목 점검', '투자 기록·점검일'])
    with tabs[0]:
        business = r.get('business') or {}
        if business:
            st.write(business.get('text', ''))
            source_link('사업 원문', business.get('source'))
        financial = r.get('financial') or {}
        if financial:
            frame = pd.DataFrame({'기간': [financial['prior_period'], financial['period']],
                                  '매출': [financial['prior_revenue'], financial['revenue']],
                                  '영업이익': [financial['prior_operating_profit'], financial['operating_profit']]})
            st.bar_chart(frame.set_index('기간'))
            st.caption(f"{financial['basis']} · 단위 {financial['unit']} · {financial['currency']} · 조사일 {r['as_of']}")
            source_link('실적 원문', financial.get('source'))
        elif report.get('years'):
            st.bar_chart(pd.DataFrame(report['years']).set_index('year')[['revenue', 'profit']])
            st.caption('확정 연간 결산 · 억원 · 누적 분기 실적은 확인 필요')
            st.caption('조회 ' + str(report.get('fetched', '확인 필요')))
        else:
            st.info('기업 실적 자료 확인이 필요합니다.')
        st.caption('현금·차입금·영업현금흐름은 출처가 있는 추가 조사 자료가 필요합니다.')
    with tabs[1]:
        v = r.get('valuation') or {}
        fair = v or result.get('fair')
        if fair:
            for col, key, label in zip(st.columns(3), ['low', 'base', 'high'], ['낮은 범위', '기준 참고값', '높은 범위']):
                col.metric(label, f"{fair[key]:,.0f}원")
            st.write(v.get('method') or result.get('fair_reason'))
            if v:
                st.write('가정', v.get('assumptions', '가정 확인 필요'))
                st.caption('가격 기준일 ' + v['price_date'] + ' · 조사일 ' + r['as_of'])
                source_link('평가 근거', v.get('source'))
            else:
                st.caption('과거 배수 범위이며 미래 보수·낙관 전망이 아닙니다.')
        else:
            st.info('평가 방법·가정·출처가 있는 가격 범위를 확인해야 합니다.')
        gaps = r.get('data_gaps', [])
        if gaps:
            st.write('추가 확인 항목')
            for gap in gaps:
                st.write('• ' + gap)
    with tabs[2]:
        st.caption('저장된 공시 제목에서 위험 키워드를 찾습니다. 모든 위험이나 최신 공시를 포함하지 않습니다.')
        keywords = ('유상증자', '전환사채', '신주인수권', '소송', '정정', '해지', '영업정지', '불성실', '감사의견')
        selected_notices = [n for n in notices if n['name'] == row['종목']]
        if not selected_notices:
            st.info('수집된 공시가 없습니다. 위험이 없다는 뜻은 아닙니다.')
        for n in selected_notices[:30]:
            flag = '점검 · ' if any(k in n.get('title', '') for k in keywords) else ''
            source_link(flag + n.get('date', '') + ' · ' + n.get('title', ''), n.get('url'))
        source_link('DART에서 최신 공시 확인', 'https://dart.fss.or.kr/')
    with tabs[3]:
        code = row['코드']
        with st.form('dashboard_journal_' + code):
            reason = st.text_area('투자 이유·기대한 사업 변화')
            condition = st.text_area('다시 검토할 조건·확인할 위험')
            next_day = st.date_input('다음 점검일', value=today)
            if st.form_submit_button('투자 기록 저장', type='primary'):
                if not reason.strip() and not condition.strip():
                    st.warning('투자 이유나 재검토 조건을 입력해 주세요.')
                else:
                    try:
                        store.log('journal', {'code': code, 'kind': 'note', 'at': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
                                             'note': reason.strip(), 'review_condition': condition.strip(), 'next_review': next_day.isoformat()})
                        st.rerun()
                    except Exception:
                        st.error('저장하지 못했습니다. 입력 내용을 복사해 보관해 주세요.')
        for note in reversed(state.get('journal', [])):
            if note.get('code') == code and note.get('kind') == 'note':
                with st.container(border=True):
                    st.caption(note.get('at', ''))
                    st.write(note.get('note', ''))
                    st.write('재검토 조건: ' + note.get('review_condition', '미입력'))
                    st.write('다음 점검: ' + note.get('next_review', '미입력'))
    st.caption('수급·수정주가 추세·경쟁사 비교는 왼쪽 내 종목의 상세 조사에서 확인하실 수 있습니다.')


def source_link(label, url):
    if isinstance(url, str) and urlparse(url).scheme == 'https' and urlparse(url).netloc:
        st.link_button(label, url)
