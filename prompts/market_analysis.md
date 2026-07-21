# 세션 B — 시장 분석 (평일 17:00 KST)

역할: 오늘의 한국 증시 전체 흐름을 분석해 시장 국면(regime)과 유망/회피 섹터를 판단한다.
이 결과는 회사 분석 세션(17:30)과 차트 분석 세션(18:00)의 입력이 된다.

## 절차

1. `prompts/common.md`를 먼저 읽는다.
2. 데이터 수집:
   - 코스피/코스닥 지수 종가와 등락률 (구글 파이낸스)
   - WebSearch: "코스피 마감 시황 오늘", "코스닥 특징주 오늘", 주요 섹터 뉴스
   - 밤사이 미국 시장 마감 (S&P500, 나스닥) 및 환율 동향
   - 이전 분석과의 연속성: `data/market_analysis/`의 최근 파일 1~2개를 읽는다.
3. 분석·판단:
   - 시장 국면: bullish / neutral / bearish 중 하나 + 근거
   - 유망 섹터 2~4개, 회피 섹터 1~3개 + 각각 한 줄 근거
   - 시장 전체 리스크 요인 (금리, 환율, 지정학 등)
4. 결과 저장 — `data/market_analysis/YYYY-MM-DD.json`:
   ```json
   {
     "date": "YYYY-MM-DD",
     "kospi": {"close": 0, "change_pct": 0},
     "kosdaq": {"close": 0, "change_pct": 0},
     "regime": "bullish|neutral|bearish",
     "favored_sectors": [{"name": "반도체", "reason": "..."}],
     "avoid_sectors": [{"name": "...", "reason": "..."}],
     "risks": ["..."],
     "summary": "3~5문장 요약"
   }
   ```
   같은 내용의 사람이 읽을 보고서를 `data/market_analysis/YYYY-MM-DD.md`로도 저장한다.
5. 커밋·푸시 후 요약: 국면 판단과 유망 섹터를 2~3문장으로.

## 주의

- 뉴스 헤드라인의 과장에 휩쓸리지 말고, 지수·수급 데이터와 교차 확인한다.
- 이전 국면 판단과 달라졌으면 무엇이 바뀌었는지 명시한다.
