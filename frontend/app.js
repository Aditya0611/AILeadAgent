const API_URL = 'https://aileadagent-oupl.onrender.com';


let allLeads = [];
let currentEditId = null;

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('App started. API_URL:', API_URL);
    loadLeads();
    loadStats();
    checkConnection();
    // Check connection every 15 seconds
    setInterval(checkConnection, 15000);

    // Initial console setup
    toggleConsole(true); // Start collapsed
});

let logPollingInterval = null;

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toastContainer');
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ===== LOAD LEADS =====
async function loadLeads() {
    try {
        const response = await fetch(`${API_URL}/leads`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        allLeads = data.leads || [];
        renderLeads(allLeads);
    } catch (error) {
        console.error('Error loading leads:', error);
        document.getElementById('leadsTableBody').innerHTML = `
            <tr><td colspan="6" class="loading">
                <div class="empty-state">
                    <div class="empty-icon">🔌</div>
                    <h3>Could not connect to API</h3>
                    <p>Make sure the backend is running on port 8001</p>
                </div>
            </td></tr>
        `;
    }
}

// ===== LOAD STATS =====
async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        if (!response.ok) throw new Error('Network response was not ok');
        const stats = await response.json();
        animateCount('totalLeads', stats.total_leads);
        animateCount('qualifiedLeads', stats.qualified_leads);
        document.getElementById('avgScore').textContent = (stats.average_score || 0).toFixed(1);
    } catch (error) {
        console.error('Error loading stats:', error);
        ['totalLeads', 'qualifiedLeads', 'avgScore'].forEach(id => {
            document.getElementById(id).textContent = '—';
        });
    }
}

// Animated counter for stat cards
function animateCount(elementId, target) {
    const el = document.getElementById(elementId);
    const duration = 800;
    const start = parseInt(el.textContent) || 0;
    const startTime = performance.now();
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(start + (target - start) * eased);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ===== RENDER LEADS =====
function renderLeads(leads) {
    const tbody = document.getElementById('leadsTableBody');
    const badge = document.getElementById('leadsCountBadge');
    if (badge) badge.textContent = leads.length;

    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="6">
                <div class="empty-state">
                    <div class="empty-icon">🔎</div>
                    <h3>No leads found</h3>
                    <p>Try adjusting your filters or add a new lead</p>
                </div>
            </td></tr>
        `;
        return;
    }

    tbody.innerHTML = leads.map(lead => `
        <tr>
            <td class="lead-name-cell">
                <strong>${escHtml(lead.name)}</strong>
                <div class="tags-container">
                    ${(lead.industry_tags || []).slice(0, 3).map(tag => `<span class="tag">${escHtml(tag)}</span>`).join('')}
                </div>
            </td>
            <td class="lead-company-cell">
                ${lead.company ? escHtml(lead.company) : '<span style="color:var(--text-muted)">—</span>'}
                ${lead.funding_info && lead.funding_info !== 'Unknown'
            ? `<div><span class="funding-badge">💰 ${escHtml(lead.funding_info)}</span></div>`
            : ''}
                ${lead.employees ? `<div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px;">👥 ${escHtml(String(lead.employees))}</div>` : ''}
            </td>
            <td>
                <div class="social-links">
                    ${lead.website ? `<a href="${lead.website}"      target="_blank" class="social-link" title="Website">🌐</a>` : ''}
                    ${lead.linkedin_url ? `<a href="${lead.linkedin_url}" target="_blank" class="social-link" title="LinkedIn">💼</a>` : ''}
                    ${lead.twitter_url ? `<a href="${lead.twitter_url}"  target="_blank" class="social-link" title="Twitter">🐦</a>` : ''}
                    ${lead.email ? `<a href="mailto:${lead.email}" class="social-link" title="${escHtml(lead.email)}">✉️</a>` : ''}
                    ${!lead.website && !lead.linkedin_url && !lead.twitter_url && !lead.email ? '<span style="color:var(--text-muted);font-size:0.8rem">—</span>' : ''}
                </div>
            </td>
            <td>
                <span class="score-badge ${getScoreClass(lead.qualification_score)}">${(lead.qualification_score || 0).toFixed(1)}</span>
                ${lead.sentiment_score != null ? `<span title="Sentiment: ${lead.sentiment_score}" style="margin-left:4px;">${getSentimentEmoji(lead.sentiment_score)}</span>` : ''}
            </td>
            <td><span class="status-badge status-${lead.status}">${lead.status}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon" onclick="editLead('${lead.id}')" title="Edit">✏️</button>
                    <button class="btn-icon" onclick="handleManagers('${lead.id}')" title="View Managers">💼</button>
                    <button class="btn-icon" onclick="deleteLead('${lead.id}')" title="Delete" style="color:#f87171;">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// ===== FILTER LEADS =====
function filterLeads() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
    const statusFilter = document.getElementById('statusFilter').value;
    const minScore = parseFloat(document.getElementById('minScoreFilter').value) || 0;

    let filtered = allLeads;

    if (searchTerm) {
        filtered = filtered.filter(lead =>
            (lead.name || '').toLowerCase().includes(searchTerm) ||
            (lead.company || '').toLowerCase().includes(searchTerm) ||
            (lead.email || '').toLowerCase().includes(searchTerm) ||
            (lead.industry_tags || []).some(t => t.toLowerCase().includes(searchTerm))
        );
    }
    if (statusFilter) {
        filtered = filtered.filter(lead => lead.status === statusFilter);
    }
    filtered = filtered.filter(lead => (lead.qualification_score || 0) >= minScore);

    renderLeads(filtered);
}

// ===== RESET FILTERS =====
function resetFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('minScoreFilter').value = '';
    renderLeads(allLeads);
}

// ===== ADD LEAD MODAL =====
function openAddLeadModal() {
    currentEditId = null;
    document.getElementById('modalTitle').textContent = '✏️ Add New Lead';
    document.getElementById('leadForm').reset();
    document.getElementById('saveLeadBtn').textContent = '💾 Save Lead';
    openModal('leadModal');
}

// ===== EDIT LEAD =====
async function editLead(id) {
    try {
        const response = await fetch(`${API_URL}/leads/${id}`);
        if (!response.ok) throw new Error();
        const lead = await response.json();

        currentEditId = id;
        document.getElementById('modalTitle').textContent = '✏️ Edit Lead';
        document.getElementById('saveLeadBtn').textContent = '💾 Update Lead';
        setValue('leadName', lead.name);
        setValue('leadCompany', lead.company);
        setValue('leadWebsite', lead.website);
        setValue('leadEmail', lead.email);
        setValue('leadPhone', lead.phone);
        setValue('leadLinkedIn', lead.linkedin_url);
        setValue('leadFunding', lead.funding_info);
        setValue('leadEmployees', lead.employees);
        setValue('leadScore', lead.qualification_score);
        setValue('leadStatus', lead.status);
        setValue('leadDescription', lead.description);
        setValue('leadTags', (lead.industry_tags || []).join(', '));

        openModal('leadModal');
    } catch (error) {
        showToast('Error loading lead details', 'error');
    }
}

// ===== SAVE LEAD =====
async function saveLead(event) {
    event.preventDefault();
    const btn = document.getElementById('saveLeadBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Saving…';

    const tagsRaw = document.getElementById('leadTags').value;
    const tags = tagsRaw ? tagsRaw.split(',').map(t => t.trim()).filter(Boolean) : [];

    const leadData = {
        name: document.getElementById('leadName').value,
        company: document.getElementById('leadCompany').value || null,
        website: document.getElementById('leadWebsite').value || null,
        email: document.getElementById('leadEmail').value || null,
        phone: document.getElementById('leadPhone').value || null,
        linkedin_url: document.getElementById('leadLinkedIn').value || null,
        funding_info: document.getElementById('leadFunding').value || null,
        employees: document.getElementById('leadEmployees').value || null,
        qualification_score: parseFloat(document.getElementById('leadScore').value) || 0,
        status: document.getElementById('leadStatus').value,
        description: document.getElementById('leadDescription').value || null,
        industry_tags: tags
    };

    try {
        const url = currentEditId ? `${API_URL}/leads/${currentEditId}` : `${API_URL}/leads`;
        const method = currentEditId ? 'PUT' : 'POST';
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(leadData)
        });

        if (response.ok) {
            closeModal('leadModal');
            await loadLeads();
            await loadStats();
            showToast(currentEditId ? 'Lead updated successfully' : 'Lead added successfully', 'success');
            currentEditId = null;
        } else {
            showToast('Error saving lead. Please try again.', 'error');
        }
    } catch (error) {
        showToast('Connection error. Is the API running?', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '💾 Save Lead';
    }
}

// ===== DELETE LEAD =====
async function deleteLead(id) {
    const lead = allLeads.find(l => l.id === id);
    const name = lead ? lead.name : 'this lead';
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;

    try {
        const response = await fetch(`${API_URL}/leads/${id}`, { method: 'DELETE' });
        if (response.ok) {
            await loadLeads();
            await loadStats();
            showToast('Lead deleted', 'info');
        } else {
            showToast('Error deleting lead', 'error');
        }
    } catch (error) {
        showToast('Connection error', 'error');
    }
}

// ===== MODAL HELPERS =====
function openModal(id) {
    const modal = document.getElementById(id);
    modal.classList.add('active');
    modal.style.display = null; // let CSS handle it via .active
    document.body.style.overflow = 'hidden';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

function closeLeadModal() { closeModal('leadModal'); currentEditId = null; }
function openAgentModal() {
    document.getElementById('agentStatus').classList.remove('active');
    document.getElementById('agentStatus').innerHTML = '';
    openModal('agentModal');
}
function closeAgentModal() { closeModal('agentModal'); }

// Close modals when clicking backdrop
window.addEventListener('click', (event) => {
    if (event.target.classList.contains('modal') && event.target.classList.contains('active')) {
        event.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// ===== RUN AGENT =====
async function runAgent(event) {
    event.preventDefault();
    const btn = document.getElementById('runAgentSubmitBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Starting…';

    const keywords = (document.getElementById('agentKeywords').value || '')
        .split(',').map(k => k.trim()).filter(Boolean);

    const agentData = {
        industry: document.getElementById('agentIndustry').value,
        location: document.getElementById('agentLocation').value || null,
        target_persona: document.getElementById('agentPersona').value || null,
        keywords
    };

    const statusDiv = document.getElementById('agentStatus');
    statusDiv.classList.add('active');
    statusDiv.innerHTML = '<p>🤖 Agent is running… This may take a few minutes.</p>';

    // Show Progress Console
    toggleConsole(false);
    startLogPolling();

    try {
        const response = await fetch(`${API_URL}/run-agent`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(agentData)
        });

        if (response.ok) {
            statusDiv.innerHTML = `
                <p class="success-msg">✅ Agent started! It runs in the background finding leads.</p>
                <p style="margin-top:0.4rem;font-size:0.82rem;color:var(--text-muted);">The table will refresh automatically. You can close this window.</p>
            `;
            let checks = 0;
            const interval = setInterval(() => {
                loadLeads();
                loadStats();
                if (++checks > 12) clearInterval(interval);
            }, 5000);
            setTimeout(() => closeAgentModal(), 3000);
        } else {
            statusDiv.innerHTML = '<p class="error-msg">❌ Agent failed to start. Check the API logs.</p>';
        }
    } catch (error) {
        statusDiv.innerHTML = '<p class="error-msg">❌ Connection error. Make sure the API is running.</p>';
    } finally {
        btn.disabled = false;
        btn.textContent = '🚀 Run Agent';
        // Stop polling after some time or on success
        setTimeout(stopLogPolling, 10000);
    }
}

// ===== MANAGERS =====
async function handleManagers(id) {
    const lead = allLeads.find(l => l.id === id);
    if (!lead) return;

    if (lead.managers_info && lead.managers_info.length > 0) {
        showManagersModal(lead.managers_info, lead.company, lead.id);
    } else {
        if (confirm(`Fetch managers for "${lead.company || lead.name}" from LinkedIn?`)) {
            await fetchManagers(id);
        }
    }
}

async function fetchManagers(id) {
    showToast('Fetching managers…', 'info', 6000);

    // Show Progress Console
    toggleConsole(false);
    startLogPolling();

    const startTime = Date.now();
    try {
        console.log(`Sending enrichment request for ${id} to ${API_URL}`);
        const response = await fetch(`${API_URL}/leads/${id}/enrich-managers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        console.log(`Response received in ${(Date.now() - startTime) / 1000}s. Status: ${response.status}`);
        const data = await response.json();

        if (response.ok) {
            const leadIndex = allLeads.findIndex(l => l.id === id);
            if (leadIndex !== -1) allLeads[leadIndex].managers_info = data.managers;
            renderLeads(allLeads);
            showManagersModal(data.managers, allLeads[leadIndex]?.company, id);
        } else {
            console.error('Server error:', data);
            showToast('Error: ' + (data.detail || 'Server returned ' + response.status), 'error');
        }
    } catch (error) {
        console.error('Fetch error after ' + (Date.now() - startTime) / 1000 + 's:', error);
        showToast('Error: ' + error.message, 'error');
    } finally {
        // Stop polling shortly after completion
        setTimeout(stopLogPolling, 5000);
    }
}

function showManagersModal(managers, company, leadId) {
    const existing = document.getElementById('managersModal');
    if (existing) existing.remove();

    const html = `
        <div id="managersModal" class="modal active" style="display:flex;">
            <div class="modal-content" style="max-width: 580px;">
                <div class="modal-header">
                    <h2>💼 Managers at ${escHtml(company || 'Company')}</h2>
                    <div style="display:flex;gap:0.5rem;align-items:center;">
                        ${leadId ? `<button class="btn btn-secondary btn-sm" onclick="document.getElementById('managersModal').remove(); fetchManagers('${leadId}')">🔄 Refetch</button>` : ''}
                        <button class="close-btn" onclick="document.getElementById('managersModal').remove(); document.body.style.overflow=''">✕</button>
                    </div>
                </div>
                <div style="max-height: 60vh; overflow-y: auto; padding-right: 4px;">
                    ${managers.length === 0
            ? `<div class="empty-state"><div class="empty-icon">🤷</div><h3>No managers found</h3><p>Try refetching or check the LinkedIn URL</p></div>`
            : managers.map(m => `
                            <div class="manager-card">
                                <h3>${escHtml(m.name || 'Unknown')}</h3>
                                <div class="manager-title">${escHtml(m.title || '')}</div>
                                <div class="manager-contact">
                                    ${m.email ? `<div>✉️ <a href="mailto:${escHtml(m.email)}">${escHtml(m.email)}</a></div>` : ''}
                                    ${m.phone ? `<div>📱 ${escHtml(m.phone)}</div>` : ''}
                                    ${m.profile_url ? `<div>🔗 <a href="${escHtml(m.profile_url)}" target="_blank">View LinkedIn Profile</a></div>` : ''}
                                </div>
                            </div>
                        `).join('')}
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', html);
    document.body.style.overflow = 'hidden';

    // Close on backdrop click
    document.getElementById('managersModal').addEventListener('click', function (e) {
        if (e.target === this) { this.remove(); document.body.style.overflow = ''; }
    });
}

// ===== EXPORT CSV =====
async function exportCSV() {
    try {
        const response = await fetch(`${API_URL}/export-csv`);
        if (!response.ok) throw new Error();
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `leads_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showToast('CSV exported successfully', 'success');
    } catch (error) {
        showToast('Error exporting CSV. Is the API running?', 'error');
    }
}

// ===== UTILITY =====
async function checkConnection() {
    const statusEl = document.getElementById('connectionStatus');
    const dot = statusEl.querySelector('.status-dot');
    const text = statusEl.querySelector('.status-text');

    try {
        const response = await fetch(`${API_URL}/debug/status`, {
            method: 'GET',
            mode: 'cors',
            credentials: 'omit'
        });

        if (response.ok) {
            statusEl.classList.remove('offline');
            statusEl.classList.add('online');
            text.textContent = 'Online';
        } else {
            throw new Error('Server returned ' + response.status);
        }
    } catch (error) {
        console.warn('Backend connection failed:', error);
        statusEl.classList.remove('online');
        statusEl.classList.add('offline');
        text.textContent = 'Offline';
    }
}

function getScoreClass(score) {
    if (score >= 7) return 'score-high';
    if (score >= 4) return 'score-medium';
    return 'score-low';
}

function getSentimentEmoji(score) {
    if (score >= 0.5) return '🚀';
    if (score >= 0.0) return '🙂';
    return '📉';
}

function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function setValue(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val ?? '';
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function truncate(str, length) {
    if ((str || '').length <= length) return str;
    return str.substring(0, length) + '…';
}

// ===== CONSOLE LOGIC =====
function toggleConsole(forceCollapse) {
    const consoleEl = document.getElementById('progressConsole');
    if (forceCollapse === true) {
        consoleEl.classList.add('collapsed');
    } else if (forceCollapse === false) {
        consoleEl.classList.remove('collapsed');
    } else {
        consoleEl.classList.toggle('collapsed');
    }
}

function startLogPolling() {
    if (logPollingInterval) clearInterval(logPollingInterval);
    document.getElementById('consoleStatus').textContent = 'Live: Syncing...';
    document.getElementById('consoleStatus').classList.add('active');

    // Initial fetch
    updateProgressConsole();
    // Poll every 3 seconds
    logPollingInterval = setInterval(updateProgressConsole, 3000);
}

function stopLogPolling() {
    if (logPollingInterval) {
        clearInterval(logPollingInterval);
        logPollingInterval = null;
    }
    document.getElementById('consoleStatus').textContent = 'Inactive';
    document.getElementById('consoleStatus').classList.remove('active');
}

async function updateProgressConsole() {
    const logContainer = document.getElementById('logContainer');
    const welcome = document.querySelector('.console-welcome');

    try {
        const response = await fetch(`${API_URL}/debug/status`);
        if (!response.ok) return;

        const data = await response.json();

        // Handle dictionary of logs from backend
        let logs = [];
        if (data.logs && data.logs["scraper_debug.log"]) {
            logs = data.logs["scraper_debug.log"];
        } else if (Array.isArray(data.logs)) {
            logs = data.logs;
        }

        if (logs.length > 0) {
            if (welcome) welcome.style.display = 'none';

            // Format and display logs
            logContainer.innerHTML = logs.map(line => {
                let typeClass = '';
                if (line.includes('SUCCESS') || line.includes('DONE')) typeClass = 'success';
                if (line.includes('ERROR') || line.includes('FAILED')) typeClass = 'warning';
                if (line.includes('SCRAPER START') || line.includes('Agent started')) typeClass = 'important';

                // Extract timestamp if exists (e.g., [10:30:15])
                const timestampMatch = line.match(/^\[.*?\]/);
                const timestamp = timestampMatch ? `<span class="log-line timestamp">${timestampMatch[0]}</span>` : '';
                const content = timestampMatch ? line.replace(timestampMatch[0], '') : line;

                return `<div class="log-line ${typeClass}">${timestamp}${escHtml(content)}</div>`;
            }).join('');

            // Auto scroll to bottom
            const body = document.getElementById('consoleBody');
            body.scrollTop = body.scrollHeight;
        }
    } catch (error) {
        console.warn('Failed to fetch logs:', error);
    }
}
