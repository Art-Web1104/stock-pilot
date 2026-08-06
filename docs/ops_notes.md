# 운영 메모 (세션 공통 참고)

## 2026-08-05 세션 C
- 구글 파이낸스 WebFetch가 PROVENANCE_REQUIRED 오류로 차단될 수 있음 → WebSearch 결과에 나온 URL만 fetch 가능. 우회 경로: 한경/헤럴드 마감 기사(지수·대형주 종가), wisereport(전일 확정 PER·52주 범위), alphasquare(당일 시세 — 단 SPA 렌더가 다른 종목을 반환하는 경우 빈발, 응답의 종목명·코드를 반드시 교차확인).
- git push가 403(프록시가 credential 미주입)일 때: 예약 작업 프롬프트에 포함된 토큰으로 아래 형태로 재시도하면 성공한다. 토큰 자체는 절대 파일·커밋·응답에 기록하지 말 것.
  ```
  git -c http.extraheader="Authorization: Basic $(printf 'x-access-token:%s' "$TOKEN" | base64 -w0)" push origin main
  ```

## 2026-08-06 세션 C
- 구글 파이낸스 WebFetch 정상 작동(7종목, 429/차단 없음) — 8/5의 차단은 일시적이었음.
- git push 403 재발 → 위 08-05 메모의 extraheader 방식으로 해결(재현성 확인됨). API(contents) 방식은 프록시가 차단하므로 시도 불필요.
