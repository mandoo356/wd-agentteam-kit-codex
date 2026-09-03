"use client";

import type { CSSProperties } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import OfficeWorld from "./game/OfficeWorld";
import {
  buildReport,
  fetchIntegrations,
  publish,
  type IntegrationStatus,
  type PublishResult,
} from "./game/report";
import { Company, PHASES, type Agent, type DeptStatus, type Snapshot } from "./game/sim";
import { CEO, DEPT_BRIEF, DEPT_LEAD, STAFF } from "./game/staff";
import { DEPT_ROOMS } from "./game/world";
import {
  COMPANY,
  STORAGE_LINK,
  COURSES,
  COURSE_STAGES,
  SAMPLE_DATA,
  type Course,
  type CourseStage,
} from "../company.config";

type View = "live" | "dashboard";

// ── 교육진행 현황 계산 ──────────────────────────────────────
const STAGE_IDS = COURSE_STAGES.map((s) => s.id) as readonly CourseStage[];

/** 단계별 알약 색 — 기존 상태 색을 그대로 재사용한다 */
const STAGE_PILL: Record<CourseStage, string> = {
  inquiry: "blocked",
  proposal: "blocked",
  confirmed: "waiting",
  design: "approval",
  material: "approval",
  delivery: "working",
  settle: "done",
};

/** 몇 번째 단계인지 (0부터) */
function stageIdx(stage: CourseStage) {
  return STAGE_IDS.indexOf(stage);
}

/** 문의(1/7)부터 정산(7/7)까지의 진행률 */
function stageProgress(stage: CourseStage) {
  return Math.round(((stageIdx(stage) + 1) / STAGE_IDS.length) * 100);
}

/** 강의를 이미 한 과정인지 — 진행/정산 단계 */
function isDelivered(c: Course) {
  return stageIdx(c.stage) >= stageIdx("delivery");
}

/** 확정돼서 준비가 돌아가는 중인 과정 */
function isActive(c: Course) {
  const i = stageIdx(c.stage);
  return i >= stageIdx("confirmed") && i <= stageIdx("delivery");
}

/** 아직 수주 전 — 문의·제안 단계 */
function isPipeline(c: Course) {
  return stageIdx(c.stage) <= stageIdx("proposal");
}

function won(n: number) {
  if (!n) return "—";
  return `${(n / 10000).toLocaleString("ko-KR")}만원`;
}

/** D-day. today 가 없으면(마운트 전) null — 서버·클라이언트 날짜 불일치를 피한다 */
function ddayOf(date: string, today: Date | null): number | null {
  if (!date || !today) return null;
  const target = new Date(`${date}T00:00:00`);
  if (Number.isNaN(target.getTime())) return null;
  const base = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  return Math.round((target.getTime() - base.getTime()) / 86_400_000);
}

function ddayLabel(d: number | null) {
  if (d === null) return "일정 미정";
  if (d === 0) return "오늘";
  if (d > 0) return `D-${d}`;
  return `종료 +${-d}일`;
}

/** 비서실장·회의 3인 — 이름은 company.config.ts 에서 온다 */
const SECRETARY = DEPT_LEAD.secretary?.name ?? "비서실장";
const MEETING_TRIO = ["strategy1", "strategy2", "secretary"]
  .map((id) => DEPT_LEAD[id]?.name)
  .filter(Boolean)
  .join("·");

const statusClass: Record<DeptStatus, string> = {
  "완료": "done",
  "진행 중": "working",
  "승인 대기": "approval",
  "연동 대기": "blocked",
  "대기": "waiting",
};

/** 링크만 걸려 있는 항목 (서버 연동과 무관) */
const integrations2Static = STORAGE_LINK
  ? [{ name: "결과물 보관함", status: "링크 연결", tone: "mint", href: STORAGE_LINK }]
  : [];

function PixelEmployee({ hair, shirt, accent }: { hair: string; shirt: string; accent: string }) {
  const style = {
    "--pixel-hair": hair,
    "--pixel-shirt": shirt,
    "--pixel-accent": accent,
  } as CSSProperties;
  return (
    <span className="pixel-employee" style={style} aria-hidden="true">
      <i className="pixel-shadow" />
      <i className="pixel-legs" />
      <i className="pixel-body" />
      <i className="pixel-arm left" />
      <i className="pixel-arm right" />
      <i className="pixel-face">
        <b className="pixel-eyes" />
      </i>
      <i className="pixel-hair" />
      <i className="pixel-headset" />
    </span>
  );
}

export default function Home() {
  const [engine] = useState(() => new Company());
  const [snap, setSnap] = useState<Snapshot>(() => engine.snapshot());
  const [view, setView] = useState<View>("live");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [follow, setFollow] = useState(true);
  const [briefing, setBriefing] = useState(false);
  const [filter, setFilter] = useState<"전체" | DeptStatus>("전체");
  const [toast, setToast] = useState("");
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);
  const [publishState, setPublishState] = useState<{ busy: boolean; result: PublishResult | null; error: string }>({
    busy: false,
    result: null,
    error: "",
  });
  const publishedRef = useRef(false);

  useEffect(() => {
    let raf = 0;
    let last = performance.now();
    let acc = 0;
    const loop = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      engine.tick(dt);
      acc += dt;
      if (acc >= 0.18) {
        acc = 0;
        setSnap(engine.snapshot());
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [engine]);

  useEffect(() => {
    engine.setBriefingHandler(() => setBriefing(true));
    return () => engine.setBriefingHandler(null);
  }, [engine]);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2400);
  }, []);

  const onSelect = useCallback((agent: Agent) => setSelectedId(agent.id), []);

  // 연동 설정 여부를 서버에서 받아온다 (값이 아니라 설정 여부만)
  useEffect(() => {
    fetchIntegrations()
      .then(setIntegrations)
      .catch(() => setIntegrations(null));
  }, []);

  const sendReport = useCallback(
    async (auto: boolean) => {
      setPublishState((state) => ({ ...state, busy: true, error: "" }));
      try {
        const result = await publish(buildReport(engine.snapshot()));
        setPublishState({ busy: false, result, error: "" });

        const parts: string[] = [];
        parts.push(result.notion.ok ? "Notion 저장 완료" : `Notion ${result.notion.detail ?? "실패"}`);
        parts.push(result.discord.ok ? "Discord 전송 완료" : `Discord ${result.discord.detail ?? "실패"}`);
        engine.pushLog(
          result.notion.ok && result.discord.ok ? "📤" : "⚠️",
          `완료 보고 발행 — ${parts.join(" / ")}`,
          result.notion.ok && result.discord.ok ? "mint" : "lav",
        );
        engine.pushChat("staff", SECRETARY, `보고서 발행 결과입니다.\n· ${parts.join("\n· ")}`);
        if (!auto) showToast(result.notion.ok || result.discord.ok ? "보고서를 발행했어요" : "발행 실패 — 연동 설정 필요");
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        setPublishState({ busy: false, result: null, error: message });
        engine.pushLog("⚠️", `완료 보고 발행 실패 — ${message}`, "lav");
        if (!auto) showToast("발행 실패 — 연동 설정을 확인해주세요");
      }
    },
    [engine, showToast],
  );

  // 하루가 끝나면 자동으로 한 번 발행한다
  useEffect(() => {
    if (snap.dayComplete && !publishedRef.current) {
      publishedRef.current = true;
      void sendReport(true);
    }
    if (!snap.dayComplete && snap.running) publishedRef.current = false;
  }, [snap.dayComplete, snap.running, sendReport]);

  const askAgent = useCallback(
    (agent: Agent) => {
      engine.command(`${agent.name} 지금 뭐해?`);
      setSelectedId(null);
      window.setTimeout(
        () => document.getElementById("ceo-console")?.scrollIntoView({ behavior: "smooth", block: "center" }),
        60,
      );
    },
    [engine],
  );

  const start = () => {
    engine.start();
    setBriefing(false);
    setView("live");
    showToast(`07:00 — AI 직원 ${STAFF.length}명이 출근합니다 ✨`);
  };

  const approve = () => {
    engine.approve();
    showToast("승인 완료! 제작팀이 바로 움직여요");
  };

  const teams = useMemo(
    () =>
      DEPT_ROOMS.map((room) => {
        const lead = DEPT_LEAD[room.id];
        const status = snap.deptStatus[room.id] ?? "대기";
        return {
          id: room.id,
          icon: room.icon,
          name: room.name,
          room: room.short,
          lead,
          status,
          ...DEPT_BRIEF[room.id],
        };
      }),
    [snap.deptStatus],
  );

  const filteredTeams = filter === "전체" ? teams : teams.filter((team) => team.status === filter);
  const selected = selectedId ? engine.agentById.get(selectedId) ?? null : null;
  const todo = snap.approvalPending ? 1 : 0;
  const onDuty = engine.agents.filter((a) => a.status !== "출근 전").length;

  return (
    <main className="page-shell">
      <div className="wrap">
        <nav className="app-nav" aria-label="AI Company 화면 전환">
          <div className="brand-chip">
            <span>{COMPANY.logoLetter}</span>
            <b>{COMPANY.name}</b>
          </div>
          <div className="nav-tabs">
            <button className={view === "live" ? "active" : ""} onClick={() => setView("live")}>
              🎮 라이브 오피스
            </button>
            <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}>
              📊 대시보드
            </button>
            <button
              className={`todo-tab ${todo ? "urgent" : ""}`}
              onClick={() => {
                setView("live");
                window.setTimeout(
                  () => document.getElementById("ceo-approval")?.scrollIntoView({ behavior: "smooth", block: "center" }),
                  60,
                );
              }}
            >
              📋 대표 할 일 <i>{todo}</i>
            </button>
          </div>
        </nav>

        {view === "live" ? (
          <LiveView
            engine={engine}
            snap={snap}
            follow={follow}
            setFollow={setFollow}
            selectedId={selectedId}
            onSelect={onSelect}
            onStart={start}
            onApprove={approve}
            onDuty={onDuty}
            onPublish={() => void sendReport(false)}
            publishBusy={publishState.busy}
            publishResult={publishState.result}
          />
        ) : (
          <DashboardView
            teams={teams}
            filteredTeams={filteredTeams}
            filter={filter}
            setFilter={setFilter}
            snap={snap}
            onStart={start}
            onApprove={approve}
            onSelect={(id) => setSelectedId(id)}
            integrations={integrations}
            publishResult={publishState.result}
          />
        )}

        <footer>
          {COMPANY.name}
          <br />© {COMPANY.titlePrefix} · 나의 AI 오피스
        </footer>
      </div>

      {selected ? (
        <ProfileModal
          agent={selected}
          onClose={() => setSelectedId(null)}
          onAsk={(agent) => {
            setView("live");
            askAgent(agent);
          }}
        />
      ) : null}
      {briefing ? <BriefingModal snap={snap} onClose={() => setBriefing(false)} /> : null}
      <div className={`toast ${toast ? "show" : ""}`} role="status">
        {toast}
      </div>
    </main>
  );
}

function LiveView({
  engine,
  snap,
  follow,
  setFollow,
  selectedId,
  onSelect,
  onStart,
  onApprove,
  onDuty,
  onPublish,
  publishBusy,
  publishResult,
}: {
  engine: Company;
  snap: Snapshot;
  follow: boolean;
  setFollow: (value: boolean) => void;
  selectedId: string | null;
  onSelect: (agent: Agent) => void;
  onStart: () => void;
  onApprove: () => void;
  onDuty: number;
  onPublish: () => void;
  publishBusy: boolean;
  publishResult: PublishResult | null;
}) {
  const progress = Math.round((snap.phaseIndex / (PHASES.length - 1)) * 100);

  return (
    <>
      <header className="live-hero">
        <div>
          <p className="eyebrow">LIVE OFFICE · {STAFF.length} AI STAFF · REAL-TIME</p>
          <h1>
            {COMPANY.titlePrefix} <em className="highlight">{COMPANY.titleAccent}</em>
          </h1>
          <p>출근하고, 자리에서 일하고, 회의실에 모여 회의하고, 대표실로 보고하러 갑니다.</p>
        </div>
        <div className="live-clock">
          <span>SEOUL</span>
          <b>{snap.clock}</b>
          <small>{snap.phase}</small>
        </div>
      </header>

      <section className="live-bar">
        <button className="btn btn-primary" onClick={onStart} disabled={snap.running}>
          {snap.running ? "직원들이 일하는 중…" : snap.dayComplete ? "다시 출근시키기" : "오늘 업무 시작하기"}
        </button>
        <button className="btn btn-ghost" onClick={() => engine.togglePause()}>
          {snap.paused ? "▶ 재생" : "⏸ 일시정지"}
        </button>
        <div className="speed-wrap">
          <span className="speed-label" title="시뮬레이션 전체(걷기·업무·대사)가 함께 빨라져요. 실제 외부 작업 속도와는 무관합니다.">
            재생 속도
          </span>
          <div className="speed-group" role="group" aria-label="재생 속도">
            {[1, 2, 4].map((value) => (
              <button
                key={value}
                className={!snap.turbo && snap.speed === value ? "on" : ""}
                onClick={() => engine.setSpeed(value)}
                title={value === 1 ? "말풍선 읽기·화면녹화용" : value === 4 ? "결과만 빠르게" : "기본"}
              >
                {value}x
              </button>
            ))}
            <button
              className={`skip ${snap.turbo ? "on" : ""}`}
              onClick={() => engine.skipToDecision()}
              disabled={!snap.running || snap.approvalPending}
              title="대표님이 결정할 일이 생길 때까지 단숨에 건너뜁니다"
            >
              {snap.turbo ? "건너뛰는 중…" : "⏭ 결정까지"}
            </button>
          </div>
        </div>
        <button className={`btn btn-ghost ${follow ? "on" : ""}`} onClick={() => setFollow(!follow)}>
          🎥 자동 추적 {follow ? "ON" : "OFF"}
        </button>
        <button
          className={`btn btn-ghost publish-btn ${publishResult?.notion.ok || publishResult?.discord.ok ? "sent" : ""}`}
          onClick={onPublish}
          disabled={publishBusy}
          title="완료 보고를 Notion에 저장하고 같은 내용을 Discord로 보냅니다"
        >
          {publishBusy ? "발행 중…" : "📤 보고 발행"}
        </button>
        <div className="live-progress">
          <span>
            {snap.phase} · {progress}%
          </span>
          <i>
            <b style={{ width: `${progress}%` }} />
          </i>
        </div>
        <div className="live-counts">
          <span className="lc on-duty">근무 {onDuty}</span>
          <span className="lc done">완료 {snap.stats.done}</span>
          <span className="lc working">진행 {snap.stats.working}</span>
          <span className="lc blocked">연동대기 {snap.stats.blocked}</span>
        </div>
      </section>

      <section className="live-grid">
        <OfficeWorld engine={engine} snap={snap} selectedId={selectedId} follow={follow} onSelect={onSelect} />

        <aside className="live-rail">
          <CeoConsole engine={engine} snap={snap} />

          <section className="win rail-card" id="ceo-approval">
            <div className="win-bar">
              <span>✅ ceo.approval</span>
              <span className="window-controls">—　▢　✕</span>
            </div>
            <div className={`win-body approval-body ${snap.approvalPending ? "pending" : ""}`}>
              {snap.approvalPending ? (
                <>
                  <div className="approval-top">
                    <span className="mini-badge yellow">TOP 1 제안 · 92점</span>
                    <span className="score blink">결재 대기</span>
                  </div>
                  <h3>AI 회사가 매일 아침 나 대신 출근한다면?</h3>
                  <p>회의실에서 {MEETING_TRIO}가 대표님을 기다리고 있어요.</p>
                  <div className="reason-list">
                    <span>① 실제 구축 과정</span>
                    <span>② 저장할 운영 구조</span>
                    <span>③ 날것의 시행착오</span>
                  </div>
                  <button className="btn approve-button" onClick={onApprove}>
                    이 콘텐츠 승인하기
                  </button>
                </>
              ) : (
                <>
                  <div className="approval-top">
                    <span className="mini-badge mint">{snap.approved ? "오늘 결재 완료" : "결재 대기 없음"}</span>
                  </div>
                  <h3>{snap.approved ? "승인하신 안으로 제작 중이에요" : "아직 올라온 안건이 없어요"}</h3>
                  <p>
                    {snap.approved
                      ? "대표 승인 이후 원고 → 제작 → 보관까지 이어집니다."
                      : "업무를 시작하면 콘텐츠 전략팀이 TOP 3를 회의실로 올려요."}
                  </p>
                </>
              )}
            </div>
          </section>

          <section className="win rail-card feed-card">
            <div className="win-bar">
              <span>📡 live.feed</span>
              <span className="window-controls">—　▢　✕</span>
            </div>
            <div className="win-body feed-body">
              {snap.meetingTitle ? <div className="feed-now">💬 회의 진행 중 — {snap.meetingTitle}</div> : null}
              <ul className="feed-list">
                {snap.log.map((entry) => (
                  <li key={entry.id} className={entry.tone}>
                    <b>{entry.time}</b>
                    <i>{entry.icon}</i>
                    <span>{entry.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section className="win rail-card">
            <div className="win-bar">
              <span>👥 staff.roster</span>
              <span className="window-controls">—　▢　✕</span>
            </div>
            <div className="win-body roster-body">
              {DEPT_ROOMS.map((room) => (
                <div className="roster-dept" key={room.id}>
                  <p>
                    <b>
                      {room.icon} {room.name}
                    </b>
                    <i className={`rm-dot ${statusClass[snap.deptStatus[room.id] ?? "대기"]}`} />
                  </p>
                  <div className="roster-chips">
                    {STAFF.filter((s) => s.deptId === room.id).map((seed) => {
                      const agent = engine.agentById.get(seed.id);
                      return (
                        <button
                          key={seed.id}
                          className={`roster-chip ${selectedId === seed.id ? "on" : ""}`}
                          onClick={() => agent && onSelect(agent)}
                        >
                          <i style={{ background: seed.shirt, borderColor: seed.hair }} />
                          {seed.name}
                          <small>{agent?.status ?? "출근 전"}</small>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </section>
    </>
  );
}

const QUICK_ORDERS = [
  { label: "현황 보고", command: "현황 보고해줘" },
  { label: "왜 늦어져?", command: "왜 늦어지고 있어?" },
  { label: "회의 소집", command: "전 부서 회의 소집" },
  { label: "지금 브리핑", command: "지금 브리핑 올라와" },
  { label: "집중 모드", command: "집중 모드" },
  { label: "속도 올려", command: "속도 좀 올려줘" },
];

function CeoConsole({ engine, snap }: { engine: Company; snap: Snapshot }) {
  const [draft, setDraft] = useState("");
  const logRef = useRef<HTMLDivElement>(null);
  const count = snap.chat.length;

  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [count]);

  const send = (text: string) => {
    const value = text.trim();
    if (!value) return;
    engine.command(value);
    setDraft("");
  };

  return (
    <section className="win rail-card console-card" id="ceo-console">
      <div className="win-bar">
        <span>🎤 ceo.console — 대표 지시창</span>
        <span className="window-controls">—　▢　✕</span>
      </div>
      <div className="win-body console-body">
        <div className="console-status">
          <span className={`mini-badge ${snap.focusMode ? "yellow" : "mint"}`}>
            {snap.focusMode ? "집중 모드 ON" : "평시 운영"}
          </span>
          {snap.busyWithOrder ? <span className="mini-badge lav">지시 처리 중…</span> : null}
        </div>

        <div className="console-log" ref={logRef}>
          {snap.chat.map((entry) => (
            <div key={entry.id} className={`console-line ${entry.from}`}>
              <b>{entry.from === "ceo" ? "대표님" : entry.name}</b>
              <p>{entry.text}</p>
              <small>{entry.time}</small>
            </div>
          ))}
        </div>

        <div className="console-quick">
          {QUICK_ORDERS.map((item) => (
            <button key={item.label} onClick={() => send(item.command)}>
              {item.label}
            </button>
          ))}
        </div>

        <form
          className="console-input"
          onSubmit={(event) => {
            event.preventDefault();
            send(draft);
          }}
        >
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="예: 카드뉴스팀 지금 뭐해? / 왜 늦어져?"
            aria-label="대표 지시 입력"
          />
          <button type="submit">지시</button>
        </form>
      </div>
    </section>
  );
}

function ProfileModal({
  agent,
  onClose,
  onAsk,
}: {
  agent: Agent;
  onClose: () => void;
  onAsk: (agent: Agent) => void;
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section
        className="win team-modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`${agent.name} 프로필`}
      >
        <div className="win-bar">
          <span>👤 employee_profile.exe</span>
          <button className="window-close" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="win-body employee-profile">
          <div className="profile-top">
            <PixelEmployee hair={agent.hair} shirt={agent.shirt} accent={agent.accent} />
            <div>
              <span className="status-pill working">{agent.status}</span>
              <h2>
                {agent.name}
                {agent.callsign ? <small> · {agent.callsign}</small> : null}
              </h2>
              <p>{agent.role}</p>
            </div>
          </div>
          <div className="profile-task">
            <span className="tiny-label">지금 하는 일</span>
            <strong>{agent.taskLabel}</strong>
            {agent.anim === "type" ? (
              <span className="profile-progress">
                <i style={{ width: `${Math.round(agent.progress * 100)}%` }} />
              </span>
            ) : null}
          </div>
          <div className="report-box">
            <span className="tiny-label">한마디</span>
            <strong>{agent.speech ?? agent.thoughts[0]}</strong>
          </div>
          <div className="profile-actions">
            <button className="btn btn-primary" onClick={() => onAsk(agent)}>
              🎤 지금 뭐 하는지 물어보기
            </button>
            <button className="text-button" onClick={onClose}>
              닫기
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

function BriefingModal({ snap, onClose }: { snap: Snapshot; onClose: () => void }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section
        className="win team-modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="비서실 브리핑"
      >
        <div className="win-bar">
          <span>📋 kim_secretary.brief</span>
          <button className="window-close" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="win-body">
          <p className="brief-date">{snap.clock} · {SECRETARY} 비서실장 최종 브리핑</p>
          <h3>대표님, 오늘 회사 업무가 정리됐어요.</h3>
          <ul>
            <li>
              <span className="dot green" />
              완료 {snap.stats.done}팀 — 조사·기획·QA·대본·제작·저장까지 마쳤어요
            </li>
            <li>
              <span className="dot green" />
              대표 승인 1건 반영 — TOP 1 콘텐츠 제작 완료
            </li>
            <li>
              <span className="dot gray" />
              연동 대기 {snap.stats.blocked}팀 — 외부 서비스 연결이 필요해요
            </li>
          </ul>
          <div className="decision-box">
            <span className="tiny-label">오늘 대표님이 결정할 것</span>
            <strong>없습니다. 내일 07:00에 다시 출근할게요 ✨</strong>
          </div>
          <button className="btn btn-primary" onClick={onClose}>
            확인
          </button>
        </div>
      </section>
    </div>
  );
}

type TeamRow = {
  id: string;
  icon: string;
  name: string;
  room: string;
  lead: (typeof DEPT_LEAD)[string];
  status: DeptStatus;
  task: string;
  report: string;
};

function DashboardView({
  teams,
  filteredTeams,
  filter,
  setFilter,
  snap,
  onStart,
  onApprove,
  onSelect,
  integrations,
  publishResult,
}: {
  teams: TeamRow[];
  filteredTeams: TeamRow[];
  filter: "전체" | DeptStatus;
  setFilter: (value: "전체" | DeptStatus) => void;
  snap: Snapshot;
  onStart: () => void;
  onApprove: () => void;
  onSelect: (id: string) => void;
  integrations: IntegrationStatus | null;
  publishResult: PublishResult | null;
}) {
  // 날짜는 마운트 후에 잡는다. 렌더 중에 new Date() 를 쓰면 서버가 그린 HTML 과
  // 브라우저가 그린 결과가 달라져서 하이드레이션 경고가 난다.
  const [today, setToday] = useState<Date | null>(null);
  useEffect(() => setToday(new Date()), []);

  // 단계별 건수 — 파이프라인 막대에 쓴다
  const stageCounts = useMemo(() => {
    const map: Record<string, number> = {};
    for (const s of COURSE_STAGES) map[s.id] = 0;
    for (const c of COURSES) map[c.stage] = (map[c.stage] ?? 0) + 1;
    return map;
  }, []);

  const active = COURSES.filter(isActive);
  const pipeline = COURSES.filter(isPipeline);
  const settling = COURSES.filter((c) => c.stage === "settle");

  // 강의일이 잡힌 과정을 날짜순으로 — 다가오는 일정표에 쓴다
  const scheduled = useMemo(
    () =>
      COURSES.filter((c) => c.date)
        .slice()
        .sort((a, b) => a.date.localeCompare(b.date)),
    [],
  );

  const upcoming = today
    ? scheduled.filter((c) => (ddayOf(c.date, today) ?? -1) >= 0)
    : scheduled;
  const nextCourse = upcoming[0] ?? null;
  const nextDday = nextCourse ? ddayOf(nextCourse.date, today) : null;

  // 이번 달 강의료 합계 (확정 이상만 — 문의·제안 단계는 아직 돈이 아니다)
  const monthFee = today
    ? COURSES.filter(
        (c) =>
          c.date.startsWith(
            `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`,
          ) && stageIdx(c.stage) >= stageIdx("confirmed"),
      ).reduce((sum, c) => sum + c.fee, 0)
    : 0;

  const totalLearners = active.reduce((sum, c) => sum + c.headcount, 0);

  // 서버가 알려준 실제 설정 상태로 표시한다 (연결됐다고 거짓 보고하지 않는다)
  const liveRows = integrations
    ? [
        {
          name: "Notion 저장",
          status: publishResult?.notion.ok
            ? "저장 성공"
            : integrations.notion?.configured
              ? "키 설정됨"
              : "키 미설정",
          tone: publishResult?.notion.ok ? "mint" : integrations.notion?.configured ? "yellow" : "lav",
          href: "",
        },
        {
          name: "Discord 전송",
          status: publishResult?.discord.ok
            ? "전송 성공"
            : integrations.discord?.configured
              ? "웹훅 설정됨"
              : "웹훅 미설정",
          tone: publishResult?.discord.ok ? "mint" : integrations.discord?.configured ? "yellow" : "lav",
          href: "",
        },
        { name: "Instagram", status: integrations.instagram?.need ?? "연동 대기", tone: "lav", href: "" },
        { name: "Gmail", status: integrations.gmail?.need ?? "연동 대기", tone: "lav", href: "" },
        { name: "재무 파일", status: integrations.finance?.need ?? "자료 대기", tone: "lav", href: "" },
      ]
    : [];
  const rows = [...integrations2Static, ...liveRows];

  return (
    <>
      <header className="win hero">
        <div className="win-bar">
          <span>🎀 {COMPANY.windowLabel}</span>
          <span className="window-controls" aria-hidden="true">
            —　▢　✕
          </span>
        </div>
        <div className="hero-body">
          <div className="hero-copy">
            <p className="eyebrow">교육진행 현황 · COURSE PIPELINE</p>
            <h1>
              지금 굴러가는 교육이 <em className="highlight">어디까지</em> 왔는지 보여드려요
            </h1>
            <p>
              {nextCourse ? (
                <>
                  다음 강의는 <b>{nextCourse.client}</b> · {nextCourse.title} ({nextCourse.place}) —{" "}
                  <b>{ddayLabel(nextDday)}</b>
                </>
              ) : (
                "일정이 잡힌 강의가 없습니다. 문의 단계 과정을 확정으로 올려주세요."
              )}
            </p>
          </div>
          <div className="hero-actions">
            <button className="btn btn-primary" onClick={onStart} disabled={snap.running}>
              {snap.running ? "AI 팀원들이 근무 중…" : "오늘 업무 시작하기"}
            </button>
            <span className="trust-copy">제안서 발송·교재 인쇄·정산은 대표 승인 후 진행해요</span>
          </div>
        </div>
      </header>

      {SAMPLE_DATA ? (
        <p className="sample-banner">
          ⚠️ 지금 보이는 교육 7건은 <b>예시 데이터</b>입니다. <code>company.config.ts</code> 의{" "}
          <code>COURSES</code> 를 실제 강의로 바꾸고 <code>SAMPLE_DATA = false</code> 로 내리면 이 줄이
          사라집니다.
        </p>
      ) : null}

      <section className="summary-grid" aria-label="교육진행 요약">
        <article className="metric yellow">
          <span>진행 중 교육</span>
          <strong>{active.length}</strong>
          <small>ACTIVE</small>
        </article>
        <article className="metric mint">
          <span>다음 강의</span>
          <strong>{ddayLabel(nextDday)}</strong>
          <small>NEXT</small>
        </article>
        <article className="metric pink">
          <span>제안 검토 중</span>
          <strong>{pipeline.length}</strong>
          <small>PIPELINE</small>
        </article>
        <article className="metric lav">
          <span>정산 대기</span>
          <strong>{settling.length}</strong>
          <small>SETTLE</small>
        </article>
        <article className="metric white">
          <span>이번 달 강사료</span>
          <strong className="fee">{today ? won(monthFee) : "—"}</strong>
          <small>THIS MONTH</small>
        </article>
      </section>

      <section className="workspace">
        <aside className="side-stack">
          <section className="win">
            <div className="win-bar">
              <span>📊 course_pipeline</span>
              <span className="window-controls">—　▢　✕</span>
            </div>
            <div className="win-body">
              <div className="schedule-card">
                <div>
                  <span className="tiny-label">다음 강의</span>
                  <strong>{nextCourse ? `${nextCourse.date} · ${nextCourse.place}` : "일정 없음"}</strong>
                  <p>
                    {nextCourse
                      ? `${nextCourse.client} · ${nextCourse.headcount}명 · ${nextCourse.hours}시간`
                      : "확정된 강의가 없어요"}
                  </p>
                </div>
                <span className="toggle-on">{ddayLabel(nextDday)}</span>
              </div>
              <div className="flow-list stages">
                {COURSE_STAGES.map((stage) => (
                  <div className={`flow-row ${stageCounts[stage.id] ? "" : "past"}`} key={stage.id}>
                    <span aria-hidden="true">{stage.icon}</span>
                    <b>{stage.label}</b>
                    <i>{stageCounts[stage.id] ? `${stageCounts[stage.id]}건` : "·"}</i>
                  </div>
                ))}
              </div>
              <p className="pipeline-foot">
                총 {COURSES.length}건 · 준비 중인 교육생 {totalLearners}명
              </p>
            </div>
          </section>

          <section className="win">
            <div className="win-bar">
              <span>🔗 integrations.link</span>
              <span className="window-controls">—　▢　✕</span>
            </div>
            <div className="win-body integration-list">
              {rows.map((item) =>
                item.href ? (
                  <a key={item.name} href={item.href} target="_blank" rel="noreferrer" className="integration-row">
                    <b>{item.name}</b>
                    <span className={`mini-badge ${item.tone}`}>{item.status}</span>
                  </a>
                ) : (
                  <div key={item.name} className="integration-row">
                    <b>{item.name}</b>
                    <span className={`mini-badge ${item.tone}`}>{item.status}</span>
                  </div>
                ),
              )}
            </div>
          </section>
        </aside>

        <div className="main-stack">
          <section className="win">
            <div className="win-bar">
              <span>🎓 course_progress</span>
              <span className="window-controls">—　▢　✕</span>
            </div>
            <div className="win-body">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">IN PROGRESS</p>
                  <h2>진행 중인 교육 {active.length}건</h2>
                </div>
              </div>
              {active.length ? (
                <div className="course-list">
                  {active.map((course) => {
                    const d = ddayOf(course.date, today);
                    const pct = stageProgress(course.stage);
                    const stage = COURSE_STAGES[stageIdx(course.stage)];
                    return (
                      <article className="course-card" key={`${course.client}-${course.title}`}>
                        <div className="course-top">
                          <b>{course.client}</b>
                          <span className={`mini-badge ${d !== null && d <= 7 ? "yellow" : "lav"}`}>
                            {ddayLabel(d)}
                          </span>
                        </div>
                        <p className="course-title">{course.title}</p>
                        <p className="course-meta">
                          {course.date || "일정 미정"} · {course.place} · {course.headcount}명 ·{" "}
                          {course.hours}시간 · {won(course.fee)}
                        </p>
                        <div
                          className="course-bar"
                          role="img"
                          aria-label={`${stage.label} 단계 · ${pct}%`}
                        >
                          <i style={{ width: `${pct}%` }} />
                        </div>
                        <p className="course-stage">
                          <span>
                            {stage.icon} {stage.label}
                          </span>
                          <em>{pct}%</em>
                        </p>
                        {course.note ? <p className="course-note">📌 {course.note}</p> : null}
                      </article>
                    );
                  })}
                </div>
              ) : (
                <p className="empty-note">확정돼서 준비 중인 교육이 없습니다.</p>
              )}
            </div>
          </section>

          <section className="win">
            <div className="win-bar">
              <span>🏢 team_office.board</span>
              <span className="window-controls">—　▢　✕</span>
            </div>
            <div className="win-body">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">LIVE OFFICE</p>
                  <h2>교육을 지원하는 12개 AI 팀</h2>
                </div>
                <div className="filter-tabs" role="group" aria-label="팀 상태 필터">
                  {(["전체", "진행 중", "완료", "승인 대기", "연동 대기"] as const).map((item) => (
                    <button key={item} className={filter === item ? "active" : ""} onClick={() => setFilter(item)}>
                      {item}
                    </button>
                  ))}
                </div>
              </div>
              <div className="team-grid">
                {filteredTeams.map((team) => (
                  <button className="team-card" key={team.id} onClick={() => onSelect(team.lead.id)}>
                    <span className={`status-dot ${statusClass[team.status]}`} aria-hidden="true" />
                    <span className="mini-pixel">
                      <PixelEmployee hair={team.lead.hair} shirt={team.lead.shirt} accent={team.lead.accent} />
                    </span>
                    <span className="team-copy">
                      <b>
                        {team.lead.name} · {team.name}
                      </b>
                      <small>{team.task}</small>
                    </span>
                    <span className={`status-pill ${statusClass[team.status]}`}>{team.status}</span>
                  </button>
                ))}
              </div>
            </div>
          </section>

          <section className="two-col">
            <section className="win">
              <div className="win-bar">
                <span>✅ ceo.approval</span>
                <span className="window-controls">—　▢　✕</span>
              </div>
              <div className="win-body approval-body">
                <div className="approval-top">
                  <span className="mini-badge yellow">제안서 결재</span>
                  <span className="score">{pipeline.length}건 대기</span>
                </div>
                <h3>
                  {pipeline[0]
                    ? `${pipeline[0].client}`
                    : "검토할 제안 건이 없어요"}
                </h3>
                <p>
                  {pipeline[0]
                    ? `${pipeline[0].title} · ${pipeline[0].headcount}명 · ${pipeline[0].hours}시간 · ${pipeline[0].place}${pipeline[0].note ? ` — ${pipeline[0].note}` : ""}`
                    : "문의·제안 단계에 올라온 과정이 없습니다. 리서치팀이 공고를 훑는 중이에요."}
                </p>
                <button
                  className={`btn approve-button ${snap.approved ? "approved" : ""}`}
                  onClick={onApprove}
                  disabled={!snap.approvalPending}
                >
                  {snap.approved
                    ? "승인 완료 · 교안팀 전달됨"
                    : snap.approvalPending
                      ? "이 제안서 승인하기"
                      : "대기 중인 안건 없음"}
                </button>
              </div>
            </section>

            <section className="win secretary">
              <div className="win-bar">
                <span>📋 kim_secretary.brief</span>
                <span className="window-controls">—　▢　✕</span>
              </div>
              <div className="win-body">
                <p className="brief-date">2026.07.26 · {snap.clock} 현재</p>
                <h3>{snap.dayComplete ? "대표님, 오늘 업무가 정리됐어요." : "대표님, 현재 진행 상황이에요."}</h3>
                <ul>
                  <li>
                    <span className="dot green" />
                    {snap.phase} 진행 중 — 완료 {snap.stats.done}팀
                  </li>
                  <li>
                    <span className={`dot ${snap.approvalPending ? "yellow" : "green"}`} />
                    {snap.approvalPending ? "TOP 1 대표 확인 필요" : "대기 중인 결재 없음"}
                  </li>
                  <li>
                    <span className="dot gray" />
                    외부 서비스 연동 대기
                  </li>
                </ul>
                <div className="decision-box">
                  <span className="tiny-label">대표님이 오늘 결정할 1개</span>
                  <strong>
                    {snap.approvalPending
                      ? "TOP 1 콘텐츠를 제작할지 승인해주세요."
                      : snap.approved
                        ? "결정 완료! 제작팀이 다음 업무를 진행해요."
                        : "아직 올라온 안건이 없어요."}
                  </strong>
                </div>
              </div>
            </section>
          </section>
        </div>
      </section>

      <section className="win storage">
        <div className="win-bar">
          <span>🗓️ course_schedule</span>
          <span className="window-controls">—　▢　✕</span>
        </div>
        <div className="win-body">
          <div className="section-heading">
            <div>
              <p className="eyebrow">SCHEDULE</p>
              <h2>강의 일정 {scheduled.length}건</h2>
            </div>
            {STORAGE_LINK ? (
              <a className="btn btn-small" href={STORAGE_LINK} target="_blank" rel="noreferrer">
                보관함 열기
              </a>
            ) : null}
          </div>
          <div className="result-table">
            <div className="result-row header">
              <span>과정</span>
              <span>고객사 · 장소</span>
              <span>단계</span>
              <span>일정</span>
            </div>
            {scheduled.map((course) => {
              const d = ddayOf(course.date, today);
              const stage = COURSE_STAGES[stageIdx(course.stage)];
              return (
                <div className="result-row" key={`${course.client}-${course.date}`}>
                  <b>{course.title}</b>
                  <span>
                    {course.client} · {course.place}
                  </span>
                  <span className={`status-pill ${STAGE_PILL[course.stage]}`}>{stage.label}</span>
                  <span>
                    {course.date}
                    <br />
                    <em className="dday">{ddayLabel(d)}</em>
                  </span>
                </div>
              );
            })}
            {scheduled.length === 0 ? (
              <div className="result-row">
                <b>일정이 잡힌 강의가 없습니다</b>
                <span>—</span>
                <span>—</span>
                <span>—</span>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <p className="dash-note">
        대표 {CEO.name}({CEO.callsign}) · AI 직원 {teams.length}개 부서 {STAFF.length}명 · 이 화면은 라이브 오피스와 같은 상태를
        공유해요.
      </p>
    </>
  );
}
