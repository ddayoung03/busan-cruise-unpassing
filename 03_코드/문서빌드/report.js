// 3주차 보고서 생성: node report.js  (docx 패키지 필요). 수치는 02_정제데이터 CSV에서 읽는다.
const fs=require('fs');const D=require('docx');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,Table,TableRow,TableCell,WidthType,ShadingType,ImageRun,AlignmentType,LevelFormat}=D;
const R='C:/Users/PTY/Desktop/지산학아이디어톤/';const F='맑은 고딕';
const csv=f=>{const L=fs.readFileSync(R+'02_정제데이터/'+f,'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/);const H=L[0].split(',');
  return L.slice(1).map(l=>{const c=[];let cur='',q=false;for(const ch of l){if(ch=='"')q=!q;else if(ch==','&&!q){c.push(cur);cur=''}else cur+=ch}c.push(cur);return Object.fromEntries(H.map((h,i)=>[h,c[i]]))})};
const p=(t,o={})=>new Paragraph({spacing:{after:120},children:[new TextRun({text:t,font:F,size:21,...o})]});
const b=t=>new Paragraph({numbering:{reference:'bl',level:0},spacing:{after:60},children:[new TextRun({text:t,font:F,size:21})]});
const h=(t,l=HeadingLevel.HEADING_1)=>new Paragraph({heading:l,children:[new TextRun({text:t,font:F})]});
const W=9026;
const tbl=(rows,ws)=>new Table({width:{size:ws.reduce((a,b)=>a+b,0),type:WidthType.DXA},columnWidths:ws,rows:rows.map((r,i)=>new TableRow({children:r.map((c,j)=>new TableCell({width:{size:ws[j],type:WidthType.DXA},shading:i==0?{type:ShadingType.CLEAR,fill:'1F4E79',color:'auto'}:undefined,margins:{top:60,bottom:60,left:80,right:80},children:[new Paragraph({children:[new TextRun({text:String(c),font:F,size:18,bold:i==0,color:i==0?'FFFFFF':'000000'})]})]}))}))});
const img=(f,w=440,hgt=250)=>new Paragraph({alignment:AlignmentType.CENTER,children:[new ImageRun({type:'png',data:fs.readFileSync(R+'04_그림/'+f),transformation:{width:w,height:hgt}})]});
const cap=t=>new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:200},children:[new TextRun({text:t,font:F,size:18,italics:true})]});
const hs={run:{font:F,bold:true,color:'1F4E79'},paragraph:{keepNext:true}};

// ---- 수치 읽기 ----
const short=s=>s.split(' → ').map(x=>x.replace(/\(.*?\)/g,'').trim()).join(' → ');
const RT=csv('루트결과_1118_B.csv');const top=s=>RT.find(r=>r['시나리오'].startsWith(s)&&r['순위']=='1');const gr=s=>RT.find(r=>r['시나리오'].startsWith(s)&&r['순위'].startsWith('탐욕'));
const NV=csv('제약무시계획_1118_B.csv');const nv=s=>NV.find(r=>r['시나리오'].startsWith(s));
const nvViol=r=>Object.keys(r).filter(k=>k.startsWith('위반:')).reduce((a,k)=>a+(+r[k]),0);
const VD=Object.fromEntries(csv('검증_1118_B.csv').map(r=>[r['지표'],+r['값']]));const vk=k=>VD[Object.keys(VD).find(x=>x.startsWith(k))];
const DF=csv('분산효과_1118_B.csv');
const newer=(f,ref)=>fs.statSync(R+'02_정제데이터/'+f).mtimeMs>fs.statSync(R+'02_정제데이터/'+ref).mtimeMs;
const dispNew=newer('분산효과_1118_B.csv','food_nodes_1118_B.csv');
const dispNote=dispNew?'':' [주의: 이 표는 노드 변경(v2) 전 16노드 모델 결과다. v2 재계산은 시간 문제로 하지 못했다.]';
const SP=csv('확산지수_모델_1118_B.csv');const sp=s=>SP.find(r=>r['대상'].startsWith(s))['원도심 밖 지출비중%'];
const S1=top('S1'),G1=gr('S1'),N1=nv('S1');

const L0=1900,R0=7126;
const lab=t=>new TableCell({width:{size:L0,type:WidthType.DXA},shading:{type:ShadingType.CLEAR,fill:'DCE6F1',color:'auto'},verticalAlign:'center',margins:{top:80,bottom:80,left:100,right:100},children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:t,font:F,size:21,bold:true})]})]});
const val=kids=>new TableCell({width:{size:R0,type:WidthType.DXA},margins:{top:100,bottom:100,left:120,right:120},children:kids});
const row=(t,kids)=>new TableRow({children:[lab(t),val(kids)]});
const team=tbl([['연번','단과대학','학과(전공)','학번','성명'],...[1,2,3,4,5].map(i=>[String(i),'','','',''])],[800,1600,1800,1400,1300]);
const doc=new Document({styles:{default:{
 title:{run:{font:F,size:32,bold:true},paragraph:{spacing:{before:0,after:200},keepNext:true}},
 heading3:{run:{font:F,size:21,bold:true,color:'1F4E79'},paragraph:{spacing:{before:160,after:80},keepNext:true}}}},
 numbering:{config:[{reference:'bl',levels:[{level:0,format:LevelFormat.BULLET,text:'•',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:300,hanging:200}}}}]}]},
 sections:[{properties:{page:{margin:{top:1134,bottom:1134,left:1134,right:1134}}},children:[
 new Paragraph({heading:HeadingLevel.TITLE,alignment:AlignmentType.CENTER,children:[new TextRun({text:'아이디어톤 3주차_ 팀별 활동 보고서',font:F})]}),
 new Table({width:{size:L0+R0,type:WidthType.DXA},columnWidths:[L0,R0],rows:[
  row('팀명',[p('크루즈 미식 루트')]),
  row('팀 구성',[team]),
  new TableRow({children:[new TableCell({columnSpan:2,width:{size:L0+R0,type:WidthType.DXA},shading:{type:ShadingType.CLEAR,fill:'1F4E79',color:'auto'},margins:{top:100,bottom:100,left:120,right:120},children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:'3주차 팀 활동 – 데이터 분석 보고서 작성 및 최종 결과물 산출',font:F,size:22,bold:true,color:'FFFFFF'})]})]})]}),
  row('발표 주제',[
 p('“면세점에서 멈추지 않게” — 크루즈 승객의 상륙 시간·영업시간·줄대기·위장 용량·승선 마감을 함께 계산해, 외국인이 실제로 원하는 부산 음식을 지각 없이 먹게 하는 루트 최적화와 혼잡 분산.'),
  ]),
  row('활용 데이터',[
 tbl([['데이터','출처','쓰임'],
 ['부산항 크루즈 입출항 신고정보(2023~2026.7, 648건)','공공데이터포털 15164568','승객 수·기항 시간·시나리오'],
 ['외국인 방문자·카드소비(구·월·업종, 2025.10~2026.9)','한국관광데이터랩 외래객 지역별 방한현황','쇼핑 쏠림(패싱) 근거, 원도심 vs 비교구'],
 ['YouTube 댓글 1,792개(영·중·일 1,492개)','YouTube Data API v3','외국인 수요점수(음식 범주 언급 수)'],
 ['대만 관광객 선호 음식 설문','부산관광공사 보도','국적 가중치 예시(돼지국밥 66.9%)'],
 ['부산맛집정보 서비스(가게 536곳)','공공데이터포털 15063472(부산시)','노드 13곳의 실제 영업시간·브레이크·좌표'],
 ['음식 노드 19곳 + 터미널 2곳','13곳 부산시 공공데이터, 시장·마을 6곳 추정','루트 후보'],
 ['이동시간 행렬','OSRM 도로 경로 + 도보 모형','택시·도보 이동 분'],
 ['제주 크루즈 관광객 실태조사 2023','공공데이터포털','지출 구성 참고(다른 모집단)']],[2599,1987,2314]),
 p('[확인 필요] 상륙 승객 수(법무부 통계)는 없다. 데이터랩 금액 단위는 화면 표기와 대조하지 못해 비중·증가율만 썼다.',{color:'C00000'}),
  ]),
  row('분석 도구',[
 p('Python(Colab 기본 라이브러리만): pandas·numpy, 분기한정으로 직접 구현한 OPTW(시간창 오리엔티어링), matplotlib, folium. 수업 경주 노트북의 탐욕 코스·folium·데이터 병합 방식을 기준선과 틀로 썼다.'),
  ]),
  row('분석 목적',[
 b('부산 패싱의 실태를 자료로 보인다: 승객 증가 대비 소비가 어디로 가는가.'),
 b('외국인 수요 기반으로, 상륙 시간 안에 지각 없이 최대 만족을 주는 루트를 찾는다.'),
 b('수업 탐욕법·무계획 대비 이득과 위험을 같은 조건에서 수치로 보인다.'),
 b('여러 그룹이 몰릴 때의 혼잡과 분산 배정 효과, 원도심 밖 확산을 추정한다.'),
  ]),
  row('분석 개요',[
 h('결론 먼저',HeadingLevel.HEADING_3),
 b('크루즈 승객은 급증했지만(2026년 1~7월 403,188명, 전년 대비 +175.7%) 부산 소비는 면세 쇼핑에 쏠린다. 원도심 중구의 외국인 카드소비 중 쇼핑업이 약 66%, 식음료는 월 19~23%다(한국관광데이터랩). 배에서 내려 면세점만 들르고 돌아가는 “부산 패싱”이다.'),
 b('외국인이 실제로 말하는 부산 음식은 해산물·회(댓글 86건), 면(39), 시장·길거리 음식(38), 고기(18) 순이다. 우리는 역사 음식 대신 이 수요를 점수로 써서, 하선 시간 안에 배를 놓치지 않고 먹을 수 있는 루트를 최적화했다.'),
 b(`북항 당일 기항(S1) 최적 루트는 ${short(S1['루트'])}로, 목적함수 ${S1['목적함수']}(수업식 탐욕법 ${G1['목적함수']})이며 ${S1['복귀']}에 복귀한다. 7곳 중 ${S1['원도심 밖 노드']}곳이 원도심 밖이라 소비가 부산 전역으로 퍼진다(원도심 밖 지출 ${sp('S1')}%).`),
 b(`대기 ±30%·이동 ±20% 1,000회 모의에서 지각 확률 ${(vk('고정 루트 복귀 지각')*100).toFixed(1)}%, 규칙 준수 ${(vk('고정 루트 전체 규칙')*100).toFixed(1)}%. 다만 복귀 여유 하위 5%가 ${vk('고정 루트 복귀 여유 하위')}분으로 빠듯하다 → 해운대·동래 구간은 승선 2시간 전 ‘복귀 알림’이 필요하다.`),
 b(`규칙을 무시한 계획은 ${N1['방문 수']}곳을 돌고 ${N1['복귀']}에 복귀(지각)하며 위반 ${nvViol(N1)}건 — 앱이 시간·줄·배 시간을 함께 계산해야 하는 이유다.`),
 b('원도심 외국인 식음료 소비는 2025.10→2026.7 +76%로 비교 3구(+57%)보다 빨리 늘었다. 크루즈 급증기와 겹치지만 월별 상관은 약해 연관으로만 본다.'),
 h('5-1. 문제: 승객은 늘고, 소비는 면세점에서 멈춘다',HeadingLevel.HEADING_3),
 tbl([['기항 유형','항차','승객','상륙 가능 중앙값'],['8시간 이하','66','62,758','4.75h'],['8~13시간','451','759,444','8.47h'],['오버나잇','94','111,258','14.33h']],[1987,1528,1681,1704]),
 img('그림5_월별승객.png'),cap('그림 1. 월별 부산항 크루즈 승객(신고 전체)'),
 p('승객의 81%가 8~13시간 기항선이고 상륙 가능 시간 중앙값은 약 8.5시간이다. 데이터랩에서 중구 외국인 카드소비는 쇼핑업(면세점 포함)이 약 66%를 차지하고, 식음료는 2025.10 기준 19.1%였다. 2025년 신고 합계 249,541명은 보도치 257,000명과 2.9% 차이가 있다(미해명).'),
 tbl([['구분','2025.10','2026.7','증가'],['원도심 3구 식음료 (지수)','100','176.0','+76%'],['비교 3구 식음료 (지수)','100','156.9','+57%'],['원도심 소비 중 식음료 비중','21.5%','26.5%','+5.0%p']],[2599,1376,1376,1549]),
 p('원도심 = 중·동·영도구, 비교 = 서·부산진·해운대구. 같은 기간 크루즈 승객은 월 2.2만→8.0만 명. 겹치는 달이 10개뿐이라 월별 상관(r=0.14)은 약하다.'),
 h('5-2. 수요: 외국인이 말하는 부산 음식',HeadingLevel.HEADING_3),
 tbl([['범주(댓글 언급)','건수','수요점수'],['해산물·회','86','100'],['면(밀면·완당)','39','91'],['시장·길거리','38','91'],['고기(갈비)','18','83'],['국밥','18','83'],['치킨·카페','10','77'],['어묵','2','62']],[3057,1528,2315]),
 p('수요점수 = 50 + 50·ln(1+언급)/ln(87). 언어별로 보면 영어권은 회·곰장어, 중국어권은 돼지국밥, 일본어권은 회 언급이 많았다(표본이 작아 참고). 대만 설문(돼지국밥 66.9%)은 국적 가중치 예시(S6)로만 쓴다.'),
 h('5-3. 모델: 시간창 오리엔티어링(OPTW)',HeadingLevel.HEADING_3),
 b('목적: Σ(수요점수 × 국적 가중치) − 0.8 × (줄대기 + 이동).'),
 b('제약: 승선 30분 전 복귀, 영업·브레이크타임, 줄대기 = 피크 × 시간대 혼잡 × 크루즈 가중 1.6, 위장 용량 4(100분에 1 소화), 식사 간격 120분·식사 시간창, 최대 7곳.'),
 b('풀이: 분기한정으로 최적해 보장(수업 탐욕법은 보장 없음). 노드 21개에서 회당 약 2분.'),
 tbl([['시나리오','OPTW','탐욕법','복귀','원도심 밖'],...['S1','S2','S3','S4','S5','S6'].map(s=>{const t=top(s),g=gr(s);return [t['시나리오'],t['목적함수'],g['목적함수'],t['복귀'],t['원도심 밖 노드']+'곳']})],[2522,993,993,1070,1322]),
 p(`S1 최적 루트: ${short(S1['루트'])}. 제약 무시 계획(S1)은 ${N1['방문 수']}곳·${N1['복귀']} 복귀·위반 ${nvViol(N1)}건.`),
 h('5-3-2. 실제 루트 시간표 (S1 북항 당일 기항)',HeadingLevel.HEADING_3),
 img('그림8_S1루트지도.png',460,230),cap('그림 2. S1 최적 루트 지도와 시간표'),
 tbl([['#','장소','이동','도착','줄','먹기 시작','떠남'],...csv('루트시간표_1118_B.csv').filter(r=>r['시나리오'].startsWith('S1')).map(r=>[r['순서'],r['장소'],r['이동']?r['이동']+' '+r['이동(분)']+'분':'',r['도착'],r['줄(분)']?r['줄(분)']+'분':'',r['먹기 시작'],r['떠남']||r['메뉴·가격']])],[382,2293,840,688,611,840,1246]),
 p('6개 시나리오의 시간표 전체는 02_정제데이터/루트시간표_1118_B.csv, 인터랙티브 지도는 04_그림/루트지도_1118_B.html. 시간표는 최적화와 같은 규칙으로 다시 계산해 목적함수가 일치한다(S1 504.6).'),
 h('5-4. 검증',HeadingLevel.HEADING_3),
 tbl([['지표','값'],['최적 방문집합 유지율(대기 ±30%, 재최적화 20회)',vk('최적 방문집합')],['고정 루트 전체 규칙 준수율(1,000회)',(vk('고정 루트 전체 규칙')*100).toFixed(1)+'%'],['고정 루트 복귀 지각 확률',(vk('고정 루트 복귀 지각')*100).toFixed(1)+'%'],['복귀 여유 중앙값 / 하위 5%',vk('고정 루트 복귀 여유 중앙값')+'분 / '+vk('고정 루트 복귀 여유 하위')+'분']],[4586,2314]),
 p('원도심 밖까지 가면서 여유가 줄었다(이전 원도심 루트는 하위 5% 41.5분). 실행 시에는 해운대·동래 구간을 선택형으로 두고 승선 2시간 전 알림을 준다.'),
 h('5-5. 혼잡 분산과 확산',HeadingLevel.HEADING_3),
 tbl([['겹침 100명당 추가대기','배정','평균 줄대기(분)','위반 그룹'],...DF.map(r=>[r['겹침당 추가대기(분)'],r['배정'],r['그룹 평균 줄대기(분)'],r['규칙 위반 그룹']+'/6'])],[1834,1681,1681,1704]),
 p('같은 배 6그룹(10분 간격, 100명씩)을 한 루트로 보내면 줄이 길어지고, 그룹마다 다른 루트로 나누면 줄어든다. 그룹을 차례로 배정하는 방식이라 결과가 배정 순서에 따라 달라진다(+4분 가정에서 2그룹, +8분 가정에서 0그룹 위반). 2026.5.8 실제 2척 동시 기항일(앱 이용 10% 가정)에는 8그룹 중 3그룹(155명)이 규칙을 지키지 못해 가게 확충과 동시 배정이 필요하다. 분산은 시간 분산만 반영하고 가게 좌석 수는 넣지 않았다.'+dispNote),
 h('6. 한계와 다음 단계',HeadingLevel.HEADING_3),
 b('영업시간·좌표는 13곳이 부산시 공공데이터 실제 값이다(이전 추정과 비교: 원조18번완당 마감 22:00→19:30 등, 노드_실데이터대조_1118_B.csv). 시장·마을 6곳과 모든 노드의 줄 대기 시간은 공개 데이터가 없어 추정 → 현장 측정 필요.'),
 b('수요점수는 범주 단위(같은 범주 = 같은 점수)이고 댓글 표본이 작다 → 구글 리뷰 등으로 가게 단위 점수로 확장.'),
 b('데이터랩은 월 단위라 기항일/비기항일 비교 불가 → 일 단위 카드 자료 확보 시 차이-속-차이.'),
 b('실행: 부산항만공사 하선 안내 QR + 상인회 줄·브레이크 정보 연동으로 시범 운영.'),
  ]),
  row('일자별 팀 활동 사진',[p('※ 팀 활동 진행 모습 촬영 사진 1장 이상 첨부',{color:'888888'}),p('(팀 전체가 찍힌 사진, 화상회의 참여자 화면 전체 캡처 등)',{color:'888888'}),p(''),p(''),p(''),p('2026. 11. 20.(금)',{bold:true})]),
 ]}),
 p('※ 개발 결과물에 따른 저작권, 특허권, 수익금, 기술이전료 등은 반드시 부산대학교에 귀속되어야 함',{size:18,color:'666666'}),
]}]});
Packer.toBuffer(doc).then(x=>{fs.writeFileSync(R+'05_문서/3주차_팀활동보고서.docx',x);console.log('report ok, dispersion v2:',dispNew)});
