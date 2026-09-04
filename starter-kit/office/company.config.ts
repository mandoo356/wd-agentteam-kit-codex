// ============================================================
//  내 AI 회사 설정 — 여기 한 파일만 고치면 됩니다
// ============================================================
//  회사 이름, 부서 이름, 직원 이름·성격·머리색까지 전부 여기 있어요.
//  다른 파일은 건드리지 않아도 됩니다.
//
//  ⚠️ 딱 2가지 규칙
//   1. 부서 id(research, brand, ...)는 절대 바꾸지 마세요. 시뮬레이션 엔진이
//      이 id로 움직입니다. 바꾸면 캐릭터가 길을 잃어요.
//      → 바꿔도 되는 건 name(부서 이름) · icon · short 입니다.
//   2. 부서는 12개를 유지하세요. 사무실 배치가 4열 3행 = 12칸 고정입니다.
//      안 쓰는 부서는 지우지 말고 이름만 바꿔서 쓰세요.
//
//  직원 수는 자유롭게 늘리고 줄여도 됩니다. 한 팀에 팀장(lead) 1명은 두세요.
//
//  📌 지금 값은 전부 견본입니다. 모듈 5의 카드 P13 으로 내 것으로 바꿉니다.
// ============================================================

/** 회사 기본 정보 */
export const COMPANY = {
  /** 좌측 상단 헤더에 뜨는 회사 이름 */
  name: "MY AI COMPANY",
  /** 헤더 로고 배지에 들어갈 글자 1개 (이모지도 됩니다) */
  logoLetter: "M",
  /** 화면 상단 큰 제목 (앞부분) */
  titlePrefix: "여기에_회사이름",
  /** 화면 상단 큰 제목 (강조되는 뒷부분) */
  titleAccent: "AI Office",
  /** 브라우저 탭 제목 */
  pageTitle: "여기에_회사이름 — AI 오피스",
  /** 검색·공유될 때 뜨는 설명 */
  description: "12개 AI 팀이 돌아가는 나의 AI 오피스",
  /** 창 하단 파일명 느낌의 라벨 */
  windowLabel: "my_office.exe — 대표실",
  /** 일일 브리핑 제목에 들어갈 이름 */
  reportName: "My AI Office",
} as const;

/** 대표(나) — 사무실 대표실에 앉아 있는 캐릭터 */
export const CEO_PROFILE = {
  name: "여기에_내이름",
  callsign: "대표님",
  role: "대표 · 1인 사업자",
  hair: "#42283a",
  shirt: "#c9b8ff",
  accent: "#b06ec2",
  skin: "#ffdcc4",
  thoughts: [
    "AI가 초안을 만들고, 마지막 판단은 내가 한다.",
    "나가기 전에 내 눈으로 한 번 더 본다.",
    "이건 고객에게 그대로 보낼 수 있는 상태인가?",
  ],
};

/**
 * 부서 12개.
 * id = 고정(엔진용) / name·short·icon = 자유롭게 변경
 * task = 오늘 하는 일 / report = 팀장 한줄보고
 */
export const DEPARTMENTS = [
  {
    id: "research",
    name: "조사팀",
    short: "research",
    icon: "🔎",
    task: "자료·동향·경쟁사 조사",
    report: "출처가 확인된 것만 올립니다.",
  },
  {
    id: "brand",
    name: "콘텐츠팀",
    short: "content",
    icon: "📝",
    task: "블로그·SNS 원고",
    report: "초안까지만 하고 발행은 대표님 승인 후에요.",
  },
  {
    id: "strategy1",
    name: "기획팀",
    short: "planning",
    icon: "💜",
    task: "제안서·기획서 작성",
    report: "고객이 뭘 원하는지부터 다시 뜯어봅니다.",
  },
  {
    id: "qa",
    name: "검수팀",
    short: "review",
    icon: "🛡️",
    task: "사실·중복·톤 검수",
    report: "근거 없는 수치는 반려합니다.",
  },
  {
    id: "strategy2",
    name: "설계팀",
    short: "design",
    icon: "🎓",
    task: "구조·순서·흐름 설계",
    report: "쓰는 사람 입장에서 말이 되는지 봅니다.",
  },
  {
    id: "reels",
    name: "제작팀",
    short: "production",
    icon: "📚",
    task: "실제 결과물 만들기",
    report: "바로 쓸 수 있는 상태로 만들어요.",
  },
  {
    id: "carousel",
    name: "디자인팀",
    short: "design.visual",
    icon: "🖼️",
    task: "이미지·카드·표지",
    report: "시안 먼저 보여드리고 승인받고 뽑습니다.",
  },
  {
    id: "partner",
    name: "브랜딩팀",
    short: "branding",
    icon: "🎤",
    task: "프로필·소개서 편집",
    report: "보낼 곳에 따라 톤을 다르게 씁니다.",
  },
  {
    id: "finance",
    name: "재무팀",
    short: "finance",
    icon: "🧾",
    task: "입금·미수금·세금 일정",
    report: "은행은 안 봅니다. 주신 내역으로 정리해요.",
  },
  {
    id: "review",
    name: "성과분석팀",
    short: "analytics",
    icon: "📈",
    task: "후기·반응·재의뢰 기록",
    report: "잘 통한 걸 다음에 넘깁니다.",
  },
  {
    id: "ops",
    name: "운영팀",
    short: "ops",
    icon: "⚙️",
    task: "일정·알림·자동화 관리",
    report: "실패하면 재시도하고 기록 남깁니다.",
  },
  {
    id: "secretary",
    name: "비서실",
    short: "secretary",
    icon: "📋",
    task: "일정·메일·한줄보고",
    report: "대표님이 결정할 것만 추려서 올립니다.",
  },
] as const;

/**
 * 직원 명단.
 * dept = 위 부서 id / rank: "lead"(팀장) 또는 "member"(팀원)
 * colors = [머리색, 옷색, 포인트색]
 * thoughts = 자리를 비웠을 때 머리 위에 뜨는 혼잣말
 *
 * 📌 지금은 팀마다 팀장 1명씩만 있는 견본입니다.
 *    .codex/agents/ 에 만든 직원 이름으로 바꾸고, 원하면 팀원을 늘리세요.
 */
export type StaffEntry = {
  dept: string;
  rank: "lead" | "member";
  name: string;
  role: string;
  colors: [string, string, string];
  thoughts: string[];
  callsign?: string;
};

export const STAFF_LIST: StaffEntry[] = [
  { dept: "research", rank: "lead", name: "조사담당", role: "조사 팀장",
    colors: ["#6b3d34", "#c9b8ff", "#b06ec2"],
    thoughts: ["이 자료, 원 출처가 어디지?", "오늘 자로 다시 훑어봅니다."] },

  { dept: "brand", rank: "lead", name: "콘텐츠담당", role: "콘텐츠 팀장",
    colors: ["#372b4a", "#c9b8ff", "#c9b8ff"],
    thoughts: ["읽는 사람이 끝까지 볼 글인가?", "발행은 안 합니다. 초안까지만."] },

  { dept: "strategy1", rank: "lead", name: "기획담당", role: "기획 팀장",
    colors: ["#c26e4b", "#b06ec2", "#c9b8ff"],
    thoughts: ["대상·기간·예산, 하나라도 비면 못 씁니다.", "짧아야 읽힙니다."] },

  { dept: "qa", rank: "lead", name: "검수담당", role: "검수 팀장",
    colors: ["#2d4b46", "#c2eddd", "#c9b8ff"],
    thoughts: ["출처 없는 수치는 그냥 뺍니다.", "나가기 전 마지막 관문이에요."] },

  { dept: "strategy2", rank: "lead", name: "설계담당", role: "설계 팀장",
    colors: ["#8b534a", "#f7e3b5", "#b06ec2"],
    thoughts: ["오늘도 신나게 설계해볼까요!", "목표부터 확정하고 시작합니다."] },

  { dept: "reels", rank: "lead", name: "제작담당", role: "제작 팀장",
    colors: ["#2c2638", "#c9b8ff", "#b06ec2"],
    thoughts: ["설계가 확정돼야 시작합니다.", "바로 쓸 수 있는 상태로 만들어요."] },

  { dept: "carousel", rank: "lead", name: "디자인담당", role: "디자인 팀장",
    colors: ["#d88d68", "#b06ec2", "#c9b8ff"],
    thoughts: ["시안 먼저 보여드리고 승인받고 뽑습니다.", "표지가 안 걸리면 다 소용없어요."] },

  { dept: "partner", rank: "lead", name: "브랜딩담당", role: "브랜딩 팀장",
    colors: ["#4a3550", "#efe6f7", "#b06ec2"],
    thoughts: ["보낼 곳에 따라 톤을 바꿉니다.", "없는 경력을 지어내진 않아요."] },

  { dept: "finance", rank: "lead", name: "재무담당", role: "재무 팀장",
    colors: ["#241533", "#c2eddd", "#f7e3b5"],
    thoughts: ["입금 안 되면 제일 먼저 압니다.", "숫자는 주신 것만 씁니다."] },

  { dept: "review", rank: "lead", name: "분석담당", role: "성과분석 팀장",
    colors: ["#3c3a4f", "#c9b8ff", "#c2eddd"],
    thoughts: ["반응이 좋았던 걸 다음에 넘깁니다.", "표본이 적으면 그렇다고 적어요."] },

  { dept: "ops", rank: "lead", name: "운영담당", role: "운영 팀장",
    colors: ["#2f2a3d", "#efe6f7", "#c9b8ff"],
    thoughts: ["실패하면 재시도하고 기록 남깁니다.", "알림은 꼭 필요한 것만."] },

  { dept: "secretary", rank: "lead", name: "비서담당", role: "비서실장",
    colors: ["#4a2f4a", "#f5d6b8", "#fb7bd6"],
    thoughts: ["오늘 결정하실 건 두 가지예요.", "일정 겹치는 것부터 알려드립니다."] },
];

/**
 * 외부 연동을 아직 안 붙인 팀 → 화면에 "연동 대기"로 표시됩니다.
 * 연동을 다 붙였거나, 그냥 전부 초록불로 보고 싶으면 빈 배열 []로 두세요.
 */
export const PENDING_INTEGRATIONS: Record<string, string> = {
  brand: "SNS 지표 연동",
  finance: "입금 내역 파일",
  review: "만족도 설문 데이터",
};

/**
 * 결과 보관함 링크 (Notion 등). 비워두면 화면에서 링크 버튼이 숨겨집니다.
 * 예: "https://www.notion.so/내페이지주소"
 */
export const STORAGE_LINK = "";

// ============================================================
//  진행 현황 — 대시보드 화면이 이 데이터를 읽습니다
// ============================================================

/**
 * 일 한 건이 문의부터 정산까지 지나는 7단계.
 * 순서가 곧 진행률이라 배열 순서를 바꾸면 진행률 계산도 따라 바뀝니다.
 */
export const COURSE_STAGES = [
  { id: "inquiry", label: "문의 접수", icon: "📥", dept: "secretary" },
  { id: "proposal", label: "제안서", icon: "💜", dept: "strategy1" },
  { id: "confirmed", label: "확정", icon: "🤝", dept: "secretary" },
  { id: "design", label: "설계", icon: "🎓", dept: "strategy2" },
  { id: "material", label: "제작", icon: "📚", dept: "reels" },
  { id: "delivery", label: "진행", icon: "🎤", dept: "review" },
  { id: "settle", label: "정산", icon: "🧾", dept: "finance" },
] as const;

export type CourseStage = (typeof COURSE_STAGES)[number]["id"];

export type Course = {
  /** 고객사·기관 이름 */
  client: string;
  /** 일감 이름 */
  title: string;
  /** 날짜 "YYYY-MM-DD". 미정이면 빈 문자열 */
  date: string;
  /** 소요 시간(시간 단위) */
  hours: number;
  /** 인원 */
  headcount: number;
  /** 지금 어느 단계인지 */
  stage: CourseStage;
  /** 금액(원). 모르면 0 */
  fee: number;
  /** 장소 */
  place: string;
  /** 메모 한 줄 */
  note?: string;
};

/**
 * 🚨 여기는 견본 데이터입니다.
 *
 * 내 실제 일감으로 바꾸고, 아래 SAMPLE_DATA 를 false 로 내리세요.
 * 그러면 화면 위 "예시 데이터" 경고 띠가 사라집니다.
 *
 * 💡 금액 규칙 — 추측으로 금액을 만들지 마세요.
 *    확정된 것만 fee 에 넣고, 미확정이면 fee: 0 + note 에 사유를 적습니다.
 *    화면의 0 은 "무료"가 아니라 "아직 확정 안 됨"이라는 뜻입니다.
 */
export const SAMPLE_DATA = true;

export const COURSES: Course[] = [
  {
    client: "○○공단",
    title: "관리자 대상 과정",
    date: "2026-09-20",
    hours: 8,
    headcount: 32,
    stage: "material",
    fee: 1_600_000,
    place: "부산",
    note: "자료 인쇄 마감 9/15",
  },
  {
    client: "△△전자",
    title: "실무자 실습 과정",
    date: "2026-09-27",
    hours: 4,
    headcount: 24,
    stage: "design",
    fee: 800_000,
    place: "동대구",
    note: "노트북 지참 확인 필요",
  },
  {
    client: "□□시 평생학습관",
    title: "디지털 역량 강화",
    date: "2026-10-03",
    hours: 6,
    headcount: 40,
    stage: "confirmed",
    fee: 1_200_000,
    place: "광주송정",
    note: "자료 40부",
  },
  {
    client: "◇◇병원",
    title: "커뮤니케이션 과정",
    date: "",
    hours: 3,
    headcount: 18,
    stage: "proposal",
    fee: 0,
    place: "대전",
    note: "예산 확인 중이라 금액 비움",
  },
  {
    client: "☆☆협회",
    title: "담당자 워크숍",
    date: "",
    hours: 4,
    headcount: 20,
    stage: "inquiry",
    fee: 0,
    place: "미정",
    note: "일정 조율 중",
  },
  {
    client: "▽▽공사",
    title: "신입 대상 과정",
    date: "2026-08-28",
    hours: 8,
    headcount: 28,
    stage: "settle",
    fee: 1_600_000,
    place: "수서",
    note: "계산서 발행 완료, 입금 대기",
  },
  {
    client: "◎◎대학교",
    title: "스킬 향상 워크숍",
    date: "2026-09-05",
    hours: 4,
    headcount: 22,
    stage: "delivery",
    fee: 800_000,
    place: "천안아산",
    note: "설문 회수 중",
  },
];
