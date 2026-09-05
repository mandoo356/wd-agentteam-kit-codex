// Codex 공식 hooks.json용 작업 기록·자동 저장·위험 작업 차단.
// 보조 안전장치이며 OS 보안 경계가 아니다. /hooks에서 신뢰한 뒤 사용한다.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const norm = s => String(s).replaceAll('\\', '/').toLowerCase();
const locked = ['.codex/hooks/', '.codex/hooks.json', '점검.py', 'configure_hooks.ps1'];
const protectedPaths = ['.codex/', '.agents/', 'workspace/memory/', 'slack-server/.env', 'office/company.config.ts', 'agents.md', '.gitignore'];
const inside = (p, list) => list.some(x => x.endsWith('/') ? p.startsWith(x) : p === x);
export function redact(s) {
  return String(s).replace(/(?:xox[baprs]-|xapp-|sk-)[A-Za-z0-9_-]+/g, '[비밀키 숨김]')
    .replace(/((?:token|password|secret|api[_-]?key)\s*[:=]\s*)[^\s,;]+/gi, '$1[숨김]');
}
export function journal(root, line) {
  const now = new Date();
  const day = [now.getFullYear(), String(now.getMonth()+1).padStart(2,'0'), String(now.getDate()).padStart(2,'0')].join('-');
  const dir = path.join(root, 'workspace', '기록');
  fs.mkdirSync(dir, {recursive:true});
  fs.appendFileSync(path.join(dir, `작업기록_${day}.md`), `- ${now.toLocaleTimeString('ko-KR')} ${redact(line).replaceAll('\n',' ').slice(0,600)}\n`, 'utf8');
}
function relative(root, p, cwd=root) {
  const absolute = path.resolve(cwd, p);
  const result = norm(path.relative(root, absolute));
  if (result.startsWith('../') || path.isAbsolute(result)) return null;
  return result;
}
export function judge(data, root=ROOT) {
  const tool = data.tool_name || '';
  const input = data.tool_input || {};
  const command = typeof input === 'string' ? input : String(input.command ?? input.cmd ?? '');
  const cwd = input.workdir || data.cwd || root;
  if (tool === 'apply_patch') {
    const entries = [...command.matchAll(/^\*\*\* (Add File|Update File|Delete File|Move to): (.+)$/gm)];
    if (!entries.length) return '패치 형식을 확인할 수 없어 차단했습니다.';
    for (const [, action, p] of entries) {
      const r = relative(root, p.trim(), cwd);
      if (r === null) return '스타터킷 바깥 원본 자료 수정은 터미널에서 확인하세요.';
      if (inside(r, locked)) return '채점표·안전장치 수정은 강사가 직접 진행합니다.';
      if (action === 'Delete File' || action === 'Move to') return '삭제·이동은 대상과 백업을 검토한 뒤 터미널에서 직접 실행하세요.';
      if (inside(r, protectedPaths) && fs.existsSync(path.resolve(cwd,p))) return '기존 직원·스킬·규약 변경은 터미널에서 확인하세요.';
      if (action === 'Add File' && fs.existsSync(path.resolve(cwd,p))) return '기존 파일 전체 덮어쓰기를 차단했습니다.';
    }
  } else if (['Bash','exec_command','shell','shell_command'].includes(tool)) {
    if (/(?:^|[\s;&|(])(?:format\s+[a-z]:|(?:diskpart|Format-Volume|Clear-Disk|Initialize-Disk|bcdedit)\b)/i.test(command)) return '디스크·시스템 변경은 차단합니다.';
    if (/(?:^|[\s;&|(])(?:rm|del|erase|rmdir|rd|Remove-Item|Move-Item|mv)\b|\b(?:os\.(?:remove|unlink|rmdir)|shutil\.(?:rmtree|move)|fs\.(?:rm|rmSync|unlink|unlinkSync))\s*\(|\.(?:unlink|rmdir)\s*\(/i.test(command)) return '삭제·이동 명령은 백업 후 사람이 터미널에서 직접 실행하세요.';
    if (/\bgit\s+(?:(?:-C|-c)\s+\S+\s+)*(?:checkout|restore|reset|clean|rm|stash|push|branch\s+-[dD])\b/i.test(command)) return '되돌리기·삭제·외부 배포 명령은 사람이 터미널에서 검토하세요.';
    if (/(?<!>)>(?!>)|\b(?:Set-Content|Out-File|Copy-Item|Add-Content|cp|tee)\b|\b(?:write_text|write_bytes|writeFile|writeFileSync|appendFile|appendFileSync)\s*\(|\bopen\s*\([^\n]*[,=]\s*['"][wax]/i.test(command)) return '셸로 파일을 덮어쓰지 마세요. 일반 문서는 apply_patch로 편집하고 보호 파일은 사람이 터미널에서 확인합니다.';
  } else if (/mcp/i.test(tool) && /write|edit|delete|remove|move|patch/i.test(tool)) {
    return '외부 파일 변경 도구는 이 과정의 검토 대상입니다. 일반 파일 편집은 apply_patch를 사용하세요.';
  }
  return '';
}
const git = (root, args) => {
  const r = spawnSync('git', args, {cwd:root,encoding:'utf8',windowsHide:true,timeout:25000});
  if (r.error || r.status !== 0) throw new Error(r.error?.message || r.stderr || 'git 실패');
  return r.stdout;
};
export function autosave(root=ROOT) {
  // 다른 저장소/상위 과정에 커밋하지 않는다. 기존 staged 변경도 건드리지 않는다.
  if (!fs.existsSync(path.join(root,'.git'))) return 'Git 저장소 없음';
  if (path.resolve(git(root,['rev-parse','--show-toplevel']).trim()) !== path.resolve(root)) return '상위 저장소 저장 제외';
  if (git(root,['diff','--cached','--name-only']).trim()) return '수동 스테이징이 있어 자동 저장 생략';
  const lock = path.join(root,'.git','wd-autosave.lock');
  let fd;
  try { fd=fs.openSync(lock,'wx'); } catch { return '다른 자동 저장 진행 중'; }
  try {
    // 결과·직원·규약만 저장. 열쇠·로그인 상태·프로그램 캐시는 수집하지 않는다.
    const names = git(root,['ls-files','-co','--exclude-standard','-z']).split('\0').filter(Boolean);
    const safe = [...new Set(names)].filter(p => {
      const n=norm(p);
      return inside(n,['workspace/결과물/','workspace/memory/','workspace/inbox/','.codex/agents/','.agents/skills/','office/company.config.ts','agents.md'])
        && !/(^|\/)(\.env(?:\..*)?|auth\.json|.*token.*|.*secret.*|.*password.*|node_modules|__pycache__)(\/|$)|\.(pem|key|pfx|pyc)$/i.test(n)
        && (!fs.existsSync(path.join(root,p)) || (fs.statSync(path.join(root,p)).isFile() && fs.statSync(path.join(root,p)).size < 20*1024*1024));
    });
    if (!safe.length) return '저장 대상 없음';
    for (let i=0;i<safe.length;i+=40) git(root,['add','-A','--',...safe.slice(i,i+40)]);
    const changed = git(root,['diff','--cached','--name-only']).trim();
    if (!changed) return '변경 없음';
    git(root,['-c','user.name=에이전트팀 자동저장','-c','user.email=autosave@agent-team.local','commit','-q','-m',`자동저장 ${new Date().toISOString()}`]);
    const sha=git(root,['rev-parse','--short','HEAD']).trim();
    return `자동 저장 지점 ${sha} (${changed.split('\n').length}파일)`;
  } finally { fs.closeSync(fd); fs.unlinkSync(lock); }
}
export function handle(data, root=ROOT) {
  const event=data.hook_event_name;
  if (event === 'PreToolUse') {
    const reason=judge(data,root);
    if (reason) {
      journal(root,`차단 [${data.tool_name}] ${reason}`);
      return {hookSpecificOutput:{hookEventName:event,permissionDecision:'deny',permissionDecisionReason:(process.env.WD_CHANNEL==='slack'?'[슬랙] ':'')+reason+' 다른 도구나 스크립트로 우회하지 마세요.'}};
    }
  } else if (event === 'UserPromptSubmit') {
    // 개인정보·열쇠가 있을 수 있어 요청 원문은 기록하지 않는다.
    journal(root,`요청 접수 [${process.env.WD_CHANNEL || '터미널'}]`);
  } else if (event === 'PostToolUse') {
    const inp=data.tool_input || {};
    const cmd=String(inp.command || inp.cmd || '');
    const files=data.tool_name==='apply_patch' ? [...cmd.matchAll(/^\*\*\* (?:Add File|Update File|Delete File): (.+)$/gm)].map(m=>m[1]).join(', ') : '';
    journal(root,`도구 종료 [${data.tool_name}] ${files}`);
  } else if (event === 'Stop') {
    const result=autosave(root); journal(root,result);
  } else if (event === 'SessionStart') {
    journal(root,'Codex 훅 실행 확인');
  }
  return null;
}
if (process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  let data;
  try {
    data=JSON.parse(fs.readFileSync(0,'utf8').replace(/^\uFEFF/,''));
    const result=handle(data); if(result) process.stdout.write(JSON.stringify(result));
  } catch(e) {
    try { journal(ROOT,`안전장치 오류: ${e.message}`); } catch {}
    if (!data || data.hook_event_name==='PreToolUse') {
      process.stderr.write('안전장치 검사 실패로 실행을 차단했습니다. 강사에게 점검을 요청하세요.'); process.exitCode=2;
    } else { process.stdout.write(JSON.stringify({systemMessage:`작업 기록·자동 저장 실패: ${redact(e.message)}`})); }
  }
}
