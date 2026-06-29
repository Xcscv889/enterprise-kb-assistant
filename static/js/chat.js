/* 聊天交互 — SSE 流式消费 + Markdown 渲染 */

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('btn-send');
  const messagesContainer = document.getElementById('chat-messages');

  let isSending = false;

  // 发送消息
  async function sendMessage() {
    const query = input.value.trim();
    if (!query || isSending) return;

    isSending = true;
    sendBtn.disabled = true;
    sendBtn.classList.add('sending');
    sendBtn.textContent = '⏳';

    // 添加用户消息
    appendMessage('user', query);
    input.value = '';
    input.style.height = 'auto';

    // 创建助手消息占位
    const assistantEl = appendMessage('assistant', '', true);
    const bubble = assistantEl.querySelector('.bubble');

    let fullText = '';

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          session_id: currentSessionId,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      fullText = '';
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 解析 SSE 事件
        const lines = buffer.split('\n');
        buffer = '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.token) {
                fullText += data.token;
                // 用 Markdown 实时渲染（去抖：每 3 个 token 渲染一次）
                renderBubble(bubble, fullText);
              } else if (data.type === 'done') {
                // 完成 — 添加来源引用
                if (data.sources && data.sources.length > 0) {
                  fullText += '\n\n---\n📌 **参考来源:**\n';
                  data.sources.forEach((s, i) => {
                    fullText += `\n<span class="citation">📄 ${escapeHtml(s.filename)}</span>`;
                  });
                }
                renderBubble(bubble, fullText);
              } else if (data.error) {
                bubble.innerHTML = '<p style="color:#ef4444">❌ ' + escapeHtml(data.error) + '</p>';
              }
            } catch (e) {
              // JSON 解析失败，保留在 buffer
              buffer = line + '\n';
            }
          } else if (line !== '') {
            buffer += line + '\n';
          }
        }
      }
    } catch (err) {
      bubble.innerHTML = '<p style="color:#ef4444">❌ 网络错误: ' + escapeHtml(err.message) + '</p>';
    }

    // 将本轮对话追加到 localStorage 消息缓存
    const cached = getLocalMessages(currentSessionId);
    cached.push({ role: 'user', content: query });
    cached.push({ role: 'assistant', content: fullText });
    saveLocalMessages(currentSessionId, cached);

    // 更新记忆状态、会话列表并滚动
    updateMemoryInfo();
    updateLocalSession(currentSessionId, {
      turn_count: Math.floor(cached.length / 2),
      preview: query.substring(0, 30),
    });
    renderSessionList();
    scrollToBottom();

    isSending = false;
    sendBtn.disabled = false;
    sendBtn.classList.remove('sending');
    sendBtn.textContent = '▶';
  }

  // 追加消息元素
  function appendMessage(role, text, isStreaming = false) {
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.innerHTML = `
      <div class="avatar">${role === 'user' ? '👤' : '🤖'}</div>
      <div class="bubble${isStreaming ? ' typing-cursor' : ''}"></div>
    `;

    if (!isStreaming && text) {
      div.querySelector('.bubble').innerHTML = marked.parse(text);
    }

    messagesContainer.appendChild(div);
    scrollToBottom();
    return div;
  }

  // 渲染 Markdown 到气泡
  function renderBubble(bubble, text) {
    bubble.innerHTML = marked.parse(text);
    // 移除光标效果（如果还在流式）
    bubble.classList.remove('typing-cursor');
    if (isSending) {
      bubble.classList.add('typing-cursor');
    }
    scrollToBottom();
  }

  // 滚动到底部
  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // 事件监听
  sendBtn.addEventListener('click', sendMessage);

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // 自动调整输入框高度
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 150) + 'px';
  });
});
