/* ChoreBoard – shared JS */

// ── State ──────────────────────────────────────────────────────────────────
let _users = [];
let _confirmResolve = null;

// ── Bootstrap ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  _users = await apiFetch('/api/users') || [];
  populateSidebarUsers();
  populateAssignedDropdown();
  updateOverdueBadge();
});

// ── Sidebar users ──────────────────────────────────────────────────────────
function populateSidebarUsers() {
  const el = document.getElementById('sidebar-users');
  if (!el) return;
  el.innerHTML = _users.map(u => `
    <div class="sidebar-user">
      <span class="avatar-circle" style="background-color:${u.avatar_color}">${u.name[0]}</span>
      <span>${u.name}</span>
    </div>
  `).join('');
}

// ── Overdue badge ──────────────────────────────────────────────────────────
async function updateOverdueBadge() {
  const data = await apiFetch('/api/dashboard');
  const badge = document.getElementById('overdue-badge');
  if (!badge || !data) return;
  if (data.overdue.length > 0) {
    badge.textContent = data.overdue.length;
    badge.classList.remove('hidden');
    badge.classList.add('flex');
  }
}

// ── Assigned dropdown ──────────────────────────────────────────────────────
function populateAssignedDropdown() {
  const sel = document.getElementById('chore-assigned');
  if (!sel) return;
  sel.innerHTML = '<option value="">Unassigned</option>' +
    _users.map(u => `<option value="${u.id}">${u.name}</option>`).join('');
}

// ── Chore Modal ────────────────────────────────────────────────────────────
function openChoreModal(choreId = null) {
  document.getElementById('chore-edit-id').value = choreId || '';
  document.getElementById('modal-title').textContent = choreId ? 'Edit Chore' : 'Add Chore';
  const form = document.getElementById('chore-form');
  form.reset();

  if (choreId) {
    apiFetch(`/api/chores?search=`).then(() => {
      // fetch specific chore via all chores list (workaround since no GET /api/chores/:id)
    });
    // Use data already in the row if available
    const row = document.getElementById(`chore-row-${choreId}`);
    if (row && row._choreData) {
      fillModalWithChore(row._choreData);
    } else {
      // Fetch chores and find by id
      apiFetch('/api/chores').then(chores => {
        if (!chores) return;
        const c = chores.find(x => x.id == choreId);
        if (c) fillModalWithChore(c);
      });
    }
  } else {
    // Default due date = today
    document.getElementById('chore-due-date').value = new Date().toISOString().split('T')[0];
  }

  document.getElementById('chore-modal').classList.remove('hidden');
}

function fillModalWithChore(c) {
  document.getElementById('chore-title').value = c.title || '';
  document.getElementById('chore-category').value = c.category || 'General';
  document.getElementById('chore-assigned').value = c.assigned_to || '';
  document.getElementById('chore-due-date').value = c.due_date || '';
  document.getElementById('chore-frequency').value = c.frequency || 'once';
  document.getElementById('chore-priority').value = c.priority || 'medium';
  document.getElementById('chore-effort').value = c.estimated_effort || 2;
  document.getElementById('chore-status').value = c.status || 'pending';
  document.getElementById('chore-description').value = c.description || '';
  document.getElementById('chore-notes').value = c.notes || '';
}

function closeChoreModal() {
  document.getElementById('chore-modal').classList.add('hidden');
}

async function submitChoreForm(e) {
  if (e) e.preventDefault();
  const id = document.getElementById('chore-edit-id').value;
  const payload = {
    title:            document.getElementById('chore-title').value.trim(),
    category:         document.getElementById('chore-category').value,
    assigned_to:      document.getElementById('chore-assigned').value || null,
    due_date:         document.getElementById('chore-due-date').value || null,
    frequency:        document.getElementById('chore-frequency').value,
    priority:         document.getElementById('chore-priority').value,
    estimated_effort: parseInt(document.getElementById('chore-effort').value),
    status:           document.getElementById('chore-status').value,
    description:      document.getElementById('chore-description').value.trim(),
    notes:            document.getElementById('chore-notes').value.trim(),
  };

  if (!payload.title) { showToast('Title is required', 'error'); return; }

  let result;
  if (id) {
    result = await apiPut(`/api/chores/${id}`, payload);
  } else {
    result = await apiPost('/api/chores', payload);
  }

  if (result) {
    closeChoreModal();
    showToast(id ? 'Chore updated' : 'Chore created', 'success');
    if (typeof window.onChoreModalSaved === 'function') window.onChoreModalSaved();
  }
}

// ── Chore actions ──────────────────────────────────────────────────────────
async function completeChore(id) {
  const result = await apiPost(`/api/chores/${id}/complete`, {});
  return !!result;
}

async function deleteChore(id) {
  const confirmed = await showConfirm('Delete this chore?', 'This cannot be undone.');
  if (!confirmed) return false;
  const result = await apiDelete(`/api/chores/${id}`);
  if (result) showToast('Chore deleted', 'success');
  return !!result;
}

async function swapChore(id) {
  const result = await apiPost(`/api/chores/${id}/swap`, {});
  if (result) showToast('Chore reassigned', 'success');
  return result;
}

async function snoozeChore(id, days = 1) {
  const result = await apiPost(`/api/chores/${id}/snooze`, { days });
  if (result) showToast(`Snoozed ${days} day${days > 1 ? 's' : ''}`, 'success');
  return result;
}

// ── Confirm dialog ─────────────────────────────────────────────────────────
function showConfirm(title = 'Confirm', message = 'Are you sure?') {
  return new Promise(resolve => {
    _confirmResolve = resolve;
    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-message').textContent = message;
    document.getElementById('confirm-dialog').classList.remove('hidden');
  });
}

function confirmResolve(val) {
  document.getElementById('confirm-dialog').classList.add('hidden');
  if (_confirmResolve) { _confirmResolve(val); _confirmResolve = null; }
}

// ── Toast ──────────────────────────────────────────────────────────────────
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `<span style="font-weight:700">${icon}</span> ${message}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ── Utilities ──────────────────────────────────────────────────────────────
function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso + 'T00:00:00');
  const today = new Date(); today.setHours(0,0,0,0);
  const diff = Math.round((d - today) / 86400000);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  if (diff === -1) return 'Yesterday';
  if (diff < 0) return `${Math.abs(diff)}d overdue`;
  if (diff <= 7) return `In ${diff}d`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function effortDots(n) {
  const dots = Array.from({length: 5}, (_, i) =>
    `<span class="effort-dot ${i < n ? 'filled' : 'empty'}"></span>`
  ).join('');
  return `<span class="effort-dots" title="${n} effort pts">${dots}</span>`;
}

function catBadge(cat) {
  const slug = (cat || 'general').toLowerCase();
  return `<span class="cat-badge cat-${slug}">${cat || 'General'}</span>`;
}

function statusBadge(status) {
  const label = status === 'in-progress' ? 'In Progress' : status;
  return `<span class="status-badge status-${status}">${label}</span>`;
}

function userBadge(user) {
  if (!user) return `<span class="text-xs text-slate-400">Unassigned</span>`;
  return `<span class="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
    style="background-color:${user.avatar_color}22;color:${user.avatar_color}">
    <span class="avatar-circle" style="background-color:${user.avatar_color};width:1rem;height:1rem;font-size:0.6rem">${user.name[0]}</span>
    ${user.name}
  </span>`;
}

function priorityDot(p) {
  return `<span class="priority-dot priority-${p}" title="${p} priority"></span>`;
}

// ── Fetch helpers ──────────────────────────────────────────────────────────
async function apiFetch(url) {
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(await r.text());
    return await r.json();
  } catch (err) {
    showToast('Request failed: ' + err.message, 'error');
    return null;
  }
}

async function apiPost(url, data) {
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!r.ok) throw new Error(await r.text());
    return await r.json();
  } catch (err) {
    showToast('Request failed: ' + err.message, 'error');
    return null;
  }
}

async function apiPut(url, data) {
  try {
    const r = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!r.ok) throw new Error(await r.text());
    return await r.json();
  } catch (err) {
    showToast('Request failed: ' + err.message, 'error');
    return null;
  }
}

async function apiDelete(url) {
  try {
    const r = await fetch(url, { method: 'DELETE' });
    if (!r.ok) throw new Error(await r.text());
    return await r.json();
  } catch (err) {
    showToast('Request failed: ' + err.message, 'error');
    return null;
  }
}
