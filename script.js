// ── Config ────────────────────────────────────────────────────────────────────
// Since FastAPI serves both the API and the static files on the same origin,
// we use relative paths.
const API = 'http://localhost:8001';    // e.g. '' means same origin; set to 'http://localhost:8000' if separate

const DEFAULT_CODE = `#include <stdio.h>
int main() {
    char ch = 'A';
    if((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
        if(ch=='a'||ch=='e'||ch=='i'||ch=='o'||ch=='u'||
           ch=='A'||ch=='E'||ch=='I'||ch=='O'||ch=='U')
            printf("Vowel\\n");
        else
            printf("Consonant\\n");
    } else if(ch >= '0' && ch <= '9') {
        printf("Digit\\n");
    } else {
        printf("Special Character\\n");
    }
    return 0;
}`;

// Read the current source code from the editable textarea
function getSourceCode() {
  const ta = document.getElementById('sourceCode');
  return ta ? ta.value : DEFAULT_CODE;
}

// Live line counter
function updateLineCount() {
  const ta = document.getElementById('sourceCode');
  if (!ta) return;
  const lines = ta.value.split('\n').length;
  const el = document.getElementById('lineCount');
  if (el) el.textContent = lines + (lines === 1 ? ' line' : ' lines');
}

const phasesDone = [false, false, false, false, false, false];
const phaseNames = [
  'Lexical Analysis', 'Syntax Analysis', 'Semantic Analysis',
  'Intermediate Code Generation', 'Code Optimization', 'Target Code Generation'
];

// ── Renderers ─────────────────────────────────────────────────────────────────
function renderPhase(index, data) {
  const fns = [renderLexical, renderSyntax, renderSemantic,
    renderIntermediate, renderOptimization, renderTarget];
  return fns[index](data);
}

function renderLexical(d) {
  const colorMap = {
    keyword: '#cba6f7', identifier: '#89dceb', operator: '#fab387',
    punctuation: '#9399b2', literal: '#a6e3a1', number: '#f38ba8'
  };
  const labelMap = {
    keyword: 'Keyword', identifier: 'Identifier', operator: 'Operator',
    punctuation: 'Punctuation', literal: 'Literal', number: 'Number'
  };
  let html = `<div class="tokens-wrap">`;
  d.tokens.forEach((tok, i) => {
    html += `<span class="token token-${tok.type}" style="animation-delay:${Math.min(i * 15, 500)}ms"
               title="${labelMap[tok.type] || tok.type}">${esc(tok.text)}</span>`;
  });
  html += `</div><div style="margin-top:.9rem;display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:.5rem;">`;
  Object.entries(d.summary).forEach(([cls, cnt]) => {
    html += `<div style="display:flex;align-items:center;gap:.5rem;background:rgba(0,0,0,.2);border-radius:6px;padding:.4rem .6rem;">
      <div style="width:8px;height:8px;border-radius:50%;background:${colorMap[cls]};flex-shrink:0;"></div>
      <span style="font-size:.72rem;color:var(--text-muted);">${labelMap[cls]}</span>
      <span style="font-size:.78rem;font-weight:700;color:var(--text);margin-left:auto;">${cnt}</span>
    </div>`;
  });
  html += `</div><div style="margin-top:.7rem;font-size:.78rem;color:var(--text-muted);">
    Total tokens: <strong style="color:var(--text)">${d.total}</strong>
  </div>`;
  return html;
}

function renderSyntax(d) {
  const ch = d.checks;
  const po = ch.parentheses, br = ch.braces;
  const depthColor = ['#cba6f7', '#89dceb', '#a6e3a1', 'var(--text-dim)'];
  let html = `<div class="syntax-result ${d.valid ? 'valid' : 'invalid'}">
    <span>${d.valid ? '✅' : '❌'}</span>
    <span>${d.valid ? 'Syntax VALID — all brackets balanced' : 'Syntax ERROR — unbalanced brackets'}</span>
  </div>
  <div class="syntax-checks">
    <div class="check-item"><span class="check-label">Parentheses ( )</span>
      <span class="check-val ${po.balanced ? 'check-match' : 'check-mismatch'}">${po.open} open · ${po.close} close · ${po.balanced ? '✓ Balanced' : '✗ Mismatch'}</span></div>
    <div class="check-item"><span class="check-label">Braces { }</span>
      <span class="check-val ${br.balanced ? 'check-match' : 'check-mismatch'}">${br.open} open · ${br.close} close · ${br.balanced ? '✓ Balanced' : '✗ Mismatch'}</span></div>
    <div class="check-item"><span class="check-label">Semicolons ;</span>
      <span class="check-val check-match">${ch.semicolons} found · ✓ OK</span></div>
    <div class="check-item"><span class="check-label">Char literals</span>
      <span class="check-val check-match">${ch.char_literals} pairs · ✓ Paired</span></div>
  </div>
  <div style="margin-top:1rem;font-size:.78rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.5rem;">Abstract Syntax Tree</div>
  <div style="background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:.8rem 1rem;font-family:var(--mono);font-size:.78rem;">`;
  d.parse_tree.forEach((node, i) => {
    const indent = '&nbsp;&nbsp;&nbsp;'.repeat(node.depth);
    const conn = node.depth > 0 ? '└─ ' : '';
    const col = depthColor[Math.min(node.depth, depthColor.length - 1)];
    html += `<div style="animation:slideRight .3s ${i * 35}ms ease both;color:${col};">${indent}${conn}${esc(node.label)}</div>`;
  });
  html += `</div>`;
  return html;
}

function renderSemantic(d) {
  let html = `<table class="symbol-table">
    <thead><tr><th>#</th><th>Name</th><th>Kind</th><th>Type</th><th>Value</th><th>Scope</th><th>Line</th></tr></thead><tbody>`;
  d.symbol_table.forEach((s, i) => {
    const col = s.kind === 'function' ? '#fab387' : '#89dceb';
    html += `<tr>
      <td>${i + 1}</td><td style="font-weight:600">${esc(s.name)}</td>
      <td><span class="type-badge" style="color:${col};background:rgba(0,0,0,.2)">${esc(s.kind)}</span></td>
      <td><span class="type-badge">${esc(s.type)}</span></td>
      <td>${esc(s.value)}</td><td>${esc(String(s.scope))}</td><td>${esc(String(s.line))}</td>
    </tr>`;
  });
  html += `</tbody></table><div style="margin-top:1rem;font-size:.78rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:.5rem;">Type Checks</div>
  <div style="display:flex;flex-direction:column;gap:.3rem;">`;
  d.type_checks.forEach((c, i) => {
    html += `<div style="display:flex;align-items:center;gap:.6rem;font-size:.8rem;padding:.4rem .7rem;background:rgba(0,0,0,.2);border-radius:6px;animation:slideRight .3s ${i * 35}ms ease both;">
      <span style="color:${c.valid ? 'var(--success)' : 'var(--error)'};">${c.valid ? '✓' : '✗'}</span>
      <span style="font-family:var(--mono);color:#89dceb;">${esc(c.expr)}</span>
      <span style="color:var(--text-muted);margin-left:auto;font-size:.72rem;">${esc(c.lhs_type)} ${esc(c.op)} ${esc(c.rhs_type)}</span>
    </div>`;
  });
  html += `</div>`;
  if (d.errors.length === 0) {
    html += `<div style="margin-top:.8rem;display:flex;align-items:center;gap:.4rem;font-size:.82rem;">
      <span style="color:var(--success);">✅</span>
      <span style="color:var(--text-muted);">No type errors · No undeclared identifiers</span>
    </div>`;
  }
  return html;
}

function renderIntermediate(d) {
  const kws = new Set(['if', 'goto', 'return', '||', '&&']);
  let html = `<div class="tac-list">`;
  d.instructions.forEach((ins, i) => {
    const isLabel = ins.code.trim().endsWith(':') && !ins.code.includes('printf');
    let styled = esc(ins.code)
      .replace(/\b(if|goto|return)\b/g, '<span class="tac-op">$1</span>')
      .replace(/(\|\||&&)/g, '<span class="tac-op">$1</span>')
      .replace(/(L_\w+)/g, '<span style="color:#89dceb">$1</span>')
      .replace(/(&amp;&amp;|\|\|)/g, '<span class="tac-op">$&</span>')
      .replace(/(&#x27;[^&#]*&#x27;|&quot;[^&]*&quot;)/g, '<span class="tac-str">$1</span>');
    html += `<div class="tac-line" style="animation-delay:${Math.min(i * 30, 700)}ms;${isLabel ? 'margin-top:.5rem;border-left-color:rgba(137,220,235,.5);' : ''}">
      <span class="tac-num">${String(ins.n).padStart(2, '0')}.</span>
      <span class="tac-code">${styled}</span>
      ${ins.comment ? `<span style="margin-left:auto;font-size:.7rem;color:var(--text-muted);font-style:italic;">${esc(ins.comment)}</span>` : ''}
    </div>`;
  });
  html += `</div>`;
  return html;
}

function renderOptimization(d) {
  let html = `<div class="opt-result">`;
  d.optimizations.forEach((o, i) => {
    html += `<div class="opt-item" style="animation-delay:${i * 55}ms">
      <span class="opt-icon">${o.icon}</span>
      <span class="opt-text">${esc(o.description)}</span>
      <span class="opt-status ${o.applied ? 'opt-applied' : 'opt-skipped'}">${o.applied ? '✓ Applied' : '— Skipped'}</span>
    </div>`;
  });
  html += `</div>
  <div style="margin-top:1rem;padding:.7rem 1rem;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:8px;font-size:.82rem;">
    <strong style="color:#6ee7b7;">Optimized result:</strong>
    <span style="color:var(--text-muted);margin-left:.5rem;">${esc(d.optimized_result)}</span>
  </div>`;
  return html;
}

function renderTarget(d) {
  let html = `<div class="asm-list">`;
  d.instructions.forEach((line, i) => {
    if (!line.instr) { html += `<div style="height:5px;"></div>`; return; }
    const isLabel = line.instr.endsWith(':');
    const isComment = line.instr.startsWith(';');
    html += `<div class="asm-line" style="animation-delay:${Math.min(i * 22, 600)}ms;">
      <span class="asm-addr" style="${!line.addr ? 'opacity:0;' : ''}">${esc(line.addr || '')}</span>
      <span class="asm-instr" style="${isLabel ? 'color:#89dceb;font-weight:700;' : isComment ? 'color:#585b70;' : ''}">${esc(line.instr)}</span>
      ${line.arg && !isLabel && !isComment ? `<span class="asm-arg">${esc(line.arg)}</span>` : (line.arg ? `<span style="color:#a6e3a1;font-size:.8rem;">${esc(line.arg)}</span>` : '')}
      ${line.comment ? `<span class="asm-comment">${esc(line.comment)}</span>` : ''}
    </div>`;
  });
  html += `</div>
  <div style="margin-top:.8rem;display:flex;gap:1rem;flex-wrap:wrap;">
    <span style="font-size:.75rem;color:var(--text-muted);"><span style="color:#cba6f7;font-weight:700;">INSTR</span> Instruction</span>
    <span style="font-size:.75rem;color:var(--text-muted);"><span style="color:#a6e3a1;">ARG</span> Operand</span>
    <span style="font-size:.75rem;color:var(--text-muted);"><span style="color:#89dceb;font-weight:700;">LABEL:</span> Jump target</span>
  </div>`;
  return html;
}

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
}

// ── Run a single phase via API ────────────────────────────────────────────────
async function runPhase(index) {
  const stepEl = document.getElementById(`step-${index}`);
  const statusEl = document.getElementById(`status-${index}`);
  const bodyEl = document.getElementById(`body-${index}`);
  const btnEl = document.getElementById(`runPhase${index}`);
  const cardEl = document.getElementById(`phase-${index}`);

  stepEl.className = 'pipeline-step running';
  statusEl.textContent = '⏳';
  cardEl.classList.add('phase-active');
  bodyEl.innerHTML = `<div style="display:flex;align-items:center;gap:.8rem;color:var(--text-muted);font-size:.85rem;padding:1rem;">
    <div class="loading-spinner"></div><span>Calling backend…</span>
  </div>`;
  btnEl.disabled = true;

  try {
    const res = await fetch(`${API}/api/phase/${index}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: getSourceCode() }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    // Check for compilation error
    if (data.error) {
      bodyEl.innerHTML = `<div style="color:var(--error);padding:1.5rem;font-size:.85rem;font-weight:600;background:rgba(239,68,68,0.05);border-radius:8px;border:1px solid rgba(239,68,68,0.1);">
        ❌ ${esc(data.error)}
      </div>`;
      
      stepEl.className = 'pipeline-step error';
      statusEl.textContent = '❌';
      cardEl.classList.remove('phase-active');
      cardEl.classList.add('phase-error');
      btnEl.textContent = '❌ Error';
      btnEl.disabled = false;
      
      showError(data.error);
      return { success: false };
    }

    bodyEl.innerHTML = renderPhase(index, data);
  } catch (err) {
    bodyEl.innerHTML = `<div style="color:var(--error);padding:1rem;font-size:.85rem;">
      ❌ API error: ${esc(err.message)}<br>
      <span style="color:var(--text-muted);font-size:.78rem;">Make sure the FastAPI backend is running on port 8000.</span>
    </div>`;
    stepEl.className = 'pipeline-step error';
    statusEl.textContent = '❌';
    cardEl.classList.remove('phase-active');
    btnEl.disabled = false;
    return { success: false };
  }

  stepEl.className = 'pipeline-step done';
  statusEl.textContent = '✅';
  cardEl.classList.remove('phase-active');
  cardEl.classList.add('phase-done');
  btnEl.textContent = '✓ Done';
  btnEl.classList.add('done-btn');
  btnEl.disabled = false;
  phasesDone[index] = true;
  
  if (phasesDone.every(Boolean)) showFinalOutput();
  return { success: true };
}

function showError(msg) {
  const summary = document.getElementById('errorSummary');
  const msgEl = document.getElementById('errorMessage');
  msgEl.textContent = msg;
  summary.style.display = 'block';
  summary.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function markSkipped(index) {
  const stepEl = document.getElementById(`step-${index}`);
  const statusEl = document.getElementById(`status-${index}`);
  const bodyEl = document.getElementById(`body-${index}`);
  const btnEl = document.getElementById(`runPhase${index}`);
  const cardEl = document.getElementById(`phase-${index}`);

  stepEl.className = 'pipeline-step skipped';
  statusEl.textContent = '⏸';
  cardEl.classList.add('phase-skipped');
  bodyEl.innerHTML = `<div class="skipped-msg">Phase skipped due to errors in previous steps.</div>`;
  btnEl.textContent = 'Skipped';
  btnEl.disabled = true;
}

// ── Run All ───────────────────────────────────────────────────────────────────
document.getElementById('btnRunAll').addEventListener('click', async () => {
  document.getElementById('errorSummary').style.display = 'none';
  for (let i = 0; i < 6; i++) {
    if (!phasesDone[i]) {
      const res = await runPhase(i);
      if (!res.success) {
        // Halt further phases
        for (let j = i + 1; j < 6; j++) {
          markSkipped(j);
        }
        break;
      }
      await sleep(120);
    }
  }
});

// ── Reset ─────────────────────────────────────────────────────────────────────
document.getElementById('btnReset').addEventListener('click', () => {
  document.getElementById('errorSummary').style.display = 'none';
  for (let i = 0; i < 6; i++) {
    phasesDone[i] = false;
    const step = document.getElementById(`step-${i}`);
    step.className = 'pipeline-step';
    document.getElementById(`status-${i}`).textContent = '⏳';
    document.getElementById(`body-${i}`).innerHTML = `<div class="phase-placeholder">Click <strong>Run</strong> to execute this phase</div>`;
    const btn = document.getElementById(`runPhase${i}`);
    btn.textContent = 'Run ▶'; btn.classList.remove('done-btn'); btn.disabled = false;
    const card = document.getElementById(`phase-${i}`);
    card.classList.remove('phase-active', 'phase-done', 'phase-error', 'phase-skipped');
  }
  document.getElementById('outputSection').style.display = 'none';
});

// ── Pipeline click → scroll ───────────────────────────────────────────────────
document.querySelectorAll('.pipeline-step').forEach(step => {
  step.addEventListener('click', () => {
    const idx = parseInt(step.dataset.phase);
    const card = document.getElementById(`phase-${idx}`);
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    card.style.transition = 'box-shadow .3s';
    card.style.boxShadow = '0 0 0 2px rgba(139,92,246,.6)';
    setTimeout(() => { card.style.boxShadow = ''; }, 1200);
  });
});

// ── Final output ──────────────────────────────────────────────────────────────
function showFinalOutput() {
  const section = document.getElementById('outputSection');
  document.getElementById('outputSummary').innerHTML = phaseNames.map(name => `
    <div class="summary-card">
      <div class="summary-phase">${name}</div>
      <div class="summary-status"><span>✅</span><span>Completed</span></div>
    </div>`).join('');
  section.style.display = 'block';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Code editor wiring ────────────────────────────────────────────────────────
(function () {
  const ta = document.getElementById('sourceCode');
  if (ta) {
    // Decode HTML entities written by the textarea's initial value
    ta.value = ta.value
      .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
    updateLineCount();
    ta.addEventListener('input', updateLineCount);
    // Tab key inserts spaces instead of leaving the field
    ta.addEventListener('keydown', e => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const s = ta.selectionStart, end = ta.selectionEnd;
        ta.value = ta.value.substring(0, s) + '    ' + ta.value.substring(end);
        ta.selectionStart = ta.selectionEnd = s + 4;
      }
    });
  }
  const clearBtn = document.getElementById('btnClearCode');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (ta) { ta.value = DEFAULT_CODE; updateLineCount(); ta.focus(); }
    });
  }
})();

// ── Floating particles ────────────────────────────────────────────────────────
(function () {
  const c = document.getElementById('bgParticles');
  for (let i = 0; i < 28; i++) {
    const d = document.createElement('div');
    const sz = Math.random() * 3 + 1;
    d.style.cssText = `position:absolute;width:${sz}px;height:${sz}px;border-radius:50%;
      left:${Math.random() * 100}%;top:${Math.random() * 100}%;
      background:rgba(139,92,246,${Math.random() * .25 + .05});
      animation:fp${i} ${Math.random() * 18 + 12}s ${Math.random() * 8}s ease-in-out infinite alternate;`;
    c.appendChild(d);
    const dx = (Math.random() > .5 ? '' : '-') + (Math.random() * 50 + 15);
    const dy = (Math.random() > .5 ? '' : '-') + (Math.random() * 50 + 15);
    const s = document.createElement('style');
    s.textContent = `@keyframes fp${i}{from{transform:translate(0,0)}to{transform:translate(${dx}px,${dy}px)}}`;
    document.head.appendChild(s);
  }
})();
