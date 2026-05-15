/* Academic Copy Studio — unified v1.0 */

const PRESET_KEY = 'copygen_kw_presets';

const S = {
  keywords: [],
  activeHistoryId: null,
  editingTemplate: null,
  historyKeywords: [],
  lastVariants: [],
  llmConfig: { has_key: false, provider: 'deepseek' },
  batchResults: [],
  dictRaw: null,
  templateFilter: '',
  kwStaging: [],
  exportItems: [],
  historyPageId: null,
};

const $ = (s, p) => (p || document).querySelector(s);
const $$ = (s, p) => [...(p || document).querySelectorAll(s)];

const PAGE_TITLES = {
  dashboard: '工作台概览',
  chat: '对话生成',
  batch: '批量生成',
  history: '历史中心',
  keywords: '关键词库',
  export: '导出中心',
  checker: '合规检测',
  templates: '文案模板',
  settings: '设置',
};

// ── Utils ──────────────────────────────────
function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  el.className = 'toast show';
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = 'toast'; }, 2400);
}

async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  let body = opts.body;
  if (body !== undefined && typeof body !== 'string') {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  } else if (typeof body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  const r = await fetch(path, { ...opts, headers, body });
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail || (await r.text()); } catch { /* */ }
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return r.json();
}

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escAttr(s) {
  return esc(s).replace(/"/g, '&quot;');
}

function fmtDate(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso.slice(0, 16);
  }
}

// ── Navigation ─────────────────────────────
function switchView(name) {
  $$('.view').forEach((v) => v.classList.remove('active'));
  const view = $(`#view-${name}`);
  if (view) view.classList.add('active');
  $$('.nav-item[data-view]').forEach((n) => {
    n.classList.toggle('active', n.dataset.view === name);
  });
  $('#pageTitle').textContent = PAGE_TITLES[name] || name;
  closeSidebar();
  if (name === 'dashboard') loadDashboard();
  if (name === 'history') loadHistoryPage();
  if (name === 'keywords') loadKeywordsPage();
  if (name === 'export') loadExportPage();
  if (name === 'settings') loadSettings();
  if (name === 'templates') loadTemplates();
  if (name === 'batch') $('#batchResults').innerHTML = '';
}

function openSidebar() {
  $('#sidebar').classList.add('open');
  $('#sidebarBackdrop').hidden = false;
  $('#sidebarBackdrop').classList.add('show');
}

function closeSidebar() {
  $('#sidebar').classList.remove('open');
  $('#sidebarBackdrop').classList.remove('show');
  $('#sidebarBackdrop').hidden = true;
}

$('#btnMenu')?.addEventListener('click', openSidebar);
$('#sidebarBackdrop')?.addEventListener('click', closeSidebar);

// ── Stats & history ──────────────────────
async function loadStats() {
  try {
    const resp = await api('/api/stats');
    $('#statTotal').textContent = resp.data.total_generations ?? 0;
    $('#statTemplates').textContent = resp.data.template_count ?? 0;
  } catch { /* ignore */ }
}

async function loadHistoryList(search = '') {
  if ($('#historyPageList')) {
    await loadHistoryPage($('#historyPageSearch')?.value.trim() || search);
  }
  await loadSidebarRecent();
}

async function openHistoryItem(id) {
  try {
    const { data: item } = await api(`/api/history/${id}`);
    if (!item) return;
    S.activeHistoryId = id;
    S.historyKeywords = [...(item.keywords || [])];
    S.lastVariants = JSON.parse(JSON.stringify(item.variants || []));
    switchView('chat');
    $('#chatArea').innerHTML = '';
    addUserMessage(item.keywords);
    const safe = item.meta?.violations_check?.safe ?? true;
    addAssistantMessage(item.keywords, item.variants, safe, false);
    showHistoryBanner(item);
    loadHistoryList();
  } catch (e) {
    toast('加载失败: ' + e.message);
  }
}

function showHistoryBanner(item) {
  const banner = $('#historyBanner');
  if (!banner) return;
  banner.hidden = false;
  $('#historyBannerTitle').textContent = (item.keywords || []).join(' ');
  const meta = item.meta || {};
  const parts = [fmtDate(item.created_at), `${(item.variants || []).length} 个版本`];
  if (meta.use_llm && meta.llm_provider) parts.push(`LLM: ${meta.llm_provider}`);
  $('#historyBannerMeta').textContent = parts.join(' · ');
}

function hideHistoryBanner() {
  const banner = $('#historyBanner');
  if (banner) banner.hidden = true;
  S.activeHistoryId = null;
  S.historyKeywords = [];
}

async function persistHistoryVariants(variants) {
  if (!S.activeHistoryId) return;
  try {
    await api(`/api/history/${S.activeHistoryId}`, {
      method: 'PUT',
      body: { variants },
    });
    S.lastVariants = variants;
  } catch { /* ignore */ }
}

$('#btnDismissHistory')?.addEventListener('click', hideHistoryBanner);

$('#btnRegenFromHistory')?.addEventListener('click', () => {
  if (!S.historyKeywords.length) return;
  S.keywords = [...S.historyKeywords];
  renderKwTags();
  hideHistoryBanner();
  doGenerate();
});

$('#btnCompareVersions')?.addEventListener('click', () => openCompareModal(S.lastVariants));
$('#btnCloseCompare')?.addEventListener('click', () => $('#compareModal')?.close());

function openCompareModal(variants) {
  if (!variants?.length) {
    toast('暂无可对比的版本');
    return;
  }
  const grid = $('#compareGrid');
  grid.innerHTML = variants.map((v, i) => `
    <article class="compare-col">
      <h4>版本 ${i + 1} · ${esc(styleLabel(v.style))}</h4>
      <p class="compare-title">${esc(v.title)}</p>
      <pre class="compare-body">${esc(v.body)}</pre>
    </article>
  `).join('');
  $('#compareModal')?.showModal();
}


// ── Keywords & send ──────────────────────
function renderKwTags() {
  const kwTags = $('#kwTags');
  if (!kwTags) return;
  kwTags.innerHTML = S.keywords.map((k, i) =>
    `<span class="kw-tag">${esc(k)}<span class="rm" data-i="${i}">×</span></span>`
  ).join('');
  $$('.rm', kwTags).forEach((el) => {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      S.keywords.splice(parseInt(el.dataset.i, 10), 1);
      renderKwTags();
      updateSendState();
    });
  });
  updateSendState();
}

function updateSendState() {
  const btnSend = $('#btnSend');
  const chatInput = $('#chatInput');
  if (!btnSend) return;
  btnSend.disabled = S.keywords.length === 0 && !(chatInput?.value.trim());
}

function bindChatInput() {
  const chatInput = $('#chatInput');
  const btnSend = $('#btnSend');
  if (!chatInput || !btnSend) return;

  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const raw = chatInput.value.trim();
      if (raw) {
        raw.split(/\s+/).filter(Boolean).forEach((w) => {
          if (!S.keywords.includes(w)) S.keywords.push(w);
        });
        chatInput.value = '';
        renderKwTags();
      }
      if (S.keywords.length > 0) doGenerate();
    }
    if (e.key === 'Backspace' && chatInput.value === '' && S.keywords.length > 0) {
      S.keywords.pop();
      renderKwTags();
    }
  });

  chatInput.addEventListener('input', updateSendState);
  btnSend.addEventListener('click', () => {
    if (S.keywords.length > 0) doGenerate();
  });
}

function runQuickSearch(text) {
  const words = text.split(/\s+/).filter(Boolean);
  words.forEach((w) => { if (!S.keywords.includes(w)) S.keywords.push(w); });
  renderKwTags();
  switchView('chat');
  doGenerate();
}

// ── Generate ─────────────────────────────
async function doGenerate() {
  if (S.keywords.length === 0) return;
  const keywords = [...S.keywords];
  const style = $('#chatStyle').value;
  const versionCount = parseInt($('#chatVersions').value, 10);
  const llmProvider = $('#chatLLM').value;
  if (llmProvider && !S.llmConfig.has_key) {
    toast('请先在设置中配置 LLM API Key');
    switchView('settings');
    $$('.stab').forEach((t) => t.classList.toggle('active', t.dataset.stab === 'llm'));
    $$('.sp').forEach((p) => p.classList.toggle('active', p.id === 'sp-llm'));
    return;
  }

  hideHistoryBanner();
  const welcome = $('#chatWelcome');
  if (welcome) welcome.remove();

  addUserMessage(keywords);
  S.keywords = [];
  renderKwTags();
  const btnSend = $('#btnSend');
  if (btnSend) btnSend.disabled = true;

  const loadId = addLoadingMessage();

  try {
    const body = {
      keywords,
      style,
      version_count: versionCount,
      use_llm: !!llmProvider,
      llm: llmProvider ? { provider: llmProvider } : {},
    };
    const resp = await api('/api/generate', { method: 'POST', body });
    removeMessage(loadId);
    const safe = resp.data.violations_check?.safe ?? true;
    S.lastVariants = resp.data.variants;
    addAssistantMessage(keywords, resp.data.variants, safe, true);
    if (resp.data.history_id) S.activeHistoryId = resp.data.history_id;
    loadHistoryList();
    loadStats();
  } catch (e) {
    removeMessage(loadId);
    toast('生成失败: ' + e.message);
  }
}

// ── Messages ─────────────────────────────
let msgIdCounter = 0;

function addUserMessage(keywords) {
  const area = $('#chatArea');
  const div = document.createElement('div');
  div.className = 'msg user';
  div.innerHTML = `
    <div class="msg-avatar">我</div>
    <div class="msg-content">
      <div class="msg-kw-tags">${keywords.map((k) => `<span class="msg-kw-tag">${esc(k)}</span>`).join('')}</div>
      <div class="msg-bubble-user">生成「${esc(keywords.join(' '))}」方向文案</div>
    </div>`;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
}

function addLoadingMessage() {
  const id = 'msg-loading';
  const area = $('#chatArea');
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.id = id;
  div.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-content">
      <div class="loading-dots"><span></span><span></span><span></span></div>
    </div>`;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
  return id;
}

function styleLabel(style) {
  const map = { comprehensive: '标准版', concise_casual: '简洁版', case_led: '案例版' };
  return map[style] || style;
}

function addAssistantMessage(keywords, variants, safe, scroll = true) {
  S.lastVariants = variants;
  const area = $('#chatArea');
  const wrap = document.createElement('div');
  wrap.className = 'msg assistant';

  let cards = '';
  variants.forEach((v, i) => {
    cards += `
    <article class="variant-card" data-idx="${i}">
      <div class="variant-head">
        <div>
          <span class="variant-title-label">版本 ${i + 1}</span>
          <span class="variant-style">${esc(styleLabel(v.style))}</span>
        </div>
        <span class="badge ${safe ? 'ok' : 'warn'}">${safe ? '✓ 合规' : '⚠ 违禁词'}</span>
      </div>
      <h4 class="copy-title">${esc(v.title)}</h4>
      <div class="copy-body">${esc(v.body)}</div>
      <div class="copy-meta">${v.body.length} 字</div>
      <div class="msg-actions">
        <button type="button" class="msg-btn primary" data-action="copy" data-idx="${i}">复制全文</button>
        <button type="button" class="msg-btn" data-action="export-txt" data-idx="${i}">导出 TXT</button>
        <button type="button" class="msg-btn" data-action="edit" data-idx="${i}">编辑</button>
        <button type="button" class="msg-btn" data-action="check" data-idx="${i}">检测敏感词</button>
        <button type="button" class="msg-btn" data-action="sanitize" data-idx="${i}">一键净化</button>
      </div>
      <input class="msg-edit-title" data-edit-idx="${i}" style="display:none" value="${escAttr(v.title)}">
      <textarea class="msg-edit-area" data-edit-idx="${i}" style="display:none">${esc(v.body)}</textarea>
      <div class="msg-actions" data-edit-actions="${i}" style="display:none;margin-top:10px">
        <button type="button" class="msg-btn primary" data-action="saveEdit" data-idx="${i}">保存</button>
        <button type="button" class="msg-btn" data-action="cancelEdit" data-idx="${i}">取消</button>
      </div>
    </article>`;
  });

  wrap.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-content">
      <div class="msg-actions" style="margin-bottom:12px">
        <button type="button" class="msg-btn" data-action="export-all">导出全部 (TXT)</button>
        <button type="button" class="msg-btn" data-action="export-json">导出 JSON</button>
      </div>
      ${cards}
    </div>`;

  area.appendChild(wrap);
  bindMsgActions(wrap, variants);
  if (scroll) area.scrollTop = area.scrollHeight;
}

function bindMsgActions(container, variants) {
  container.querySelectorAll('[data-action="copy"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const i = parseInt(btn.dataset.idx, 10);
      const v = variants[i];
      navigator.clipboard.writeText(`标题: ${v.title}\n\n${v.body}`).then(() => toast('已复制到剪贴板'));
    });
  });

  container.querySelectorAll('[data-action="export-txt"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const i = parseInt(btn.dataset.idx, 10);
      await downloadExport([variants[i]], 'txt', `copy-v${i + 1}.txt`);
    });
  });

  container.querySelector('[data-action="export-all"]')?.addEventListener('click', () => {
    downloadExport(variants, 'txt', 'copy-all.txt');
  });

  container.querySelector('[data-action="export-json"]')?.addEventListener('click', () => {
    downloadExport(variants, 'json', 'copy-all.json');
  });

  container.querySelectorAll('[data-action="edit"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const i = parseInt(btn.dataset.idx, 10);
      const card = btn.closest('.variant-card');
      const titleEl = card.querySelector(`.msg-edit-title[data-edit-idx="${i}"]`);
      const bodyEl = card.querySelector(`.msg-edit-area[data-edit-idx="${i}"]`);
      const actions = card.querySelector(`[data-edit-actions="${i}"]`);
      const on = titleEl.style.display === 'block';
      titleEl.style.display = on ? 'none' : 'block';
      bodyEl.style.display = on ? 'none' : 'block';
      actions.style.display = on ? 'none' : 'flex';
    });
  });

  container.querySelectorAll('[data-action="saveEdit"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const i = parseInt(btn.dataset.idx, 10);
      const card = btn.closest('.variant-card');
      variants[i].title = card.querySelector(`.msg-edit-title[data-edit-idx="${i}"]`).value;
      variants[i].body = card.querySelector(`.msg-edit-area[data-edit-idx="${i}"]`).value;
      card.querySelector('.copy-title').textContent = variants[i].title;
      card.querySelector('.copy-body').textContent = variants[i].body;
      card.querySelector('.copy-meta').textContent = variants[i].body.length + ' 字';
      card.querySelector(`.msg-edit-title[data-edit-idx="${i}"]`).style.display = 'none';
      card.querySelector(`.msg-edit-area[data-edit-idx="${i}"]`).style.display = 'none';
      card.querySelector(`[data-edit-actions="${i}"]`).style.display = 'none';
      persistHistoryVariants(variants);
      toast('已保存修改');
    });
  });

  container.querySelectorAll('[data-action="cancelEdit"]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const i = parseInt(btn.dataset.idx, 10);
      const card = btn.closest('.variant-card');
      card.querySelector(`.msg-edit-title[data-edit-idx="${i}"]`).value = variants[i].title;
      card.querySelector(`.msg-edit-area[data-edit-idx="${i}"]`).value = variants[i].body;
      card.querySelector(`.msg-edit-title[data-edit-idx="${i}"]`).style.display = 'none';
      card.querySelector(`.msg-edit-area[data-edit-idx="${i}"]`).style.display = 'none';
      card.querySelector(`[data-edit-actions="${i}"]`).style.display = 'none';
    });
  });

  container.querySelectorAll('[data-action="check"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const i = parseInt(btn.dataset.idx, 10);
      const v = variants[i];
      try {
        const resp = await api('/api/check', { method: 'POST', body: { text: v.title + '\n' + v.body } });
        toast(resp.safe ? '未检测到违禁词' : '发现: ' + (resp.violations || []).join(', '));
      } catch {
        toast('检测失败');
      }
    });
  });

  container.querySelectorAll('[data-action="sanitize"]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const i = parseInt(btn.dataset.idx, 10);
      const v = variants[i];
      try {
        const [tResp, bResp] = await Promise.all([
          api('/api/check', { method: 'POST', body: { text: v.title } }),
          api('/api/check', { method: 'POST', body: { text: v.body } }),
        ]);
        let changed = false;
        if (tResp.changed) { v.title = tResp.sanitized; changed = true; }
        if (bResp.changed) { v.body = bResp.sanitized; changed = true; }
        const card = btn.closest('.variant-card');
        card.querySelector('.copy-title').textContent = v.title;
        card.querySelector('.copy-body').textContent = v.body;
        card.querySelector('.copy-meta').textContent = v.body.length + ' 字';
        toast(changed ? '已净化文案' : '无需修改');
      } catch {
        toast('净化失败');
      }
    });
  });
}

async function downloadExport(variants, fmt, filename) {
  try {
    const resp = await api('/api/export', { method: 'POST', body: { variants, format: fmt } });
    const blob = new Blob([resp.content], { type: fmt === 'json' ? 'application/json' : 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
    toast('已下载');
  } catch (e) {
    toast('导出失败: ' + e.message);
  }
}

function removeMessage(id) {
  document.getElementById(id)?.remove();
}



// ── Batch ────────────────────────────────
$('#btnBatchRun')?.addEventListener('click', async () => {
  const lines = $('#batchInput').value.split('\n').map((l) => l.trim()).filter(Boolean);
  if (!lines.length) {
    toast('请至少输入一行关键词');
    return;
  }
  const llmProvider = $('#batchLLM')?.value || '';
  if (llmProvider && !S.llmConfig.has_key) {
    toast('请先在设置中配置 LLM API Key');
    return;
  }
  const keywordSets = lines.map((l) => l.split(/\s+/).filter(Boolean));
  const style = $('#batchStyle').value;
  const out = $('#batchResults');
  const prog = $('#batchProgress');
  const fill = $('#batchProgressFill');
  const progLabel = $('#batchProgressLabel');
  const toolbar = $('#batchToolbar');
  out.innerHTML = '';
  if (toolbar) toolbar.hidden = true;
  if (prog) {
    prog.hidden = false;
    fill.style.width = '10%';
    progLabel.textContent = '正在生成…';
  }
  $('#btnBatchRun').disabled = true;

  try {
    const resp = await api('/api/generate-batch', {
      method: 'POST',
      body: {
        keyword_sets: keywordSets,
        style,
        use_llm: !!llmProvider,
        llm: llmProvider ? { provider: llmProvider } : {},
      },
    });
    if (fill) fill.style.width = '100%';
    S.batchResults = resp.data.results || [];
    out.innerHTML = S.batchResults.map((r, idx) => {
      const v = r.variants[0] || {};
      const safe = r.violations_check?.safe;
      return `<article class="batch-item">
        <h4>#${idx + 1} · ${esc((r.keywords || []).join(' '))}
          <span class="badge ${safe ? 'ok' : 'warn'}" style="margin-left:8px;font-size:10px">${safe ? '合规' : '违禁'}</span>
        </h4>
        <p class="copy-title" style="border:none;padding:0">${esc(v.title || '')}</p>
        <div class="copy-body">${esc(v.body || '')}</div>
        <div class="msg-actions">
          <button type="button" class="msg-btn primary batch-copy" data-i="${idx}">复制</button>
          <button type="button" class="msg-btn batch-to-chat" data-i="${idx}">填入对话</button>
        </div>
      </article>`;
    }).join('');

    out.querySelectorAll('.batch-copy').forEach((btn) => {
      btn.addEventListener('click', () => {
        const v = S.batchResults[parseInt(btn.dataset.i, 10)].variants[0];
        navigator.clipboard.writeText(`标题: ${v.title}\n\n${v.body}`);
        toast('已复制');
      });
    });
    out.querySelectorAll('.batch-to-chat').forEach((btn) => {
      btn.addEventListener('click', () => {
        S.keywords = [...S.batchResults[parseInt(btn.dataset.i, 10)].keywords];
        renderKwTags();
        switchView('chat');
        toast('关键词已填入对话');
      });
    });
    if (toolbar) {
      toolbar.hidden = false;
      $('#batchSummary').textContent = `共 ${resp.data.total} 组`;
    }
    loadStats();
    loadHistoryList();
    toast(`完成 ${resp.data.total} 组`);
  } catch (e) {
    out.innerHTML = `<p class="muted">失败: ${esc(e.message)}</p>`;
    toast('批量生成失败: ' + e.message);
  } finally {
    $('#btnBatchRun').disabled = false;
    if (prog) setTimeout(() => { prog.hidden = true; }, 500);
  }
});

$('#btnBatchExportAll')?.addEventListener('click', async () => {
  const allVariants = S.batchResults.flatMap((r) => r.variants || []);
  if (!allVariants.length) return toast('无内容可导出');
  await downloadExport(allVariants, 'txt', `batch-${Date.now()}.txt`);
});

// ── Templates ────────────────────────────
async function loadTemplates() {
  const grid = $('#templateGrid');
  const q = (S.templateFilter || $('#templateSearch')?.value || '').trim().toLowerCase();
  try {
    const resp = await api('/api/templates');
    let items = resp.data || [];
    if (q) items = items.filter((t) => (t.name || '').toLowerCase().includes(q));
    if (!items.length) {
      grid.innerHTML = '<p class="empty-state">暂无模板，点击「新建模板」添加</p>';
      return;
    }
    grid.innerHTML = items.map((t) => `
      <article class="tpl-card">
        <h4>${esc(t.name)}</h4>
        <pre>${esc((t.content || '').slice(0, 200))}${(t.content || '').length > 200 ? '…' : ''}</pre>
        <span class="muted">${fmtDate(t.updated_at)}</span>
        <div class="tpl-actions">
          <button type="button" class="msg-btn primary" data-tpl-use="${escAttr(t.name)}">使用</button>
          <button type="button" class="msg-btn" data-tpl-copy="${escAttr(t.name)}">复制</button>
          <button type="button" class="msg-btn" data-tpl-edit="${escAttr(t.name)}">编辑</button>
          <button type="button" class="msg-btn" data-tpl-del="${escAttr(t.name)}">删除</button>
        </div>
      </article>
    `).join('');

    const all = resp.data || [];
    grid.querySelectorAll('[data-tpl-use]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const t = all.find((x) => x.name === btn.dataset.tplUse);
        if (!t) return;
        chatInput.value = (t.content || '').trim();
        switchView('chat');
        chatInput.focus();
        toast('模板内容已填入输入框');
      });
    });
    grid.querySelectorAll('[data-tpl-copy]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const t = all.find((x) => x.name === btn.dataset.tplCopy);
        if (t) navigator.clipboard.writeText(t.content || '').then(() => toast('已复制'));
      });
    });

    grid.querySelectorAll('[data-tpl-edit]').forEach((btn) => {
      btn.addEventListener('click', () => openTemplateModal(btn.dataset.tplEdit));
    });
    grid.querySelectorAll('[data-tpl-del]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        if (!confirm(`删除模板「${btn.dataset.tplDel}」？`)) return;
        await api(`/api/templates/${encodeURIComponent(btn.dataset.tplDel)}`, { method: 'DELETE' });
        loadTemplates();
        loadStats();
        toast('已删除');
      });
    });
  } catch {
    grid.innerHTML = '<p class="empty-state">加载失败</p>';
  }
}

const templateModal = $('#templateModal');

function openTemplateModal(name = null) {
  S.editingTemplate = name;
  $('#templateModalTitle').textContent = name ? '编辑模板' : '新建模板';
  $('#tplName').value = name || '';
  $('#tplName').disabled = !!name;
  $('#tplContent').value = '';
  if (name) {
    api('/api/templates').then((resp) => {
      const t = (resp.data || []).find((x) => x.name === name);
      if (t) $('#tplContent').value = t.content || '';
    });
  }
  templateModal.showModal();
}

$('#btnNewTemplate')?.addEventListener('click', () => openTemplateModal());
$('#btnTplCancel')?.addEventListener('click', () => templateModal.close());

$('#templateForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = $('#tplName').value.trim();
  const content = $('#tplContent').value;
  try {
    if (S.editingTemplate) {
      await api(`/api/templates/${encodeURIComponent(S.editingTemplate)}`, {
        method: 'PUT',
        body: { content },
      });
    } else {
      await api('/api/templates', { method: 'POST', body: { name, content } });
    }
    templateModal.close();
    loadTemplates();
    loadStats();
    toast('模板已保存');
  } catch (err) {
    toast('保存失败: ' + err.message);
  }
});

// ── Settings ─────────────────────────────
const PROFILE_FIELDS = [
  ['identity', '身份描述'],
  ['highlight', '亮点'],
  ['contact', '联系方式引导'],
  ['extra', '补充说明'],
];

function renderProfileForm(data) {
  const grid = $('#profileForm');
  grid.innerHTML = PROFILE_FIELDS.map(([key, label]) => `
    <div class="form-row">
      <label>${label}</label>
      <input class="input" data-pkey="${key}" value="${escAttr(data[key] || '')}">
    </div>
  `).join('');

  if (Array.isArray(data.role_tags)) {
    grid.innerHTML += `
      <div class="form-row">
        <label>角色标签（逗号分隔）</label>
        <input class="input" id="profileRoleTags" value="${escAttr(data.role_tags.join('，'))}">
      </div>`;
  }
  if (Array.isArray(data.audience)) {
    grid.innerHTML += `
      <div class="form-row">
        <label>目标受众（逗号分隔）</label>
        <input class="input" id="profileAudience" value="${escAttr(data.audience.join('，'))}">
      </div>`;
  }
}

function collectProfileFromForm(base) {
  const data = { ...base };
  $$('#profileForm [data-pkey]').forEach((inp) => {
    data[inp.dataset.pkey] = inp.value;
  });
  const tags = $('#profileRoleTags');
  if (tags) data.role_tags = tags.value.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
  const aud = $('#profileAudience');
  if (aud) data.audience = aud.value.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
  return data;
}

async function loadSettings() {
  try {
    const p = await api('/api/profile');
    $('#editProfile').value = JSON.stringify(p.data, null, 2);
    renderProfileForm(p.data);
  } catch { /* */ }

  try {
    const s = await api('/api/services');
    $('#editServices').value = JSON.stringify(s.data, null, 2);
    renderServicesForm(s.data);
  } catch { /* */ }

  try {
    const st = await api('/api/style');
    renderStyleForm(st.data);
  } catch { /* */ }

  try {
    const w = await api('/api/sensitive-words');
    renderDict(w.data);
  } catch { /* */ }

  try {
    const c = await api('/api/llm-config');
    const d = c.data || {};
    $('#llmCfgProvider').value = d.provider || 'deepseek';
    $('#llmCfgUrl').value = d.base_url || '';
    $('#llmCfgModel').value = d.model || '';
    $('#llmCfgKey').value = '';
    $('#llmCfgKey').placeholder = d.has_key ? '已配置，留空不修改' : 'sk-...';
    $('#llmKeyHint').textContent = d.has_key ? `当前: ${d.key_hint}` : '未配置 API Key';
  } catch { /* */ }
}

function linesToArr(text) {
  return text.split('\n').map((s) => s.trim()).filter(Boolean);
}

function renderServicesForm(data) {
  const el = $('#servicesForm');
  if (!el) return;
  el.innerHTML = `
    <div class="form-row">
      <label>服务类型（每行一条）</label>
      <textarea class="textarea" id="svcTypes" rows="6">${esc((data.service_types || []).join('\n'))}</textarea>
    </div>
    <div class="form-row">
      <label>期刊 / 会议级别（每行一条）</label>
      <textarea class="textarea" id="svcLevels" rows="6">${esc((data.levels || []).join('\n'))}</textarea>
    </div>
    <div class="form-row">
      <label>代表会议（每行一条）</label>
      <textarea class="textarea" id="svcConfs" rows="4">${esc((data.featured_conferences || []).join('\n'))}</textarea>
    </div>
    <div class="form-row">
      <label>交叉方向（每行一条）</label>
      <textarea class="textarea" id="svcCross" rows="3">${esc((data.cross_fields || []).join('\n'))}</textarea>
    </div>
    <div class="form-row">
      <label>默认标签（每行一条）</label>
      <textarea class="textarea" id="svcTags" rows="3">${esc((data.default_tags || []).join('\n'))}</textarea>
    </div>
    <p class="muted">研究方向 domains 请在下方 JSON 中维护（结构较复杂）</p>`;
}

function collectServicesFromForm(base) {
  const data = { ...base };
  const t = $('#svcTypes');
  if (t) data.service_types = linesToArr(t.value);
  const l = $('#svcLevels');
  if (l) data.levels = linesToArr(l.value);
  const c = $('#svcConfs');
  if (c) data.featured_conferences = linesToArr(c.value);
  const x = $('#svcCross');
  if (x) data.cross_fields = linesToArr(x.value);
  const g = $('#svcTags');
  if (g) data.default_tags = linesToArr(g.value);
  return data;
}

function renderStyleForm(data) {
  const el = $('#styleForm');
  if (!el) return;
  el.innerHTML = `
    <div class="form-row">
      <label>默认生成版本数</label>
      <select class="select" id="styleVersionCount">
        ${[1, 2, 3].map((n) => `<option value="${n}" ${data.version_count === n ? 'selected' : ''}>${n}</option>`).join('')}
      </select>
    </div>
    <div class="form-row">
      <label>语气描述</label>
      <input class="input" id="styleTone" value="${escAttr(data.tone || '')}">
    </div>
    <div class="form-row">
      <label>标题最大字数</label>
      <input class="input" type="number" id="styleMaxTitle" value="${data.max_title_len ?? 30}">
    </div>
    <div class="form-row">
      <label>正文最大字数</label>
      <input class="input" type="number" id="styleMaxBody" value="${data.max_body_len ?? 500}">
    </div>`;
}

function collectStyleFromForm(base) {
  const data = { ...base };
  const vc = $('#styleVersionCount');
  if (vc) data.version_count = parseInt(vc.value, 10);
  const tone = $('#styleTone');
  if (tone) data.tone = tone.value;
  const mt = $('#styleMaxTitle');
  if (mt) data.max_title_len = parseInt(mt.value, 10);
  const mb = $('#styleMaxBody');
  if (mb) data.max_body_len = parseInt(mb.value, 10);
  return data;
}

let dictFilter = '';

function renderDict(data, filter = '') {
  S.dictRaw = data;
  const grid = $('#dictGrid');
  const q = (filter || dictFilter || '').trim().toLowerCase();
  const sections = [
    ['直接替换', data.direct_replace || {}],
    ['上下文替换', data.context_replace || {}],
    ['短语替换', data.phrase_replace || {}],
    ['绝对禁止', Object.fromEntries((data.must_avoid || []).map((w) => [w, '屏蔽']))],
  ];
  grid.innerHTML = sections.map(([title, items]) => {
    let entries = Object.entries(items);
    if (q) entries = entries.filter(([f, t]) => f.toLowerCase().includes(q) || String(t).toLowerCase().includes(q));
    const rows = entries.slice(0, 30).map(([f, t]) =>
      `<div class="dict-row"><span class="dict-from">${esc(f)}</span><span>→</span><span class="dict-to">${esc(t || '(删除)')}</span></div>`
    ).join('');
    const more = entries.length > 30 ? `<p class="muted" style="margin-top:8px">显示 30 / ${entries.length} 条</p>` : '';
    return `<div class="dict-section"><h4>${title}</h4>${rows || '<p class="muted">无匹配</p>'}${more}</div>`;
  }).join('');
}

$('#dictSearch')?.addEventListener('input', (e) => {
  dictFilter = e.target.value;
  if (S.dictRaw) renderDict(S.dictRaw, dictFilter);
});

$('#templateSearch')?.addEventListener('input', (e) => {
  S.templateFilter = e.target.value;
  loadTemplates();
});

$$('.stab').forEach((tab) => {
  tab.addEventListener('click', () => {
    $$('.stab').forEach((t) => t.classList.remove('active'));
    tab.classList.add('active');
    $$('.sp').forEach((p) => p.classList.remove('active'));
    $(`#sp-${tab.dataset.stab}`).classList.add('active');
    if (tab.dataset.stab === 'style') {
      api('/api/style').then((r) => renderStyleForm(r.data));
    }
    if (tab.dataset.stab === 'words') {
      api('/api/sensitive-words').then((r) => renderDict(r.data));
    }
    if (tab.dataset.stab === 'llm') {
      api('/api/llm-config').then((r) => {
        const d = r.data || {};
        $('#llmKeyHint').textContent = d.has_key ? `当前: ${d.key_hint}` : '未配置 API Key';
      });
    }
  });
});

$('#btnSaveProfile')?.addEventListener('click', async () => {
  try {
    let data = {};
    try {
      data = JSON.parse($('#editProfile').value);
    } catch { /* use form only */ }
    data = collectProfileFromForm(data);
    await api('/api/profile', { method: 'PUT', body: data });
    $('#editProfile').value = JSON.stringify(data, null, 2);
    toast('个人资料已保存');
  } catch {
    toast('保存失败，请检查表单或 JSON');
  }
});

$('#editProfile')?.addEventListener('blur', () => {
  try {
    renderProfileForm(JSON.parse($('#editProfile').value));
  } catch { /* */ }
});

$('#btnSaveServices')?.addEventListener('click', async () => {
  try {
    let data = {};
    try { data = JSON.parse($('#editServices').value); } catch { /* */ }
    data = collectServicesFromForm(data);
    await api('/api/services', { method: 'PUT', body: data });
    $('#editServices').value = JSON.stringify(data, null, 2);
    toast('服务项目已保存');
  } catch {
    toast('保存失败，请检查 JSON');
  }
});

$('#btnSaveStyle')?.addEventListener('click', async () => {
  try {
    const base = await api('/api/style');
    const data = collectStyleFromForm(base.data);
    await api('/api/style', { method: 'PUT', body: data });
    const vc = $('#chatVersions');
    if (vc && data.version_count) vc.value = String(data.version_count);
    toast('生成风格已保存');
  } catch {
    toast('保存失败');
  }
});

$('#btnSaveLLM')?.addEventListener('click', async () => {
  try {
    const keyVal = $('#llmCfgKey').value.trim();
    await api('/api/llm-config', {
      method: 'PUT',
      body: {
        provider: $('#llmCfgProvider').value,
        api_key: keyVal || '__KEEP__',
        base_url: $('#llmCfgUrl').value.trim(),
        model: $('#llmCfgModel').value.trim(),
      },
    });
    $('#llmCfgKey').value = '';
    toast('LLM 配置已保存');
    await refreshLlmConfig();
  } catch (e) {
    toast('保存失败: ' + e.message);
  }
});

$('#btnTestLLM')?.addEventListener('click', async () => {
  try {
    const keyVal = $('#llmCfgKey').value.trim();
    const body = {
      provider: $('#llmCfgProvider').value,
      base_url: $('#llmCfgUrl').value.trim(),
      model: $('#llmCfgModel').value.trim(),
    };
    if (keyVal) body.api_key = keyVal;
    else body.api_key = '__KEEP__';
    const resp = await api('/api/llm-config/test', { method: 'POST', body });
    toast('连接成功: ' + (resp.data?.reply || 'OK'));
  } catch (e) {
    toast('测试失败: ' + e.message);
  }
});

async function refreshLlmConfig() {
  try {
    const c = await api('/api/llm-config');
    S.llmConfig = c.data || {};
    const provider = S.llmConfig.provider || 'deepseek';
    if ($('#llmCfgProvider')) $('#llmCfgProvider').value = provider;
    if ($('#chatLLM')) $('#chatLLM').value = '';
    if ($('#batchLLM')) $('#batchLLM').value = '';
    updateLlmStatus();
    if ($('#llmKeyHint')) {
      $('#llmKeyHint').textContent = S.llmConfig.has_key
        ? `当前: ${S.llmConfig.key_hint}` : '未配置 API Key';
    }
  } catch { /* */ }
}

function updateLlmStatus() {
  const el = $('#llmStatus');
  if (!el) return;
  if (S.llmConfig.has_key) {
    el.textContent = '●';
    el.className = 'llm-status ok';
    el.title = `已配置 ${S.llmConfig.provider || ''} (${S.llmConfig.key_hint || ''})`;
  } else {
    el.textContent = '○';
    el.className = 'llm-status warn';
    el.title = '未配置 API Key';
  }
}

$('#chatLLM')?.addEventListener('change', updateLlmStatus);
$('#llmCfgProvider')?.addEventListener('change', () => {
  S.llmConfig.provider = $('#llmCfgProvider').value;
  if ($('#chatLLM').value) $('#chatLLM').value = $('#llmCfgProvider').value;
});


function bindGlobalEvents() {
  document.addEventListener('click', (e) => {
    const chip = e.target.closest('.chip[data-quick]');
    if (chip?.dataset.quick) {
      runQuickSearch(chip.dataset.quick);
      return;
    }
    const nav = e.target.closest('[data-view]');
    if (!nav || nav.tagName === 'SECTION') return;
    const view = nav.dataset.view;
    if (!view) return;
    if (nav.classList.contains('nav-item') || nav.classList.contains('sb-link-full')
        || nav.classList.contains('quick-card')
        || (nav.classList.contains('btn-primary') && nav.dataset.view)) {
      switchView(view);
    }
  });
}

function resetChatWelcome() {
  const area = $('#chatArea');
  if (!area) return;
  area.innerHTML = "<div class=\"chat-welcome\" id=\"chatWelcome\">\n      <div class=\"welcome-icon\">\n        <svg width=\"40\" height=\"40\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"><path d=\"M12 20h9\"/><path d=\"M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z\"/></svg>\n      </div>\n      <h2>学术辅导文案生成</h2>\n      <p>输入研究方向关键词，一键生成闲鱼商品标题与详情，支持多风格版本与敏感词检测。</p>\n      <div class=\"welcome-chips\">\n        <button class=\"chip\" type=\"button\" data-quick=\"目标检测 YOLO 计算机视觉\">目标检测 · YOLO</button>\n        <button class=\"chip\" type=\"button\" data-quick=\"CCF论文 深度学习\">CCF · 深度学习</button>\n        <button class=\"chip\" type=\"button\" data-quick=\"NLP 大语言模型 LLM\">NLP · 大模型</button>\n        <button class=\"chip\" type=\"button\" data-quick=\"医学图像 人工智能\">医学图像 AI</button>\n        <button class=\"chip\" type=\"button\" data-quick=\"论文润色 期刊发表\">论文润色</button>\n        <button class=\"chip\" type=\"button\" data-quick=\"SCI论文 写作指导\">SCI 写作</button>\n      </div>\n    </div>";
}

function newChat() {
  S.keywords = [];
  hideHistoryBanner();
  renderKwTags();
  const btnSend = $('#btnSend');
  if (btnSend) btnSend.disabled = true;
  resetChatWelcome();
  switchView('chat');
}

// ── 工作台概览 ─────────────────────────────────────────
async function loadDashboard() {
  const metrics = $('#dashMetrics');
  const table = $('#dashRecentTable');
  const tags = $('#dashTopKeywords');
  const actions = $('#dashQuickActions');
  if (!metrics) return;

  try {
    const { data: d } = await api('/api/dashboard');
    metrics.innerHTML = `
      <div class="metric-card">
        <span class="metric-value">${d.total_generations ?? 0}</span>
        <span class="metric-label">累计生成</span>
      </div>
      <div class="metric-card">
        <span class="metric-value">${d.template_count ?? 0}</span>
        <span class="metric-label">文案模板</span>
      </div>
      <div class="metric-card ${d.llm_configured ? 'ok' : 'warn'}">
        <span class="metric-value">${d.llm_configured ? '已配置' : '未配置'}</span>
        <span class="metric-label">LLM · ${esc(d.llm_provider || '—')}</span>
      </div>
      <div class="metric-card">
        <span class="metric-value">${(d.top_keywords || []).length}</span>
        <span class="metric-label">活跃关键词</span>
      </div>`;

    const recent = d.recent || [];
    if (!recent.length) {
      table.innerHTML = '<p class="empty-state">暂无生成记录</p>';
    } else {
      table.innerHTML = `<table class="data-table">
        <thead><tr><th>关键词</th><th>版本</th><th>时间</th><th></th></tr></thead>
        <tbody>${recent.map((item) => `
          <tr>
            <td>${esc((item.keywords || []).join(' '))}</td>
            <td>${item.variant_count ?? 0}</td>
            <td class="muted">${esc(fmtDate(item.created_at))}</td>
            <td><button type="button" class="link-btn" data-open-history="${item.id}">查看</button></td>
          </tr>`).join('')}
        </tbody></table>`;
      table.querySelectorAll('[data-open-history]').forEach((btn) => {
        btn.addEventListener('click', () => {
          switchView('history');
          setTimeout(() => openHistoryPageItem(parseInt(btn.dataset.openHistory, 10)), 100);
        });
      });
    }

    tags.innerHTML = (d.top_keywords || []).map((k) =>
      `<button type="button" class="tag-btn" data-kw="${escAttr(k.word)}">${esc(k.word)} <small>${k.count}</small></button>`
    ).join('') || '<p class="muted">暂无数据</p>';

    tags.querySelectorAll('[data-kw]').forEach((btn) => {
      btn.addEventListener('click', () => {
        addKwStaging(btn.dataset.kw);
        switchView('keywords');
      });
    });

    actions.innerHTML = `
      <button type="button" class="quick-card" data-view="chat"><strong>对话生成</strong><span>单组关键词多版本</span></button>
      <button type="button" class="quick-card" data-view="batch"><strong>批量生成</strong><span>多行关键词一次铺货</span></button>
      <button type="button" class="quick-card" data-view="checker"><strong>合规检测</strong><span>敏感词检测与净化</span></button>
      <button type="button" class="quick-card" data-view="export"><strong>导出中心</strong><span>批量导出历史文案</span></button>`;

    $('#statTotal').textContent = d.total_generations ?? 0;
    $('#statTemplates').textContent = d.template_count ?? 0;
  } catch (e) {
    metrics.innerHTML = `<p class="muted">加载失败: ${esc(e.message)}</p>`;
  }
}

// ── 历史中心 ───────────────────────────────────────────
async function loadHistoryPage(search = '') {
  const list = $('#historyPageList');
  const count = $('#historyCount');
  if (!list) return;
  list.innerHTML = '<p class="muted">加载中…</p>';

  try {
    const q = search ? `?search=${encodeURIComponent(search)}&limit=200` : '?limit=200';
    const resp = await api(`/api/history${q}`);
    const items = resp.data || [];
    count.textContent = `(${items.length})`;
    S.exportItems = items;

    if (!items.length) {
      list.innerHTML = '<p class="empty-state">暂无历史记录</p>';
      $('#historyDetailPanel').innerHTML = '<p class="empty-state">选择左侧记录查看详情</p>';
      return;
    }

    list.innerHTML = items.map((item) => {
      const active = S.historyPageId === item.id ? ' active' : '';
      const label = (item.keywords || []).join(' ');
      const safe = item.meta?.violations_check?.safe !== false;
      return `<button type="button" class="history-row${active}" data-hid="${item.id}">
        <span class="history-row-title">${esc(label)}</span>
        <span class="history-row-meta">${esc(fmtDate(item.created_at))} · ${item.variant_count} 版
          <span class="badge ${safe ? 'ok' : 'warn'}" style="margin-left:6px">${safe ? '合规' : '违禁'}</span>
        </span>
      </button>`;
    }).join('');

    list.querySelectorAll('.history-row').forEach((btn) => {
      btn.addEventListener('click', () => openHistoryPageItem(parseInt(btn.dataset.hid, 10)));
    });

    if (S.historyPageId) openHistoryPageItem(S.historyPageId, false);
  } catch (e) {
    list.innerHTML = `<p class="muted">加载失败</p>`;
  }
}

async function openHistoryPageItem(id, scrollList = true) {
  S.historyPageId = id;
  try {
    const { data: item } = await api(`/api/history/${id}`);
    $('.history-row').forEach((r) => r.classList.toggle('active', parseInt(r.dataset.hid, 10) === id));
    const panel = $('#historyDetailPanel');
    const safe = item.meta?.violations_check?.safe !== false;
    panel.innerHTML = `
      <div class="detail-head">
        <h3>${esc((item.keywords || []).join(' '))}</h3>
        <p class="muted">${esc(fmtDate(item.created_at))} · 风格 ${esc(item.style)}</p>
        <div class="detail-actions">
          <button type="button" class="msg-btn primary" id="histOpenChat">在对话中打开</button>
          <button type="button" class="msg-btn" id="histCompare">版本对比</button>
          <button type="button" class="msg-btn" id="histDelete">删除</button>
        </div>
      </div>
      ${(item.variants || []).map((v, i) => `
        <article class="variant-card compact">
          <div class="variant-head">
            <span class="variant-title-label">版本 ${i + 1}</span>
            <span class="badge ${safe ? 'ok' : 'warn'}">${safe ? '合规' : '违禁'}</span>
          </div>
          <h4 class="copy-title">${esc(v.title)}</h4>
          <div class="copy-body">${esc(v.body)}</div>
          <button type="button" class="msg-btn primary hist-copy" data-i="${i}">复制</button>
        </article>`).join('')}`;

    $('#histOpenChat')?.addEventListener('click', () => {
      S.historyKeywords = [...(item.keywords || [])];
      S.activeHistoryId = id;
      switchView('chat');
      openHistoryItem(id);
    });
    $('#histCompare')?.addEventListener('click', () => openCompareModal(item.variants));
    $('#histDelete')?.addEventListener('click', async () => {
      if (!confirm('删除此记录？')) return;
      await api(`/api/history/${id}`, { method: 'DELETE' });
      S.historyPageId = null;
      loadHistoryPage($('#historyPageSearch')?.value.trim() || '');
      loadHistoryList();
      loadStats();
      toast('已删除');
    });
    panel.querySelectorAll('.hist-copy').forEach((btn) => {
      btn.addEventListener('click', () => {
        const v = item.variants[parseInt(btn.dataset.i, 10)];
        navigator.clipboard.writeText(`标题: ${v.title}\n\n${v.body}`);
        toast('已复制');
      });
    });
    if (scrollList) panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (e) {
    toast('加载详情失败');
  }
}

$('#historyPageSearch')?.addEventListener('input', (e) => {
  clearTimeout($('#historyPageSearch')._d);
  $('#historyPageSearch')._d = setTimeout(() => loadHistoryPage(e.target.value.trim()), 300);
});

$('#btnHistoryClearPage')?.addEventListener('click', async () => {
  if (!confirm('清空全部历史？')) return;
  await api('/api/history', { method: 'DELETE' });
  S.historyPageId = null;
  loadHistoryPage();
  loadHistoryList();
  loadStats();
  toast('已清空');
});

// ── 关键词库 ───────────────────────────────────────────
function loadPresets() {
  try {
    return JSON.parse(localStorage.getItem(PRESET_KEY) || '[]');
  } catch {
    return [];
  }
}

function savePresets(list) {
  localStorage.setItem(PRESET_KEY, JSON.stringify(list));
}

function renderKwStaging() {
  const el = $('#kwStaging');
  if (!el) return;
  if (!S.kwStaging.length) {
    el.innerHTML = '<p class="muted">点击左侧词库添加，或下方自定义输入</p>';
    return;
  }
  el.innerHTML = S.kwStaging.map((k, i) =>
    `<span class="kw-tag">${esc(k)}<span class="rm" data-ki="${i}">×</span></span>`
  ).join('');
  el.querySelectorAll('.rm').forEach((x) => {
    x.addEventListener('click', () => {
      S.kwStaging.splice(parseInt(x.dataset.ki, 10), 1);
      renderKwStaging();
    });
  });
}

function addKwStaging(word) {
  const w = (word || '').trim();
  if (!w || S.kwStaging.includes(w)) return;
  S.kwStaging.push(w);
  renderKwStaging();
}

async function loadKeywordsPage() {
  const acc = $('#domainAccordions');
  const presets = $('#presetList');
  if (!acc) return;
  renderKwStaging();

  try {
    const { data } = await api('/api/keywords');
    const domains = data.domains || [];
    const q = ($('#kwLibSearch')?.value || '').trim().toLowerCase();

    acc.innerHTML = domains.map((d) => {
      let kws = d.keywords || [];
      if (q) kws = kws.filter((k) => k.toLowerCase().includes(q) || (d.name || '').toLowerCase().includes(q));
      if (!kws.length && q) return '';
      return `<details class="domain-block" ${q ? 'open' : ''}>
        <summary>${esc(d.name)} <span class="muted">(${kws.length})</span></summary>
        <div class="domain-kws">${kws.map((k) =>
          `<button type="button" class="chip sm" data-add-kw="${escAttr(k)}">${esc(k)}</button>`
        ).join('')}</div>
      </details>`;
    }).join('') || '<p class="empty-state">无匹配关键词</p>';

    acc.querySelectorAll('[data-add-kw]').forEach((btn) => {
      btn.addEventListener('click', () => addKwStaging(btn.dataset.addKw));
    });

    const list = loadPresets();
    presets.innerHTML = list.length ? list.map((p, i) => `
      <div class="preset-item">
        <button type="button" class="preset-load" data-pi="${i}">${esc(p.name)}</button>
        <button type="button" class="preset-del" data-pi="${i}">×</button>
      </div>`).join('') : '<p class="muted">暂无保存的预设</p>';

    presets.querySelectorAll('.preset-load').forEach((btn) => {
      btn.addEventListener('click', () => {
        S.kwStaging = [...list[parseInt(btn.dataset.pi, 10)].keywords];
        renderKwStaging();
        toast('已加载预设');
      });
    });
    presets.querySelectorAll('.preset-del').forEach((btn) => {
      btn.addEventListener('click', () => {
        list.splice(parseInt(btn.dataset.pi, 10), 1);
        savePresets(list);
        loadKeywordsPage();
      });
    });
  } catch {
    acc.innerHTML = '<p class="muted">加载词库失败</p>';
  }
}

$('#kwLibSearch')?.addEventListener('input', () => loadKeywordsPage());

$('#kwCustomInput')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    addKwStaging(e.target.value);
    e.target.value = '';
  }
});

$('#btnSavePreset')?.addEventListener('click', () => {
  const name = $('#presetNameInput')?.value.trim();
  if (!name) return toast('请输入预设名称');
  if (!S.kwStaging.length) return toast('请先添加关键词');
  const list = loadPresets();
  const idx = list.findIndex((p) => p.name === name);
  const entry = { name, keywords: [...S.kwStaging] };
  if (idx >= 0) list[idx] = entry;
  else list.push(entry);
  savePresets(list);
  $('#presetNameInput').value = '';
  loadKeywordsPage();
  toast('预设已保存');
});

$('#btnKwToChat')?.addEventListener('click', () => {
  if (!S.kwStaging.length) return toast('请先添加关键词');
  S.keywords = [...S.kwStaging];
  renderKwTags();
  switchView('chat');
  toast('已填入对话，按 Enter 生成');
});

$('#btnKwClear')?.addEventListener('click', () => {
  S.kwStaging = [];
  renderKwStaging();
});

// ── 导出中心 ───────────────────────────────────────────
async function loadExportPage() {
  const list = $('#exportList');
  if (!list) return;
  try {
    const resp = await api('/api/history?limit=200');
    const items = resp.data || [];
    S.exportItems = items;
    if (!items.length) {
      list.innerHTML = '<p class="empty-state">暂无历史可导出</p>';
      return;
    }
    list.innerHTML = items.map((item) => `
      <label class="export-row">
        <input type="checkbox" class="export-check" value="${item.id}">
        <span class="export-row-body">
          <strong>${esc((item.keywords || []).join(' '))}</strong>
          <span class="muted">${esc(fmtDate(item.created_at))} · ${item.variant_count} 版</span>
        </span>
      </label>`).join('');
  } catch {
    list.innerHTML = '<p class="muted">加载失败</p>';
  }
}

$('#exportSelectAll')?.addEventListener('change', (e) => {
  $('.export-check').forEach((c) => { c.checked = e.target.checked; });
});

$('#btnExportSelected')?.addEventListener('click', async () => {
  const ids = $('.export-check:checked').map((c) => parseInt(c.value, 10));
  if (!ids.length) return toast('请勾选记录');
  const variants = [];
  for (const id of ids) {
    try {
      const { data: item } = await api(`/api/history/${id}`);
      (item.variants || []).forEach((v, i) => {
        variants.push({
          ...v,
          version: `${(item.keywords || []).join('_')}_v${i + 1}`,
        });
      });
    } catch { /* skip */ }
  }
  const fmt = $('#exportFormat')?.value || 'txt';
  await downloadExport(variants, fmt, `export-${Date.now()}.${fmt === 'json' ? 'json' : 'txt'}`);
});

// ── 合规检测 ───────────────────────────────────────────
function renderCheckerResult(html) {
  const el = $('#checkerResult');
  if (el) el.innerHTML = html;
}

$('#btnCheckerRun')?.addEventListener('click', async () => {
  const title = $('#checkerTitle')?.value || '';
  const body = $('#checkerBody')?.value || '';
  const text = [title, body].filter(Boolean).join('\n');
  if (!text.trim()) return toast('请输入内容');
  try {
    const resp = await api('/api/check', { method: 'POST', body: { text } });
    renderCheckerResult(`
      <p class="checker-status ${resp.safe ? 'ok' : 'bad'}">${resp.safe ? '✓ 未检测到违禁词' : '⚠ 发现违禁词'}</p>
      ${resp.violations?.length ? `<p><strong>违规项：</strong>${esc(resp.violations.join('、'))}</p>` : ''}
      ${resp.changed ? '<p class="muted">净化后内容与原文不同，可点击「一键净化」应用</p>' : ''}`);
  } catch {
    toast('检测失败');
  }
});

$('#btnCheckerSanitize')?.addEventListener('click', async () => {
  const title = $('#checkerTitle')?.value || '';
  const body = $('#checkerBody')?.value || '';
  try {
    const [t, b] = await Promise.all([
      title ? api('/api/check', { method: 'POST', body: { text: title } }) : null,
      body ? api('/api/check', { method: 'POST', body: { text: body } }) : null,
    ]);
    if (t?.changed) $('#checkerTitle').value = t.sanitized;
    if (b?.changed) $('#checkerBody').value = b.sanitized;
    renderCheckerResult('<p class="checker-status ok">已应用净化结果到左侧输入框</p>');
    toast('净化完成');
  } catch {
    toast('净化失败');
  }
});

$('#btnCheckerCopy')?.addEventListener('click', () => {
  const t = $('#checkerTitle')?.value || '';
  const b = $('#checkerBody')?.value || '';
  navigator.clipboard.writeText(`标题: ${t}\n\n${b}`).then(() => toast('已复制'));
});

// 侧栏最近记录仅显示 5 条
async function loadSidebarRecent() {
  const list = $('#chatList');
  if (!list) return;
  try {
    const resp = await api('/api/history?limit=5');
    const items = resp.data || [];
    if (!items.length) {
      list.innerHTML = '<p class="sb-empty">暂无记录</p>';
      return;
    }
    list.innerHTML = items.map((item) => {
      const label = (item.keywords || []).slice(0, 2).join(' ');
      return `<button type="button" class="sb-item" data-id="${item.id}">
        <span class="sb-item-label">${esc(label)}</span>
      </button>`;
    }).join('');
    list.querySelectorAll('.sb-item').forEach((btn) => {
      btn.addEventListener('click', () => openHistoryItem(parseInt(btn.dataset.id, 10)));
    });
  } catch {
    list.innerHTML = '<p class="sb-empty">加载失败</p>';
  }
}


function initApp() {
  bindGlobalEvents();
  bindChatInput();
  $('#btnNewChat')?.addEventListener('click', newChat);
  updateSendState();
  refreshLlmConfig();
  loadStats();
  loadHistoryList();
  loadDashboard();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
