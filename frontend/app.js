const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8001'
    : 'https://aileadagent-oupl.onrender.com';


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
        <tr class="lead-row" onclick="openSidebar(${lead.id})">
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
                    ${lead.website ? `<a href="${lead.website}"      target="_blank" class="social-link" title="Website" onclick="event.stopPropagation()">🌐</a>` : ''}
                    ${lead.linkedin_url ? `<a href="${lead.linkedin_url}" target="_blank" class="social-link" title="LinkedIn" onclick="event.stopPropagation()">💼</a>` : ''}
                    ${lead.email ? `<a href="mailto:${lead.email}" class="social-link" title="${escHtml(lead.email)}" onclick="event.stopPropagation()">✉️</a>` : ''}
                </div>
            </td>
            <td>
                <span class="score-badge ${getScoreClass(lead.qualification_score)}">${(lead.qualification_score || 0).toFixed(1)}</span>
            </td>
            <td>
                <span class="status-badge status-${lead.status}">${lead.status}</span>
                <div id="status-${lead.id}" class="inline-status" style="display: none;">
                    <div class="spinner"></div>
                    <span>Enriching...</span>
                </div>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon" onclick="event.stopPropagation(); editLead('${lead.id}')" title="Edit">✏️</button>
                    <button class="btn-icon" onclick="event.stopPropagation(); handleManagers('${lead.id}')" title="Fetch Managers">🔍</button>
                    <button class="btn-icon" onclick="event.stopPropagation(); deleteLead('${lead.id}')" title="Delete" style="color:#f87171;">🗑️</button>
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

// ===== MANAGERS & ENRICHMENT =====
async function handleManagers(id) {
    const lead = allLeads.find(l => String(l.id) === String(id));
    if (!lead) return;

    // If we have managers, just show sidebar. If not, trigger enrichment.
    if (lead.managers && lead.managers.length > 0) {
        openSidebar(id);
    } else {
        await fetchManagers(id);
    }
}

async function fetchManagers(id) {
    const statusEl = document.getElementById(`status-${id}`);
    if (statusEl) statusEl.style.display = 'flex';

    window.prompting2FA = false;
    showToast('Starting background enrichment...', 'info', 4000);

    startSilentLogPolling();

    try {
        const response = await fetch(`${API_URL}/enrich/${id}`, { method: 'POST' });
        const result = await response.json();

        if (response.ok) {
            showToast(`Enrichment complete for ${result.company}!`, "success");
            await loadLeads(); // Refresh leads to get new managers
            // Sidebar will be refreshed/opened in renderLeads if needed, 
            // but we call it here to be sure.
            openSidebar(id);
        } else {
            showToast(result.detail || "Enrichment failed", "error");
        }
    } catch (e) {
        console.error("Fetch error:", e);
        showToast("Connection error", "error");
    } finally {
        if (statusEl) statusEl.style.display = 'none';
        stopSilentLogPolling();
    }
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

// ===== SIDEBAR LOGIC =====
function openSidebar(id) {
    const lead = allLeads.find(l => l.id === id);
    if (!lead) return;

    const sidebar = document.getElementById('leadSidebar');
    const body = document.getElementById('sidebarBody');
    const title = document.getElementById('sidebarTitle');

    title.textContent = lead.name;
    sidebar.classList.add('active');

    // Build sidebar content
    body.innerHTML = `
        <div class="sidebar-section">
            <div class="sidebar-section-title">📍 Contact Information</div>
            <div class="detail-card">
                <div class="detail-row">
                    <div class="detail-label">Email</div>
                    <div class="detail-value">${lead.email || 'N/A'}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Phone</div>
                    <div class="detail-value">${lead.phone || 'N/A'}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Website</div>
                    <div class="detail-value"><a href="${lead.website}" target="_blank" style="color:var(--primary-light)">${lead.website || 'N/A'}</a></div>
                </div>
            </div>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-section-title">🏢 Company Details</div>
            <div class="detail-card">
                <div class="detail-row">
                    <div class="detail-label">Company Name</div>
                    <div class="detail-value">${lead.company || 'N/A'}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Founding / Info</div>
                    <div class="detail-value">${lead.funding_info || 'N/A'}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Employee Count</div>
                    <div class="detail-value">${lead.employee_count || 'N/A'}</div>
                </div>
            </div>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-section-title">💼 Discovered Managers</div>
            <div id="sidebarManagersContainer">
                ${renderSidebarManagers(lead)}
            </div>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-section-title">📝 Description & Notes</div>
            <div class="detail-card">
                <div class="detail-value" style="font-size:0.85rem; line-height:1.6;">
                    ${lead.description || 'No additional notes available.'}
                </div>
            </div>
        </div>
    `;
}

function renderSidebarManagers(lead) {
    const managers = lead.managers || [];
    if (managers.length === 0) {
        return `
            <div class="empty-state" style="padding: 1rem; border: 1px dashed var(--border); border-radius: var(--radius-md);">
                <p style="font-size:0.85rem;">No managers fetched yet.</p>
                <button class="btn btn-primary btn-sm" style="margin-top:0.5rem;" onclick="enrichLead(${lead.id})">🔍 Enrich Now</button>
            </div>
        `;
    }

    return managers.map(m => `
        <div class="sidebar-manager-card">
            <div class="manager-name">${escHtml(m.name)}</div>
            <div class="manager-title">${escHtml(m.title)}</div>
            ${m.profile_url ? `<a href="${m.profile_url}" target="_blank" class="btn btn-secondary btn-sm" style="font-size:0.7rem;">View LinkedIn</a>` : ''}
        </div>
    `).join('');
}

function closeSidebar() {
    document.getElementById('leadSidebar').classList.remove('active');
}

// ===== SILENT LOG POLLING (Background 2FA) =====
let silentPollingInterval = null;

function startSilentLogPolling() {
    if (silentPollingInterval) clearInterval(silentPollingInterval);
    silentPollingInterval = setInterval(checkLogsFor2FA, 3000);
}

function stopSilentLogPolling() {
    if (silentPollingInterval) {
        clearInterval(silentPollingInterval);
        silentPollingInterval = null;
    }
}

async function checkLogsFor2FA() {
    try {
        const response = await fetch(`${API_URL}/debug/status`);
        if (!response.ok) return;
        const data = await response.json();

        const logs = data.logs ? (data.logs["scraper_debug.log"] || []) : [];
        const fullText = logs.join('\n');

        if (fullText.includes("ACTION REQUIRED") && !window.prompting2FA) {
            window.prompting2FA = true;
            const code = prompt("LinkedIn security checkpoint! Please enter the 6-digit verification code sent to your email:");
            if (code) {
                submit2FA(code);
            } else {
                window.prompting2FA = false;
            }
        }
    } catch (e) {
        console.warn("Silent log check failed:", e);
    }
}

async function submit2FA(code) {
    try {
        const response = await fetch(`${API_URL}/submit-2fa`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });
        if (response.ok) {
            showToast("2FA Code submitted! Resuming scraper...", "success");
        } else {
            showToast("Failed to submit 2FA code.", "error");
            window.prompting2FA = false;
        }
    } catch (error) {
        console.error("Error submitting 2FA:", error);
        window.prompting2FA = false;
    }
}
