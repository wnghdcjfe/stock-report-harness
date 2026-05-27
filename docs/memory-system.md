# Memory System

같은 실패를 반복하지 않기 위한 학습 누적 시스템임.

> 규칙은 이 파일에 두고, 실제 관측은 `memory/` 아래에 둠.

## 원칙

- 1 entry = 1 관측 사건으로 기록함. 추상적 권고는 금지함.
- 새 관측은 항상 daily에 append함. 반복 패턴은 topic으로 추출함.
- daily는 append-only로 유지함. topic으로 추출해도 원본 entry는 삭제하지 않음.
- 본문은 한국어 `~함` 톤으로 작성함. 단, 코드·명령어·로그·에러 메시지·라이브러리/제품명·파일 경로·식별자는 원문 유지함.
- memory는 작업 전에 전부 읽는 지식베이스가 아님. 작업 도메인이 맞을 때만 관련 topic을 읽음.
- topic에 등록된 실패가 다시 나오면 텍스트 룰을 늘리지 않고 hook / linter / schema / test 같은 결정론적 mechanism으로 차단함.

## 디렉터리

```text
memory/
├── _template.md
├── _daily/YYYY-MM-DD.md
└── topics/{slug}.md
```

- `_daily/`: 모든 신규 관측의 입구임.
- `topics/`: 3회 이상 반복되었거나 재발 비용이 큰 패턴을 정제한 곳임.
- `_template.md`: daily와 topic entry 작성 템플릿임.

## Daily entry 형식

파일은 `# YYYY-MM-DD` 한 줄로 시작하고, 그 아래에 entry를 append함.

```markdown
# 2026-05-03

## Entry: 2026-05-03 — 짧은 한국어 제목
- **상황**: 어떤 작업 중이었나 (브랜치, 환경, 직전 커밋)
- **증상**: 관측된 잘못된 동작. 에러 메시지는 원문 인용
- **원인**: 왜 발생했나 (모르면 "추정")
- **해결**: 어떻게 해결했나. 재현 가능한 명령/코드 포함
- **검증**: 실행한 명령과 결과 (안 했으면 "미검증")
```

## Topic entry 형식

Topic은 daily 5섹션 + **일자** 1개 = 6섹션 고정임. 새 헤더 추가를 금지함.

```markdown
## ENTRY-001: 짧은 한국어 제목

**상황**
어떤 작업 중이었는지 기록함.

**증상**
관측된 잘못된 동작을 기록함. 에러 메시지는 원문 인용함.

**원인**
왜 발생했는지 기록함. 모르면 "추정"으로 표시함.

**해결**
어떻게 해결했는지 기록함. 재현 가능한 명령/코드 포함함.

**검증**
실행한 명령과 결과를 기록함. 안 했으면 "미검증"으로 표시함.

**일자**
- 2026-04-12 최초 / 2026-05-01 검증
```

파일이 200라인을 넘으면 `{slug}-2.md`로 분할함.

## 단계: Daily → Topic → Mechanism

| 단계 | 트리거 | 행동 |
| --- | --- | --- |
| Daily | 1~2회 관측 | `memory/_daily/{date}.md`에 append함 |
| Topic 추출 | 같은 패턴 3회 또는 재발 비용 큰 실패 | `memory/topics/{slug}.md`에 6섹션 entry 추가함 |
| Mechanism | topic 등록 후 또 재발 | hook / linter / schema / test로 결정론적 차단함 |

## 작업 시작 로딩 규칙

작업 도메인이 해당될 때만 해당 topic을 읽음. 무관한 topic은 로드하지 않음.

| 도메인 | 파일 |
| --- | --- |
| 날짜 계산, 기간 계산, yfinance 기간, 거래일 라벨 | `memory/topics/time-sync.md` |
| OpenAI `image_gen`, 외부 뉴스/API 호출, yfinance 호출 | `memory/topics/external-api.md` |
| hero 이미지 후보/선택, 이미지 manifest, selected-image | `memory/topics/image-workflow.md` |
| `/plan`, `/research`, `/draft`, `/review`, `/build` 순서 | `memory/topics/pipeline-order.md` |
| `uv sync`, `pnpm install`, Python/Node 빌드 | `memory/topics/build-errors.md` |
| git commit / push / PR | `memory/topics/git-workflow.md` |
| Claude/Codex hook, validator, schema 차단 | `memory/topics/guardrails.md` |


## 자동 주입 방식

Claude Code `UserPromptSubmit` hook이 사용자 프롬프트를 분석해 관련 topic을 자동으로 컨텍스트에 주입함.

- hook: `.claude/hooks/inject-memory-context.sh`
- selector: `scripts/memory_context.py`
- 연결: `.claude/settings.json`의 `hooks.UserPromptSubmit`

동작 방식:

1. 프롬프트에서 도메인 키워드를 탐지함.
2. `memory/topics/{slug}.md`가 존재하고 내용이 있으면 해당 topic을 `additionalContext`로 주입함.
3. topic이 없거나 비어 있으면 상태만 알려주고 작업은 막지 않음.
4. 실패/고비용 재시도 관측이 생기면 daily에 기록하라는 짧은 규칙을 함께 주입함.

수동 테스트:

```bash
echo '{"prompt":"/build samsung-electronics-recent-30d-2026-05"}' | python3 scripts/memory_context.py
```

자동 주입은 topic 로딩을 돕는 장치이며, memory 기록 자체는 여전히 관측 기반으로 수행함.

## 기록 절차

1. 실패나 재시도 비용이 큰 관측이 생기면 오늘 daily 파일을 열거나 생성함.
2. daily 파일 첫 줄이 `# YYYY-MM-DD`인지 확인함.
3. 관측 1건을 `## Entry: YYYY-MM-DD — 제목` 형식으로 append함.
4. 같은 패턴이 3회 이상이거나 재발 비용이 크면 관련 topic으로 6섹션 entry를 추출함.
5. topic 등록 후 같은 실패가 재발하면 `scripts/validate_memory.py`, hook, build 검증, test 중 하나로 차단 mechanism을 추가함.
6. `python3 scripts/validate_memory.py`로 스키마를 검증함.

## 감사

주 1회 또는 릴리스 전 아래 항목을 확인함.

- [ ] `AGENTS.md` 메모리 로딩 표와 이 문서 로딩 규칙이 일치함.
- [ ] topic 파일이 6섹션 스키마를 지킴.
- [ ] topic 등록 후 재발한 실패가 mechanism으로 격상됨.
- [ ] 90일 이상 된 daily 로그를 archive할 필요가 있는지 판단함.

```bash
for f in memory/topics/*.md; do
  printf "%-40s %s lines\n" "$(basename "$f")" "$(wc -l < "$f")"
done
```

## 안티패턴

- 한 entry에 여러 사건을 묶는 것 금지함.
- "여러 에러가 있었다" 같은 추상 기록 금지함.
- 해결만 적고 원인 / 검증을 비우는 것 금지함.
- daily 로그를 "정리"한다며 삭제하는 것 금지함.
- topic 재발을 텍스트 룰로만 덮는 것 금지함.
