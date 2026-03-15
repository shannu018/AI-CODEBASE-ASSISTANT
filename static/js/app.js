/**
 * app.js - AI Codebase Assistant Frontend
 * Handles: file upload, indexing, chat with RAG responses
 */

// ── State ──────────────────────────────────────
let uploadId = null;
let sessionId = null;
let isIndexing = false;
let isSending = false;

// ── DOM refs ────────────────────────────────────
const dropZone    = document.getElementById('dropZone');
const fileInput   = document.getElementById('fileInput');
const uploadStatus = document.getElementById('uploadStatus');
const indexBtn    = document.getElementById('indexBtn');
const indexStatus = document.getElementById('indexStatus');
const statsBox    = document.getElementById('statsBox');
const chatMessages = document.getElementById('chatMessages');
const queryInput  = document.getElementById('queryInput');
const sendBtn     = document.getElementById('sendBtn');

// ── Upload ──────────────────────────────────────
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

  showStatus(uploadStatus, 'info', `Uploading ${files.length} files...`);
  indexBtn.disabled = true;

  const formData = new FormData();
  for (const file of files) {
    // Use webkitRelativePath for directory structure preservation
    const name = file.webkitRelativePath || file.name;
    formData.append('files', file, name);
  }

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Upload failed');

    uploadId = data.upload_id;
    showStatus(uploadStatus, 'success', `✅ Uploaded ${data.file_count} files`);
    indexBtn.disabled = false;
  } catch (err) {
    showStatus(uploadStatus, 'error', `❌ ${err.message}`);
  }
}

// ── Indexing ─────────────────────────────────────
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
        'parsing': '📂 Parsing files...',
        'chunking': '✂️ Chunking code...',
        'embedding': `🧠 Embedding chunks... (${job.total_chunks || '?'} chunks)`,
        'storing': '💾 Storing in vector database...',
        'complete': `✅ ${job.message}`,
        'error': `❌ ${job.message}`
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

      setTimeout(poll, 2000);  // poll every 2 seconds
    } catch (err) {
      showStatus(indexStatus, 'error', `❌ Poll error: ${err.message}`);
      isIndexing = false;
    }
  };
  poll();
}

// ── Stats ─────────────────────────────────────────
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

// ── Chat ─────────────────────────────────────────
queryInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Auto-resize textarea
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

// ── Message Rendering ────────────────────────────
function appendMessage(role, text, sources = []) {
  const div = document.createElement('div');
  div.className = `message ${role}`;

  const content = document.createElement('div');
  content.className = 'message-content';

  // Convert markdown-like formatting
  content.innerHTML = formatText(text);

  // Add source tags if provided
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
}

function formatText(text) {
  // Very basic markdown: code blocks, inline code, bold
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
      `<pre><code class="language-${lang}">${escapeHtml(code.trim())}</code></pre>`)
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
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  </div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ── Utilities ─────────────────────────────────────
function showStatus(el, type, message) {
  el.className = `status-box ${type}`;
  el.textContent = message;
  el.classList.remove('hidden');
}

// Load initial stats on page load
loadStats();
