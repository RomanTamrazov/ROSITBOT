const input = document.getElementById('inputText');
const parseBtn = document.getElementById('parseBtn');
const clearBtn = document.getElementById('clearBtn');
const planEl = document.getElementById('plan');
const statusEl = document.getElementById('status');
const jsonEl = document.getElementById('jsonOutput');
const strictToggle = document.getElementById('strictToggle');
const chips = document.querySelectorAll('.chips button');
const copyBtn = document.getElementById('copyBtn');

const setStatus = (text, tone = 'muted') => {
  statusEl.textContent = text;
  statusEl.className = `status ${tone}`;
};

const renderPlan = (plan = []) => {
  planEl.innerHTML = '';
  if (!plan.length) {
    planEl.innerHTML = '<div class="plan-card"><div class="meta">Нет команд</div></div>';
    return;
  }

  plan.forEach((step, idx) => {
    const card = document.createElement('div');
    card.className = 'plan-card';

    const left = document.createElement('div');
    left.innerHTML = `<div class="cmd">${idx + 1}. ${step.cmd}</div>`;

    const meta = document.createElement('div');
    meta.className = 'meta';
    const from = step.from ? `от ${step.from}` : '';
    const to = step.to ? `в ${step.to}` : '';
    meta.textContent = [from, to].filter(Boolean).join(' → ');

    const tag = document.createElement('div');
    tag.className = 'tag';
    tag.textContent = step.cmd;

    card.appendChild(left);
    card.appendChild(meta);
    card.appendChild(tag);
    planEl.appendChild(card);
  });
};

const prettyJson = (data) => JSON.stringify(data, null, 2);

const parseCommand = async () => {
  const text = input.value.trim();
  if (!text) {
    setStatus('Введите команду', 'warn');
    return;
  }

  setStatus('Обработка...', 'muted');
  parseBtn.disabled = true;

  try {
    const res = await fetch('/parse_command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, strict: strictToggle.checked })
    });

    const data = await res.json();
    jsonEl.textContent = prettyJson(data);

    if (data.status === 'ok') {
      setStatus('План готов', 'ok');
      renderPlan(data.plan || []);
    } else {
      setStatus(data.message || 'Ошибка', 'error');
      renderPlan([]);
    }
  } catch (err) {
    setStatus('Не удалось соединиться с сервером', 'error');
    jsonEl.textContent = JSON.stringify({ error: String(err) }, null, 2);
    renderPlan([]);
  } finally {
    parseBtn.disabled = false;
  }
};

parseBtn.addEventListener('click', parseCommand);

const copyJson = async () => {
  const payload = jsonEl.textContent || '{}';
  try {
    await navigator.clipboard.writeText(payload);
    copyBtn.classList.add('copied');
    copyBtn.textContent = 'Скопировано';
  } catch (err) {
    const textarea = document.createElement('textarea');
    textarea.value = payload;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    copyBtn.classList.add('copied');
    copyBtn.textContent = 'Скопировано';
  }
  setTimeout(() => {
    copyBtn.classList.remove('copied');
    copyBtn.textContent = 'Скопировать';
  }, 1600);
};

copyBtn.addEventListener('click', copyJson);
clearBtn.addEventListener('click', () => {
  input.value = '';
  renderPlan([]);
  jsonEl.textContent = '{}';
  setStatus('Ожидание команды', 'muted');
});

chips.forEach((chip) => {
  chip.addEventListener('click', () => {
    input.value = chip.dataset.example;
    input.focus();
  });
});

input.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    parseCommand();
  }
});

renderPlan([]);
