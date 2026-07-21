# 세션 C — 회사 분석 (평일 17:30 KST)

역할: 시장 분석이 지목한 유망 섹터에서 펀더멘털이 탄탄한 회사를 골라 후보로 제안한다.
이 결과는 차트 분석 세션(18:00)의 입력이 된다.

## 절차

1. `prompts/common.md`를 먼저 읽는다.
2. 입력 읽기:
   - 오늘의 `data/market_analysis/YYYY-MM-DD.json` (없으면 가장 최근 것)
   - 최근 `data/company_analysis/` 파일 1~2개 (중복 제안 방지, 기존 후보 재평가)
   - `config.json`의 exclude_codes와 `python3 scripts/pilot.py status`의 진행 중 종목
3. 후보 발굴 — 유망 섹터별로:
   - WebSearch: "{섹터} 대장주", "{섹터} 실적 개선 종목 2026", "{종목명} 실적 전망" 등
   - 발굴한 종목마다 구글 파이낸스에서 확인: 현재가, 시총, PER, EPS, 52주 범위
   - 시총 3,000억 원 미만(config.json min_market_cap_krw_bil)은 제외
4. 평가 — 종목별로 다음을 종합해 score 1~10 부여:
   - 실적: 매출/이익 성장 여부, 흑자 여부 (뉴스·공시 검색으로 확인)
   - 밸류에이션: PER이 섹터 평균 대비 과도하지 않은가
   - 재료: 향후 2~4주 안에 주가를 움직일 만한 모멘텀(실적발표, 수주, 신제품 등)이 있는가
   - 리스크: 유상증자, 소송, 규제 등 악재 여부
5. 결과 저장 — `data/company_analysis/YYYY-MM-DD.json`:
   ```json
   {
     "date": "YYYY-MM-DD",
     "based_on_market": "YYYY-MM-DD",
     "candidates": [
       {"code": "005930", "name": "삼성전자", "sector": "반도체",
        "price": 0, "market_cap": "...", "per": 0,
        "score": 8, "thesis": "2~3문장: 왜 이 회사인가",
        "risks": "한 줄", "catalyst": "임박한 재료"}
     ],
     "summary": "..."
   }
   ```
   상위 3~5개만 candidates에 담는다. 같은 내용을 `.md` 보고서로도 저장.
6. 커밋·푸시 후 요약: 최상위 후보 2~3개와 핵심 논거.

## 주의

- 이미 2주 검증이 진행 중인 종목은 다시 제안하지 않는다.
- 근거 없는 급등주·테마주 추격은 하지 않는다. thesis에 반드시 실적 또는 구체적 재료를 포함할 것.
- 어제 후보였던 종목이 오늘 조건을 잃었으면 (급등해버림, 악재 발생) 명시적으로 탈락시킨다.
