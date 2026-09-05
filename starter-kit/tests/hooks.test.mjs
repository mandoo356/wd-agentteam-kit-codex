import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {judge,autosave,handle,redact} from '../.codex/hooks/runtime.mjs';
const temp=()=>fs.mkdtempSync(path.join(os.tmpdir(),'wd-hooks-'));
const put=(r,p,s='시험')=>{const f=path.join(r,p);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,s)};
const git=(r,...args)=>{const p=spawnSync('git',args,{cwd:r,encoding:'utf8',windowsHide:true});assert.equal(p.status,0,p.stderr);return p.stdout.trim()};
// 삭제 범위를 OS TEMP 내 이번 시험 폴더로 한정한다.
const clean=r=>{assert.ok(path.resolve(r).startsWith(path.resolve(os.tmpdir())+path.sep));assert.ok(path.basename(r).startsWith('wd-hooks-'));fs.rmSync(r,{recursive:true,force:true})};
for(const command of ['del sample.txt','Remove-Item -LiteralPath sample.txt','git reset --hard','git restore sample.txt','git push origin main','Set-Content x y','echo hi > x','format C:','shutil.rmtree("a")','fs.unlinkSync("a")']) {
  test(`위험 명령 차단: ${command}`,()=>assert.ok(judge({tool_name:'Bash',tool_input:{command}})));
}
test('읽기 허용',()=>assert.equal(judge({tool_name:'Bash',tool_input:{command:'git status --short'}}),''));
test('패치: 일반 수정·새 직원 허용, 기존 규약·채점표·삭제 차단',()=>{
 const r=temp();try{
 put(r,'workspace/결과물/보고.md');put(r,'workspace/memory/facts.md');
 for(const [action,p,allowed] of [['Update File','workspace/결과물/보고.md',true],['Add File','.codex/agents/staff1.toml',true],['Update File','workspace/memory/facts.md',false],['Update File','점검.py',false],['Delete File','workspace/결과물/보고.md',false],['Add File','workspace/결과물/보고.md',false],['Add File','../outside.txt',false]]) {
   assert.equal(judge({cwd:r,tool_name:'apply_patch',tool_input:{command:`*** Begin Patch\n*** ${action}: ${p}\n*** End Patch`}},r)==='',allowed,p);
 }
 }finally{clean(r)}
});
test('원문 미기록·한글 파일 로그·키 마스킹',()=>{const r=temp();try{
 handle({hook_event_name:'UserPromptSubmit',prompt:'password=VERY_PRIVATE'},r);
 handle({hook_event_name:'PostToolUse',tool_name:'apply_patch',tool_input:{command:'*** Update File: workspace/결과물/한글.md'}},r);
 const d=path.join(r,'workspace/기록');const s=fs.readFileSync(path.join(d,fs.readdirSync(d)[0]),'utf8');assert.ok(s.includes('한글.md'));assert.ok(!s.includes('VERY_PRIVATE'));assert.ok(!redact('token=ABC xoxb-12345678').includes('12345678'));
 }finally{clean(r)}});
test('자동저장: 결과만 커밋, 비밀 제외, 무변경·수동 staged 보존',()=>{const r=temp();try{
 git(r,'init','-q');put(r,'workspace/결과물/결과.md');put(r,'slack-server/.env','SECRET');put(r,'workspace/결과물/.env','SECRET');
 assert.match(autosave(r),/자동 저장 지점/);const files=git(r,'ls-tree','-r','--name-only','HEAD');assert.ok(!files.includes('.env'));
 const head=git(r,'rev-parse','HEAD');assert.equal(autosave(r),'변경 없음');assert.equal(git(r,'rev-parse','HEAD'),head);
 put(r,'manual.txt');git(r,'add','manual.txt');put(r,'workspace/결과물/결과.md','수정');assert.match(autosave(r),/수동 스테이징/);assert.equal(git(r,'diff','--cached','--name-only'),'manual.txt');
 }finally{clean(r)}});
test('Git 초기화 전에는 자동 커밋 생략',()=>{const r=temp();try{assert.equal(autosave(r),'Git 저장소 없음')}finally{clean(r)}});
