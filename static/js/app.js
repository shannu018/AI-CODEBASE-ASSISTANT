/**
 * app.js - AI Codebase Assistant | Full Feature Edition
 */

// ── State ──────────────────────────────────────────────────
let uploadId = null;
let sessionId = null;
let isIndexing = false;
let isSending = false;
let activeProject = null;
let fileSearchTimer = null;

// ── DOM refs ────────────────────────────────────────────────
const dropZone     = document.getElementById('dropZone');
const fileInput    = document.getElementById('fileInput');
const uploadStatus = document.getElementById('uploadStatus');
const indexBtn     = document.getElementById('indexBtn');
const indexStatus  = document.getElementById('indexStatus');
const statsBox     = document.getElementById('statsBox');
const chatMessages = document.getElementById('chatMessages');
const queryInput   = document.getElementById('queryInput');
const sendBtn      = document.getElementById('sendBtn');

// ── Theme ────────────────────────────────────────────────────
function toggleTheme() {
  const root = document.getElementById('htmlRoot');
  root.classList.toggle('light-theme');
  const isLight = root.classList.contains('light-theme');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
}

function applyStoredTheme() {
  if (localStorage.getItem('theme') === 'light') {
    document.getElementById('htmlRoot').classList.add('light-theme');
  }
}

// ── Upload ────────────────────────────────────────────────────
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  handleFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', e => handleFiles(e.target.files));

async function handleFiles(files) {
  if (!files || files.length === 0) return;

  const projectName = document.getElementById('projectNameInput').value.trim();
  const progressWrap = document.getElementById('uploadProgressWrap');
  const progressBar = document.getElementById('uploadProgressBar');
  const progressText = document.getElementById('uploadProgressText');

  progressWrap.classList.remove('hidden');
  progressBar.style.width = '0%';
  progressText.textContent = '0%';
  showStatus(uploadStatus, 'info', `Uploading ${files.length} files...`);
  indexBtn.disabled = true;

  const formData = new FormData();
  for (const file of files) {
    const name = file.webkitRelativePath || file.name;
    formData.append('files', file, name);
  }
  if (projectName) formData.append('project_name', projectName);

  try {
    // Simulate progress while uploading
    let progress = 0;
    const progressInterval = setInterval(() => {
      if (progress < 90) {
        progress += Math.random() * 15;
        progressBar.style.width = Math.min(progress, 90) + '%';
        progressText.textContent = Math.round(Math.min(progress, 90)) + '%';
      }
    }, 300);

    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();
    clearInterval(progressInterval);

    progressBar.style.width = '100%';
    progressText.textContent = '100%';
    setTimeout(() => progressWrap.classList.add('hidden'), 1500);

    if (!res.ok) throw new Error(data.error || 'Upload failed');

    uploadId = data.upload_id;
    activeProject = projectName || uploadId.substring(0, 8);
    document.getElementById('activeProjectLabel').textContent = `Active: ${activeProject}`;
    showStatus(uploadStatus, 'success', `✅ Uploaded ${data.file_count} files`);
    indexBtn.disabled = false;
    loadUploadedCodebases();
  } catch (err) {
    document.getElementById('uploadProgressWrap').classList.add('hidden');
    showStatus(uploadStatus, 'error', `❌ ${err.message}`);
  }
}

// ── Indexing ───────────────────────────────────────────────────
indexBtn.addEventListener('click', startIndexing);

async function startIndexing() {
  if (!uploadId || isIndexing) return;
  isIndexing = true;
  indexBtn.disabled = true;
  showStatus(indexStatus, 'info', '⚙️ Starting indexing pipeline...');

  try {
    const res = await fetch('/api/index', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ upload_id: uploadId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Indexing failed to start');
    pollIndexStatus(uploadId);
  } catch (err) {
    showStatus(indexStatus, 'error', `❌ ${err.message}`);
    isIndexing = false;
    indexBtn.disabled = false;
  }
}

async function pollIndexStatus(id) {
  const poll = async () => {
    try {
      const res = await fetch(`/api/index/status/${id}`);
      const job = await res.json();
      const statusMessages = {
        'parsing':   '📂 Parsing files...',
        'chunking':  '✂️ Chunking code...',
        'embedding': `🧠 Embedding chunks... (${job.total_chunks || '?'} chunks)`,
        'storing':   '💾 Storing in vector database...',
        'complete':  `✅ ${job.message}`,
        'error':     `❌ ${job.message}`
      };
      const msg = statusMessages[job.status] || job.message;
      const type = job.status === 'complete' ? 'success' : job.status === 'error' ? 'error' : 'info';
      showStatus(indexStatus, type, msg);

      if (job.status === 'complete') {
        isIndexing = false;
        loadStats();
        appendMessage('assistant', '✅ Codebase indexed! I\'m ready to answer your questions. Ask me anything about your code.');
        return;
      } else if (job.status === 'error') {
        isIndexing = false;
        indexBtn.disabled = false;
        return;
      }
      setTimeout(poll, 2000);
    } catch (err) {
      showStatus(indexStatus, 'error', `❌ Poll error: ${err.message}`);
      isIndexing = false;
    }
  };
  poll();
}

// ── Stats ──────────────────────────────────────────────────────
async function loadStats() {
  try {
    const res = await fetch('/api/index/stats');
    const data = await res.json();
    statsBox.innerHTML = `
      <div class="stat"><span>Chunks</span><span class="stat-value">${data.total_chunks ?? 0}</span></div>
      <div class="stat"><span>Collection</span><span class="stat-value">${data.collection_name ?? '-'}</span></div>
    `;
  } catch (err) {
    statsBox.innerHTML = `<span style="color:var(--error)">Error loading stats</span>`;
  }
}

// ── Chat ───────────────────────────────────────────────────────
queryInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
queryInput.addEventListener('input', () => {
  queryInput.style.height = 'auto';
  queryInput.style.height = Math.min(queryInput.scrollHeight, 120) + 'px';
});

async function sendMessage() {
  const query = queryInput.value.trim();
  if (!query || isSending) return;
  isSending = true;
  sendBtn.disabled = true;
  queryInput.value = '';
  queryInput.style.height = 'auto';
  appendMessage('user', query);
  const typingId = appendTypingIndicator();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: sessionId })
    });
    const data = await res.json();
    removeTypingIndicator(typingId);
    if (!res.ok) throw new Error(data.error || 'Chat failed');
    sessionId = data.session_id;
    appendMessage('assistant', data.answer, data.sources);
  } catch (err) {
    removeTypingIndicator(typingId);
    appendMessage('assistant', `❌ Error: ${err.message}`);
  } finally {
    isSending = false;
    sendBtn.disabled = false;
    queryInput.focus();
  }
}

// ── Message Rendering ─────────────────────────────────────────
function appendMessage(role, text, sources = []) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  const content = document.createElement('div');
  content.className = 'message-content';
  content.innerHTML = formatText(text);

  if (sources && sources.length > 0) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'sources';
    sourcesDiv.innerHTML = `<div class="sources-label">📎 Sources</div>` +
      sources.map(s => `<span class="source-tag" title="Score: ${s.score}">${s.file} L${s.lines}</span>`).join('');
    content.appendChild(sourcesDiv);
  }

  div.appendChild(content);
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Apply Prism syntax highlighting to code blocks
  if (window.Prism) {
    content.querySelectorAll('pre code').forEach(el => Prism.highlightElement(el));
  }
}

function formatText(text) {
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
      `<pre><code class="language-${lang || 'plaintext'}">${escapeHtml(code.trim())}</code></pre>`)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>');
}

function escapeHtml(text) {
  return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

let typingCounter = 0;
function appendTypingIndicator() {
  const id = `typing-${typingCounter++}`;
  const div = document.createElement('div');
  div.className = 'message assistant';
  div.id = id;
  div.innerHTML = `<div class="message-content typing-indicator">
    <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
  </div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ── Export Chat ─────────────────────────────────────────────────
function exportChat() {
  const messages = chatMessages.querySelectorAll('.message');
  let md = `# CodeBrain Chat Export\n\n`;
  messages.forEach(msg => {
    const role = msg.classList.contains('user') ? '**You**' : '**CodeBrain**';
    const text = msg.querySelector('.message-content')?.innerText || '';
    md += `${role}:\n${text}\n\n---\n\n`;
  });
  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `codebrain-chat-${Date.now()}.md`;
  a.click();
}

// ── Analysis Panel ─────────────────────────────────────────────
function showAnalysisPanel(tab) {
  document.getElementById('analysisPanel').classList.remove('hidden');
  switchAnalysisTab(tab);
}

function switchAnalysisTab(tab) {
  document.querySelectorAll('.analysis-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.analysis-pane').forEach(p => p.classList.remove('active'));
  document.getElementById(`tab-${tab}`)?.classList.add('active');
  document.getElementById(`panel-${tab}`)?.classList.add('active');
}

async function runAnalysis(type) {
  const inputMap = { security: 'securityInput', diff: 'diffInput', docs: 'docsInput', tests: 'testsInput' };
  const resultMap = { security: 'securityResult', diff: 'diffResult', docs: 'docsResult', tests: 'testsResult' };
  const endpointMap = {
    security: { url: '/api/analyze/security', body: code => ({ code }), key: 'security_report' },
    diff:     { url: '/api/analyze/diff',     body: diff => ({ diff }), key: 'explanation' },
    docs:     { url: '/api/analyze/docs',     body: code => ({ code }), key: 'docs' },
    tests:    { url: '/api/analyze/tests',    body: code => ({ code }), key: 'tests' }
  };

  const inputEl = document.getElementById(inputMap[type]);
  const resultEl = document.getElementById(resultMap[type]);
  const ep = endpointMap[type];
  const value = inputEl?.value.trim();
  if (!value) { resultEl.textContent = 'Please paste some input first.'; resultEl.classList.remove('hidden'); return; }

  const btnEl = inputEl.closest('.analysis-pane').querySelector('button');
  const origText = btnEl.textContent;
  btnEl.disabled = true;
  btnEl.textContent = '⏳ Running...';
  resultEl.textContent = 'Analyzing...';
  resultEl.classList.remove('hidden');

  try {
    const res = await fetch(ep.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ep.body(value))
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Analysis failed');
    resultEl.textContent = data[ep.key] || 'No result';
  } catch (err) {
    resultEl.textContent = `❌ ${err.message}`;
  } finally {
    btnEl.disabled = false;
    btnEl.textContent = origText;
  }
}

// ── Uploaded Codebases ─────────────────────────────────────────
async function loadUploadedCodebases() {
  const listEl = document.getElementById('uploadedFilesList');
  try {
    const res = await fetch('/api/uploads');
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();

    if (!data.uploads || data.uploads.length === 0) {
      listEl.innerHTML = '<div style="font-size:0.85rem;color:#64748b;font-style:italic;">No codebases uploaded yet</div>';
      return;
    }

    listEl.innerHTML = data.uploads.map(u => `
      <div class="uploaded-item" onclick="selectUpload('${u.id}')" title="Click to select">
        <span class="uploaded-name">📁 ${u.name}</span>
        <div style="display:flex;gap:6px;align-items:center;">
          <span class="uploaded-count">${u.size || '?'}</span>
          <span class="uploaded-count" style="background:rgba(124,110,245,0.1);color:#7c6ef5;">${u.file_count || 0}</span>
          <button class="delete-btn" onclick="deleteUpload(event, '${u.id}')" title="Delete codebase">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    listEl.innerHTML = `<div style="font-size:0.85rem;color:var(--error);">Error loading codebases</div>`;
  }
}

async function deleteUpload(e, id) {
  e.stopPropagation();
  const btn = e.currentTarget;
  if (!btn.dataset.confirming) {
    btn.dataset.confirming = 'true';
    btn.style.background = 'rgba(239,68,68,0.2)';
    btn.style.color = 'var(--error)';
    btn.title = 'Click again to confirm delete';
    setTimeout(() => {
      delete btn.dataset.confirming;
      btn.style.background = '';
      btn.style.color = '';
      btn.title = 'Delete codebase';
    }, 2500);
    return;
  }
  delete btn.dataset.confirming;
  btn.disabled = true;
  try {
    const res = await fetch(`/api/uploads/${id}`, { method: 'DELETE' });
    if (res.ok) {
      if (uploadId === id) { uploadId = null; indexBtn.disabled = true; }
      loadUploadedCodebases();
    } else {
      showStatus(uploadStatus, 'error', 'Failed to delete codebase from server.');
    }
  } catch (err) {
    console.error('Delete error:', err);
  } finally {
    btn.disabled = false;
  }
}

function selectUpload(id) {
  uploadId = id;
  indexBtn.disabled = false;
  showStatus(uploadStatus, 'success', `✅ Selected codebase — click Index Codebase to re-index`);
  document.getElementById('activeProjectLabel').textContent = `Active: ${id.substring(0, 8)}...`;
}

// ── File Search ─────────────────────────────────────────────────
function debounceFileSearch() {
  clearTimeout(fileSearchTimer);
  fileSearchTimer = setTimeout(runFileSearch, 400);
}

async function runFileSearch() {
  const q = document.getElementById('fileSearchInput').value.trim();
  const resultsEl = document.getElementById('fileSearchResults');
  if (q.length < 2) { resultsEl.classList.add('hidden'); return; }

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (!data.results || data.results.length === 0) {
      resultsEl.innerHTML = '<div class="file-search-result-item" style="color:#64748b;">No files found</div>';
    } else {
      resultsEl.innerHTML = data.results.map(r => `
        <div class="file-search-result-item" onclick="fileSearchItemClick('${r.path}')">
          ${r.path}
        </div>
      `).join('');
    }
    resultsEl.classList.remove('hidden');
  } catch (err) {
    resultsEl.classList.add('hidden');
  }
}

function fileSearchItemClick(path) {
  document.getElementById('queryInput').value = `Show me the content of ${path}`;
  document.getElementById('fileSearchInput').value = '';
  document.getElementById('fileSearchResults').classList.add('hidden');
  queryInput.focus();
}

// ── Sidebar Resize ─────────────────────────────────────────────
function initSidebarResize() {
  const handle = document.getElementById('resizeHandle');
  const sidebar = document.getElementById('sidebar');
  let isResizing = false;

  handle.addEventListener('mousedown', e => { isResizing = true; e.preventDefault(); });
  document.addEventListener('mousemove', e => {
    if (!isResizing) return;
    const newWidth = Math.min(Math.max(e.clientX, 200), 500);
    sidebar.style.width = newWidth + 'px';
  });
  document.addEventListener('mouseup', () => { isResizing = false; });
}

// ── Auth ────────────────────────────────────────────────────────
async function handleLogout() {
  await fetch('/api/logout', { method: 'POST' });
  window.location.href = '/login';
}

// ── Utilities ────────────────────────────────────────────────────
function showStatus(el, type, message) {
  el.className = `status-box ${type}`;
  el.textContent = message;
  el.classList.remove('hidden');
}

// ── Init ────────────────────────────────────────────────────────
function initializeApp() {
  applyStoredTheme();
  loadStats();
  loadUploadedCodebases();
  initSidebarResize();
}

document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});
