# 통합 제출용 HWP(지산학 .hwp)의 3주차 서식 빈 칸을 채운다. 한컴오피스 한글(HWPFrame.HwpObject) 필요.
# 사용: powershell -ExecutionPolicy Bypass -File hwp_fill.ps1 <입력.hwp> <작업.json> <출력.hwp> [<출력.pdf>]
# 작업.json = [{ "label": "발표 주제", "items": [ {"t":"h","text":".."}, {"t":"p","text":".."}, {"t":"table","rows":[[..],[..]]}, {"t":"img","path":"..","w":150} ] }, ...]
param([string]$In, [string]$Ops, [string]$Out, [string]$Pdf = "")
$ErrorActionPreference = "Stop"
$h = New-Object -ComObject HWPFrame.HwpObject
try { $h.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule") | Out-Null } catch {}
$h.XHwpWindows.Item(0).Visible = $false
if (-not $h.Open($In, "HWP", "forceopen:true")) { throw "열기 실패: $In" }

function Find([string]$s) {
  $h.HAction.Run("MoveDocBegin") | Out-Null
  $p = $h.HParameterSet.HFindReplace
  $h.HAction.GetDefault("RepeatFind", $p.HSet) | Out-Null
  $p.FindString = $s; $p.Direction = 0; $p.IgnoreMessage = 1; $p.FindType = 1; $p.WholeWordOnly = 0
  if (-not $h.HAction.Execute("RepeatFind", $p.HSet)) { throw "못 찾음: $s" }
}
function Txt([string]$s) {
  $a = $h.CreateAction("InsertText"); $ps = $a.CreateSet(); $ps.SetItem("Text", $s); $a.Execute($ps) | Out-Null
}
function Para { Txt "`r`n" }   # BreakPara는 COM에서 동작하지 않아 줄바꿈 문자로 문단을 나눈다
function Left { $q = $h.HParameterSet.HParaShape; $h.HAction.GetDefault("ParagraphShape", $q.HSet) | Out-Null; $q.AlignType = 1; $h.HAction.Execute("ParagraphShape", $q.HSet) | Out-Null }   # 왼쪽 정렬
function Bold([string]$s) { $h.HAction.Run("CharShapeBold") | Out-Null; Txt $s; $h.HAction.Run("CharShapeBold") | Out-Null }
function Table($rows) {
  $r = $rows.Count; $c = $rows[0].Count
  $p = $h.HParameterSet.HTableCreation
  $h.HAction.GetDefault("TableCreate", $p.HSet) | Out-Null
  $p.Rows = $r; $p.Cols = $c; $p.WidthType = 1; $p.HeightType = 0   # 1 = 칸(문단) 너비에 맞춤
  $h.HAction.Execute("TableCreate", $p.HSet) | Out-Null
  for ($i = 0; $i -lt $r; $i++) {
    for ($j = 0; $j -lt $c; $j++) {
      $v = [string]$rows[$i][$j]
      if ($i -eq 0) { Bold $v } else { Txt $v }
      $h.HAction.Run("MoveRight") | Out-Null   # 칸 끝에서 오른쪽 = 다음 칸 (마지막 칸 다음은 표 밖)
    }
  }
}
function Img([string]$path, [double]$w) {
  Add-Type -AssemblyName System.Drawing
  $im = [System.Drawing.Image]::FromFile($path); $hh = [math]::Round($w * $im.Height / $im.Width, 1); $im.Dispose()
  $ctrl = $h.InsertPicture($path, $true, 1, $false, $false, 0, $w, $hh)
  if ($null -eq $ctrl) { "그림 넣기 실패: $path"; return }
  $ps = $ctrl.Properties; $ps.SetItem("TreatAsChar", 1); $ctrl.Properties = $ps   # 글자처럼 취급(칸 안에 고정)
}

$jobs = [IO.File]::ReadAllText($Ops, [Text.Encoding]::UTF8) | ConvertFrom-Json
foreach ($cell in $jobs) {
  Find $cell.label
  $h.HAction.Run("Cancel") | Out-Null       # 찾은 라벨 선택 해제 (안 하면 라벨이 덮어써짐)
  $h.HAction.Run("MoveLineEnd") | Out-Null
  $h.HAction.Run("MoveRight") | Out-Null    # 라벨 칸 끝에서 오른쪽 = 내용 칸 (TableRightCell은 찾기 직후 동작 안 함)
  $first = $true
  foreach ($it in $cell.items) {
    if (-not $first) { Para }
    Left
    $first = $false
    switch ($it.t) {
      "h"     { Bold $it.text }
      "p"     { Txt $it.text }
      "table" { Table $it.rows }
      "img"   { Img $it.path $it.w }
    }
  }
  "채움: " + $cell.label
}
if (-not $h.SaveAs($Out, "HWP", "")) { throw "저장 실패" }
if ($Pdf) { $h.SaveAs($Pdf, "PDF", "") | Out-Null }
"저장: $Out (쪽수 " + $h.PageCount + ")"
$h.Clear(1); $h.Quit()
