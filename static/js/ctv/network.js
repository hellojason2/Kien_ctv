/**
 * CTV Portal - Network Module
 * DOES: Loads and displays MLM hierarchy tree and downline
 * INPUTS: API responses from /api/ctv/my-hierarchy and /api/ctv/my-downline
 * OUTPUTS: Renders hierarchy tree visualization
 * FLOW: loadNetwork -> calculateTreeStats -> renderTree
 */

// Calculate tree stats helper
function calculateTreeStats(node, depth = 1) {
    let stats = {
        totalMembers: 1,
        maxDepth: depth,
        directRecruits: node.children ? node.children.length : 0
    };
    
    if (node.children && node.children.length > 0) {
        node.children.forEach(child => {
            const childStats = calculateTreeStats(child, depth + 1);
            stats.totalMembers += childStats.totalMembers;
            stats.maxDepth = Math.max(stats.maxDepth, childStats.maxDepth);
        });
    }
    
    return stats;
}

// Load Network
async function loadNetwork() {
    // Load hierarchy tree
    const treeResult = await api('/api/ctv/my-hierarchy');
    if (treeResult.status === 'success') {
        // Calculate stats
        const stats = calculateTreeStats(treeResult.hierarchy);
        
        // Render with wrapper structure
        const treeHTML = `
            <div class="tree-stats">
                <div class="tree-stat">
                    <div class="number">${stats.totalMembers}</div>
                    <div class="label">${t('total_members')}</div>
                </div>
                <div class="tree-stat">
                    <div class="number">${stats.maxDepth}</div>
                    <div class="label">${t('levels_deep')}</div>
                </div>
                <div class="tree-stat">
                    <div class="number">${stats.directRecruits}</div>
                    <div class="label">${t('direct_recruits')}</div>
                </div>
            </div>
            <div class="tree-controls">
                <button class="tree-btn" onclick="expandAllTreeNodes()">${t('expand_all')}</button>
                <button class="tree-btn" onclick="collapseAllTreeNodes()">${t('collapse_all')}</button>
            </div>
            <div class="tree-wrapper">
                <ul>${renderTree(treeResult.hierarchy)}</ul>
            </div>
        `;
        document.getElementById('networkTree').innerHTML = treeHTML;
    }
    
    // Load direct downline
    const downlineResult = await api('/api/ctv/my-downline');
    if (downlineResult.status === 'success') {
        const container = document.getElementById('directDownline');
        if (downlineResult.downline.length === 0) {
            container.innerHTML = `<div class="empty-state">${t('no_referrals')}</div>`;
        } else {
            container.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>${t('ctv_code_col')}</th>
                            <th>${t('name_col')}</th>
                            <th>${t('email_col')}</th>
                            <th>${t('phone_col')}</th>
                            <th>${t('rank_col')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${downlineResult.downline.map(d => `
                            <tr>
                                <td>${d.ma_ctv}</td>
                                <td>${d.ten}</td>
                                <td>${d.email || '-'}</td>
                                <td>${d.sdt || '-'}</td>
                                <td>${d.cap_bac || 'Bronze'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
    }
}

// Render tree node recursively
function renderTree(node) {
    // Display level matches database level (L0-L4)
    const displayLevel = node.level;
    const levelClass = `l${displayLevel}`;
    
    const hasChildren = node.children && node.children.length > 0;
    const hasChildrenClass = hasChildren ? 'has-children expanded' : '';
    
    // Cut-off badge for level 4 (L4)
    const cutoffBadge = node.level === 4 ? '<span class="cutoff-badge">CUT OFF</span>' : '';
    
    let html = `
        <li>
            <div class="tree-node ${hasChildrenClass}" onclick="toggleTreeNode(this)">
                <span class="level-badge ${levelClass}">L${displayLevel}</span>
                <span class="node-name">${node.ten || 'Unknown'}</span>
                <span class="node-code">${node.ma_ctv}</span>
                <span class="node-info">${node.cap_bac || 'Bronze'}</span>
                ${cutoffBadge}
            </div>
    `;
    
    if (hasChildren) {
        html += '<ul class="tree-children">';
        node.children.forEach(child => {
            html += renderTree(child);
        });
        html += '</ul>';
    }
    
    html += '</li>';
    return html;
}

// Toggle tree node expand/collapse
function toggleTreeNode(element) {
    const li = element.parentElement;
    const children = li.querySelector(':scope > ul.tree-children');
    
    if (children) {
        element.classList.toggle('expanded');
        children.classList.toggle('collapsed');
    }
}

// Expand all tree nodes
function expandAllTreeNodes() {
    document.querySelectorAll('#networkTree .tree-node.has-children').forEach(node => {
        node.classList.add('expanded');
    });
    document.querySelectorAll('#networkTree .tree-children').forEach(child => {
        child.classList.remove('collapsed');
    });
}

// Collapse all tree nodes
function collapseAllTreeNodes() {
    document.querySelectorAll('#networkTree .tree-node.has-children').forEach(node => {
        node.classList.remove('expanded');
    });
    document.querySelectorAll('#networkTree .tree-children').forEach(child => {
        child.classList.add('collapsed');
    });
}

