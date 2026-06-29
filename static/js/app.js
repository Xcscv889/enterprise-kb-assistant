/* 应用初始化 + 会话管理 + 侧边栏 + 消息本地持久化 v2 */
'use strict';

const SESSION_KEY = 'kb_current_session';
const SESSION_LIST_KEY = 'kb_session_list';
const MSG_PREFIX = 'kb_msgs_';

const LOG = true;
function debug(...args) { if (LOG) console.log('[KB]', ...args); }

// ── 会话 ID ──

function genSessionId() {
  return crypto.randomUUID().replace(/-/g, '').substring(0, 12);
}

function getCurrentSessionId() {
  let sid = localStorage.getItem(SESSION_KEY);
  if (!sid) {
    sid = genSessionId();
    localStorage.setItem(SESSION_KEY, sid);
    debug('新会话ID:', sid);
  }
  return sid;
}

let currentSessionId = getCurrentSessionId();

// ── 会话元数据 ──

function getLocalSessionList() {
  try { return JSON.parse(localStorage.getItem(SESSION_LIST_KEY) || '{}'); }
  catch { return {}; }
}

function saveLocalSessionList(list) {
  try { localStorage.setItem(SESSION_LIST_KEY, JSON.stringify(list)); }
  catch {}
}

function updateLocalSession(sid, data) {
  const list = getLocalSessionList();
  list[sid] = { ...list[sid], ...data, last_accessed: Date.now() };
  saveLocalSessionList(list);
}

function removeLocalSession(sid) {
  const list = getLocalSessionList();
  delete list[sid];
  saveLocalSessionList(list);
  localStorage.removeItem(MSG_PREFIX + sid);
}

// ── 消息持久化 ──

function getLocalMessages(sid) {
  try {
    const raw = localStorage.getItem(MSG_PREFIX + sid);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveLocalMessages(sid, messages) {
  try {
    if (messages.length > 200) messages = messages.slice(-200);
    localStorage.setItem(MSG_PREFIX + sid, JSON.stringify(messages));
  } catch {
    const list = getLocalSessionList();
    const sorted = Object.entries(list).sort((a, b) => a[1].last_accessed - b[1].last_accessed);
    for (const [id] of sorted.slice(0, 3)) {
      localStorage.removeItem(MSG_PREFIX + id);
      delete list[id];
    }
    saveLocalSessionList(list);
    try { localStorage.setItem(MSG_PREFIX + sid, JSON.stringify(messages)); } catch {}
  }
}

// ── 默认欢迎 ──

function showDefaultGreeting() {
  document.getElementById('chat-messages').innerHTML = `
    <div class="message assistant">
      <div class="avatar">🤖</div>
      <div class="bubble">
        <p>👋 你好！我是企业知识库智能助手。</p>
        <p>请先上传文档（PDF、DOCX、TXT、Markdown），然后向我提问。</p>
        <p>我会基于文档内容为你提供准确、有据可查的回答。</p>
      </div>
    </div>
  `;
}

// ── 渲染消息 ──

function renderMessagesToContainer(messages, append) {
  const container = document.getElementById('chat-messages');

  if (!append) {
    if (!messages || messages.length === 0) {
      showDefaultGreeting();
      return;
    }
    container.innerHTML = '';
  }

  for (const msg of messages) {
    if (!msg.content || !msg.content.trim()) continue;
    const div = document.createElement('div');
    div.className = 'message ' + (msg.role === 'user' ? 'user' : 'assistant');
    div.innerHTML = `
      <div class="avatar">${msg.role === 'user' ? '👤' : '🤖'}</div>
      <div class="bubble">${marked.parse(msg.content)}</div>
    `;
    container.appendChild(div);
  }
  container.scrollTop = container.scrollHeight;
}

// ── 加载聊天历史（后端优先 → localStorage 兜底） ──

async function loadChatHistory(sid) {
  debug('loadChatHistory:', sid);

  // ① 后端
  try {
    const res = await fetch('/api/memory/' + sid + '/history');
    if (res.ok) {
      const data = await res.json();
      debug('  后端返回:', data.count, '条消息');
      if (data.messages && data.messages.length > 0) {
        renderMessagesToContainer(data.messages);
        saveLocalMessages(sid, data.messages);
        return true;
      }
    } else {
      debug('  后端HTTP错误:', res.status);
    }
  } catch (e) {
    debug('  后端请求失败:', e.message);
  }

  // ② localStorage
  const localMsgs = getLocalMessages(sid);
  debug('  localStorage:', localMsgs.length, '条消息');
  if (localMsgs.length > 0) {
    renderMessagesToContainer(localMsgs);
    return true;
  }

  return false;
}

// ── 更新预览（从已有消息中提取） ──

function refreshPreview(sid) {
  const msgs = getLocalMessages(sid);
  if (msgs.length === 0) return;
  const firstUser = msgs.find(m => m.role === 'user');
  updateLocalSession(sid, {
    turn_count: Math.floor(msgs.length / 2),
    preview: firstUser ? firstUser.content.substring(0, 30) : '',
  });
}

// ── 切换会话 ──

async function switchSession(sid) {
  if (sid === currentSessionId) return;
  debug('switchSession:', currentSessionId, '→', sid);

  // 保存当前会话的预览信息
  refreshPreview(currentSessionId);

  currentSessionId = sid;
  localStorage.setItem(SESSION_KEY, sid);
  document.getElementById('session-id-display').textContent = sid;

  const loaded = await loadChatHistory(sid);
  if (!loaded) showDefaultGreeting();

  updateMemoryInfo();
  highlightCurrentSession();
}

// ── 新建会话 ──

function newSession() {
  refreshPreview(currentSessionId);

  currentSessionId = genSessionId();
  localStorage.setItem(SESSION_KEY, currentSessionId);
  updateLocalSession(currentSessionId, { turn_count: 0, preview: '新会话' });

  showDefaultGreeting();

  document.getElementById('session-id-display').textContent = currentSessionId;
  renderSessionList();
  updateMemoryInfo();
  highlightCurrentSession();
}

// ── 删除会话 ──

async function deleteSession(sid) {
  debug('deleteSession:', sid);

  // 清除后端记忆
  try { await fetch('/api/memory/' + sid, { method: 'DELETE' }); } catch {}

  // 清除本地数据
  removeLocalSession(sid);

  // 如果删的是当前会话，切换到最近的另一个会话
  if (sid === currentSessionId) {
    const list = getLocalSessionList();
    const others = Object.entries(list).sort((a, b) => b[1].last_accessed - a[1].last_accessed);
    if (others.length > 0) {
      await switchSession(others[0][0]);
    } else {
      newSession();
    }
  }

  renderSessionList();
}

// ── 渲染会话列表 ──

async function renderSessionList() {
  const listEl = document.getElementById('session-list');
  if (!listEl) return;

  let backendSessions = [];
  try {
    const res = await fetch('/api/sessions');
    if (res.ok) backendSessions = await res.json();
  } catch {}

  const localList = getLocalSessionList();
  const sessions = [];
  const seen = new Set();

  for (const s of backendSessions) {
    seen.add(s.session_id);
    const local = localList[s.session_id] || {};
    sessions.push({
      session_id: s.session_id,
      turn_count: s.turn_count || local.turn_count || 0,
      last_accessed: (local.last_accessed || 0),
      preview: local.preview || '',
    });
  }

  for (const [id, info] of Object.entries(localList)) {
    if (!seen.has(id)) {
      sessions.push({
        session_id: id,
        turn_count: info.turn_count || 0,
        last_accessed: info.last_accessed || 0,
        preview: info.preview || '',
      });
    }
  }

  sessions.sort((a, b) => b.last_accessed - a.last_accessed);

  if (sessions.length === 0) {
    listEl.innerHTML = '<p class="empty-hint">暂无历史会话</p>';
    return;
  }

  listEl.innerHTML = sessions.map(s => {
    const isActive = s.session_id === currentSessionId;
    const display = s.preview || '💬 会话 ' + s.session_id;
    const timeStr = s.last_accessed
      ? new Date(s.last_accessed).toLocaleString('zh-CN', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' })
      : '';
    return `
      <div class="session-item${isActive ? ' active' : ''}"
           data-session-id="${s.session_id}"
           onclick="switchSession('${s.session_id}')"
           oncontextmenu="event.preventDefault(); showSessionMenu(event, '${s.session_id}')">
        <span class="session-preview">${escapeHtml(display)}</span>
        <span class="session-meta">${s.turn_count}轮 · ${escapeHtml(timeStr)}</span>
        <span class="session-del" onclick="event.stopPropagation(); deleteSession('${s.session_id}')" title="删除会话">×</span>
      </div>
    `;
  }).join('');

  updateLocalSession(currentSessionId, {});
}

// ── 右键菜单 ──

function showSessionMenu(e, sid) {
  // 先切换到这个会话
  switchSession(sid);

  const menu = document.getElementById('session-context-menu');
  menu.style.left = e.clientX + 'px';
  menu.style.top = e.clientY + 'px';
  menu.classList.add('show');
  menu.dataset.sessionId = sid;

  // 点击其他地方关闭
  const close = () => {
    menu.classList.remove('show');
    document.removeEventListener('click', close);
  };
  setTimeout(() => document.addEventListener('click', close), 0);
}

function confirmDeleteSession() {
  const menu = document.getElementById('session-context-menu');
  const sid = menu.dataset.sessionId;
  menu.classList.remove('show');
  if (sid && confirm('确定要删除此会话及其所有聊天记录吗？')) {
    deleteSession(sid);
  }
}

function highlightCurrentSession() {
  document.querySelectorAll('.session-item').forEach(el => {
    el.classList.toggle('active', el.dataset.sessionId === currentSessionId);
  });
}

// ── 文档列表 ──

async function loadDocList() {
  try {
    const res = await fetch('/api/documents');
    const data = await res.json();
    const list = document.getElementById('doc-list');
    if (!data.documents || data.documents.length === 0) {
      list.innerHTML = '<p class="empty-hint">暂无文档，点击上方按钮上传</p>';
      return;
    }
    list.innerHTML = data.documents.map(d => `
      <div class="doc-item">
        <span class="doc-name">📄 ${escapeHtml(d.filename)}</span>
        <span class="doc-chunks">${d.chunks}块</span>
        <span class="doc-del" onclick="deleteDoc('${d.id}')" title="删除">×</span>
      </div>
    `).join('');
  } catch (err) {
    console.error('加载文档列表失败:', err);
  }
}

async function deleteDoc(docId) {
  if (!confirm('确定要删除此文档吗？')) return;
  try {
    await fetch('/api/documents/' + docId, { method: 'DELETE' });
    loadDocList();
  } catch (err) {
    console.error('删除文档失败:', err);
  }
}

// ── 记忆 ──

async function updateMemoryInfo() {
  try {
    const res = await fetch('/api/memory/' + currentSessionId);
    const data = await res.json();
    document.getElementById('mem-turns').textContent = data.short_term?.turn_count || 0;
    document.getElementById('mem-long').textContent = data.long_term?.fact_count || 0;
  } catch {}
}

async function clearMemory() {
  if (!confirm('确定要清除当前会话记忆吗？')) return;
  try {
    await fetch('/api/memory/' + currentSessionId, { method: 'DELETE' });
    updateMemoryInfo();
  } catch (err) {
    console.error('清除记忆失败:', err);
  }
}

// ── 工具 ──

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text || '';
  return div.innerHTML;
}

// ── 初始化 ──

document.addEventListener('DOMContentLoaded', async () => {
  debug('初始化, 当前会话:', currentSessionId);

  document.getElementById('session-id-display').textContent = currentSessionId;

  loadDocList();
  await renderSessionList();

  debug('尝试恢复历史...');
  const restored = await loadChatHistory(currentSessionId);
  if (!restored) {
    debug('无历史数据，显示欢迎');
    showDefaultGreeting();
  }

  updateMemoryInfo();
  highlightCurrentSession();

  document.getElementById('btn-new-chat').addEventListener('click', newSession);
  document.getElementById('btn-clear-memory').addEventListener('click', clearMemory);
  document.getElementById('ctx-delete-session').addEventListener('click', confirmDeleteSession);
});
