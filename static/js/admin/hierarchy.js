/**
 * Admin Dashboard - Hierarchy Module
 * Hierarchy tree, searchable dropdown, tree controls
 * 
 * Created: December 30, 2025
 */

// State
let currentHierarchyData = null;
let hierarchyDropdownOpen = false;
let highlightedIndex = -1;

/**
 * Initialize hierarchy dropdown
 */
async function initHierarchyDropdown() {
    const dropdown = document.getElementById('hierarchyDropdown');
    const input = document.getElementById('hierarchySearch');
    const list = document.getElementById('hierarchyList');
    
    if (!dropdown || !input || !list) return;
    
    // Load CTV list if not already loaded or if it's empty
    if (!window.allCTV || window.allCTV.length === 0) {
        try {
            const result = await api('/api/admin/ctv?active_only=true');
            if (result.status === 'success') {
                window.allCTV = result.data;
            }
        } catch (error) {
            console.error('Error loading CTV list for hierarchy:', error);
        }
    }
    
    // Render all items initially (this will use the loaded CTV list)
    renderHierarchyList('');
    
    // Input events
    input.addEventListener('focus', () => {
        // Clear the input when clicked/focused so user can search fresh
        input.value = '';
        renderHierarchyList('');
        openHierarchyDropdown();
    });
    
    input.addEventListener('input', (e) => {
        renderHierarchyList(e.target.value);
        openHierarchyDropdown();
        highlightedIndex = -1;
    });
    
    input.addEventListener('keydown', (e) => {
        const items = list.querySelectorAll('.dropdown-item');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);
            updateHighlight(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            highlightedIndex = Math.max(highlightedIndex - 1, 0);
            updateHighlight(items);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (highlightedIndex >= 0 && items[highlightedIndex]) {
                selectHierarchyCTV(items[highlightedIndex].dataset.value);
            }
        } else if (e.key === 'Escape') {
            closeHierarchyDropdown();
        }
    });
    
    // Click outside to close
    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target)) {
            closeHierarchyDropdown();
        }
    });
    
    // Arrow click to toggle
    const arrow = dropdown.querySelector('.dropdown-arrow');
    if (arrow) {
        arrow.addEventListener('click', (e) => {
            e.stopPropagation();
            if (hierarchyDropdownOpen) {
                closeHierarchyDropdown();
            } else {
                input.focus();
                openHierarchyDropdown();
            }
        });
    }
}

function openHierarchyDropdown() {
    const dropdown = document.getElementById('hierarchyDropdown');
    if (dropdown) {
        dropdown.classList.add('open');
        hierarchyDropdownOpen = true;
    }
}

function closeHierarchyDropdown() {
    const dropdown = document.getElementById('hierarchyDropdown');
    if (dropdown) {
        dropdown.classList.remove('open');
        hierarchyDropdownOpen = false;
        highlightedIndex = -1;
    }
}

function renderHierarchyList(searchTerm) {
    const list = document.getElementById('hierarchyList');
    if (!list) return;
    
    const term = searchTerm.toLowerCase();
    
    // Only show active CTVs in hierarchy dropdown
    const filtered = (window.allCTV || []).filter(c => 
        c.is_active !== false &&
        (c.ma_ctv.toLowerCase().includes(term) ||
        c.ten.toLowerCase().includes(term))
    );
    
    if (filtered.length === 0) {
        list.innerHTML = `<div class="no-results">${t('no_ctv_found')}</div>`;
        return;
    }
    
    // Sort: exact code match first, then by code
    filtered.sort((a, b) => {
        const aExact = a.ma_ctv.toLowerCase() === term;
        const bExact = b.ma_ctv.toLowerCase() === term;
        if (aExact && !bExact) return -1;
        if (!aExact && bExact) return 1;
        return a.ma_ctv.localeCompare(b.ma_ctv);
    });
    
    const selectedValue = document.getElementById('hierarchyRoot')?.value || '';
    
    list.innerHTML = filtered.slice(0, 50).map(c => {
        // Show level badge if CTV has levels below
        // Check both max_depth_below property and ensure it's a number > 0
        const maxDepth = c.max_depth_below !== undefined && c.max_depth_below !== null 
            ? parseInt(c.max_depth_below) 
            : 0;
        const levelBadge = (maxDepth > 0) 
            ? `<span class="level-count-badge">${maxDepth}</span>` 
            : '';
        
        return `
        <div class="dropdown-item ${c.ma_ctv === selectedValue ? 'selected' : ''}" 
             data-value="${c.ma_ctv}" 
             onclick="selectHierarchyCTV('${c.ma_ctv}')">
            <span><strong>${c.ma_ctv}</strong> - ${c.ten}</span>${levelBadge}
        </div>
        `;
    }).join('');
}

function updateHighlight(items) {
    items.forEach((item, i) => {
        item.classList.toggle('highlighted', i === highlightedIndex);
    });
    if (highlightedIndex >= 0 && items[highlightedIndex]) {
        items[highlightedIndex].scrollIntoView({ block: 'nearest' });
    }
}

function selectHierarchyCTV(ctvCode) {
    const ctv = (window.allCTV || []).find(c => c.ma_ctv === ctvCode);
    if (ctv) {
        document.getElementById('hierarchySearch').value = `${ctv.ma_ctv} - ${ctv.ten}`;
        document.getElementById('hierarchyRoot').value = ctvCode;
        closeHierarchyDropdown();
        loadHierarchy(ctvCode);
    }
}

/**
 * Load hierarchy tree for a CTV
 * @param {string} ctvCode - CTV code
 */
async function loadHierarchy(ctvCode) {
    // Show loading indicator, hide placeholder and wrapper
    const loadingEl = document.getElementById('hierarchyLoading');
    const wrapperEl = document.getElementById('hierarchyTreeWrapper');
    const placeholderEl = document.getElementById('hierarchyPlaceholder');
    
    if (loadingEl) loadingEl.classList.add('active');
    if (wrapperEl) wrapperEl.style.display = 'none';
    if (placeholderEl) placeholderEl.style.display = 'none';
    
    try {
        const result = await api(`/api/admin/hierarchy/${ctvCode}`);
        
        // Hide loading indicator
        if (loadingEl) loadingEl.classList.remove('active');
        
        if (result.status === 'success') {
            currentHierarchyData = result.hierarchy;
            
            // Show the wrapper
            if (wrapperEl) wrapperEl.style.display = 'block';
            
            // Calculate and display stats
            const stats = calculateTreeStats(result.hierarchy);
            document.getElementById('statTotalMembers').textContent = stats.totalMembers;
            document.getElementById('statLevelsDeep').textContent = stats.maxDepth;
            document.getElementById('statDirectRecruits').textContent = stats.directRecruits;
            
            // Render the tree
            document.getElementById('hierarchyTree').innerHTML = '<ul>' + renderTree(result.hierarchy) + '</ul>';
            
            // Initialize search
            initTreeSearch();
            
            // Expand all by default
            expandAllNodes();
        } else {
            // Show placeholder on error
            if (placeholderEl) placeholderEl.style.display = 'block';
        }
    } catch (error) {
        // Hide loading and show placeholder on error
        if (loadingEl) loadingEl.classList.remove('active');
        if (placeholderEl) placeholderEl.style.display = 'block';
        console.error('Error loading hierarchy:', error);
    }
}

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

function renderTree(node) {
    // Display level matches database level (L0-L4)
    const displayLevel = node.level;
    const levelClass = `l${displayLevel}`;
    
    const hasChildren = node.children && node.children.length > 0;
    const hasChildrenClass = hasChildren ? 'has-children expanded' : '';
    
    // Get custom label for this level
    const levelLabel = getCommissionLabel(displayLevel);
    
    // Commission rate display
    const commissionPercent = (node.commission_rate * 100).toFixed(2);
    
    // Cut-off badge for level 4 (L4)
    const cutoffBadge = node.level === 4 ? '<span class="cutoff-badge">CUT OFF</span>' : '';
    
    let html = `
        <li>
            <div class="tree-node ${hasChildrenClass}" 
                 data-name="${node.ten || ''}" 
                 data-code="${node.ma_ctv || ''}"
                 onclick="toggleTreeNode(this)">
                <span class="level-badge ${levelClass}">${levelLabel}</span>
                <span class="node-name">${node.ten || 'Unknown'}</span>
                <span class="node-code">${node.ma_ctv}</span>
                <span class="node-rank">${levelLabel} | ${commissionPercent}%</span>
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

function toggleTreeNode(element) {
    const li = element.parentElement;
    const children = li.querySelector(':scope > ul.tree-children');
    
    if (children) {
        element.classList.toggle('expanded');
        children.classList.toggle('collapsed');
    }
}

function expandAllNodes() {
    document.querySelectorAll('#hierarchyTree .tree-node.has-children').forEach(node => {
        node.classList.add('expanded');
    });
    document.querySelectorAll('#hierarchyTree .tree-children').forEach(child => {
        child.classList.remove('collapsed');
    });
}

function collapseAllNodes() {
    document.querySelectorAll('#hierarchyTree .tree-node.has-children').forEach(node => {
        node.classList.remove('expanded');
    });
    document.querySelectorAll('#hierarchyTree .tree-children').forEach(child => {
        child.classList.add('collapsed');
    });
}

function initTreeSearch() {
    const searchBox = document.getElementById('treeSearchBox');
    const searchInfo = document.getElementById('treeSearchInfo');
    
    if (!searchBox || !searchInfo) return;
    
    // Clear previous listeners by cloning
    const newSearchBox = searchBox.cloneNode(true);
    searchBox.parentNode.replaceChild(newSearchBox, searchBox);
    
    newSearchBox.addEventListener('input', function() {
        const query = this.value.toLowerCase().trim();
        const allNodes = document.querySelectorAll('#hierarchyTree .tree-node');
        
        // Remove all highlights first
        allNodes.forEach(node => node.classList.remove('highlighted'));
        
        if (query === '') {
            searchInfo.textContent = '';
            return;
        }
        
        let matchCount = 0;
        let firstMatch = null;
        
        allNodes.forEach(node => {
            const name = (node.dataset.name || '').toLowerCase();
            const code = (node.dataset.code || '').toLowerCase();
            
            if (name.includes(query) || code.includes(query)) {
                node.classList.add('highlighted');
                matchCount++;
                
                if (!firstMatch) {
                    firstMatch = node;
                }
                
                // Expand all parents to show this node
                let parent = node.parentElement;
                while (parent) {
                    if (parent.classList && parent.classList.contains('tree-children')) {
                        parent.classList.remove('collapsed');
                        const parentNode = parent.parentElement.querySelector(':scope > .tree-node');
                        if (parentNode) {
                            parentNode.classList.add('expanded');
                        }
                    }
                    parent = parent.parentElement;
                }
            }
        });
        
        if (matchCount > 0) {
            searchInfo.textContent = `Tìm thấy ${matchCount} kết quả`;
            if (firstMatch) {
                firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } else {
            searchInfo.textContent = 'Không tìm thấy kết quả nào';
        }
    });
}

/**
 * View hierarchy for a CTV (called from CTV table)
 * @param {string} ctvCode - CTV code
 */
function viewHierarchy(ctvCode) {
    const ctv = (window.allCTV || []).find(c => c.ma_ctv === ctvCode);
    if (ctv) {
        document.getElementById('hierarchySearch').value = `${ctv.ma_ctv} - ${ctv.ten}`;
        document.getElementById('hierarchyRoot').value = ctvCode;
    }
    loadHierarchy(ctvCode);
    navigateTo('hierarchy');
}

