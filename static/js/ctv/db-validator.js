/**
 * CTV Portal - Database Schema Validator
 * Checks database connection and schema validity on page load
 * 
 * Created: January 4, 2026
 */

// Configuration
const DB_VALIDATION_TIMEOUT = 10000; // 10 seconds
const DB_VALIDATION_ENDPOINT = '/api/validate-schema';

/**
 * Show database error modal
 */
function showDatabaseError(errorMessage, details = []) {
    // Remove existing error modal if any
    const existingModal = document.getElementById('dbErrorModal');
    if (existingModal) existingModal.remove();
    
    // Create modal HTML
    const modalHTML = `
        <div id="dbErrorModal" class="db-error-modal">
            <div class="db-error-content">
                <div class="db-error-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                </div>
                <h2>Database Error</h2>
                <p class="db-error-message">${errorMessage}</p>
                ${details.length > 0 ? `
                    <div class="db-error-details">
                        <strong>Details:</strong>
                        <ul>
                            ${details.map(d => `<li>${d}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                <p class="db-error-hint">Please check your database configuration or contact support.</p>
                <button onclick="location.reload()" class="db-error-retry-btn">Retry Connection</button>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add styles if not already present
    if (!document.getElementById('dbErrorStyles')) {
        const styles = document.createElement('style');
        styles.id = 'dbErrorStyles';
        styles.textContent = `
            .db-error-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.9);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 99999;
                animation: fadeIn 0.3s ease;
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            .db-error-content {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                border: 1px solid #e74c3c;
                border-radius: 16px;
                padding: 40px;
                max-width: 500px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(231, 76, 60, 0.3);
            }
            .db-error-icon {
                width: 80px;
                height: 80px;
                margin: 0 auto 20px;
                background: rgba(231, 76, 60, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .db-error-icon svg {
                width: 48px;
                height: 48px;
                color: #e74c3c;
            }
            .db-error-content h2 {
                color: #e74c3c;
                font-size: 28px;
                margin-bottom: 16px;
                font-weight: 700;
            }
            .db-error-message {
                color: #fff;
                font-size: 16px;
                margin-bottom: 20px;
                line-height: 1.6;
            }
            .db-error-details {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 20px;
                text-align: left;
            }
            .db-error-details strong {
                color: #f39c12;
                display: block;
                margin-bottom: 8px;
            }
            .db-error-details ul {
                margin: 0;
                padding-left: 20px;
                color: #bdc3c7;
                font-size: 13px;
            }
            .db-error-details li {
                margin-bottom: 4px;
            }
            .db-error-hint {
                color: #95a5a6;
                font-size: 14px;
                margin-bottom: 24px;
            }
            .db-error-retry-btn {
                background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                color: white;
                border: none;
                padding: 14px 32px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .db-error-retry-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(231, 76, 60, 0.4);
            }
        `;
        document.head.appendChild(styles);
    }
}

/**
 * Validate database schema
 * @returns {Promise<boolean>} True if valid, false if error
 */
async function validateDatabaseSchema() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), DB_VALIDATION_TIMEOUT);
    
    try {
        const response = await fetch(DB_VALIDATION_ENDPOINT, {
            method: 'GET',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            showDatabaseError(
                data.message || 'Failed to connect to database',
                data.details || []
            );
            return false;
        }
        
        const data = await response.json();
        
        if (!data.valid) {
            showDatabaseError(
                data.message || 'Connected to wrong database',
                data.details || []
            );
            return false;
        }
        
        console.log('Database schema validated successfully:', data.database);
        return true;
        
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            showDatabaseError(
                'Database connection timed out',
                ['Connection took longer than 10 seconds', 'The database server may be unreachable']
            );
        } else {
            showDatabaseError(
                'Cannot reach database server',
                [error.message || 'Network error occurred']
            );
        }
        return false;
    }
}

/**
 * Initialize database validation on page load
 */
async function initDatabaseValidation() {
    const isValid = await validateDatabaseSchema();
    if (!isValid) {
        // Disable interactions if database is invalid
        document.body.style.pointerEvents = 'none';
        const modal = document.getElementById('dbErrorModal');
        if (modal) {
            modal.style.pointerEvents = 'auto';
        }
    }
    return isValid;
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.validateDatabaseSchema = validateDatabaseSchema;
    window.showDatabaseError = showDatabaseError;
    window.initDatabaseValidation = initDatabaseValidation;
}


