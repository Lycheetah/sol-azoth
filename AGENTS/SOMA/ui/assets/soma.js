/* ☿ SOMA — Agent Harness JS
   Claude-Code polish level. Full markdown rendering, streaming, animations.
   ⊚ Sol ∴ P∧H∧B ∴ Albedo */

/* ── State ── */
let busy = false;
let currentView = 'chat';
let queueOpen = false;

/* ── Elements ── */
const msgsEl      = document.getElementById('messages');
const inputEl     = document.getElementById('chat-input');
const sendBtn     = document.getElementById('send-btn');
const thinkEl     = document.getElementById('thinking');
const statusDot   = document.getElementById('status-dot');
const statusText  = document.getElementById('status-text');
const scrollBtn   = document.getElementById('scroll-bottom');
const toastEl     = document.getElementById('toast');
const agentSelect = document.getElementById('agent-select');
const agentCount  = document.getElementById('agent-count');

/* ── Helpers ── */
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

function now() {
  const d = new Date();
  return d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
}

function autosize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

/* ── View switching ── */
function switchView(view) {
  currentView = view;
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById('view-' + view).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`.nav-item[data-view="${view}"]`).classList.add('active');
  if (view === 'agents') refreshAgents();
  if (view === 'forge') loadForge();
}

/* ── SSE Connection ── */
let eventSource = null;

function connectSSE() {
  if (eventSource) eventSource.close();
  eventSource = new EventSource('/api/stream');

  eventSource.onopen = () => {
    statusDot.className = 'status-dot';
    statusText.textContent = 'Connected';
  };

  eventSource.addEventListener('init', (e) => {
    const data = JSON.parse(e.data);
    if (data.agents) {
      updateAgentSelect(data.agents);
    }
  });

  eventSource.addEventListener('message', (e) => {
    const data = JSON.parse(e.data);
    addMsg(data.role, data.text, data.ts);
    if (data.role === 'assistant' || data.role === 'error') {
      setBusy(false);
    }
  });

  eventSource.addEventListener('stream', (e) => {
    const data = JSON.parse(e.data);
    updateStream(data.text);
  });

  eventSource.addEventListener('stream_end', () => {
    finalizeStream();
    setBusy(false);
  });

  eventSource.addEventListener('agents', (e) => {
    const data = JSON.parse(e.data);
    updateAgentSelect(data.agents);
    if (data.count !== undefined) {
      agentCount.textContent = data.count;
    }
  });

  eventSource.onerror = () => {
    statusDot.className = 'status-dot off';
    statusText.textContent = 'Disconnected';
    setTimeout(connectSSE, 3000);
  };
}

/* ── Agent management ── */
function updateAgentSelect(agents) {
  const current = agentSelect.value;
  agentSelect.innerHTML = '';
  agents.forEach(a => {
    const opt = document.createElement('option');
    opt.value = a;
    opt.textContent = a;
    agentSelect.appendChild(opt);
  });
  if (agents.includes(current)) agentSelect.value = current;
  agentCount.textContent = agents.length;
}

function onAgentChange() {
  // Future: switch active agent
}

function refreshAgents() {
  fetch('/api/agents').then(r => r.json()).then(data => {
    const agents = Array.isArray(data) ? data : (data.agents || []);
    updateAgentSelect(agents);
    renderAgentList(agents);
  }).catch(() => {});
}

function renderAgentList(agents) {
  const list = document.getElementById('agent-list');
  if (!list) return;
  if (!agents.length) {
    list.innerHTML = '<div class="agent-card empty"><div class="agent-card-body"><p>No agents running.</p></div></div>';
    return;
  }
  list.innerHTML = agents.map(a => `
    <div class="agent-card">
      <div class="agent-card-body">
        <div class="agent-card-name">${esc(a)}</div>
        <div class="agent-card-desc">Agent ready</div>
      </div>
      <div class="agent-card-footer">
        <button class="agent-btn" onclick="switchToAgent('${esc(a)}')">Switch</button>
      </div>
    </div>
  `).join('');
}

function switchToAgent(name) {
  agentSelect.value = name;
  switchView('chat');
  addMsg('system', `Switched to ${name}`, now());
}

/* ── Forge queue ── */
function loadForge() {
  // Forge queue endpoint TBD — stub for now
  const list = document.getElementById('forge-list');
  if (!list) return;
  list.innerHTML = '<div class="forge-item"><span style="color:var(--dim)">Forge queue — coming soon</span></div>';
}

/* ── Markdown renderer ── */
function renderMarkdown(text) {
  if (!text) return '';
  let html = esc(text);

  // Code blocks (fenced) — must be first
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const langLabel = lang ? `<span class="code-lang">${esc(lang)}</span>` : '<span class="code-lang">code</span>';
    const escaped = esc(code);
    return `<div class="code-block">
      <div class="code-header">
        ${langLabel}
        <button class="code-copy" onclick="copyCode(this, \`${esc(code).replace(/`/g, '\\`')}\`)">copy</button>
      </div>
      <pre><code>${escaped}</code></pre>
    </div>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Bold and italic
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Blockquotes
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr>');

  // Unordered lists
  html = html.replace(/^[\s]*[-*] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

  // Ordered lists
  html = html.replace(/^[\s]*\d+\. (.+)$/gm, '<li>$1</li>');

  // Tables
  html = html.replace(/\|(.+)\|/g, (match, content) => {
    const cells = content.split('|').map(c => c.trim()).filter(c => c);
    if (cells.every(c => /^[-:]+$/.test(c))) return '<tr class="table-divider"></tr>';
    const tag = match.includes('\n---') ? 'th' : 'td';
    return '<tr>' + cells.map(c => `<${tag}>${c}</${tag}>`).join('') + '</tr>';
  });
  html = html.replace(/(<tr>.*<\/tr>\n?)+/g, '<table>$&</table>');

  // Paragraphs — wrap remaining text in <p> tags
  const lines = html.split('\n');
  let result = '';
  let inP = false;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (/^<(h[1-4]|ul|ol|li|pre|blockquote|hr|table|tr|th|td|div)/.test(trimmed) ||
        /^<\/(ul|ol|pre|blockquote|table|div)>/.test(trimmed)) {
      if (inP) { result += '</p>'; inP = false; }
      result += line + '\n';
      continue;
    }
    if (trimmed === '') {
      if (inP) { result += '</p>\n'; inP = false; }
      else result += '\n';
      continue;
    }
    if (!inP) { result += '<p>'; inP = true; }
    else result += '\n';
    result += trimmed;
  }
  if (inP) result += '</p>';

  return result;
}

/* ── Copy code ── */
function copyCode(btn, code) {
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = 'copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = 'copy';
      btn.classList.remove('copied');
    }, 1500);
  }).catch(() => {
    const ta = document.createElement('textarea');
    ta.value = code;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    btn.textContent = 'copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = 'copy';
      btn.classList.remove('copied');
    }, 1500);
  });
}

/* ── Messages ── */
function addMsg(role, text, ts) {
  const row = document.createElement('div');
  row.className = 'message ' + role;

  const label = document.createElement('div');
  label.className = `msg-label ${role}-label`;
  const roleNames = { user: 'You', assistant: 'SOMA', error: 'Error', system: 'System' };
  label.innerHTML = `${roleNames[role] || role} <span class="ts">${esc(ts || '')}</span>`;
  row.appendChild(label);

  const bubble = document.createElement('div');
  bubble.className = 'msg-content';
  bubble.innerHTML = renderMarkdown(text);
  row.appendChild(bubble);

  msgsEl.appendChild(row);
  scrollBottom();
}

/* ── Stream bubble ── */
let streamBubble = null;
let streamTimeout = null;

function getOrCreateStreamBubble() {
  if (!streamBubble) {
    streamBubble = document.createElement('div');
    streamBubble.className = 'message assistant';
    const label = document.createElement('div');
    label.className = 'msg-label assistant-label';
    label.innerHTML = 'SOMA <span class="ts">' + now() + '</span>';
    streamBubble.appendChild(label);
    const content = document.createElement('div');
    content.className = 'msg-content';
    content.id = 'stream-content';
    streamBubble.appendChild(content);
    msgsEl.appendChild(streamBubble);
  }
  return document.getElementById('stream-content');
}

function updateStream(text) {
  const el = getOrCreateStreamBubble();
  let content = el.innerHTML;
  if (content.endsWith('<span class="cursor"></span>')) {
    content = content.slice(0, -35);
  }
  const rendered = renderMarkdown(text);
  el.innerHTML = content + rendered + '<span class="cursor"></span>';
  scrollBottom(true);
  clearTimeout(streamTimeout);
  streamTimeout = setTimeout(() => {
    let c = el.innerHTML;
    if (c.endsWith('<span class="cursor"></span>')) {
      el.innerHTML = c.slice(0, -35);
    }
  }, 500);
}

function finalizeStream() {
  if (streamBubble) {
    const el = document.getElementById('stream-content');
    if (el) {
      let c = el.innerHTML;
      if (c.endsWith('<span class="cursor"></span>')) {
        el.innerHTML = c.slice(0, -35);
      }
    }
    streamBubble = null;
  }
}

/* ── Thinking indicator ── */
function showThink() {
  thinkEl.classList.add('visible');
}

function clearThink() {
  thinkEl.classList.remove('visible');
}

/* ── Send ── */
function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || busy) return;
  inputEl.value = '';
  inputEl.style.height = 'auto';
  doSend(text);
}

function doSend(text) {
  if (busy) return;
  busy = true;
  sendBtn.disabled = true;
  addMsg('user', text, now());
  showThink();
  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, agent: agentSelect.value }),
  }).catch(() => {
    addMsg('error', 'Send failed — check connection.', now());
    setBusy(false);
  });
}

function setBusy(b) {
  busy = b;
  sendBtn.disabled = b;
  if (!b) clearThink();
}

/* ── Keyboard ── */
function onKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
  // Focus input on any key when not already focused
}

document.addEventListener('keydown', (e) => {
  if (e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'INPUT' && !e.metaKey && !e.ctrlKey) {
    const active = document.activeElement;
    if (active && (active.tagName === 'BUTTON' || active.tagName === 'SELECT')) return;
    inputEl.focus();
  }
});

/* ── Auto-scroll ── */
function scrollBottom(force) {
  requestAnimationFrame(() => {
    if (force || msgsEl.scrollTop + msgsEl.clientHeight >= msgsEl.scrollHeight - 60) {
      msgsEl.scrollTop = msgsEl.scrollHeight;
    }
  });
}

msgsEl.addEventListener('scroll', () => {
  const nearBottom = msgsEl.scrollTop + msgsEl.clientHeight >= msgsEl.scrollHeight - 60;
  scrollBtn.classList.toggle('visible', !nearBottom);
});

/* ── Toast ── */
function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add('visible');
  setTimeout(() => toastEl.classList.remove('visible'), 2000);
}

/* ── Clear chat ── */
function clearChat() {
  msgsEl.innerHTML = '';
  streamBubble = null;
  showToast('Chat cleared');
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', () => {
  connectSSE();
  refreshAgents();
  loadForge();
});
