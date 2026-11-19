// 3주차 발표자료 생성: node deck.js  (pptxgenjs 필요). 수치는 02_정제데이터 CSV에서 읽는다.
// 흐름: 무엇을 만드나 → ①문제 → ②원인 → ③데이터·모델 → ④결과(루트) → ⑤효과·실행
const fs=require('fs');const PPTX=require('pptxgenjs');
const R='C:/Users/PTY/Desktop/지산학아이디어톤/';
const split=l=>{const c=[];let cur='',q=false;for(const ch of l){if(ch=='"')q=!q;else if(ch==','&&!q){c.push(cur);cur=''}else cur+=ch}c.push(cur);return c};
const csv=f=>{const L=fs.readFileSync(R+'02_정제데이터/'+f,'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/);const H=split(L[0]);
  return L.slice(1).map(l=>{const c=[];let cur='',q=false;for(const ch of l){if(ch=='"')q=!q;else if(ch==','&&!q){c.push(cur);cur=''}else cur+=ch}c.push(cur);return Object.fromEntries(H.map((h,i)=>[h,c[i]]))})};
const short=s=>s.replace(/\(.*?\)/g,'').trim();
const RT=csv('루트결과_1118_B.csv');const top=s=>RT.find(r=>r['시나리오'].startsWith(s)&&r['순위']=='1');const gr=s=>RT.find(r=>r['시나리오'].startsWith(s)&&r['순위'].startsWith('탐욕'));
const N1=csv('제약무시계획_1118_B.csv')[0];const nvViol=Object.keys(N1).filter(k=>k.startsWith('위반:')).reduce((a,k)=>a+(+N1[k]),0);
const VD=Object.fromEntries(csv('검증_1118_B.csv').map(r=>[r['지표'],+r['값']]));const vk=k=>VD[Object.keys(VD).find(x=>x.startsWith(k))];
const DF=csv('분산효과_1118_B.csv');
const DISP_NEW=fs.statSync(R+'02_정제데이터/분산효과_1118_B.csv').mtimeMs>fs.statSync(R+'02_정제데이터/food_nodes_1118_B.csv').mtimeMs;const TT=csv('루트시간표_1118_B.csv');
const S1=top('S1'),G1=gr('S1');
const late=(vk('고정 루트 복귀 지각')*100).toFixed(1),ok=(vk('고정 루트 전체 규칙')*100).toFixed(1),p5=vk('고정 루트 복귀 여유 하위');
const gain=((S1['목적함수']/G1['목적함수']-1)*100).toFixed(1);

// ---------- 테마: 항구의 밤(네이비) + 바다(청록) + 음식(코랄) ----------
const NAVY='0B3C5D',SEA='328CC1',CORAL='E8573F',ICE='EAF2F8',INK='1D2B36',MUTE='5B6B78',WHITE='FFFFFF';
const FONT='Malgun Gothic';
const p=new PPTX();p.layout='LAYOUT_WIDE';p.title='크루즈 승객의 부산 패싱 끊기';
p.theme={headFontFace:FONT,bodyFontFace:FONT};
p.defineSlideMaster({title:'DARK',background:{color:NAVY},objects:[
 {placeholder:{options:{name:'title',type:'title',x:0.8,y:2.0,w:11.7,h:2.2,fontFace:FONT,fontSize:40,bold:true,color:WHITE,valign:'top',align:'left'},text:''}}]});
p.defineSlideMaster({title:'SECTION',background:{color:NAVY},objects:[
 {placeholder:{options:{name:'title',type:'title',x:2.3,y:2.9,w:10.2,h:1.2,fontFace:FONT,fontSize:36,bold:true,color:WHITE,valign:'middle',align:'left'},text:''}}],
 slideNumber:{x:12.4,y:7.0,w:0.6,h:0.3,fontFace:FONT,fontSize:10,color:'9FB8CC'}});
p.defineSlideMaster({title:'CONTENT',background:{color:WHITE},objects:[
 {placeholder:{options:{name:'title',type:'title',x:0.6,y:0.55,w:12.1,h:0.85,fontFace:FONT,fontSize:28,bold:true,color:NAVY,valign:'middle',align:'left'},text:''}}],
 slideNumber:{x:12.4,y:7.0,w:0.6,h:0.3,fontFace:FONT,fontSize:10,color:MUTE}});

const tb=(s,text,o)=>s.addText(text,{isTextBox:true,fontFace:FONT,color:INK,fontSize:15,valign:'top',margin:0,...o});
const dot=(s,n,x,y,d=0.55,fill=NAVY)=>{s.addShape(p.ShapeType.ellipse,{x,y,w:d,h:d,fill:{color:fill},line:{color:WHITE,width:1.5}});
 tb(s,String(n),{x,y,w:d,h:d,align:'center',valign:'middle',color:WHITE,bold:true,fontSize:d>0.7?24:14});};
const card=(s,x,y,w,h,fill=ICE)=>s.addShape(p.ShapeType.roundRect,{x,y,w,h,fill:{color:fill},line:{color:fill},rectRadius:0.08});
const th=t=>({text:t,options:{bold:true,color:WHITE,fill:{color:NAVY}}});
const T=(s,rows,o)=>s.addTable(rows,{fontFace:FONT,fontSize:13,color:INK,border:{type:'solid',color:'C9D6E0',pt:0.75},valign:'middle',margin:0.06,...o});
let SEC='';
const slide=(title,kicker,master='CONTENT')=>{const s=p.addSlide({masterName:master,sectionTitle:SEC});s.addText(title,{placeholder:'title'});
 if(kicker)tb(s,kicker,{x:0.6,y:0.22,w:12,h:0.35,fontSize:13,bold:true,color:CORAL});return s;};
const section=(n,title,sub)=>{SEC=title;p.addSection({title});const s=p.addSlide({masterName:'SECTION',sectionTitle:SEC});
 dot(s,n,0.8,2.95,1.1,CORAL);s.addText(title,{placeholder:'title'});tb(s,sub,{x:2.3,y:4.1,w:10,h:0.8,fontSize:18,color:'C9DCEB'});return s;};
const stat=(s,x,y,w,big,lab,color=NAVY)=>{tb(s,big,{x,y,w,h:0.95,fontSize:44,bold:true,color});tb(s,lab,{x,y:y+0.95,w,h:0.8,fontSize:14,color:MUTE});};

// ===== 0. 표지 =====
SEC='표지';p.addSection({title:SEC});
let s=p.addSlide({masterName:'DARK',sectionTitle:SEC});
s.addText('면세점에서 멈추지 않게\n크루즈 승객의 부산 패싱 끊기',{placeholder:'title'});
tb(s,'하선 시간 안에, 배를 놓치지 않고, 외국인이 원하는 부산 음식으로',{x:0.8,y:4.3,w:11.5,h:0.5,fontSize:20,color:'C9DCEB'});
tb(s,'크루즈 미식 루트 팀 · 2026 지산학 아이디어톤 「부산의 맛, 로컬에서 글로컬」 3주차',{x:0.8,y:6.5,w:11.5,h:0.4,fontSize:13,color:'9FB8CC'});
s.addNotes('크루즈 승객이 부산에 내려도 면세점만 들르고 배로 돌아가는 “부산 패싱”을, 데이터와 최적화로 끊어 보겠다는 발표입니다.');

// ===== 1. 우리가 만든 것 (한 장 요약) =====
SEC='요약';p.addSection({title:SEC});
s=slide('우리가 만든 것: 배를 놓치지 않는 “부산 한 끼” 루트 추천','한 장 요약');
const flow=[['하선','QR로 배 이름만 입력\n→ 하선·승선 시각 자동'],['루트 추천','외국인이 원하는 음식 +\n영업·줄·이동을 계산'],['시간표','몇 시에 어디서\n줄 서고 먹는지'],['복귀 알림','승선 2시간 전\n남은 일정 조정']];
flow.forEach(([a,b],i)=>{const x=0.6+i*3.1;card(s,x,1.75,2.8,2.3);dot(s,i+1,x+0.2,1.95);tb(s,a,{x:x+0.9,y:2.0,w:1.8,h:0.5,fontSize:19,bold:true,color:NAVY});
 tb(s,b,{x:x+0.2,y:2.75,w:2.45,h:1.2,fontSize:14,color:INK});if(i<3)tb(s,'→',{x:x+2.8,y:2.6,w:0.3,h:0.5,fontSize:22,bold:true,color:CORAL,align:'center'});});
stat(s,0.6,4.55,3.9,'403,188명','2026년 1~7월 크루즈 승객\n전년 대비 +175.7%');
stat(s,4.75,4.55,3.9,'약 66%','중구 외국인 카드소비 중 쇼핑\n(면세점 포함) — 식음료는 19~23%',CORAL);
stat(s,8.9,4.55,3.9,`지각 ${late}%`,`최적 루트 1,000회 모의\n규칙 준수 ${ok}%`,SEA);
s.addNotes(`우리가 만든 것은 크루즈 승객용 루트 추천입니다. 배 이름만 넣으면 하선·승선 시각이 정해지고, 외국인이 실제로 원하는 음식과 가게 영업시간, 줄, 이동시간을 함께 계산해 시간표를 줍니다. 승객은 1년 새 거의 3배로 늘었는데 소비의 약 66%가 쇼핑에 머뭅니다. 우리 루트는 무작위 1,000번 흔들어도 지각 확률이 ${late}%입니다.`);

// ===== 목차 =====
s=slide('발표 순서','목차');
const parts=[['문제','승객은 늘었는데 소비는 면세점에서 멈춘다'],['원인','왜 가게까지 못 가나 — 4가지'],['데이터 수집과 처리','원데이터 6종을 어떻게 모으고 다듬었나'],['분석','퍼널, 원도심 비교, 외국인 수요'],['모델과 검토','시간창 최적화(OPTW)와 세 번의 검토'],['결과','6개 시나리오의 실제 루트와 검증'],['효과와 실행','무엇이 해결되고, 누가 실행하나']];
parts.forEach(([a,b],i)=>{const y=1.6+i*0.72;dot(s,i+1,0.9,y,0.5);tb(s,a,{x:1.65,y:y+0.06,w:3.6,h:0.45,fontSize:18,bold:true,color:NAVY});tb(s,b,{x:5.3,y:y+0.08,w:7.4,h:0.45,fontSize:15,color:MUTE});});
s.addNotes('문제와 원인, 데이터를 모으고 다듬은 과정, 분석, 모델과 검토, 결과, 효과와 실행 순서로 말씀드리겠습니다.');

// ===== 진행 과정 =====
s=slide('어떻게 진행했나: 3주 동안의 흐름','프로젝트 진행 과정');
const tl=[['1주차','아이디어','부산 음식 점수표 아이디어 → 근거 부족으로 폐기'],['2주차','문제 정의','크루즈 승객의 짧은 상륙 시간과 “부산 패싱”에 집중'],
 ['3주차 ①','수집·정제','입출항 신고·데이터랩·댓글·맛집 API·이동시간'],['3주차 ②','분석·모델','퍼널, 원도심 비교, 수요점수, OPTW 최적화'],
 ['3주차 ③','검토·개선','Codex 검토 3회 → 오류 수정, 방향 전환, 실제 가게 데이터로 교체'],['3주차 ④','결과물','시나리오별 시간표·실제 지도, 보고서·발표자료']];
s.addShape(p.ShapeType.line,{x:0.9,y:2.25,w:11.6,h:0,line:{color:'C9D6E0',width:2}});
tl.forEach(([w,a,b],i)=>{const x=0.6+i*2.03;dot(s,i+1,x+0.68,1.98,0.55,i>=4?CORAL:NAVY);tb(s,w,{x,y:2.75,w:1.9,h:0.35,fontSize:12,color:MUTE,align:'center'});
 tb(s,a,{x,y:3.1,w:1.9,h:0.45,fontSize:17,bold:true,color:NAVY,align:'center'});card(s,x,3.7,1.9,2.1);tb(s,b,{x:x+0.1,y:3.85,w:1.7,h:1.85,fontSize:12});});
tb(s,'코드·데이터·검토 기록은 모두 GitHub 저장소에 커밋해 재현 가능하게 관리',{x:0.6,y:6.15,w:12,h:0.4,fontSize:13,color:MUTE});
s.addNotes('1주차 점수표 아이디어는 근거가 부족해 접었고, 2주차에 크루즈 승객 문제로 좁혔습니다. 3주차에는 데이터를 모으고 다듬은 뒤 분석과 모델을 만들었고, Codex로 세 번 검토받아 고쳤습니다. 그 과정에서 역사 음식 중심에서 부산 패싱 해결로 방향을 바꾸고, 추정치였던 가게 정보를 부산시 공공데이터로 교체했습니다.');

// ===== ① 문제 =====
section(1,'문제','승객은 늘었는데 소비는 면세점에서 멈춘다');
s=slide('크루즈 승객은 3년 새 거의 3배, 머무는 시간은 8시간 남짓','문제 ① 기회는 커졌다');
s.addImage({path:R+'04_그림/그림5_월별승객.png',x:0.6,y:1.6,w:7.4,h:4.6});
stat(s,8.5,1.8,4.3,'+175.7%','2026년 1~7월 승객 403,188명\n(전년 같은 기간 대비)');
stat(s,8.5,3.6,4.3,'8.5시간','상륙 가능 시간 중앙값\n승객 81%가 8~13시간 기항선',SEA);
tb(s,'자료: 부산항 크루즈 입출항 신고정보(공공데이터포털 15164568, 2023~2026.7)',{x:0.6,y:6.5,w:12,h:0.35,fontSize:11,color:MUTE});
s.addNotes('공공데이터포털의 입출항 신고 648건을 정리했습니다. 2026년 1~7월 승객은 40만 명으로 전년보다 175% 늘었습니다. 그런데 머무는 시간은 대부분 8~13시간, 실제로 돌아다닐 수 있는 시간은 8시간 남짓입니다.');

s=slide('그런데 지갑은 면세점에서 닫힌다 — “부산 패싱”','문제 ② 지역 가게로 돈이 안 간다');
s.addChart(p.ChartType.doughnut,[{name:'중구 외국인 카드소비',labels:['쇼핑(면세 포함)','식음료','기타'],values:[66,21,13]}],
 {x:0.6,y:1.55,w:5.2,h:4.6,holeSize:55,chartColors:[CORAL,SEA,'C9D6E0'],showLegend:true,legendPos:'b',legendFontFace:FONT,legendFontSize:12,
  dataLabelColor:WHITE,showPercent:true,showValue:false,dataLabelFontSize:13,dataLabelFontFace:FONT,showTitle:true,title:'중구 외국인 카드소비 구성(약)',titleFontFace:FONT,titleFontSize:14,titleColor:INK});
card(s,6.3,1.7,6.4,1.45);tb(s,[{text:'먹을 수요는 있다  ',options:{bold:true,color:NAVY}},{text:'원도심 외국인 식음료 소비 +76% (2025.10→2026.7), 비교 3구 +57%보다 빠르다'}],{x:6.5,y:1.85,w:6.0,h:1.2,fontSize:15});
card(s,6.3,3.35,6.4,1.45);tb(s,[{text:'하지만 오래 못 간다  ',options:{bold:true,color:CORAL}},{text:'식음료는 월 19~23%에 머물고, 소비는 터미널·면세점 근처에서 끝난다'}],{x:6.5,y:3.5,w:6.0,h:1.2,fontSize:15});
card(s,6.3,5.0,6.4,1.15,'F7F9FB');tb(s,'주의: 쇼핑·식음료 비중은 데이터랩 업종 구성(2025.10~2026.9). 월별 크루즈 승객과의 상관은 약해(r=0.14) 연관으로만 해석',{x:6.5,y:5.1,w:6.0,h:0.95,fontSize:12,color:MUTE});
s.addNotes('한국관광데이터랩에서 구별 외국인 카드소비를 받았습니다. 중구는 쇼핑이 약 3분의 2입니다. 식음료는 원도심에서 비교 지역보다 빨리 늘고 있어 먹을 의지는 있습니다. 문제는 짧은 시간 안에 어디를 어떻게 갈지 모른다는 것입니다. 다만 월별 상관은 약해서 인과로 단정하지 않습니다.');

// ===== ② 원인 =====
section(2,'원인','왜 가게까지 못 가나 — 네 가지 원인, 네 가지 과제');
s=slide('네 가지 원인을 동시에 풀어야 한다','원인 → 우리가 풀 과제');
const causes=[['시간이 짧다','상륙 8시간 남짓, 승선 마감 30분 전 복귀','배 시간을 지키는 일정','입출항 신고'],
 ['가게 사정을 모른다','브레이크타임·마감 시각이 제각각','영업시간을 피한 방문 순서','부산시 맛집 API'],
 ['줄·이동에 시간을 버린다','크루즈 몰리는 시간대 줄 1.6배','줄·이동을 줄인 동선','OSRM 이동시간'],
 ['한꺼번에 내린다','2척 동시 기항일 7,831명','그룹별로 다른 루트','입출항 신고']];
causes.forEach(([a,b,c,d],i)=>{const x=0.6+(i%2)*6.15,y=1.65+Math.floor(i/2)*2.5;card(s,x,y,5.95,2.25);dot(s,i+1,x+0.25,y+0.25);
 tb(s,a,{x:x+1.0,y:y+0.28,w:4.7,h:0.5,fontSize:19,bold:true,color:NAVY});tb(s,b,{x:x+1.0,y:y+0.8,w:4.7,h:0.5,fontSize:14,color:MUTE});
 tb(s,[{text:'→ 과제  ',options:{bold:true,color:CORAL}},{text:c}],{x:x+1.0,y:y+1.3,w:4.7,h:0.4,fontSize:15});tb(s,'근거: '+d,{x:x+1.0,y:y+1.75,w:4.7,h:0.35,fontSize:12,color:MUTE});});
s.addNotes('가게까지 못 가는 원인은 네 가지입니다. 시간이 짧고, 가게 영업시간을 모르고, 줄과 이동에 시간을 버리고, 한꺼번에 내려 같은 곳에 몰립니다. 이 네 가지를 동시에 만족하는 경로를 찾는 것은 수학의 “시간창이 있는 오리엔티어링 문제”입니다.');

// ===== ③ 데이터 수집과 처리 =====
section(3,'데이터 수집과 처리','원데이터 6종 → 정제 → 분석용 표');
s=slide('원데이터: 어디서, 무엇을, 얼마나 받았나','데이터 ① 원데이터 목록');
T(s,[[th('원데이터'),th('출처·받은 방법'),th('규모·기간'),th('쓰임')],
 ['크루즈 입출항 신고정보','공공데이터포털 15164568 (CSV, cp949)','656행 × 34열, 2023.1~2026.7','승객 수, 입·출항 시각'],
 ['외국인 방문자·카드소비','한국관광데이터랩 (로그인, 조회 화면)','6개 구 × 12개월, 업종별','쇼핑 쏠림, 원도심 비교'],
 ['YouTube 댓글','YouTube Data API v3 (영·중·일 검색 상위 10개 영상)','1,792개 (작성자명 저장 안 함)','외국인 음식 수요'],
 ['부산맛집정보','공공데이터포털 15063472 (부산시, API 활용신청)','536곳, 국문·영문·일문','영업·브레이크·좌표'],
 ['도로 이동시간','OSRM 공개 경로 API','21곳 × 21곳 = 480쌍','택시·도보 이동 분'],
 ['참고 자료','제주 크루즈 실태조사·대만 설문·언론 27건','—','비교·국적 가중치']],
 {x:0.6,y:1.55,w:12.1,colW:[2.6,3.9,3.0,2.6],fontSize:13,rowH:0.62});
tb(s,'API 키는 저장소 밖 .ent 파일에만 보관 · 원데이터는 01_원천데이터/에 원본 그대로 저장',{x:0.6,y:6.3,w:12,h:0.4,fontSize:13,color:MUTE});
s.addNotes('원데이터는 여섯 갈래입니다. 입출항 신고는 공공데이터포털 CSV, 외국인 카드소비는 데이터랩, 외국인 수요는 YouTube 댓글, 가게 영업시간은 부산시 맛집 API, 이동시간은 OSRM입니다. 원본은 그대로 보관하고, 키는 저장소 밖에 두었습니다.');

s=slide('데이터 처리: 원데이터를 분석용 표로','데이터 ② 처리 파이프라인');
const pipe=[['입출항 신고','cp949 읽기 → 중복 제거(656→648) → 체류시간 계산 → 기항 유형·기항일 표','체류시간요약 · 연도별실적 · 기항일여부'],
 ['데이터랩','구·월별 조회 결과 정리 → 원도심 3구 vs 비교 3구 → 식음료 지수·비중','외국인소비_원도심비교'],
 ['YouTube 댓글','문자로 언어 판정(가나=일, 한자=중, 라틴=영) → 메뉴 사전 매칭 → 범주별 언급 수','메뉴언급_언어별 · 수요점수'],
 ['맛집 API','가게명으로 노드와 짝짓기 → 영업·브레이크 파싱 → 좌표 교체','food_nodes · 실데이터 대조표'],
 ['OSRM','21개 지점 전 쌍 경로 → 택시(+5분 호출) / 1.5km 이하 도보','travel_time 480쌍']];
pipe.forEach(([a,b,c],i)=>{const y=1.55+i*0.97;dot(s,i+1,0.6,y+0.12,0.5);tb(s,a,{x:1.3,y:y+0.15,w:2.0,h:0.45,fontSize:16,bold:true,color:NAVY});
 card(s,3.35,y,6.0,0.8);tb(s,b,{x:3.5,y:y+0.08,w:5.7,h:0.66,fontSize:13,valign:'middle'});tb(s,'→',{x:9.4,y:y+0.15,w:0.4,h:0.45,fontSize:18,bold:true,color:CORAL});
 tb(s,c,{x:9.85,y:y+0.08,w:2.9,h:0.66,fontSize:12,color:MUTE,valign:'middle'});});
s.addNotes('원데이터마다 정제 과정을 거쳤습니다. 입출항 신고는 인코딩을 맞추고 중복을 지운 뒤 체류시간을 계산했습니다. 댓글은 문자 종류로 언어를 나누고 메뉴 사전으로 음식 범주를 셌습니다. 맛집 API는 우리 지점과 이름으로 짝을 지어 실제 영업시간으로 바꿨습니다.');

const RC=csv('2025승객수_기준차이_1118_A.csv'),ST=csv('체류시간요약_1118_A.csv');
s=slide('숫자 맞추기: 보도 25.7만 명 vs 신고 24.9만 명','데이터 ③ 기준 차이 확인과 기항 유형');
T(s,[[th('기준'),th('항차'),th('승객')],...RC.map(r=>[r['기준'],r['항차'],(+r['승객']).toLocaleString()])],{x:0.6,y:1.6,w:6.0,colW:[3.6,1.0,1.4],fontSize:13,rowH:0.55});
tb(s,'보도치와 2.9% 차이(원인 미해명) — 발표에서는 신고 원자료 기준을 쓰고 차이를 공개',{x:0.6,y:3.95,w:6.0,h:0.8,fontSize:13,color:CORAL});
T(s,[[th('기항 유형'),th('항차'),th('승객 비중'),th('상륙 가능 중앙값')],...ST.map(r=>[r['type'],r['항차'],r['승객비중%']+'%',r['상륙가능_중앙값h']+'시간'])],{x:7.0,y:1.6,w:5.7,colW:[1.8,1.0,1.3,1.6],fontSize:13,rowH:0.55});
tb(s,'상륙 가능 시간 = 체류시간 − 2.5시간(하선·입국심사·승선 마감)',{x:7.0,y:3.95,w:5.7,h:0.6,fontSize:12,color:MUTE});
s.addImage({path:R+'04_그림/그림4_체류시간분포.png',x:7.0,y:4.5,w:5.7,h:1.95,sizing:{type:'contain',w:5.7,h:1.95}});
s.addNotes('분석 전에 숫자부터 맞췄습니다. 언론의 25.7만 명과 신고 원자료 24.9만 명이 2.9% 차이가 나서 기준을 표로 공개했습니다. 기항 유형별로 보면 승객의 81%가 8~13시간 기항선이고 실제로 돌아다닐 수 있는 시간은 중앙값 8.5시간입니다.');

const ND=csv('노드_실데이터대조_1118_B.csv').filter(r=>r['추정(이전)']);
s=slide('추정치를 실제 데이터로: 가게 13곳 교체','데이터 ④ 부산시 맛집 API로 검증');
T(s,[[th('이전(추정)'),th('실제(부산시 맛집 API)'),th('위치 차이')],...ND.slice(0,7).map(r=>[r['추정(이전)'],r['실제(부산시 API)'],r['좌표 이동(m)']+'m'])],{x:0.6,y:1.55,w:12.1,colW:[4.7,5.6,1.8],fontSize:12,rowH:0.5});
tb(s,'예: 원조18번완당 마감 22:00 → 19:30, 할매국밥 22:00 → 19:00, 동래할매파전 브레이크 15~17시 추가 · 골목 단위 좌표는 최대 3.3km 어긋나 있었다',{x:0.6,y:6.2,w:12.1,h:0.6,fontSize:13,color:CORAL});
s.addNotes('처음에는 가게 영업시간을 웹 검색으로 추정했습니다. 부산시 맛집 API를 신청해 실제 값과 비교해 보니 마감 시각이 2시간 이상 다른 곳도 있었습니다. 19곳 중 13곳을 실제 가게 데이터로 바꿨고, 시장·마을 6곳과 줄 대기 시간은 공개 데이터가 없어 추정으로 남았습니다.');

// ===== ④ 분석 =====
section(4,'분석','퍼널 · 원도심 vs 비교 지역 · 외국인 수요');
s=slide('퍼널: 승객이 부산 가게까지 가는 단계','분석 ① 퍼널 구성');
const fstep=[['① 입항 승객','403,188명 (2026.1~7, +175.7%)','입출항 신고',true],['② 상륙·하선 승객','미측정 — 법무부 상륙허가 통계 필요','—',false],
 ['③ 부산에서 결제','원도심 3구가 외국인 소비의 19~23%','데이터랩',true],['④ 음식업 결제','원도심 식음료 +76% (비교 +57%)','데이터랩',true],['⑤ 대표 음식·시장','해산물·회 86건, 면 39건','YouTube 댓글',true]];
fstep.forEach(([a,b,c,okk],i)=>{const w=12.1-i*1.3,x=0.6+i*0.65,y=1.55+i*0.95;
 s.addShape(p.ShapeType.roundRect,{x,y,w,h:0.8,fill:{color:okk?(i%2?SEA:NAVY):'D5DDE4'},line:{color:WHITE},rectRadius:0.08});
 tb(s,a,{x:x+0.25,y,w:3.0,h:0.8,fontSize:16,bold:true,color:okk?WHITE:INK,valign:'middle'});tb(s,b,{x:x+2.9,y,w:w-4.6,h:0.8,fontSize:14,color:okk?WHITE:INK,valign:'middle'});
 tb(s,c,{x:x+w-1.6,y,w:1.4,h:0.8,fontSize:11,color:okk?'D6E6F2':MUTE,valign:'middle',align:'right'});});
tb(s,'회색 = 아직 측정하지 못한 단계. 단계마다 모집단이 달라 전환율로 곱하지 않는다',{x:0.6,y:6.4,w:12,h:0.4,fontSize:13,color:MUTE});
s.addNotes('승객이 배에서 내려 부산 가게까지 가는 과정을 다섯 단계 퍼널로 나눴습니다. 입항 승객, 원도심 소비 비중, 음식업 증가, 외국인이 원하는 음식은 데이터로 채웠고, 상륙 승객 수는 아직 자료가 없어 비워 두었습니다. 단계마다 모집단이 달라서 전환율을 곱해 과장하지 않았습니다.');

const DT=csv('외국인소비_원도심비교_1118_A.csv');
const ml=DT.map(r=>r['연월'].slice(2,4)+'.'+r['연월'].slice(4));
s=slide('원도심 외국인 식음료는 비교 지역보다 빨리 늘었다','분석 ② 원도심 3구 vs 비교 3구 (데이터랩, 월별)');
s.addChart(p.ChartType.line,[{name:'원도심 3구 (중·동·영도)',labels:ml,values:DT.map(r=>+r['원도심 식음료(지수, 2025.10=100)'])},
 {name:'비교 3구 (서·부산진·해운대)',labels:ml,values:DT.map(r=>+r['비교 식음료(지수, 2025.10=100)'])}],
 {x:0.6,y:1.55,w:7.6,h:4.9,chartColors:[CORAL,'8FA3B3'],lineSize:3,lineDataSymbol:'circle',lineDataSymbolSize:6,showLegend:true,legendPos:'t',legendFontFace:FONT,legendFontSize:12,
  catAxisLabelFontFace:FONT,catAxisLabelFontSize:11,catAxisLabelColor:INK,valAxisLabelFontFace:FONT,valAxisLabelFontSize:11,valAxisLabelColor:MUTE,valGridLine:{color:'E3E9EE',size:0.5},catGridLine:{style:'none'},
  showTitle:true,title:'외국인 식음료 카드소비 지수 (2025.10 = 100)',titleFontFace:FONT,titleFontSize:14,titleColor:INK});
stat(s,8.6,1.8,4.1,'+76%','원도심 3구 식음료\n(2025.10 → 2026.7)',CORAL);stat(s,8.6,3.5,4.1,'+57%','비교 3구 식음료',MUTE);
card(s,8.6,5.25,4.1,1.2,'F7F9FB');tb(s,'같은 기간 크루즈 승객 월 2.2만 → 8.0만 명. 다만 월별 상관 r=0.14로 약해 “연관”으로만 해석',{x:8.75,y:5.33,w:3.8,h:1.05,fontSize:12,color:MUTE});
s.addNotes('데이터랩에서 원도심 3구와 비교 3구의 외국인 식음료 카드소비를 월별로 비교했습니다. 원도심은 76%, 비교 지역은 57% 늘었습니다. 크루즈 승객이 급증한 시기와 겹치지만, 겹치는 달이 10개뿐이고 상관도 약해서 인과로 말하지는 않습니다.');

s=slide('무엇을 먹게 할까 — 외국인이 실제로 말하는 음식','분석 ③ 수요점수 (YouTube 댓글 영·중·일 1,492개)');
s.addChart(p.ChartType.bar,[{name:'댓글 언급 수',labels:['해산물·회','면(밀면·완당)','시장·길거리','고기(갈비)','국밥','치킨·카페','어묵'],values:[86,39,38,18,18,10,2]}],
 {x:0.6,y:1.55,w:7.2,h:4.9,barDir:'bar',chartColors:[SEA],showValue:true,dataLabelPosition:'outEnd',dataLabelFontFace:FONT,dataLabelFontSize:12,dataLabelColor:INK,
  catAxisLabelFontFace:FONT,catAxisLabelFontSize:13,catAxisLabelColor:INK,valAxisHidden:true,valGridLine:{style:'none'},catAxisOrientation:'maxMin',showLegend:false,
  showTitle:true,title:'음식 범주별 댓글 언급 수',titleFontFace:FONT,titleFontSize:14,titleColor:INK});
card(s,8.2,1.7,4.5,4.6);
tb(s,[{text:'역사 음식이 아니라\n“먹고 싶은 것” 기준\n\n',options:{bold:true,color:NAVY,fontSize:18}},
 {text:'영어권: 회·곰장어\n중국어권: 돼지국밥\n일본어권: 회\n\n',options:{fontSize:15}},
 {text:'수요점수 = 50 + 50·ln(1+언급)/ln(87)\n해산물 100점 … 어묵 62점',options:{fontSize:13,color:MUTE}}],{x:8.45,y:1.95,w:4.0,h:4.2});
s.addNotes('어디를 갈지는 팀 취향이 아니라 외국인 데이터로 정했습니다. 부산 음식 영상의 영어·중국어·일본어 댓글을 모아 음식 범주별 언급을 셌더니 해산물과 회가 압도적이었습니다. 이 언급 수를 50~100점의 수요점수로 바꿔 모델의 만족도로 씁니다.');

// ===== ⑤ 모델과 검토 =====
section(5,'모델과 검토','시간창 오리엔티어링(OPTW) · 검토 3회 · 버전 3개');
s=slide('모델: 만족은 최대로, 위험은 제약으로 막는다','시간창 오리엔티어링 문제 (OPTW)');
card(s,0.6,1.6,12.1,1.0,NAVY);tb(s,'최대화   Σ 수요점수 × 국적 가중치  −  0.8 × (줄 대기 + 이동 시간)',{x:0.9,y:1.6,w:11.5,h:1.0,fontSize:22,bold:true,color:WHITE,valign:'middle'});
const cons=[['승선 30분 전 복귀','배를 놓침'],['영업·브레이크타임','도착했는데 문 닫음'],['시간대 혼잡 줄 대기','줄에 시간 낭비'],['위 용량·식사 간격','배불러 못 먹음'],['최대 7곳','무리한 일정']];
cons.forEach(([a,b],i)=>{const x=0.6+i*2.47;card(s,x,2.95,2.27,2.0);tb(s,a,{x:x+0.15,y:3.1,w:1.97,h:0.85,fontSize:15,bold:true,color:NAVY});tb(s,[{text:'막는 문제\n',options:{fontSize:11,color:MUTE}},{text:b,options:{fontSize:14,color:CORAL,bold:true}}],{x:x+0.15,y:3.95,w:1.97,h:0.9});});
tb(s,`풀이: 분기한정법으로 최적해 보장 (수업의 탐욕법 = 가까운 곳부터, 보장 없음) · Colab 기본 라이브러리만 사용\n제약을 무시하면? ${N1['방문 수']}곳을 돌고 ${N1['복귀']} 복귀 — 배를 놓치고 규칙 위반 ${nvViol}건`,{x:0.6,y:5.25,w:12.1,h:1.0,fontSize:15,color:INK});
s.addNotes(`목표는 수요점수 합에서 줄과 이동 시간을 뺀 값을 최대로 하는 것입니다. 다섯 가지 제약이 각각 현실의 실패를 막습니다. 수업에서 배운 탐욕법은 가까운 곳부터 고르지만 최적을 보장하지 않습니다. 제약을 무시한 계획은 ${N1['복귀']}에 돌아와 배를 놓칩니다.`);


s=slide('검토하고 고치며 세 번 바뀐 모델','모델 개발과 검토 과정');
T(s,[[th('검토'),th('주요 지적'),th('고친 것')],
 ['Codex 1차 (12건)','기다리면 갈 수 있는 가게 누락 · 위 소화 누락 · 탐욕법과 제약 불일치 · 퍼널 분모 혼재','대기 선택 추가, 체류 중 소화, 같은 제약의 탐욕법, 퍼널 재작성'],
 ['Codex 2차 (8건)','줄 서기 시점 판정 오류 · 분산 재평가 불일치 · 위험도 평가 누락','먹기 시작 기준 판정, 공동 반복평가, 공통 평가기'],
 ['Codex 3차 (4건)','브레이크 후 재개장 대기 누락 · 비수렴 결과 집계 · 해 없음 처리','재개장 후보 추가, 비수렴=실패, 빈 루트 처리']],
 {x:0.6,y:1.55,w:12.1,colW:[2.2,5.2,4.7],fontSize:13,rowH:0.85});
const ver=[['v1','부산 고유성 점수(역사 음식) · 16곳 · 추정 영업시간'],['v2','외국인 댓글 수요점수 · 19곳 · “부산 패싱” 해결로 방향 전환'],['v3','부산시 맛집 API로 13곳 실제 영업·좌표 · 이동시간 재계산']];
ver.forEach(([a,b],i)=>{const x=0.6+i*4.1;card(s,x,5.15,3.9,1.25,i==2?NAVY:ICE);tb(s,a,{x:x+0.2,y:5.25,w:0.8,h:0.5,fontSize:20,bold:true,color:i==2?WHITE:CORAL});tb(s,b,{x:x+0.2,y:5.7,w:3.5,h:0.65,fontSize:12,color:i==2?WHITE:INK});});
s.addNotes('모델은 다른 AI(Codex)에게 세 번 검토받고 그때마다 고쳤습니다. 1차에서 12건, 2차에서 8건, 3차에서 4건이 나왔습니다. 모델도 세 번 바뀌었습니다. 처음에는 역사 음식 점수였지만, 외국인 수요 점수로 바꾸고, 마지막에는 부산시 공식 데이터로 가게 정보를 교체했습니다. 규칙 테스트는 매번 통과시켰습니다.');

// ===== ⑥ 결과 =====
section(6,'결과','6개 시나리오의 실제 루트 · 1,000회 검증');
const routeSlide=(k,title,kicker,note)=>{const t=top(k),rows=TT.filter(r=>r['시나리오']==t['시나리오']);
 const sl=slide(title,kicker);const img=R+`04_그림/그림8_${k}루트지도.png`;
 sl.addImage({path:img,x:0.5,y:1.5,w:7.4,h:4.95,sizing:{type:'contain',w:7.4,h:4.95}});
 T(sl,[[th('#'),th('장소'),th('먹기'),th('이동·줄')],...rows.map(r=>[r['순서']==='0'?'':r['순서'],short(r['장소']).replace('부산항국제여객터미널','북항 터미널'),r['먹기 시작']||r['도착']||r['떠남'],r['이동']?`${r['이동']} ${r['이동(분)']}분${r['줄(분)']?' · 줄 '+r['줄(분)']+'분':''}`:'하선'])],
  {x:8.1,y:1.5,w:4.7,colW:[0.35,2.05,0.75,1.55],fontSize:11,rowH:0.36});
 tb(sl,note,{x:8.1,y:6.45,w:4.7,h:0.6,fontSize:12,color:CORAL,bold:true});sl.addNotes(note);};
routeSlide('S1',`북항 당일 기항: 08:30 하선 → ${S1['복귀']} 복귀, 7곳`,'결과 ① 대표 루트 (S1)',`탐욕법 대비 +${gain}%, 7곳 중 ${S1['원도심 밖 노드']}곳이 원도심 밖`);
const NOTE={S2:'짧게 머무는 배는 원도심 4곳만, 멀리 보내지 않는다',S3:'오버나잇 2일차는 전포·동래·해운대까지 확장',S4:'부산 승선객은 체크인 전 영도·자갈치·남포동 반나절 (여유 9분, 마지막 1곳은 선택)',S5:'크루즈 없는 날은 줄이 짧아 원도심 + 해운대·동래·전포',S6:'대만 승객 가중을 주면 돼지국밥(범일동·서면)이 들어온다'};
s=slide('상황마다 루트가 달라진다 — 6개 시나리오 비교','결과 ② 시나리오');
const ks=['S1','S2','S3','S4','S5','S6'];
s.addChart(p.ChartType.bar,[{name:'최적화(OPTW)',labels:ks,values:ks.map(k=>+top(k)['목적함수'])},{name:'수업 탐욕법',labels:ks,values:ks.map(k=>+gr(k)['목적함수'])}],
 {x:0.6,y:1.5,w:6.6,h:4.9,barDir:'col',barGrouping:'clustered',chartColors:[NAVY,'B8C7D3'],showValue:true,dataLabelPosition:'outEnd',dataLabelFontSize:10,dataLabelFontFace:FONT,dataLabelColor:INK,
  catAxisLabelFontFace:FONT,catAxisLabelFontSize:12,catAxisLabelColor:INK,valAxisHidden:true,valGridLine:{style:'none'},showLegend:true,legendPos:'t',legendFontFace:FONT,legendFontSize:12,
  showTitle:true,title:'시나리오별 목적함수 (높을수록 좋음)',titleFontFace:FONT,titleFontSize:14,titleColor:INK});
T(s,[[th(''),th('상황'),th('복귀'),th('원도심 밖')],...ks.map(k=>{const t=top(k);return [k,t['시나리오'].replace(/^S\d /,'').replace(/\(.*\)/,'').trim(),t['복귀'],t['원도심 밖 노드']+'곳']})],{x:7.5,y:1.6,w:5.2,colW:[0.5,2.8,0.9,1.0],fontSize:12,rowH:0.5});
tb(s,'6개 시나리오 모두 최적화 > 탐욕법,\n규칙 위반 0건',{x:7.5,y:5.4,w:5.2,h:0.8,fontSize:14,bold:true,color:CORAL});
s.addNotes('하선 터미널, 머무는 시간, 크루즈 혼잡, 국적에 따라 6개 상황을 만들었습니다. 모든 상황에서 우리 최적화가 수업의 탐욕법보다 점수가 높고, 시간표로 다시 확인해도 규칙 위반이 없었습니다. 이어서 각 상황의 실제 루트를 보겠습니다.');
ks.slice(1).forEach(k=>{const t=top(k);routeSlide(k,`${t['시나리오'].replace(/\(.*\)/,'').trim()}: ${t['복귀']} 복귀`,'결과 ② 시나리오별 루트',NOTE[k]);});

s=slide('흔들어도 배는 놓치지 않는다 — 단, 원거리 구간은 빠듯','결과 ③ 검증 (대기 ±30%, 이동 ±20%, 1,000회)');
stat(s,0.6,1.8,3.9,late+'%','복귀 지각 확률',NAVY);stat(s,4.75,1.8,3.9,ok+'%','전체 규칙 준수율',SEA);stat(s,8.9,1.8,3.9,p5+'분','복귀 여유 하위 5%',CORAL);
card(s,0.6,4.2,12.1,1.9);tb(s,[{text:'그래서 운영은 이렇게  ',options:{bold:true,color:NAVY}},{text:`해운대·동래처럼 먼 곳은 “시간 여유가 있을 때만” 가는 선택 구간으로 두고, 승선 2시간 전 복귀 알림으로 남은 일정을 줄인다. 최적 방문 집합은 재최적화 20회 중 ${Math.round(vk('최적 방문집합')*100)}% 유지돼 루트 자체는 안정적이다.`}],{x:0.9,y:4.4,w:11.5,h:1.5,fontSize:16});
s.addNotes(`줄과 이동시간을 무작위로 흔들어 1,000번 시뮬레이션했습니다. 지각 확률은 ${late}%이지만 하위 5%의 여유는 ${p5}분으로 빠듯합니다. 그래서 먼 구간은 선택형으로 두고 복귀 알림을 줍니다.`);

s=slide('한꺼번에 내려도 나눠 보내면 줄이 준다','결과 ④ 혼잡 분산 (같은 배 6그룹, 100명씩)');
const d4=DF.filter(r=>r['겹침당 추가대기(분)'].startsWith('4')),d8=DF.filter(r=>r['겹침당 추가대기(분)'].startsWith('8'));
s.addChart(p.ChartType.bar,[{name:'겹침 100명당 +4분',labels:d4.map(r=>r['배정']),values:d4.map(r=>+r['그룹 평균 줄대기(분)'])},
 {name:'겹침 100명당 +8분',labels:d8.map(r=>r['배정']),values:d8.map(r=>+r['그룹 평균 줄대기(분)'])}],
 {x:0.6,y:1.5,w:6.4,h:4.9,barDir:'col',barGrouping:'clustered',chartColors:['F2A493',CORAL],showValue:true,dataLabelPosition:'outEnd',dataLabelFontFace:FONT,dataLabelFontSize:12,dataLabelColor:INK,
  catAxisLabelFontFace:FONT,catAxisLabelFontSize:14,catAxisLabelColor:INK,valAxisHidden:true,valGridLine:{style:'none'},showLegend:true,legendPos:'t',legendFontFace:FONT,legendFontSize:12,
  showTitle:true,title:'그룹 평균 줄 대기(분)',titleFontFace:FONT,titleFontSize:14,titleColor:INK});
card(s,7.4,1.7,5.3,4.5);tb(s,[{text:'같은 루트로 몰리면\n',options:{bold:true,color:NAVY,fontSize:17}},{text:`평균 ${d4[0]['그룹 평균 줄대기(분)']}~${d8[0]['그룹 평균 줄대기(분)']}분 줄, 6그룹 모두 위반\n\n`},
 {text:'그룹마다 다른 루트로 보내면\n',options:{bold:true,color:CORAL,fontSize:17}},{text:`평균 ${d4[1]['그룹 평균 줄대기(분)']}~${d8[1]['그룹 평균 줄대기(분)']}분, 위반 +4분 ${d4[1]['규칙 위반 그룹']}그룹 · +8분 ${d8[1]['규칙 위반 그룹']}그룹\n\n`},
 {text:'순서대로 배정해 결과가 배정 순서에 따라 달라진다 → 동시 배정은 다음 과제'+(DISP_NEW?'':'\n(가게 변경 전 모델로 계산한 결과)'),options:{fontSize:12,color:MUTE}}],{x:7.7,y:1.95,w:4.8,h:4.1,fontSize:15});
s.addNotes(`같은 배의 승객 6그룹이 한 루트로 몰리면 평균 ${d4[0]['그룹 평균 줄대기(분)']}~${d8[0]['그룹 평균 줄대기(분)']}분을 줄 서고 모든 그룹이 배 시간을 놓칩니다. 그룹마다 다른 루트를 배정하면 평균 ${d4[1]['그룹 평균 줄대기(분)']}~${d8[1]['그룹 평균 줄대기(분)']}분으로 줄고, 상인에게는 손님이 고르게 갑니다. 다만 그룹을 차례로 배정하는 방식이라 결과가 순서에 따라 달라지고, 더 약한 혼잡(+4분)에서 오히려 2그룹이 규칙을 어겼습니다. 모든 그룹을 동시에 배정하는 방식은 다음 과제입니다.`+(DISP_NEW?'':' 이 결과는 가게를 실제 데이터로 바꾸기 전 모델로 계산한 것입니다.'));

// ===== ⑦ 효과·실행 =====
section(7,'효과와 실행','무엇이 해결되고, 누가 실행하나');
s=slide('그래서 무엇이 해결되나','해결 효과');
T(s,[[th('문제'),th('해결책'),th('근거')],
 ['배를 놓칠까 봐 터미널 근처에만 머문다','승선 마감을 지키는 최적 루트',`지각 ${late}%, ${S1['복귀']} 복귀`],
 ['문 닫은 가게·긴 줄에 시간 낭비','실제 영업·브레이크·혼잡 반영',`탐욕법 대비 +${gain}%`],
 ['무엇을 먹을지 모른다','외국인 댓글 기반 수요점수','해산물·시장·면·고기 우선'],
 ['소비가 면세점·원도심에 갇힌다','원도심 밖까지 잇는 루트',`7곳 중 ${S1['원도심 밖 노드']}곳이 원도심 밖`],
 ['한꺼번에 몰려 줄이 길어진다','그룹별 분산 배정',`줄 대기 평균 ${d4[0]['그룹 평균 줄대기(분)']}분 → ${d4[1]['그룹 평균 줄대기(분)']}분`]],
 {x:0.6,y:1.6,w:12.1,colW:[4.3,4.0,3.8],fontSize:15,rowH:0.75});
s.addNotes('정리하면 다섯 가지 문제가 각각 해결책과 수치 근거로 연결됩니다.');

s=slide('누가 어떻게 실행하나','실행 계획과 한계');
const who=[['부산항만공사','하선 안내 QR → 배 이름만 넣으면 맞춤 루트'],['상인회·전통시장','브레이크·줄 정보 제공, 분산 배정으로 손님 고르게'],['우리 팀','주요 가게 줄 대기 현장 측정, 리뷰로 가게 단위 수요점수']];
who.forEach(([a,b],i)=>{const y=1.65+i*1.15;dot(s,i+1,0.6,y);tb(s,a,{x:1.4,y:y+0.03,w:3.2,h:0.5,fontSize:18,bold:true,color:NAVY});tb(s,b,{x:4.6,y:y+0.06,w:8.1,h:0.5,fontSize:15});});
card(s,0.6,5.2,12.1,1.35,'F7F9FB');tb(s,[{text:'한계  ',options:{bold:true,color:CORAL}},{text:'줄 대기 시간은 추정(공개 데이터 없음) · 수요점수는 범주 단위·표본 작음 · 데이터랩은 월 단위라 기항일 효과는 일 단위 자료로 검증 필요'}],{x:0.85,y:5.35,w:11.6,h:1.1,fontSize:14});
s.addNotes('부산항만공사는 하선 안내에 QR을, 상인회는 영업과 줄 정보를, 우리 팀은 현장 측정으로 추정치를 실제 값으로 바꿉니다. 한계도 분명히 말씀드립니다.');

SEC='마무리';p.addSection({title:SEC});
s=p.addSlide({masterName:'DARK',sectionTitle:SEC});
s.addText('배에서 내린 8시간을\n부산의 맛으로',{placeholder:'title'});
tb(s,'승객은 배를 놓치지 않고 더 먹고, 소비는 면세점 밖 부산 가게로',{x:0.8,y:4.3,w:11.5,h:0.5,fontSize:20,color:'C9DCEB'});
tb(s,'감사합니다 · 코드와 데이터는 팀 GitHub 저장소(비공개)에 정리',{x:0.8,y:6.5,w:11.5,h:0.4,fontSize:13,color:'9FB8CC'});
s.addNotes('배에서 내린 8시간을 부산의 맛으로 채우는 것이 우리 제안입니다. 감사합니다.');

p.writeFile({fileName:process.env.DECK_OUT||R+'05_문서/3주차_발표자료.pptx'}).then(()=>console.log('deck ok'));
