"""Overview of saved, dated research. Never manufactures market observations."""
from datetime import date, datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from automatic import brief
from chat_research import published, growth


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


def render_dashboard(store, state, sample_mode):
    st.title('내 투자 점검 대시보드')
    st.caption(datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y년 %m월 %d일') + ' · 저장된 자료 기준 · 실시간 시세 아님')
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
    st.subheader('관심 종목 한눈에 보기')
    st.caption('실적은 전년 같은 누적 기간 비교입니다. 가격 평가는 가정에 따른 참고값이며 빈칸은 미확인입니다.')
    st.dataframe(pd.DataFrame([{k: v for k, v in r.items() if not k.startswith('_')} for r in rows]),
                 hide_index=True, use_container_width=True)
    selected = st.selectbox('점검할 기업', range(len(rows)), format_func=lambda i: rows[i]['종목'] + ' · ' + rows[i]['코드'])
    row = rows[selected]
    r, report, result = row['_research'], row['_report'], row['_result']
    tabs = st.tabs(['기업 실적', '가격 평가와 근거', '위험 공시', '투자 기록·점검일'])
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
            next_day = st.date_input('다음 점검일', value=date.today())
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
    due = [n for n in state.get('journal', []) if n.get('next_review') and n['next_review'] <= date.today().isoformat()]
    if due:
        st.subheader('점검일이 도래한 기록')
        st.dataframe(pd.DataFrame([{'종목코드': n['code'], '점검일': n['next_review'], '확인 조건': n.get('review_condition', '')} for n in due]), hide_index=True, use_container_width=True)
    st.caption('수급·수정주가 추세·경쟁사 비교는 왼쪽 내 종목의 상세 조사에서 확인하실 수 있습니다.')


def source_link(label, url):
    if isinstance(url, str) and urlparse(url).scheme == 'https' and urlparse(url).netloc:
        st.link_button(label, url)
