// 최종 발표자료(비전공자용): node deck_final.js → 05_문서/최종발표자료.pptx, 05_문서/최종발표대본.md
// 원칙: 전문용어 대신 쉬운 말, 기법마다 "산업수학으로 보면" 해석 한 줄. 수치는 02_정제데이터·README의 결과값.
const fs = require('fs'); const PPTX = require('pptxgenjs');
const R = 'C:/Users/PTY/Desktop/지산학아이디어톤/';
const OUT = process.env.DECK_OUT || R + '05_문서/최종발표자료.pptx';

const NAVY = '0B3C5D', CORAL = 'E8573F', ICE = 'EAF2F8', INK = '1D2B36', MUTE = '5B6B78', WHITE = 'FFFFFF', LINE = 'C9D6E0', SOFT = '9FB8CC';
const FONT = 'Malgun Gothic';

const p = new PPTX(); p.layout = 'LAYOUT_WIDE'; p.title = '배에서 내린 8시간, 부산을 맛보게 하는 법';
p.theme = { headFontFace: FONT, bodyFontFace: FONT };
p.defineSlideMaster({ title: 'COVER', background: { color: NAVY }, objects: [
  { placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 1.9, w: 11.7, h: 2.2, fontFace: FONT, fontSize: 44, bold: true, color: WHITE, valign: 'top', align: 'left' }, text: '' } }] });
p.defineSlideMaster({ title: 'CONTENT', background: { color: WHITE }, objects: [
  { placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.62, w: 12.1, h: 0.8, fontFace: FONT, fontSize: 28, bold: true, color: NAVY, valign: 'middle', align: 'left' }, text: '' } }],
  slideNumber: { x: 12.4, y: 7.0, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 10, color: MUTE } });

const tb = (s, text, o) => s.addText(text, { isTextBox: true, fontFace: FONT, color: INK, fontSize: 16, valign: 'top', margin: 0, ...o });
const card = (s, x, y, w, h, fill = ICE) => s.addShape(p.ShapeType.roundRect, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08 });
const dot = (s, n, x, y, d = 0.5, fill = CORAL) => { s.addShape(p.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  tb(s, String(n), { x, y, w: d, h: d, align: 'center', valign: 'middle', color: WHITE, bold: true, fontSize: 16 }); };
const stat = (s, x, y, w, big, lab, color = NAVY) => { tb(s, big, { x, y, w, h: 0.9, fontSize: 40, bold: true, color }); tb(s, lab, { x, y: y + 0.9, w, h: 0.8, fontSize: 14, color: MUTE }); };
// 쉬운 말 / 산업수학으로 보면 — 방법 슬라이드의 반복 모티프
const mathCard = (s, x, y, w, h, body) => { card(s, x, y, w, h, NAVY);
  tb(s, '산업수학으로 보면', { x: x + 0.3, y: y + 0.25, w: w - 0.6, h: 0.35, fontSize: 14, bold: true, color: 'F4A08F' });
  tb(s, body, { x: x + 0.3, y: y + 0.7, w: w - 0.6, h: h - 0.9, fontSize: 15, color: WHITE, paraSpaceAfter: 6 }); };
const src = (s, t) => tb(s, t, { x: 0.6, y: 6.95, w: 11.5, h: 0.3, fontSize: 10, color: MUTE });
const CH = { catAxisLabelFontFace: FONT, valAxisLabelFontFace: FONT, dataLabelFontFace: FONT, legendFontFace: FONT, titleFontFace: FONT,
  catAxisLabelColor: MUTE, valAxisLabelColor: MUTE, catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, dataLabelFontSize: 12, dataLabelColor: INK,
  valGridLine: { color: 'E3E9EE', size: 0.75 }, catGridLine: { style: 'none' }, showLegend: false };

const NOTES = [];
let SEC = '';
const sec = t => { SEC = t; p.addSection({ title: t }); };
const slide = (title, kicker, notes) => { const s = p.addSlide({ masterName: 'CONTENT', sectionTitle: SEC });
  s.addText(title, { placeholder: 'title' }); if (kicker) tb(s, kicker, { x: 0.6, y: 0.28, w: 12, h: 0.35, fontSize: 13, bold: true, color: CORAL });
  s.addNotes(notes); NOTES.push([title, notes]); return s; };

// ============ 1. 표지 ============
sec('시작');
let s = p.addSlide({ masterName: 'COVER', sectionTitle: SEC });
s.addText('배에서 내린 8시간,\n부산을 맛보게 하는 법', { placeholder: 'title' });
tb(s, '크루즈 승객이 배를 놓치지 않고 부산 음식을 먹게 돕는 서비스, Busan Bite Pass', { x: 0.8, y: 4.3, w: 11.5, h: 0.5, fontSize: 20, color: 'C9DCEB' });
tb(s, '크루즈 미식 루트 팀 · 2026 지산학 아이디어톤 「부산의 맛, 로컬에서 글로컬」', { x: 0.8, y: 6.5, w: 11.5, h: 0.4, fontSize: 13, color: SOFT });
let n = '안녕하세요, 크루즈 미식 루트 팀입니다. 크루즈를 타고 부산에 온 외국인이 배에서 내린 몇 시간 동안, 배를 놓치지 않으면서 부산 음식을 먹게 돕는 서비스를 만들었습니다.';
s.addNotes(n); NOTES.push(['표지', n]);

// ============ 2. 한 장 요약 ============
s = slide('한 장 요약: 문제, 우리의 답, 결과', '결론부터',
  '결론부터 말씀드리겠습니다. 크루즈 승객은 1년 새 세 배 가까이 늘었는데, 원도심에서 외국인이 쓴 돈의 66%는 면세점 같은 쇼핑입니다. 시간이 짧아 가게까지 못 가기 때문입니다. 저희는 배 시간에 맞춰 먹을 곳과 순서를 짜 주는 서비스를 만들었고, 일이 틀어지는 상황을 1,000번 흉내 내도 배를 놓친 경우는 한 번도 없었습니다.');
[['문제', '승객은 늘었는데 돈은 면세점으로', '크루즈 승객 40만 명(1년 새 +176%), 원도심 외국인 소비의 66%는 쇼핑'],
 ['우리의 답', '배 시간에 맞춘 맛집 시간표', 'QR로 배 이름만 넣으면 어디서 무엇을 먹고 언제 돌아올지 알려 준다'],
 ['결과', '1,000번 시험해도 지각 0번', '대표 루트: 8시 30분 하선 → 음식 6곳·볼거리 2곳 → 15시 48분 복귀']].forEach(([k, h, b], i) => {
  const x = 0.6 + i * 4.1; card(s, x, 1.75, 3.85, 4.6);
  tb(s, k, { x: x + 0.35, y: 2.05, w: 3.2, h: 0.4, fontSize: 15, bold: true, color: CORAL });
  tb(s, h, { x: x + 0.35, y: 2.55, w: 3.2, h: 1.3, fontSize: 24, bold: true, color: NAVY });
  tb(s, b, { x: x + 0.35, y: 4.15, w: 3.2, h: 1.9, fontSize: 16, color: INK }); });

// ============ 문제 ============
sec('문제');
s = slide('어느 크루즈 승객의 하루', '문제 ① 부산에 내렸지만 부산을 못 본다',
  '한 승객의 하루를 따라가 보겠습니다. 아침 8시, 수천 명과 함께 북항에 도착합니다. 입국 심사를 마치면 9시 반입니다. 점심에 이름난 밀면집에 가 보니 줄이 40분입니다. 배 시간이 걱정돼 줄을 포기하고 면세점에 들렀다가, 결국 부산 음식은 못 먹고 배로 돌아갑니다. 언론은 이것을 부산 패싱이라고 부릅니다.');
[['08:00', '입항', '수천 명이 한꺼번에 북항에 도착'], ['09:30', '하선', '입국 심사를 마치면 벌써 9시 반'], ['12:00', '점심', '이름난 밀면집 줄은 40분'],
 ['13:00', '포기', '배 시간이 걱정돼 면세점이나 단체버스로'], ['16:30', '복귀', '부산 음식은 못 먹고 배로']].forEach(([t, k, d], i) => {
  const y = 1.75 + i * 0.92, c = i >= 3 ? CORAL : NAVY;
  tb(s, t, { x: 0.8, y, w: 1.3, h: 0.5, fontSize: 22, bold: true, color: c }); dot(s, i + 1, 2.2, y, 0.48, c);
  tb(s, k, { x: 2.95, y: y + 0.05, w: 1.1, h: 0.45, fontSize: 18, bold: true, color: c }); tb(s, d, { x: 4.1, y: y + 0.07, w: 4.4, h: 0.45, fontSize: 16 }); });
card(s, 8.9, 1.75, 3.85, 4.3, NAVY);
tb(s, '“사실 부산 여행할 시간이 없어요”', { x: 9.25, y: 2.15, w: 3.2, h: 1.5, fontSize: 22, bold: true, color: WHITE });
tb(s, '크루즈로 온 독일 관광객\nKBS부산, 2026.1.18', { x: 9.25, y: 3.8, w: 3.2, h: 0.8, fontSize: 13, color: 'C9DCEB' });
tb(s, '부산에 내렸지만 부산을 지나친다 — “부산 패싱”', { x: 9.25, y: 4.9, w: 3.2, h: 0.9, fontSize: 15, bold: true, color: 'F4A08F' });
src(s, '시간표는 북항 당일 기항을 가정한 예시');

s = slide('기회는 커졌다: 승객은 3년 새 6배, 머무는 시간은 8시간 남짓', '문제 ② 기회',
  '기회는 커지고 있습니다. 부산항 입출항 신고를 정리해 보니 1월부터 7월까지 승객이 2023년 6만 7천 명에서 올해 40만 명으로 늘었습니다. 승객 10명 중 8명은 8시간에서 13시간 머무는 배를 타고 오고, 실제로 돌아다닐 수 있는 시간은 보통 8시간 반입니다. 이 8시간을 어디서 쓰게 하느냐가 관건입니다.');
s.addChart(p.ChartType.bar, [{ name: '1~7월 승객(만 명)', labels: ['2023', '2024', '2025', '2026'], values: [6.7, 9.3, 14.6, 40.3] }],
  { x: 0.6, y: 1.7, w: 7.4, h: 4.9, barDir: 'col', chartColors: [NAVY, NAVY, NAVY, CORAL], showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0.0"만"',
    showTitle: true, title: '부산항 크루즈 승객 (1~7월, 만 명)', titleFontSize: 14, titleColor: INK, valAxisHidden: true, ...CH });
stat(s, 8.6, 2.0, 4.2, '+176%', '2026년 1~7월 403,188명\n(전년 같은 기간 대비)', CORAL);
stat(s, 8.6, 4.2, 4.2, '8.5시간', '돌아다닐 수 있는 시간(가운데 값)\n승객 81%가 8~13시간 머무는 배');
src(s, '자료: 공공데이터포털 부산항 크루즈 입출항 신고 648건(2023.1~2026.7, 중복 제거)');

s = slide('그런데 돈은 면세점에서 끝난다, 제주는 이미 겪었다', '문제 ③ 데이터로 확인',
  '그런데 돈은 어디로 갈까요? 한국관광데이터랩의 외국인 카드 결제를 보면 원도심 중구에서 쓴 돈의 66%가 쇼핑이고, 음식은 21% 정도입니다. 이대로 두면 어떻게 되는지는 제주가 보여 줍니다. 승객은 늘었는데 한 사람이 쓰는 돈은 2년 만에 188달러에서 122달러로 35% 줄었습니다. 승객이 늘어도 지역 가게는 손해를 볼 수 있다는 뜻입니다.');
s.addChart(p.ChartType.doughnut, [{ name: '중구 외국인 소비', labels: ['쇼핑(면세 포함)', '음식', '기타'], values: [66, 21, 13] }],
  { x: 0.5, y: 1.7, w: 5.6, h: 4.6, chartColors: [CORAL, NAVY, 'C9D6E0'], holeSize: 55, showPercent: true, showValue: false, dataLabelColor: WHITE, dataLabelFontSize: 14,
    showLegend: true, legendPos: 'b', legendFontSize: 13, showTitle: true, title: '원도심(중구) 외국인 카드 소비 구성', titleFontSize: 14, titleColor: INK, ...{ catAxisLabelFontFace: FONT, dataLabelFontFace: FONT, legendFontFace: FONT, titleFontFace: FONT } });
s.addChart(p.ChartType.bar, [{ name: '1인당 지출(달러)', labels: ['2023', '2024', '2025'], values: [188.3, 157.1, 122.1] }],
  { x: 6.6, y: 1.7, w: 6.1, h: 4.6, barDir: 'col', chartColors: [CORAL], showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0',
    showTitle: true, title: '대조군 제주: 크루즈객 1인당 지출(달러)  −35%', titleFontSize: 14, titleColor: INK, valAxisHidden: true, ...CH });
src(s, '자료: 한국관광데이터랩 외국인 카드소비(2025.10~2026.7), 서울신문(2026.11.4)');

s = slide('왜 가게까지 못 갈까: 네 가지 벽', '문제 ④ 원인',
  '왜 가게까지 못 갈까요? 네 가지 벽이 있습니다. 시간이 짧고, 가게가 언제 쉬는지 모르고, 줄과 이동에 시간을 버리고, 무엇보다 수천 명이 한꺼번에 내립니다. 하나만 풀면 다른 벽에 막힙니다. 그래서 네 가지를 동시에 계산해야 합니다.');
[['시간이 짧다', '머무는 시간 8시간 남짓,\n승선 30분 전에는 돌아와야 한다'], ['가게 사정을 모른다', '쉬는 시간·문 닫는 시각이\n가게마다 다르다'],
 ['줄과 이동에 시간을 버린다', '크루즈 승객이 몰리는 시간엔\n줄이 1.6배로 길어진다'], ['한꺼번에 내린다', '큰 배 두 척이 겹친 날\n7,831명이 동시에 하선']].forEach(([h, b], i) => {
  const x = 0.6 + (i % 2) * 6.2, y = 1.75 + Math.floor(i / 2) * 2.4; card(s, x, y, 5.9, 2.1); dot(s, i + 1, x + 0.35, y + 0.35, 0.55);
  tb(s, h, { x: x + 1.15, y: y + 0.38, w: 4.5, h: 0.5, fontSize: 20, bold: true, color: NAVY }); tb(s, b, { x: x + 1.15, y: y + 1.0, w: 4.5, h: 0.9, fontSize: 16 }); });
src(s, '근거: 입출항 신고(시간·하선 인원), 부산시 맛집 API(영업시간), 2026.5.8 2척 동시 기항');

// ============ 우리의 답 ============
sec('우리의 답');
s = slide('우리의 답: 배 시간에 맞춘 맛집 시간표, Busan Bite Pass', '해결',
  '저희의 답은 배 시간에 맞춘 맛집 시간표입니다. 하선할 때 QR을 찍고 배 이름만 넣으면, 몇 시에 어디서 무엇을 먹고 언제 돌아와야 하는지 시간표를 줍니다. 돌아갈 시간 두 시간 전에는 알림도 보냅니다. 같은 정보로 상인에게는 몇 시에 손님이 몇 명 올지 미리 알려 줍니다. 승객과 상인 모두에게 쓸모가 있습니다.');
[['QR 찍고 배 이름 입력', '내릴 시각과 돌아갈 시각이 자동으로 정해진다'], ['맞춤 시간표 받기', '먹을 곳·볼거리·순서·이동 수단·줄 서는 시간까지'], ['복귀 알림', '승선 2시간 전, 남은 일정을 다시 맞춰 준다']].forEach(([h, b], i) => {
  const x = 0.6 + i * 3.25; card(s, x, 1.75, 3.0, 3.0); dot(s, i + 1, x + 0.3, 2.05, 0.55);
  tb(s, h, { x: x + 0.3, y: 2.8, w: 2.45, h: 0.85, fontSize: 18, bold: true, color: NAVY }); tb(s, b, { x: x + 0.3, y: 3.65, w: 2.45, h: 1.0, fontSize: 14 }); });
card(s, 0.6, 5.0, 9.4, 1.55, 'FDECE8');
tb(s, '상인에게는', { x: 0.9, y: 5.2, w: 2, h: 0.4, fontSize: 15, bold: true, color: CORAL });
tb(s, '같은 입항 정보로 “몇 시에 손님 몇 명”을 미리 알려 준다 → 재료·인력 준비, 쉬는 시간 조정', { x: 0.9, y: 5.65, w: 8.8, h: 0.7, fontSize: 16 });
s.addImage({ path: R + '05_문서/QR/QR_BusanBitePass.png', x: 10.5, y: 1.85, w: 2.2, h: 2.2, altText: '서비스 QR 코드' });
tb(s, '지금 써 보기\nddayoung03.github.io/\nbusan-bite-pass', { x: 10.35, y: 4.2, w: 2.6, h: 1.1, fontSize: 13, color: MUTE, align: 'center' });

// ============ 어떻게 만들었나 ============
sec('어떻게 만들었나');
s = slide('어떻게 만들었나: 네 단계', '방법 한눈에',
  '어떻게 만들었는지 네 단계로 말씀드리겠습니다. 먼저 공공데이터와 외국인 댓글을 모았고, 외국인이 먹고 싶어 하는 정도를 점수로 바꿨습니다. 그다음 규칙을 지키면서 점수가 가장 높은 루트를 컴퓨터로 찾았고, 마지막으로 일이 틀어지는 상황을 수천 번 흉내 내서 정말 배를 놓치지 않는지 시험했습니다. 괄호 안은 실제로 쓴 수학 기법의 이름입니다.');
[['모으기', '공공데이터 + 외국인 댓글', '데이터 정제'], ['점수 매기기', '“얼마나 먹고 싶어 하나”를 숫자로', '로그 변환 · 한계효용'],
 ['루트 짜기', '규칙을 지키며 점수가 가장 높은 순서', '최적화 · 오리엔티어링'], ['시험하기', '일이 틀어지는 상황을 수천 번 흉내', '몬테카를로 · 대기행렬']].forEach(([h, b, m], i) => {
  const x = 0.6 + i * 3.15; card(s, x, 1.85, 2.9, 3.9); dot(s, i + 1, x + 0.3, 2.15, 0.6);
  tb(s, h, { x: x + 0.3, y: 2.95, w: 2.4, h: 0.5, fontSize: 22, bold: true, color: NAVY }); tb(s, b, { x: x + 0.3, y: 3.55, w: 2.4, h: 1.1, fontSize: 16 });
  tb(s, m, { x: x + 0.3, y: 4.85, w: 2.4, h: 0.7, fontSize: 13, color: CORAL, bold: true });
  if (i < 3) s.addShape(p.ShapeType.rightArrow, { x: x + 2.93, y: 3.6, w: 0.2, h: 0.35, fill: { color: SOFT }, line: { color: SOFT } }); });
tb(s, '모든 단계는 코드로 다시 돌려 볼 수 있다 (GitHub 저장소에 데이터·코드·검토 기록 공개)', { x: 0.6, y: 6.1, w: 12, h: 0.4, fontSize: 14, color: MUTE });

s = slide('① 모으기: 무료로, 누구나 구할 수 있는 데이터', '방법 ① 데이터',
  '데이터는 무료로, 누구나 구할 수 있는 것만 썼습니다. 배가 언제 몇 명을 태우고 오는지, 외국인이 어디에 돈을 쓰는지, 무엇을 먹고 싶어 하는지, 가게는 언제 여는지, 이동은 몇 분인지를 각각 공공데이터와 댓글로 모았습니다. 처음 검색으로 추정한 영업시간은 부산시 자료와 맞춰 보니 19곳 중 13곳이 달라 모두 바꿨습니다.');
[['648건', '크루즈 입출항 신고', '언제, 몇 명이 내리나'], ['6개 구 × 12개월', '외국인 카드 결제', '돈을 어디에 쓰나'], ['1,492개', '영·중·일 음식 영상 댓글', '무엇을 먹고 싶어 하나'],
 ['536곳', '부산시 맛집 정보', '가게는 언제 여나'], ['1,072개', '지도 경로', '걸어서·택시로 몇 분인가']].forEach(([big, h, q], i) => {
  const x = 0.6 + i * 2.5; card(s, x, 1.8, 2.3, 3.2);
  tb(s, big, { x: x + 0.2, y: 2.05, w: 1.95, h: 0.7, fontSize: i == 1 ? 18 : 26, bold: true, color: CORAL, valign: 'bottom' });
  tb(s, h, { x: x + 0.2, y: 2.95, w: 1.95, h: 0.9, fontSize: 15, bold: true, color: NAVY }); tb(s, q, { x: x + 0.2, y: 3.9, w: 1.95, h: 0.9, fontSize: 14, color: MUTE }); });
card(s, 0.6, 5.3, 12.1, 1.3, 'FDECE8');
tb(s, '추정 대신 실제 자료로', { x: 0.9, y: 5.48, w: 3, h: 0.4, fontSize: 15, bold: true, color: CORAL });
tb(s, '검색으로 추정했던 영업시간을 부산시 공식 자료와 맞춰 보니 19곳 중 13곳이 달랐다 → 모두 교체\n예: 원조18번완당 마감 22:00 → 19:30', { x: 0.9, y: 5.88, w: 11.5, h: 0.7, fontSize: 15 });
src(s, '출처: 공공데이터포털(15164568, 15063472), 한국관광데이터랩, YouTube Data API, OSRM 공개 경로 API');

s = slide('② 점수 매기기: 외국인이 많이 말한 음식일수록 높은 점수', '방법 ② 수요점수',
  '어디로 보낼지는 외국인이 실제로 한 말로 정했습니다. 댓글에서 해산물과 회가 86번으로 가장 많이 나왔고, 면과 시장 음식이 뒤를 이었습니다. 이 횟수를 50점에서 100점 사이 점수로 바꿨는데, 비례하게 하지 않았습니다. 86번 언급된 음식이 2번 언급된 음식보다 43배 맛있는 건 아니니까요. 산업수학에서는 이것을 한계효용 체감이라고 하고, 로그로 표현합니다. 많이 언급될수록 점수는 오르지만 오르는 폭은 점점 줄어듭니다.');
const MEN = [['해산물·회', 86], ['면(밀면·완당)', 39], ['시장 길거리', 38], ['고기(갈비)', 18], ['국밥', 18], ['치킨·카페', 10], ['어묵', 2]];
const sc = m => Math.round(50 + 50 * Math.log(1 + m) / Math.log(87));
s.addChart(p.ChartType.bar, [{ name: '댓글 언급 수', labels: MEN.map(x => x[0]), values: MEN.map(x => x[1]) }],
  { x: 0.5, y: 1.65, w: 5.6, h: 4.9, barDir: 'bar', catAxisOrientation: 'maxMin', chartColors: [NAVY], showValue: true, dataLabelPosition: 'outEnd',
    showTitle: true, title: '댓글에서 언급된 횟수', titleFontSize: 14, titleColor: INK, valAxisHidden: true, ...CH });
s.addChart(p.ChartType.bar, [{ name: '수요점수', labels: MEN.map(x => x[0]), values: MEN.map(x => sc(x[1])) }],
  { x: 6.0, y: 1.65, w: 3.2, h: 4.9, barDir: 'bar', catAxisOrientation: 'maxMin', catAxisHidden: true, chartColors: [CORAL], showValue: true, dataLabelPosition: 'outEnd',
    valAxisMinVal: 0, valAxisMaxVal: 120, showTitle: true, title: '점수(50~100)', titleFontSize: 14, titleColor: INK, valAxisHidden: true, ...CH });
mathCard(s, 9.45, 1.75, 3.3, 4.75, '86번이 2번보다 43배 좋은 건 아니다.\n\n많이 말할수록 점수는 오르지만, 오르는 폭은 줄어든다 = 한계효용 체감.\n\n점수 = 50 + 50 × log(1+언급) / log(87)');
src(s, '자료: 부산 음식 영상 영·중·일 댓글 1,492개. 영어권은 회·곰장어, 중국어권은 돼지국밥, 일본어권은 회를 많이 언급');

s = slide('③ 루트 짜기: 문제를 수학 한 줄로 옮기다', '방법 ③ 최적화 모델',
  '이제 이 점수로 루트를 짭니다. 목표는 한 줄입니다. 들른 곳의 점수를 모두 더하고, 줄 서고 이동한 시간만큼 빼서, 그 값이 가장 큰 루트를 찾는 것입니다. 대신 배 떠나기 30분 전 복귀를 비롯한 다섯 가지 규칙은 반드시 지킵니다. 여기서 0.8이라는 숫자가 중요합니다. 1분 기다리면 점수 0.8점을 잃는다는 뜻으로, 시간에 매긴 가격입니다.');
card(s, 0.6, 1.75, 7.6, 1.55, NAVY);
tb(s, '목표', { x: 0.9, y: 1.92, w: 2, h: 0.35, fontSize: 14, bold: true, color: 'F4A08F' });
tb(s, '(들른 곳 점수의 합) − 0.8 × (줄 선 시간 + 이동 시간)  을 가장 크게', { x: 0.9, y: 2.35, w: 7.1, h: 0.8, fontSize: 19, bold: true, color: WHITE });
tb(s, '반드시 지킬 규칙', { x: 0.6, y: 3.55, w: 4, h: 0.4, fontSize: 15, bold: true, color: CORAL });
[['배 떠나기 30분 전 복귀', '(계획엔 20분을 더 남긴다)'], ['가게 영업·쉬는 시간', '닫힌 가게엔 보내지 않는다'], ['시간대별 줄', '점심엔 줄이 길어진다'],
 ['배부름·식사 간격', '먹은 뒤 소화할 시간, 사이엔 볼거리'], ['가게가 받을 수 있는 인원', '한 시간에 보낼 수 있는 손님 수 제한']].forEach(([h, b], i) => {
  const y = 4.0 + i * 0.52; dot(s, i + 1, 0.6, y + 0.04, 0.38, NAVY);
  tb(s, h, { x: 1.15, y, w: 3.4, h: 0.45, fontSize: 16, bold: true, color: NAVY, valign: 'middle' }); tb(s, b, { x: 4.5, y, w: 3.7, h: 0.45, fontSize: 14, color: MUTE, valign: 'middle' }); });
mathCard(s, 8.55, 1.75, 4.2, 4.85, '0.8 = 시간의 가격.\n기다림 1분은 점수 0.8점의 손해다.\n\n그래서 80점짜리 한 곳을 더 가려고 100분 넘게 기다리는 건 손해 — 모델이 스스로 그 선을 판단한다.\n\n이런 문제를 “시간 제한이 있는 보물찾기(오리엔티어링) 최적화”라고 한다.');

s = slide('컴퓨터는 어떻게 답을 찾나: 가지치기와 바꿔 보기', '방법 ③ 푸는 법',
  '문제는 경우의 수입니다. 29곳 중 8곳을 골라 순서를 정하는 방법만 1,700억 가지가 넘습니다. 그래서 세 단계로 풉니다. 먼저 규칙을 어길 게 뻔한 길은 일찍 버리는 가지치기로 음식 루트를 찾고, 그 사이에 볼거리를 끼워 넣은 뒤, 한 곳을 넣고 빼고 바꿔 보며 더 좋은 루트를 찾습니다. 수업에서 배운 “가장 좋아 보이는 곳부터 고르기”와 비교하면 여섯 상황 모두에서 더 높은 점수가 나왔습니다.');
[['가지치기', '규칙을 어길 게 뻔한 길은 끝까지 가 보지 않고 일찍 버린다', '분기한정법'], ['끼워 넣기', '배부를 때쯤 걷기 좋은 볼거리를 사이에 넣는다', '삽입 휴리스틱'], ['바꿔 보기', '한 곳을 넣고·빼고·바꿔 보며 점수가 오르면 받아들인다', '지역탐색']].forEach(([h, b, m], i) => {
  const y = 1.75 + i * 1.55; dot(s, i + 1, 0.6, y + 0.1, 0.55);
  tb(s, h, { x: 1.35, y: y + 0.08, w: 2.2, h: 0.5, fontSize: 20, bold: true, color: NAVY }); tb(s, m, { x: 3.45, y: y + 0.14, w: 2.2, h: 0.4, fontSize: 13, bold: true, color: CORAL });
  tb(s, b, { x: 1.35, y: y + 0.62, w: 4.8, h: 0.8, fontSize: 15 }); });
const GAIN = [['북항 당일', 5.6], ['영도 짧은 기항', 10.3], ['하룻밤 정박', 12.8], ['부산 출발 전', 15.7], ['크루즈 없는 날', 3.3], ['대만 승객 많음', 2.7]];
s.addChart(p.ChartType.bar, [{ name: '점수 향상(%)', labels: GAIN.map(x => x[0]), values: GAIN.map(x => x[1]) }],
  { x: 6.5, y: 1.65, w: 6.3, h: 4.3, barDir: 'bar', catAxisOrientation: 'maxMin', chartColors: [CORAL], showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '"+"0.0"%"',
    showTitle: true, title: '“좋아 보이는 곳부터” 방식보다 점수가 얼마나 높나', titleFontSize: 14, titleColor: INK, valAxisHidden: true, ...CH });
tb(s, '29곳 중 8곳을 골라 순서를 정하는 방법 = 약 1,730억 가지 → 다 해 볼 수 없다', { x: 6.6, y: 6.1, w: 6.2, h: 0.5, fontSize: 14, bold: true, color: NAVY });

// ============ 결과와 시험 ============
sec('결과와 시험');
s = slide('결과: 북항 당일 기항 승객의 하루, 8시 30분 → 15시 48분', '결과 ① 대표 루트',
  '이렇게 찾은 대표 루트입니다. 8시 30분에 내려 시장이 열기 전 40계단을 먼저 보고, 국제시장과 깡통시장, 씨앗호떡을 걸어서 돈 뒤 자갈치 성일집에서 곰장어를 먹습니다. 배가 부를 때쯤 감천문화마을을 한 시간 걸으며 소화하고, 18번완당과 창고카페를 들러 15시 48분에 돌아옵니다. 배 떠나기 1시간 12분 전입니다. 국제시장과 깡통시장처럼 피란 시절 부산의 이야기가 담긴 곳도 함께 지납니다.');
s.addImage({ path: R + '04_그림/그림8_S1루트지도.png', x: 0.5, y: 1.6, w: 7.6, h: 7.6 * 952 / 2185, altText: '북항 당일 기항 최적 루트 지도' });
const TL = [['08:30', '하선'], ['08:40', '40계단 (볼거리)'], ['09:09', '국제시장 먹자골목'], ['09:56', '부평깡통시장'], ['11:00', 'BIFF광장 씨앗호떡'], ['11:35', '자갈치 성일집 · 곰장어'],
  ['12:46', '감천문화마을 (볼거리)'], ['14:12', '원조18번완당'], ['14:57', '봉래동 창고카페'], ['15:48', '복귀 (승선 마감 17:00)']];
TL.forEach(([t, k], i) => { const y = 1.6 + i * 0.42, last = i == 0 || i == TL.length - 1;
  tb(s, t, { x: 8.5, y, w: 0.9, h: 0.38, fontSize: 14, bold: true, color: last ? CORAL : NAVY, valign: 'middle' });
  tb(s, k, { x: 9.45, y, w: 3.4, h: 0.38, fontSize: 14, color: INK, valign: 'middle' }); });
card(s, 0.5, 5.1, 7.6, 1.55, 'FDECE8');
tb(s, '루트에 담긴 부산 이야기', { x: 0.8, y: 5.25, w: 4, h: 0.4, fontSize: 15, bold: true, color: CORAL });
tb(s, '국제시장 — 피란 시절 구호물자·군수품이 오가던 “도떼기시장”\n깡통시장 — 전쟁 후 미군 통조림이 거래되며 붙은 이름(전해지는 이야기)', { x: 0.8, y: 5.68, w: 7.1, h: 0.9, fontSize: 14 });
tb(s, '음식 6곳 + 볼거리 2곳', { x: 8.5, y: 6.0, w: 4.3, h: 0.5, fontSize: 18, bold: true, color: NAVY });
src(s, '지도 © OpenStreetMap contributors · 이야기 출처: 서울신문·주간경향 등(02_정제데이터/서사검증_1118_C.csv)');

s = slide('정말 배를 놓치지 않을까: 1,000번 흉내 내 보기', '시험 ① 핵심 질문',
  '가장 중요한 질문입니다. 정말 배를 놓치지 않을까요? 줄 서는 시간을 30%까지, 이동 시간을 20%까지 무작위로 바꿔 가며 같은 루트를 1,000번 돌려 봤습니다. 배를 놓친 경우는 0번이었고, 운이 가장 나쁜 5%의 날에도 24분 넘게 남았습니다. 사실 처음에는 실패했습니다. 점수만 높이게 했더니 일정을 꽉 채워서 61%가 지각했습니다. 그래서 계획할 때 20분을 보험처럼 남기게 했습니다.');
stat(s, 0.6, 1.8, 3.0, '0번', '1,000번 중 배를 놓친 횟수', CORAL);
stat(s, 3.8, 1.8, 3.0, '97%', '모든 규칙을 지킨 비율');
stat(s, 7.0, 1.8, 3.0, '24.6분', '운이 가장 나쁜 5%의 날에도\n남는 시간');
card(s, 0.6, 3.9, 6.9, 2.7);
tb(s, '어떻게 시험했나', { x: 0.9, y: 4.1, w: 4, h: 0.4, fontSize: 15, bold: true, color: CORAL });
tb(s, '줄 서는 시간 ±30%, 이동 시간 ±20%를 주사위처럼 무작위로 바꿔 같은 루트를 1,000번 돌렸다.\n\n처음엔 점수만 높이다 일정을 꽉 채워 61%가 지각 → 계획에 20분 여유를 의무로 넣었다.', { x: 0.9, y: 4.55, w: 6.4, h: 1.9, fontSize: 15 });
mathCard(s, 7.8, 3.9, 4.95, 2.7, '몬테카를로 시뮬레이션: 불확실한 값을 무작위로 뽑아 수천 번 돌려 위험을 확률로 잰다.\n20분 여유 = 보험료. 점수 조금을 내고 지각 61% → 0%.');

s = slide('“인기 있는 곳부터” 가면? 기다리다 하루가 끝난다', '시험 ② 인기순 경로와 비교',
  '교수님께서 인기 있는 곳부터 차례로 가면 어떻게 되는지 비교해 보라고 하셨습니다. 결과는 분명했습니다. 인기순으로 가면 문이 열리길 기다리고, 줄을 서고, 배가 꺼지길 기다리느라 북항 당일 기준 3시간 넘게 서 있고 네 곳밖에 못 갑니다. 저희 루트는 순서만 바꿔서 기다림을 56분으로 줄이고 여덟 곳을 갑니다.');
const POPL = ['북항 당일', '영도 짧은 기항', '하룻밤 정박', '부산 출발 전', '크루즈 없는 날', '대만 승객 많음'];
s.addChart(p.ChartType.bar, [{ name: '인기순', labels: POPL, values: [195, 20, 249, 105, 196, 231] }, { name: '우리 루트', labels: POPL, values: [56, 11, 48, 25, 39, 52] }],
  { x: 0.5, y: 1.65, w: 8.2, h: 4.9, barDir: 'col', barGrouping: 'clustered', chartColors: ['C9D6E0', CORAL], showValue: true, dataLabelPosition: 'outEnd', dataLabelFontSize: 11,
    showTitle: true, title: '하루 동안 기다린 시간(분): 줄 + 문 열기·소화 기다림', titleFontSize: 14, titleColor: INK, valAxisHidden: true, ...CH, showLegend: true, legendPos: 't', legendFontSize: 13 });
stat(s, 9.1, 1.9, 3.7, '8곳 vs 4곳', '북항 당일, 들른 곳(우리 vs 인기순)', CORAL);
stat(s, 9.1, 3.75, 3.7, '56분 vs 195분', '하루 동안 기다린 시간');
tb(s, '같은 가게, 같은 규칙.\n순서만 바꿨다.', { x: 9.1, y: 5.6, w: 3.7, h: 0.9, fontSize: 16, bold: true, color: NAVY });

s = slide('일이 틀어지면: 늦게 내려도, 단체가 몰려도 B안이 있다', '시험 ③ 최악의 상황',
  '최악의 상황도 시험했습니다. 하선이 20분 늦어지는 경우와, 점심에 200명 단체가 모든 식당에 몰리는 경우입니다. 여섯 상황 중 몇 곳은 원래 루트로는 규칙을 지키지 못했지만, 한 곳만 빼면 모두 제시간에 돌아왔습니다. 서비스는 이 B안을 미리 계산해 두고, 늦게 내리면 “40계단은 빼고 가세요”처럼 알려 줍니다.');
const ST = [['북항 당일', '× → 40계단 빼면 OK', 'OK'], ['영도 짧은 기항', 'OK', 'OK'], ['하룻밤 정박', 'OK', 'OK'], ['부산 출발 전', '× → 부산타워 빼면 OK', 'OK'],
  ['크루즈 없는 날', '× → 40계단 빼면 OK', '× → 삼진어묵 빼면 OK'], ['대만 승객 많은 날', 'OK', '× → 40계단 빼면 OK']];
const hd = t => ({ text: t, options: { bold: true, color: WHITE, fill: { color: NAVY } } });
const cell = t => ({ text: t, options: { color: t == 'OK' ? NAVY : CORAL, bold: t != 'OK' } });
s.addTable([[hd('상황'), hd('하선 20분 지연'), hd('점심 단체 200명')], ...ST.map(r => [r[0], cell(r[1]), cell(r[2])])],
  { x: 0.6, y: 1.75, w: 8.0, colW: [2.4, 2.8, 2.8], rowH: 0.55, fontFace: FONT, fontSize: 15, color: INK, border: { type: 'solid', color: LINE, pt: 0.75 }, valign: 'middle', margin: 0.08 });
mathCard(s, 9.0, 1.75, 3.75, 4.1, '스트레스 테스트: 가정을 일부러 나쁘게 바꿔 계획이 버티는지 본다.\n\n서비스의 154개 상황 중 88개에 “늦으면 이곳을 빼라” B안을 미리 계산해 두었다.');
src(s, 'OK = 승선 30분 전까지 복귀하고 모든 규칙을 지킴 · × = 원래 루트로는 규칙 위반');

s = slide('줄의 수학: 손님이 조금만 늘어도 줄은 폭발한다', '시험 ④ 대기행렬',
  '여기서 수업에서 배운 대기행렬 이론을 썼습니다. 줄은 손님 수에 비례해 늘지 않습니다. 가게가 절반쯤 찼을 땐 5분이지만, 95%가 차면 한 시간 반을 기다립니다. 마지막 몇 명이 줄을 폭발시키는 겁니다. 그래서 모든 승객에게 같은 1등 가게를 추천하면, 바로 그 가게가 가장 먼저 무너집니다. 추천을 나눠야 하는 수학적 이유입니다.');
const RHO = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95];
s.addChart(p.ChartType.line, [{ name: '평균 대기(분)', labels: RHO.map(r => Math.round(r * 100) + '%'), values: RHO.map(r => Math.round(5 * r / (1 - r))) }],
  { x: 0.5, y: 1.65, w: 7.6, h: 4.9, chartColors: [CORAL], lineSize: 3, lineDataSymbol: 'circle', lineDataSymbolSize: 9, showValue: true, dataLabelPosition: 't', dataLabelFormatCode: '0"분"',
    showTitle: true, title: '가게가 찬 정도(가동률)별 평균 대기 — 1명 처리에 5분 걸리는 가게', titleFontSize: 13, titleColor: INK, valAxisHidden: true, ...CH });
mathCard(s, 8.5, 1.75, 4.25, 4.8, '대기행렬 이론(M/M/c): 손님이 오는 속도와 처리하는 속도로 줄 길이를 계산한다.\n\n기다림 ∝ ρ / (1 − ρ)\n가동률 ρ가 1에 가까우면 분모가 0에 가까워져 줄이 폭발한다.\n\n→ 1등 가게 하나만 추천하면 안 된다.');
src(s, '그래프는 창구 1개(M/M/1)·처리 5분 가정의 계산 예시. 모델에서는 가게별 창구·테이블 수 c를 넣은 Erlang C 공식을 썼다');

s = slide('그래서 나눠 보낸다: 같은 날, 추천 방식만 바꿔 비교', '시험 ⑤ 분산과 A/B 모의실험',
  '그래서 나눠 보냅니다. 같은 배 여섯 그룹을 한 루트로 보내면 평균 97분에서 124분을 줄 서고 모두 배를 놓치지만, 그룹마다 다른 루트를 주면 55분으로 줄고 지각은 없습니다. 정말 추천 덕분인지는 컴퓨터 속 가상 승객으로 확인했습니다. 앱을 실제로 배포한 것은 아니고, 같은 승객과 같은 날을 놓고 추천 방식만 바꿔 400번 모의실험했습니다. 앱 때문에 늘어난 줄이 순위만 보여 주면 245분, 나눠 추천하면 34분이었습니다. 실제 효과는 입항일을 나눠 현장 A/B로 확인하겠습니다.');
card(s, 0.6, 1.75, 4.6, 4.8);
tb(s, '같은 배, 6그룹(30명씩)', { x: 0.9, y: 1.95, w: 4, h: 0.4, fontSize: 15, bold: true, color: CORAL });
stat(s, 0.9, 2.45, 4.0, '97~124분', '모두 같은 루트 → 평균 줄,\n6그룹 모두 규칙 위반', MUTE);
stat(s, 0.9, 4.35, 4.0, '55분', '그룹마다 다른 루트 → 위반 0그룹', CORAL);
s.addChart(p.ChartType.bar, [{ name: '앱 때문에 늘어난 대기(분)', labels: ['앱 없음', '순위만 표시', '루트 나열', '나눠서 추천'], values: [471, 245, 60, 34] }],
  { x: 5.5, y: 1.65, w: 7.3, h: 4.2, barDir: 'col', chartColors: ['C9D6E0', 'C9D6E0', 'C9D6E0', CORAL], showValue: true, dataLabelPosition: 'outEnd', dataLabelFormatCode: '0"분"',
    showTitle: true, title: 'A/B 모의실험 400회(가상 승객 60명): 추천 방식별 늘어난 대기', titleFontSize: 14, titleColor: INK, valAxisHidden: true, ...CH });
tb(s, '실제 배포 전이라 컴퓨터 속 가상 승객으로 실험했다 → 다음 단계: 입항일을 무작위로 나눠 현장 A/B', { x: 5.6, y: 5.95, w: 7.1, h: 0.7, fontSize: 14, bold: true, color: NAVY });
src(s, '가정값: 좌석·창구 수, 점심 가동률, 앱 이용 60명, 순위별 선택 확률(1위일수록 높게) → 숫자보다 방식 간 차이를 본다');


// ============ 현장으로 ============
sec('현장으로');
s = slide('데이터로 확인한 것, 아직 모르는 것', '검증과 한계',
  '저희가 확인한 것과 아직 모르는 것을 구분하겠습니다. 원도심 외국인 음식 소비는 비교 지역보다 빨리 늘었고, 배가 많이 온 달엔 부산 전체가 함께 늘었습니다. 하지만 이것이 크루즈 때문인지는 말할 수 없습니다. 원도심만 더 늘었는지와 입항 횟수의 상관은 거의 0이었습니다. 월 단위 자료로는 크루즈 효과와 관광 성수기를 떼어 낼 수 없습니다. 그래서 직접 가서 재기로 했습니다.');
s.addChart(p.ChartType.line, [{ name: '원도심 3구', labels: ['25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05', '26.06', '26.07'], values: [100, 97.3, 84.4, 66.4, 75.2, 120.1, 148.5, 168.4, 159.6, 176] },
  { name: '비교 3구', labels: ['25.10', '25.11', '25.12', '26.01', '26.02', '26.03', '26.04', '26.05', '26.06', '26.07'], values: [100, 100.6, 81.1, 55.3, 63.4, 105.4, 139.6, 157.2, 156.3, 156.9] }],
  { x: 0.5, y: 1.65, w: 6.6, h: 4.6, chartColors: [CORAL, '9FB0BF'], lineSize: 3, lineDataSymbol: 'circle', lineDataSymbolSize: 6,
    showTitle: true, title: '외국인 음식 소비 지수 (2025.10 = 100)', titleFontSize: 14, titleColor: INK, ...CH, showLegend: true, legendPos: 't', legendFontSize: 13 });
card(s, 7.4, 1.75, 5.35, 2.15);
tb(s, '확인한 것', { x: 7.7, y: 1.92, w: 4, h: 0.4, fontSize: 15, bold: true, color: NAVY });
tb(s, '원도심 음식 소비가 비교 지역보다 빨리 늘었다(176 vs 157)\n입항이 많은 달엔 부산 6개 구 모두 늘었다(상관 0.61~0.79)', { x: 7.7, y: 2.35, w: 4.9, h: 1.4, fontSize: 14 });
card(s, 7.4, 4.1, 5.35, 2.5, 'FDECE8');
tb(s, '아직 모르는 것', { x: 7.7, y: 4.27, w: 4, h: 0.4, fontSize: 15, bold: true, color: CORAL });
tb(s, '크루즈 “때문”인가? 원도심만 더 늘었는지와 입항 횟수의 상관 0.02\n→ 월 단위로는 성수기 효과와 못 떼어 낸다\n→ 입항일·비입항일을 현장에서 직접 비교한다', { x: 7.7, y: 4.7, w: 4.9, h: 1.8, fontSize: 14 });
src(s, '사회과학적 검증: 대조군(비교 3구·제주)과 상관분석. 상관은 인과가 아니므로 연관으로만 해석');

s = slide('현장 관측: 가정을 실제 숫자로 바꾼다', '실행 ① 다음 단계',
  '지금 모델에서 줄 서는 시간과 좌석 수는 추정입니다. 그래서 추천에 가장 많이 나오는 다섯 곳에 직접 가서 잽니다. 손님이 도착한 시각, 음식을 받은 시각, 떠난 시각, 열린 창구 수를 적고, 크루즈가 들어온 날과 안 들어온 날을 하루씩 비교합니다. 기록을 넣으면 앞에서 본 대기행렬 모델과 루트 계산에 바로 들어가도록 코드를 만들어 두었습니다.');
s.addTable([[hd('가게'), hd('추천 루트 등장')], ['국제시장 먹자골목', '154개 중 151'], ['BIFF광장 씨앗호떡', '150'], ['부평깡통시장', '133'], ['원조18번완당', '97'], ['성일집(자갈치)', '49']],
  { x: 0.6, y: 1.75, w: 5.2, colW: [3.0, 2.2], rowH: 0.55, fontFace: FONT, fontSize: 15, color: INK, border: { type: 'solid', color: LINE, pt: 0.75 }, valign: 'middle', margin: 0.08 });
[['무엇을 적나', '도착·주문·음식 받은·떠난 시각, 열린 창구 수, 크루즈 손님 여부'], ['언제', '같은 요일의 크루즈 입항일 1일 + 비입항일 1일 (부산항 크루즈 일정 API로 선정)'],
 ['그다음', '도착 속도·처리 속도·창구 수 → 대기행렬 모델 → 루트 계산에 바로 반영']].forEach(([h, b], i) => {
  const y = 1.75 + i * 1.6; card(s, 6.2, y, 6.55, 1.4); dot(s, i + 1, 6.45, y + 0.25, 0.48);
  tb(s, h, { x: 7.15, y: y + 0.27, w: 5.3, h: 0.4, fontSize: 17, bold: true, color: NAVY }); tb(s, b, { x: 7.15, y: y + 0.72, w: 5.4, h: 0.6, fontSize: 14 }); });
src(s, '관측 계획·기록지: 05_문서/현장관측_계획.md, 현장관측_기록지.csv');

s = slide('실제로 쓸 수 있는 서비스', '실행 ② Busan Bite Pass',
  '그리고 이 모든 계산은 실제로 쓸 수 있는 서비스가 되었습니다. 터미널과 내리는 시각, 배 떠나는 시각을 고르면 미리 풀어 둔 154가지 상황 중 맞는 루트를 시간표와 지도로 보여 줍니다. 다섯 개 언어를 지원하고 상인용 수요 예보 화면도 있습니다. 휴대폰으로 지금 바로 열어 보실 수 있습니다.');
s.addImage({ path: R + '04_그림/그림10_서비스화면.png', x: 0.6, y: 1.6, w: 5.1 * 1280 / 1150, h: 5.1, altText: 'Busan Bite Pass 서비스 화면' });
[['내 루트', '터미널·하선·승선 시각 → 시간표, 지도, 이동 수단, 줄, 가격, 복귀 알림'], ['5개 언어', '한국어 · English · 日本語 · 简体 · 繁體'], ['154개 상황 미리 계산', '하선 08:00~13:00 × 머무는 시간 3~9시간 × 터미널 2곳'], ['상인 수요 예보', '시간대별 예상 크루즈 손님 수']].forEach(([h, b], i) => {
  const y = 1.7 + i * 1.12; tb(s, h, { x: 7.0, y, w: 5.8, h: 0.4, fontSize: 17, bold: true, color: NAVY }); tb(s, b, { x: 7.0, y: y + 0.42, w: 5.8, h: 0.55, fontSize: 14, color: MUTE }); });
tb(s, 'ddayoung03.github.io/busan-bite-pass', { x: 7.0, y: 6.3, w: 5.8, h: 0.4, fontSize: 16, bold: true, color: CORAL });

s = slide('누가 함께하나: 지역·산업·학교가 각자 할 일', '실행 ③ 지산학 연계',
  '실행은 세 주체가 함께합니다. 부산항만공사는 하선 안내문에 QR을 넣어 주면 되고, 상인회와 전통시장은 영업 정보를 주는 대신 손님 예보를 받습니다. 저희 학교 팀은 현장에서 줄을 재고 모델을 고칩니다. 그리고 같은 방법을 해운대 같은 부산 전역, KTX 당일 여행객에게도 넓힐 수 있습니다.');
[['지역', '부산항만공사', '하선 안내문에 QR 한 장'], ['산업', '상인회 · 전통시장', '영업 정보를 주고 손님 예보를 받는다'], ['학교', '우리 팀', '현장 관측으로 모델을 계속 고친다']].forEach(([k, h, b], i) => {
  const x = 0.6 + i * 4.1; card(s, x, 1.75, 3.85, 2.4);
  tb(s, k, { x: x + 0.3, y: 1.95, w: 3, h: 0.4, fontSize: 15, bold: true, color: CORAL }); tb(s, h, { x: x + 0.3, y: 2.4, w: 3.3, h: 0.55, fontSize: 20, bold: true, color: NAVY });
  tb(s, b, { x: x + 0.3, y: 3.1, w: 3.3, h: 0.9, fontSize: 15 }); });
tb(s, '넓히는 순서', { x: 0.6, y: 4.5, w: 4, h: 0.4, fontSize: 15, bold: true, color: CORAL });
[['원도심 안에서 나누기', '한 가게에 몰리지 않게'], ['부산 전역으로', '하룻밤 정박 배 → 서면·동래·해운대'], ['다른 방문객에게', 'KTX 당일 여행객·공연 관객']].forEach(([h, b], i) => {
  const x = 0.6 + i * 4.1; dot(s, i + 1, x, 5.0, 0.48, NAVY);
  tb(s, h, { x: x + 0.65, y: 5.0, w: 3.3, h: 0.45, fontSize: 17, bold: true, color: NAVY, valign: 'middle' }); tb(s, b, { x: x + 0.65, y: 5.5, w: 3.3, h: 0.5, fontSize: 14, color: MUTE }); });
src(s, '효과 측정: 입항일 외국인 음식 결제 중 원도심(터미널 3km) 밖 비중, 도입 전후 대조군과 비교');

// ============ 정리 ============
sec('정리');
s = slide('산업수학으로 다시 보기: 현실의 질문을 수학으로', '정리',
  '정리하겠습니다. 저희는 현실의 질문 다섯 개를 수학으로 옮겼습니다. 무엇을 먹고 싶어 하는지는 한계효용을 담은 점수로, 어떤 순서로 갈지는 최적화로, 정말 안전한지는 몬테카를로로, 줄이 왜 폭발하는지는 대기행렬로, 추천이 효과가 있는지는 A/B 모의실험으로 답했습니다. 수학은 어려운 계산이 아니라, 현실의 결정을 근거 있게 만드는 도구였습니다.');
const SUM = [['외국인은 무엇을 먹고 싶나?', '로그 점수(한계효용 체감)', '해산물·회가 1위, 많이 말할수록 점수는 덜 오른다'],
  ['어떤 순서로 돌아야 하나?', '시간 제한 최적화', '좋아 보이는 곳부터보다 점수 3~16% 높다'], ['정말 배를 안 놓치나?', '몬테카를로 1,000회', '지각 0번, 20분 여유가 보험'],
  ['줄은 왜 폭발하나?', '대기행렬 ρ/(1−ρ)', '1등 가게 하나만 추천하면 안 된다'], ['우리 추천 덕분인가?', 'A/B 모의실험 400회', '늘어난 대기 245분 → 34분(가상)']];
s.addTable([[hd('현실의 질문'), hd('쓴 수학'), hd('알게 된 것')], ...SUM.map(r => [{ text: r[0], options: { bold: true, color: NAVY } }, { text: r[1], options: { color: CORAL, bold: true } }, r[2]])],
  { x: 0.6, y: 1.7, w: 12.1, colW: [3.6, 3.5, 5.0], rowH: 0.66, fontFace: FONT, fontSize: 15, color: INK, border: { type: 'solid', color: LINE, pt: 0.75 }, valign: 'middle', margin: 0.1 });

s = p.addSlide({ masterName: 'COVER', sectionTitle: SEC });
s.addText('배에서 내린 8시간을\n부산의 맛으로', { placeholder: 'title' });
tb(s, '승객은 배를 놓치지 않고 더 먹고, 소비는 면세점 밖 부산 가게로', { x: 0.8, y: 4.3, w: 11.5, h: 0.5, fontSize: 20, color: 'C9DCEB' });
s.addImage({ path: R + '05_문서/QR/QR_BusanBitePass.png', x: 10.6, y: 5.1, w: 1.7, h: 1.7, altText: '서비스 QR 코드' });
tb(s, '감사합니다 · 크루즈 미식 루트 팀 · ddayoung03.github.io/busan-bite-pass', { x: 0.8, y: 6.5, w: 9.5, h: 0.4, fontSize: 13, color: SOFT });
n = '배에서 내린 8시간을 부산의 맛으로 채우는 것, 그것이 저희 제안입니다. 승객은 배를 놓치지 않고 더 먹고, 소비는 면세점 밖 부산 가게로 갑니다. 감사합니다.';
s.addNotes(n); NOTES.push(['마무리', n]);

// ============ 저장 + 대본 ============
const total = NOTES.reduce((a, x) => a + x[1].length, 0);
const md = ['# 최종 발표대본', '', `총 ${NOTES.length}장 · ${total.toLocaleString()}자 (분당 약 300자 기준 약 ${(total / 300).toFixed(1)}분) · 슬라이드 노트와 같은 내용`, ''];
NOTES.forEach(([t, x], i) => md.push(`## ${i + 1}. ${t}`, '', x, ''));
fs.writeFileSync(R + '05_문서/최종발표대본.md', md.join('\n'));
// 배포용 Word 대본(같은 노트)
const D = require('docx');
const run = (text, o = {}) => new D.TextRun({ text, font: FONT, ...o });
const doc = new D.Document({
  styles: { default: { document: { run: { font: FONT, size: 22 } },
    heading1: { run: { font: FONT, size: 36, bold: true, color: NAVY }, paragraph: { spacing: { before: 0, after: 120 }, keepNext: true } },
    heading2: { run: { font: FONT, size: 24, bold: true, color: NAVY }, paragraph: { spacing: { before: 280, after: 80 }, keepNext: true } } } },
  sections: [{ properties: { page: { margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new D.Footer({ children: [new D.Paragraph({ alignment: D.AlignmentType.CENTER, children: [new D.TextRun({ children: [D.PageNumber.CURRENT], font: FONT, size: 18, color: MUTE })] })] }) },
    children: [
      new D.Paragraph({ heading: D.HeadingLevel.HEADING_1, children: [run('최종 발표대본 — 배에서 내린 8시간, 부산을 맛보게 하는 법')] }),
      new D.Paragraph({ spacing: { after: 240 }, children: [run(`크루즈 미식 루트 팀 · 총 ${NOTES.length}장 · 약 ${(total / 300).toFixed(0)}분 발표 + 질의응답 5분 · 발표자료(최종발표자료.pptx) 슬라이드 노트와 같은 내용`, { size: 20, color: MUTE })] }),
      ...NOTES.flatMap(([t, x], i) => [
        new D.Paragraph({ heading: D.HeadingLevel.HEADING_2, children: [run(`${i + 1}. ${t}`)] }),
        new D.Paragraph({ spacing: { after: 80, line: 340 }, children: [run(x)] }),
      ]),
    ] }],
});
const DOCX_OUT = OUT.replace(/최종발표자료\.pptx$/, '최종발표대본.docx').replace(/\.pptx$/, '_대본.docx');
D.Packer.toBuffer(doc).then(b => { fs.writeFileSync(DOCX_OUT, b); console.log('docx ok'); });
// pptxgenjs는 글자를 en-US로 표시해 PowerPoint가 한글 단어 중간에서 줄을 바꾼다 → ko-KR로 바꾸고, ZIP의 폴더 항목은 뺀다
const JSZip = require('jszip');
p.write({ outputType: 'nodebuffer' }).then(JSZip.loadAsync).then(async z => {
  const out = new JSZip();
  for (const [name, f] of Object.entries(z.files)) {
    if (f.dir) continue;
    let d = await f.async('nodebuffer');
    if (/^ppt\/(slides|notesSlides|slideLayouts|slideMasters)\/[^/]+\.xml$/.test(name)) d = Buffer.from(d.toString('utf8').replace(/lang="en-US"/g, 'lang="ko-KR" altLang="en-US"'));
    out.file(name, d, { createFolders: false });
  }
  fs.writeFileSync(OUT, await out.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }));
  console.log('deck ok', NOTES.length, 'slides', total, 'chars');
});
