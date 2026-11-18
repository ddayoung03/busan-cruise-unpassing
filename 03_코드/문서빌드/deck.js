// 3주차 발표자료 생성: node deck.js  (pptxgenjs 필요). 수치는 02_정제데이터 CSV에서 읽는다.
const fs=require('fs');const P=require('pptxgenjs');const p=new P();p.layout='LAYOUT_WIDE';
const R='C:/Users/PTY/Desktop/지산학아이디어톤/';const F='Malgun Gothic',N='1F4E79',A='E07A1F';
const csv=f=>{const L=fs.readFileSync(R+'02_정제데이터/'+f,'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/);const H=L[0].split(',');
  return L.slice(1).map(l=>{const c=[];let cur='',q=false;for(const ch of l){if(ch=='"')q=!q;else if(ch==','&&!q){c.push(cur);cur=''}else cur+=ch}c.push(cur);return Object.fromEntries(H.map((h,i)=>[h,c[i]]))})};
const short=s=>s.split(' → ').map(x=>x.replace(/\(.*?\)/g,'').trim()).join(' → ');
const RT=csv('루트결과_1118_B.csv');const top=s=>RT.find(r=>r['시나리오'].startsWith(s)&&r['순위']=='1');const gr=s=>RT.find(r=>r['시나리오'].startsWith(s)&&r['순위'].startsWith('탐욕'));
const N1=csv('제약무시계획_1118_B.csv')[0];const nvViol=Object.keys(N1).filter(k=>k.startsWith('위반:')).reduce((a,k)=>a+(+N1[k]),0);
const VD=Object.fromEntries(csv('검증_1118_B.csv').map(r=>[r['지표'],+r['값']]));const vk=k=>VD[Object.keys(VD).find(x=>x.startsWith(k))];
const DF=csv('분산효과_1118_B.csv');const d8=DF.filter(r=>r['겹침당 추가대기(분)'].startsWith('8'));const d4=DF.filter(r=>r['겹침당 추가대기(분)'].startsWith('4'));
const dispNew=fs.statSync(R+'02_정제데이터/분산효과_1118_B.csv').mtimeMs>fs.statSync(R+'02_정제데이터/food_nodes_1118_B.csv').mtimeMs;
const S1=top('S1'),G1=gr('S1');
function s(title,kicker){const x=p.addSlide();x.background={color:'FFFFFF'};
 if(kicker)x.addText(kicker,{x:0.6,y:0.3,w:12,h:0.4,fontFace:F,fontSize:14,color:A,bold:true});
 x.addText(title,{x:0.6,y:0.65,w:12.1,h:0.9,fontFace:F,fontSize:26,bold:true,color:N});return x;}
const bl=(x,items,o={})=>x.addText(items.map(t=>({text:t,options:{bullet:true,breakLine:true}})),{x:o.x||0.6,y:o.y||1.7,w:o.w||12,h:o.h||5,fontFace:F,fontSize:o.fs||18,color:'222222',valign:'top',paraSpaceAfter:10});
const im=(x,f,o)=>x.addImage({path:R+'04_그림/'+f,...o});
const th=t=>({text:t,options:{bold:true,color:'FFFFFF',fill:{color:N}}});
// 1 표지
let x=p.addSlide();x.background={color:N};
x.addText('면세점에서 멈추지 않게\n크루즈 승객의 부산 패싱 끊기',{x:0.8,y:1.8,w:11.5,h:2.2,fontFace:F,fontSize:40,bold:true,color:'FFFFFF'});
x.addText('상륙 시간 안에 지각 없이, 외국인이 원하는 부산 음식으로 · 크루즈 미식 루트 팀 · 2026 지산학 아이디어톤 3주차',{x:0.8,y:4.4,w:11.5,h:0.6,fontFace:F,fontSize:18,color:'D0DCEB'});
// 2 결론
x=s('결론: 최적 루트로 소비를 면세점 밖, 부산 전역으로','한 장 요약');
bl(x,['크루즈 승객 2026년 1~7월 403,188명 (+175.7%) — 그러나 중구 외국인 소비의 약 66%는 쇼핑',
 '외국인 댓글이 가장 많이 말한 음식: 해산물·회, 면, 시장 길거리 음식, 고기',
 `최적 루트(S1) ${S1['목적함수']}점 vs 수업 탐욕법 ${G1['목적함수']}점, ${S1['복귀']} 복귀`,
 `7곳 중 ${S1['원도심 밖 노드']}곳이 원도심 밖(해운대·동래·서면) — 소비가 부산 전역으로`,
 `1,000회 변동 모의: 지각 ${(vk('고정 루트 복귀 지각')*100).toFixed(1)}%, 규칙 준수 ${(vk('고정 루트 전체 규칙')*100).toFixed(1)}%`]);
// 3 문제
x=s('승객은 3년 새 거의 3배, 머무는 시간은 8시간 남짓','문제 ①');
im(x,'그림5_월별승객.png',{x:0.5,y:1.7,w:6.2,h:4.2});im(x,'그림4_체류시간분포.png',{x:6.9,y:1.7,w:6.0,h:4.2});
x.addText('승객 81%가 8~13시간 기항선 · 상륙 가능 중앙값 8.5시간 · 2025년 이후 36%의 날이 2척 이상',{x:0.6,y:6.2,w:12,h:0.6,fontFace:F,fontSize:16,color:'444444'});
// 4 패싱
x=s('내려서 면세점 들르고 배로 — “부산 패싱”','문제 ②');
bl(x,['한국관광데이터랩 외국인 카드소비(중구): 쇼핑업 약 66%, 식음료 월 19~23%',
 '원도심 외국인 식음료는 늘고 있다: 2025.10→2026.7 +76% (비교 3구 +57%)',
 '즉 먹을 의지는 있는데, 짧은 시간·줄·브레이크타임·배 시간 때문에 동선이 끊긴다',
 '단, 월별 크루즈 승객과의 상관은 약함(r=0.14, 10개월) — 연관으로만 해석']);
// 5 수요
x=s('외국인이 실제로 말하는 부산 음식','수요 근거 (YouTube 댓글 1,492개, 영·중·일)');
x.addTable([[th('범주'),th('언급'),th('수요점수')],['해산물·회','86','100'],['면(밀면·완당)','39','91'],['시장·길거리','38','91'],['고기(갈비)','18','83'],['국밥','18','83'],['치킨·카페','10','77'],['어묵','2','62']],{x:0.6,y:1.7,w:6.2,fontFace:F,fontSize:15,border:{color:'BBBBBB',pt:1}});
bl(x,['역사 음식(피란 음식)보다 “먹고 싶은 것” 기준','영어권 회·곰장어, 중국어권 돼지국밥, 일본어권 회','수요점수 = 50 + 50·ln(1+언급)/ln(87)','표본이 작아 범주 단위로만 사용'],{x:7.2,w:5.6,fs:16});
// 6 데이터
x=s('데이터 파이프라인','데이터');
im(x,'그림1_데이터흐름.png',{x:0.6,y:1.6,w:7.2,h:4.8});
x.addText([{text:'입출항 신고 648건 (공공데이터포털)\n',options:{bold:true}},{text:'데이터랩 외국인 카드소비 (구·월·업종)\nYouTube 댓글 1,792개\n부산시 맛집정보 API (실제 영업·좌표)\n음식 노드 19곳 (13곳 실데이터)\nOSRM 실도로 이동시간\n\n'},{text:'[미확보] 상륙 승객 수 · 일 단위 소비',options:{color:'C00000'}}],{x:8.1,y:1.8,w:4.8,h:4.5,fontFace:F,fontSize:16,valign:'top'});
// 7 모델
x=s('모델: 시간창 오리엔티어링 문제 (OPTW)','방법');
bl(x,['최대화  Σ 수요점수 × 국적 가중치 − 0.8 × (줄대기 + 이동)','제약: 승선 30분 전 복귀 · 영업/브레이크 · 혼잡 줄대기 · 위 용량 · 식사 간격 · 최대 7곳','분기한정으로 최적해 보장 (수업 탐욕법은 보장 없음)','Colab 기본 라이브러리만 사용 → 재현 가능']);
// 8 결과1
x=s('같은 조건, 최적화가 이기고 소비는 원도심 밖으로','결과 ① 루트');
x.addTable([[th('시나리오'),th('OPTW'),th('탐욕법'),th('복귀'),th('원도심 밖')],...['S1','S2','S3','S4','S5'].map(k=>{const t=top(k),g=gr(k);return [t['시나리오'].replace(/\(.*\)/,''),t['목적함수'],g['목적함수'],t['복귀'],t['원도심 밖 노드']+'곳']})],{x:0.6,y:1.7,w:7.4,fontFace:F,fontSize:13,border:{color:'BBBBBB',pt:1}});
x.addText(`S1 최적 루트\n${short(S1['루트'])}\n\n제약 무시: ${N1['방문 수']}곳 · ${N1['복귀']} 복귀 · 위반 ${nvViol}건`,{x:8.3,y:1.7,w:4.6,h:4.8,fontFace:F,fontSize:15,color:'333333',valign:'top'});
// 9 검증
x=s('흔들어도 대부분 지킨다 — 다만 원거리 구간은 빠듯','결과 ② 검증');
bl(x,['대기 ±30%, 이동 ±20% 무작위 1,000회',`지각 ${(vk('고정 루트 복귀 지각')*100).toFixed(1)}%, 전체 규칙 준수 ${(vk('고정 루트 전체 규칙')*100).toFixed(1)}%`,`복귀 여유 중앙값 ${vk('고정 루트 복귀 여유 중앙값')}분, 하위 5% ${vk('고정 루트 복귀 여유 하위')}분`,`최적 방문 집합 유지율 ${vk('최적 방문집합')} (재최적화 20회)`,'→ 해운대·동래는 선택 구간, 승선 2시간 전 복귀 알림']);
// 10 분산
x=s('모두 같은 루트면 줄이 길어진다 — 나눠 보내자','결과 ③ 분산');
im(x,'그림6_기준선비교_분산효과.png',{x:0.5,y:1.6,w:7.6,h:4.9});
const dl=(r)=>r?`${r['배정']}: ${r['그룹 평균 줄대기(분)']}분, 위반 ${r['규칙 위반 그룹']}/6`:'';
x.addText([{text:'+4분 가정\n',options:{bold:true}},{text:d4.map(dl).join('\n')+'\n\n'},{text:'+8분 가정\n',options:{bold:true}},{text:d8.map(dl).join('\n')+'\n\n→ 혼잡이 크면 노드 확충 필요'+(dispNew?'':'\n(v2 노드 재계산 전 결과)')}],{x:8.3,y:1.7,w:4.6,h:4.8,fontFace:F,fontSize:14,valign:'top'});
// 11 실행
x=s('실행 계획과 한계','다음 단계');
bl(x,['부산항만공사: 하선 안내 QR → 하선 시각·승선 마감 맞춤 루트','상인회: 줄·브레이크 정보 제공, 그룹 분산 배정으로 쏠림 완화','영업·좌표 13곳은 부산시 공공데이터, 줄 대기는 공개 데이터 없음 → 현장 측정','수요점수 범주 단위 → 리뷰로 가게 단위 확장','일 단위 카드 자료 확보 시 기항일 효과 검증(차이-속-차이)']);
p.writeFile({fileName:R+'05_문서/3주차_발표자료.pptx'}).then(()=>console.log('deck ok, dispersion v2:',dispNew));
