/**
 * TEMPORARY DEBUG MODULE - DELETE WHEN DONE
 * Commission verification with bidirectional sync
 */

// Store data globally for easy access
let hierarchyData = null;
let rawData = null;
let selectedCTV = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadAllData();
});

/**
 * Load all data from API
 */
async function loadAllData() {
    try {
        // Load hierarchy and raw data in parallel
        const [hierarchyRes, rawRes] = await Promise.all([
            fetch('/api/admin/debug/hierarchy-full'),
            fetch('/api/admin/debug/raw-data')
        ]);
        
        hierarchyData = await hierarchyRes.json();
        rawData = await rawRes.json();
        
        // Render everything
        renderHierarchy();
        renderRawData();
        renderStats();
        
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('debug-stats').innerHTML = 
            '<span style="color: #ff6b6b;">Error loading data: ' + error.message + '</span>';
    }
}

/**
 * Render debug stats
 */
function renderStats() {
    const stats = document.getElementById('debug-stats');
    if (!rawData || !rawData.counts) {
        stats.innerHTML = 'No data loaded';
        return;
    }
    const ratesStr = rawData.rates && rawData.rates.length > 0 
        ? rawData.rates.map(r => 'L' + r.level + ':' + (r.rate * 100) + '%').join(', ')
        : 'No rates';
    stats.innerHTML = `
        CTVs: ${rawData.counts.ctvs} | 
        Clients: ${rawData.counts.clients} | 
        Commissions: ${rawData.counts.commissions} |
        Rates: ${ratesStr}
    `;
}

/**
 * Render hierarchy tree
 */
function renderHierarchy() {
    const container = document.getElementById('hierarchy-tree');
    container.innerHTML = '';
    
    if (!hierarchyData || !hierarchyData.hierarchy) {
        container.innerHTML = '<p>No hierarchy data</p>';
        return;
    }
    
    hierarchyData.hierarchy.forEach(root => {
        container.appendChild(createTreeNode(root, 0));
    });
}

/**
 * Create a tree node element
 */
function createTreeNode(node, depth) {
    const div = document.createElement('div');
    div.className = 'tree-node-wrapper';
    div.setAttribute('data-ctv', node.ma_ctv);
    
    const hasChildren = node.children && node.children.length > 0;
    
    div.innerHTML = `
        <div class="tree-node" data-ctv="${node.ma_ctv}" onclick="selectCTV('${node.ma_ctv}')">
            <div class="tree-node-header">
                <span>
                    ${hasChildren ? '<span class="tree-toggle" onclick="event.stopPropagation(); toggleChildren(this)">[-]</span>' : ''}
                    <span class="tree-node-name">${node.ten || 'Unknown'}</span>
                </span>
                <span class="tree-node-code">${node.ma_ctv}</span>
            </div>
            <div class="tree-node-stats">
                <span class="clients">${node.client_count} clients</span>
                <span class="revenue">${formatMoney(node.total_revenue)}</span>
                <span class="commission">${formatMoney(node.total_commission)}</span>
            </div>
        </div>
    `;
    
    if (hasChildren) {
        const childContainer = document.createElement('div');
        childContainer.className = 'tree-children';
        node.children.forEach(child => {
            childContainer.appendChild(createTreeNode(child, depth + 1));
        });
        div.appendChild(childContainer);
    }
    
    return div;
}

/**
 * Toggle children visibility
 */
function toggleChildren(toggleBtn) {
    const wrapper = toggleBtn.closest('.tree-node-wrapper');
    const children = wrapper.querySelector('.tree-children');
    if (children) {
        const isHidden = children.style.display === 'none';
        children.style.display = isHidden ? 'block' : 'none';
        toggleBtn.textContent = isHidden ? '[-]' : '[+]';
    }
}

/**
 * Select a CTV (left panel click)
 */
function selectCTV(ctvCode) {
    // Clear previous selection
    document.querySelectorAll('.tree-node.selected').forEach(el => {
        el.classList.remove('selected');
    });
    
    // Select new node
    const node = document.querySelector(`.tree-node[data-ctv="${ctvCode}"]`);
    if (node) {
        node.classList.add('selected');
    }
    
    selectedCTV = ctvCode;
    
    // Highlight in raw data (RIGHT SIDE)
    highlightInRawData(ctvCode);
    
    // Show detail modal
    showCTVDetail(ctvCode);
}

/**
 * Highlight matching rows in raw data tables (Left -> Right)
 */
function highlightInRawData(ctvCode) {
    // Clear all highlights
    document.querySelectorAll('.debug-table tr.highlighted').forEach(el => {
        el.classList.remove('highlighted');
    });
    
    // Highlight CTV row
    document.querySelectorAll(`#ctvs-table tr[data-ctv="${ctvCode}"]`).forEach(el => {
        el.classList.add('highlighted');
    });
    
    // Highlight client rows for this CTV
    document.querySelectorAll(`#clients-table tr[data-ctv="${ctvCode}"]`).forEach(el => {
        el.classList.add('highlighted');
    });
    
    // Highlight commission rows for this CTV
    document.querySelectorAll(`#commissions-table tr[data-ctv="${ctvCode}"]`).forEach(el => {
        el.classList.add('highlighted');
    });
    
    // Scroll to first highlighted row
    const firstHighlighted = document.querySelector('.debug-table tr.highlighted');
    if (firstHighlighted) {
        firstHighlighted.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * Scroll to CTV in hierarchy (Right -> Left)
 */
function scrollToHierarchy(ctvCode) {
    // Clear previous highlights
    document.querySelectorAll('.tree-node.highlighted').forEach(el => {
        el.classList.remove('highlighted');
    });
    
    // Find the node
    const node = document.querySelector(`.tree-node[data-ctv="${ctvCode}"]`);
    if (!node) {
        console.log('CTV not found in hierarchy:', ctvCode);
        return;
    }
    
    // Expand all parent nodes
    let parent = node.closest('.tree-children');
    while (parent) {
        parent.style.display = 'block';
        const toggle = parent.previousElementSibling?.querySelector('.tree-toggle');
        if (toggle) toggle.textContent = '[-]';
        parent = parent.parentElement?.closest('.tree-children');
    }
    
    // Highlight and scroll
    node.classList.add('highlighted');
    node.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Also highlight in raw data
    highlightInRawData(ctvCode);
}

/**
 * Render raw data tables
 */
function renderRawData() {
    renderRatesTable();
    renderCTVsTable();
    renderClientsTable();
    renderCommissionsTable();
}

/**
 * Render rates table
 */
function renderRatesTable() {
    const tbody = document.querySelector('#rates-table tbody');
    if (!rawData.rates || rawData.rates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3">No rates configured</td></tr>';
        return;
    }
    tbody.innerHTML = rawData.rates.map(r => `
        <tr>
            <td><span class="level-badge level-${r.level}">Level ${r.level}</span></td>
            <td>${(r.rate * 100).toFixed(1)}%</td>
            <td>${r.description || '-'}</td>
        </tr>
    `).join('');
}

/**
 * Render CTVs table
 */
function renderCTVsTable() {
    const tbody = document.querySelector('#ctvs-table tbody');
    if (!rawData.ctvs || rawData.ctvs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No CTVs found</td></tr>';
        return;
    }
    tbody.innerHTML = rawData.ctvs.map(c => `
        <tr data-ctv="${c.ma_ctv}" onclick="scrollToHierarchy('${c.ma_ctv}')">
            <td>${c.ma_ctv}</td>
            <td>${c.ten || '-'}</td>
            <td>${c.sdt || '-'}</td>
            <td>${c.nguoi_gioi_thieu || '-'}</td>
            <td>${c.cap_bac || '-'}</td>
        </tr>
    `).join('');
}

/**
 * Render clients table (grouped by CTV)
 */
function renderClientsTable() {
    const tbody = document.querySelector('#clients-table tbody');
    if (!rawData.clients || rawData.clients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8">No clients found</td></tr>';
        return;
    }
    let lastCTV = null;
    
    tbody.innerHTML = rawData.clients.map(c => {
        const isNewGroup = c.nguoi_chot !== lastCTV;
        lastCTV = c.nguoi_chot;
        
        return `
            <tr data-ctv="${c.nguoi_chot || ''}" 
                class="${isNewGroup ? 'group-start' : ''}"
                onclick="scrollToHierarchy('${c.nguoi_chot || ''}')">
                <td>${c.id}</td>
                <td>${c.ho_ten || '-'}</td>
                <td>${c.sdt || '-'}</td>
                <td class="money">${formatMoney(c.tong_tien)}</td>
                <td>${c.ngay_hen_lam || '-'}</td>
                <td>${c.dich_vu || '-'}</td>
                <td>${c.nguoi_chot || '-'}</td>
                <td>${c.ctv_name || '-'}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Render commissions table (grouped by CTV)
 */
function renderCommissionsTable() {
    const tbody = document.querySelector('#commissions-table tbody');
    if (!rawData.commissions || rawData.commissions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8">No commissions found</td></tr>';
        return;
    }
    let lastCTV = null;
    
    tbody.innerHTML = rawData.commissions.map(c => {
        const isNewGroup = c.ctv_code !== lastCTV;
        lastCTV = c.ctv_code;
        
        return `
            <tr data-ctv="${c.ctv_code}" 
                class="${isNewGroup ? 'group-start' : ''}"
                onclick="scrollToHierarchy('${c.ctv_code}')">
                <td>${c.id}</td>
                <td>${c.ctv_code}</td>
                <td>${c.ctv_name || '-'}</td>
                <td><span class="level-badge level-${c.level}">L${c.level}</span></td>
                <td>${c.source_name || '-'}</td>
                <td class="money">${formatMoney(c.source_amount)}</td>
                <td class="money">${formatMoney(c.commission_amount)}</td>
                <td>${c.closer_ctv || '-'}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Show CTV detail modal
 */
async function showCTVDetail(ctvCode) {
    try {
        const response = await fetch(`/api/admin/debug/ctv-detail/${ctvCode}`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }
        
        const modal = document.getElementById('ctv-detail-modal');
        const title = document.getElementById('modal-title');
        const body = document.getElementById('modal-body');
        
        title.textContent = `${data.ctv.ten} (${data.ctv.ma_ctv})`;
        
        body.innerHTML = `
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="value">${data.summary.total_clients}</div>
                    <div class="label">Clients</div>
                </div>
                <div class="summary-card">
                    <div class="value">${formatMoney(data.summary.total_revenue)}</div>
                    <div class="label">Revenue</div>
                </div>
                <div class="summary-card">
                    <div class="value">${formatMoney(data.summary.total_commission)}</div>
                    <div class="label">Commission</div>
                </div>
                <div class="summary-card">
                    <div class="value">${data.summary.downline_count}</div>
                    <div class="label">Downline</div>
                </div>
            </div>
            
            <div class="modal-section">
                <h3>Commission Breakdown</h3>
                <table class="debug-table">
                    <thead>
                        <tr>
                            <th>Level</th>
                            <th>Source</th>
                            <th>Source Amount</th>
                            <th>Commission</th>
                            <th>Expected</th>
                            <th>Match?</th>
                        </tr>
                    </thead>
                    <tbody>
                            ${data.commissions.map(c => {
                            const rate = rawData.rates.find(r => r.level === c.level)?.rate || 0;
                            const expected = (c.source_amount || 0) * rate;
                            const actual = c.commission_amount || 0;
                            const match = Math.abs(expected - actual) < 1;
                            return `
                                <tr>
                                    <td><span class="level-badge level-${c.level}">L${c.level}</span></td>
                                    <td>${c.source_name || '-'}</td>
                                    <td class="money">${formatMoney(c.source_amount)}</td>
                                    <td class="money">${formatMoney(actual)}</td>
                                    <td class="money">${formatMoney(expected)}</td>
                                    <td class="${match ? 'match-yes' : 'match-no'}">${match ? 'YES' : 'NO'}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
            
            <div class="modal-section">
                <h3>Clients (${data.clients.length})</h3>
                <table class="debug-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Phone</th>
                            <th>Revenue</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.clients.map(c => `
                            <tr>
                                <td>${c.id}</td>
                                <td>${c.ho_ten || '-'}</td>
                                <td>${c.sdt || '-'}</td>
                                <td class="money">${formatMoney(c.tong_tien)}</td>
                                <td>${c.ngay_hen_lam || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            
            ${data.downline.length > 0 ? `
                <div class="modal-section">
                    <h3>Downline CTVs (${data.downline.length})</h3>
                    <table class="debug-table">
                        <thead>
                            <tr>
                                <th>Level</th>
                                <th>Code</th>
                                <th>Name</th>
                                <th>Referrer</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.downline.map(d => `
                                <tr>
                                    <td><span class="level-badge level-${d.level}">L${d.level}</span></td>
                                    <td>${d.ma_ctv}</td>
                                    <td>${d.ten || '-'}</td>
                                    <td>${d.nguoi_gioi_thieu || '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : ''}
        `;
        
        modal.classList.add('show');
        
    } catch (error) {
        console.error('Error loading CTV detail:', error);
    }
}

/**
 * Close modal
 */
function closeModal() {
    document.getElementById('ctv-detail-modal').classList.remove('show');
}

/**
 * Format money
 */
function formatMoney(amount) {
    if (!amount) return '0d';
    return new Intl.NumberFormat('vi-VN').format(amount) + 'd';
}

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Close modal on background click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('debug-modal')) {
        closeModal();
    }
});

