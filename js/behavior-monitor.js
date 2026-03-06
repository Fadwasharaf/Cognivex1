/**
 * COGNIVEX v2.0 - BEHAVIORAL BIOMETRICS
 * Phase 1: Session-Based Behavior Monitoring
 * 
 * This module:
 * - Tracks keyboard, mouse, and scroll events
 * - Sends 30-second snapshots to backend
 * - Handles OTP challenges
 * - Manages session lifecycle
 */

console.log("🚀 COGNIVEX Behavior Monitor v2.0");

// ============================================
// CONFIGURATION
// ============================================

const API_BASE_URL = 'http://localhost:5000';
const SNAPSHOT_INTERVAL = 30000; // 30 seconds
const SESSION_ID_PREFIX = 'session_';

// ============================================
// STATE MANAGEMENT
// ============================================

let sessionId = null;
let sessionStartTime = null;
let currentUserId = null;
let isMonitoring = false;
let monitoringInterval = null;

let eventBuffer = {
    key_events: [],
    mouse_events: [],
    scroll_events: [],
    summary: {
        total_keys: 0,
        total_mouse_moves: 0,
        total_scrolls: 0,
        window_start: null,
        window_end: null
    }
};

// ============================================
// SESSION INITIALIZATION
// ============================================

function initializeSession(userId) {
    /**
     * Initialize a new session when user logs in
     */
    
    if (isMonitoring) {
        console.warn("⚠️ Session already initialized");
        return;
    }
    
    currentUserId = userId;
    sessionId = SESSION_ID_PREFIX + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    sessionStartTime = Date.now();
    
    console.log(`✅ Session initialized`);
    console.log(`   User ID: ${currentUserId}`);
    console.log(`   Session ID: ${sessionId}`);
    
    // Clear event buffer
    eventBuffer = {
        key_events: [],
        mouse_events: [],
        scroll_events: [],
        summary: {
            total_keys: 0,
            total_mouse_moves: 0,
            total_scrolls: 0,
            window_start: null,
            window_end: null
        }
    };
    
    // Start event tracking
    attachEventListeners();
    
    // Start 30-second snapshot timer
    startMonitoring();
    
    console.log(`📊 Monitoring started (30-sec intervals)`);
}

// ============================================
// EVENT TRACKING
// ============================================

function attachEventListeners() {
    /**
     * Attach event listeners to document
     */
    
    document.addEventListener('keydown', trackKeyDown, true);
    document.addEventListener('keyup', trackKeyUp, true);
    document.addEventListener('mousemove', throttle(trackMouseMove, 100), true);
    document.addEventListener('scroll', throttle(trackScroll, 200), true);
    
    console.log(`✅ Event listeners attached`);
}

function detachEventListeners() {
    /**
     * Remove event listeners from document
     */
    
    document.removeEventListener('keydown', trackKeyDown, true);
    document.removeEventListener('keyup', trackKeyUp, true);
    document.removeEventListener('mousemove', trackMouseMove, true);
    document.removeEventListener('scroll', trackScroll, true);
    
    console.log(`✅ Event listeners detached`);
}

function trackKeyDown(event) {
    /**
     * Track keyboard key down event
     */
    
    eventBuffer.key_events.push({
        type: 'keydown',
        key: event.key,
        code: event.code,
        timestamp: Date.now()
    });
    
    eventBuffer.summary.total_keys++;
}

function trackKeyUp(event) {
    /**
     * Track keyboard key up event
     */
    
    eventBuffer.key_events.push({
        type: 'keyup',
        key: event.key,
        code: event.code,
        timestamp: Date.now()
    });
}

function trackMouseMove(event) {
    /**
     * Track mouse movement (throttled)
     */
    
    eventBuffer.mouse_events.push({
        x: Math.round(event.clientX),
        y: Math.round(event.clientY),
        timestamp: Date.now()
    });
    
    eventBuffer.summary.total_mouse_moves++;
}

function trackScroll(event) {
    /**
     * Track scroll events
     */
    
    eventBuffer.scroll_events.push({
        scrollY: Math.round(window.scrollY),
        scrollX: Math.round(window.scrollX),
        timestamp: Date.now()
    });
    
    eventBuffer.summary.total_scrolls++;
}

// ============================================
// THROTTLE UTILITY
// ============================================

function throttle(func, limit) {
    /**
     * Throttle function calls
     */
    
    let inThrottle;
    return function() {
        if (!inThrottle) {
            func.apply(this, arguments);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// ============================================
// MONITORING CONTROL
// ============================================

function startMonitoring() {
    /**
     * Start 30-second snapshot monitoring
     */
    
    if (isMonitoring) {
        console.warn("⚠️ Already monitoring");
        return;
    }
    
    isMonitoring = true;
    
    // Send first snapshot immediately (after 30 seconds of first activity)
    monitoringInterval = setInterval(() => {
        flushSnapshot();
    }, SNAPSHOT_INTERVAL);
    
    console.log(`🔄 Monitoring started`);
}

function stopMonitoring() {
    /**
     * Stop 30-second snapshot monitoring
     */
    
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
        monitoringInterval = null;
    }
    
    isMonitoring = false;
    console.log(`⏹️ Monitoring stopped`);
}

// ============================================
// SNAPSHOT SENDING (Every 30 seconds)
// ============================================

async function flushSnapshot() {
    /**
     * Send 30-second behavioral snapshot to backend
     * - Stores in behavior_logs (temporary)
     * - Backend extracts features in-memory
     * - Backend scores with model
     * - Returns risk level (LOW/MEDIUM/HIGH)
     */
    
    if (!currentUserId || !sessionId) {
        console.warn("⚠️ No active session");
        return;
    }
    
    if (eventBuffer.key_events.length === 0) {
        console.log("ℹ️ No events in this window, skipping snapshot");
        return;
    }
    
    console.log(`\n📤 Sending 30-sec snapshot...`);
    console.log(`   Events: ${eventBuffer.key_events.length} keys, ${eventBuffer.mouse_events.length} mouse, ${eventBuffer.scroll_events.length} scrolls`);
    
    try {
        const payload = {
            user_id: currentUserId,
            session_id: sessionId,
            raw_data: {
                key_events: eventBuffer.key_events,
                mouse_events: eventBuffer.mouse_events,
                scroll_events: eventBuffer.scroll_events,
                summary: eventBuffer.summary
            }
        };
        
        const response = await fetch(`${API_BASE_URL}/session/snapshot`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        console.log(`📊 Backend response:`);
        console.log(`   Status: ${result.status}`);
        console.log(`   Risk Level: ${result.risk_level || 'N/A'}`);
        console.log(`   Message: ${result.message}`);
        
        // Handle risk levels
        if (result.status === 'OTP_REQUIRED') {
            console.log(`⚠️ MEDIUM RISK - OTP Challenge Required`);
            stopMonitoring(); // Pause monitoring during OTP
            showOTPChallenge(result.session_id);
        } 
        else if (result.status === 'SESSION_TERMINATED') {
            console.log(`❌ HIGH RISK - Session Terminated`);
            stopMonitoring();
            alert('🚨 Suspicious activity detected. Your session has been terminated.');
            await window.authHandler.logout();
        }
        else if (result.status === 'OK') {
            console.log(`✅ LOW RISK - Continuing normally`);
            updateDashboardIndicator(result.risk_level);
        }
        
    } catch (err) {
        console.error(`❌ Error sending snapshot:`, err);
    } finally {
        // Clear event buffer for next window
        eventBuffer = {
            key_events: [],
            mouse_events: [],
            scroll_events: [],
            summary: {
                total_keys: 0,
                total_mouse_moves: 0,
                total_scrolls: 0,
                window_start: Date.now(),
                window_end: null
            }
        };
    }
}

// ============================================
// RISK INDICATOR (Dashboard UI)
// ============================================

function updateDashboardIndicator(riskLevel) {
    /**
     * Update risk indicator on dashboard
     */
    
    const indicator = document.getElementById('risk-indicator');
    const riskText = document.getElementById('risk-level-text');
    
    if (!indicator || !riskText) {
        return; // Not on dashboard
    }
    
    // Remove all classes
    indicator.className = 'risk-indicator';
    
    // Add appropriate class and text
    switch(riskLevel) {
        case 'LOW':
            indicator.classList.add('low-risk');
            riskText.textContent = '✅ Normal Activity';
            riskText.style.color = '#10b981';
            break;
        case 'MEDIUM':
            indicator.classList.add('medium-risk');
            riskText.textContent = '⚠️ Verification Required';
            riskText.style.color = '#f59e0b';
            break;
        case 'HIGH':
            indicator.classList.add('high-risk');
            riskText.textContent = '🚨 Suspicious Activity';
            riskText.style.color = '#ef4444';
            break;
    }
    
    console.log(`🎨 Dashboard indicator updated: ${riskLevel}`);
}

// ============================================
// OTP CHALLENGE UI
// ============================================

function showOTPChallenge(sessionId) {
    /**
     * Show OTP verification modal
     * User must enter 4-digit OTP within 2 minutes
     */
    
    console.log(`🔐 Showing OTP challenge modal`);
    
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'otp-challenge-modal';
    modal.className = 'otp-modal';
    modal.innerHTML = `
        <div class="otp-modal-content">
            <div class="otp-icon">⚠️</div>
            <h2>Verify Your Activity</h2>
            <p>We detected unusual behavior. Please enter the 4-digit code sent to your email.</p>
            
            <input 
                type="text" 
                id="otp-input" 
                class="otp-input" 
                placeholder="0000" 
                maxlength="4"
                inputmode="numeric"
            >
            
            <div class="otp-timer">
                <span id="otp-time-remaining">2:00</span> remaining
            </div>
            
            <div class="otp-buttons">
                <button id="verify-otp-btn" class="btn btn-primary">Verify OTP</button>
                <button id="cancel-otp-btn" class="btn btn-secondary">Logout</button>
            </div>
            
            <div id="otp-error" class="otp-error" style="display: none;"></div>
            <div id="otp-success" class="otp-success" style="display: none;"></div>
        </div>
    `;
    
    document.body.appendChild(modal);
    addOTPStyles();
    
    // Focus on input
    setTimeout(() => {
        document.getElementById('otp-input').focus();
    }, 300);
    
    // Timer (2 minutes)
    let timeRemaining = 120;
    const timerInterval = setInterval(() => {
        timeRemaining--;
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        document.getElementById('otp-time-remaining').textContent = 
            `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            showOTPError('OTP expired. Please logout and try again.');
            document.getElementById('verify-otp-btn').disabled = true;
        }
    }, 1000);
    
    // Verify button
    document.getElementById('verify-otp-btn').addEventListener('click', async () => {
        clearInterval(timerInterval);
        const otp = document.getElementById('otp-input').value;
        
        if (!otp || otp.length !== 4) {
            showOTPError('Please enter a 4-digit OTP');
            return;
        }
        
        await verifyOTP(sessionId, otp);
    });
    
    // Cancel button
    document.getElementById('cancel-otp-btn').addEventListener('click', async () => {
        clearInterval(timerInterval);
        console.log(`❌ User cancelled OTP - Logging out`);
        modal.remove();
        alert('Session terminated.');
        await window.authHandler.logout();
    });
    
    // Allow Enter key to submit
    document.getElementById('otp-input').addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            clearInterval(timerInterval);
            document.getElementById('verify-otp-btn').click();
        }
    });
}

function showOTPError(message) {
    /**
     * Show OTP error message
     */
    const errorDiv = document.getElementById('otp-error');
    errorDiv.textContent = `❌ ${message}`;
    errorDiv.style.display = 'block';
}

function showOTPSuccess(message) {
    /**
     * Show OTP success message
     */
    const successDiv = document.getElementById('otp-success');
    successDiv.textContent = `✅ ${message}`;
    successDiv.style.display = 'block';
}

// ============================================
// OTP VERIFICATION
// ============================================

async function verifyOTP(sessionId, otpCode) {
    /**
     * Verify OTP with backend
     * If correct: Resume session
     * If wrong: Logout immediately
     */
    
    console.log(`🔐 Verifying OTP...`);
    
    try {
        const response = await fetch(`${API_BASE_URL}/verify-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUserId,
                session_id: sessionId,
                otp_code: otpCode
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'OTP_VERIFIED') {
            console.log(`✅ OTP Verified! Resuming session`);
            showOTPSuccess('OTP verified! Resuming your session...');
            
            setTimeout(() => {
                document.getElementById('otp-challenge-modal').remove();
                startMonitoring(); // Resume monitoring
            }, 2000);
        } 
        else {
            console.log(`❌ OTP Failed - Logging out`);
            showOTPError('Invalid OTP. Session terminated.');
            
            setTimeout(async () => {
                document.getElementById('otp-challenge-modal').remove();
                await window.authHandler.logout();
            }, 2000);
        }
        
    } catch (err) {
        console.error(`❌ Error verifying OTP:`, err);
        showOTPError('Error verifying OTP. Please logout and try again.');
    }
}

// ============================================
// OTP STYLES
// ============================================

function addOTPStyles() {
    /**
     * Add CSS styles for OTP modal
     */
    
    if (document.getElementById('otp-styles')) return;
    
    const styles = document.createElement('style');
    styles.id = 'otp-styles';
    styles.textContent = `
        .otp-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            animation: fadeIn 0.3s ease-out;
        }
        
        .otp-modal-content {
            background: white;
            padding: 2.5rem;
            border-radius: 16px;
            width: 90%;
            max-width: 450px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            text-align: center;
            animation: slideUp 0.3s ease-out;
        }
        
        .otp-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            animation: pulse 2s infinite;
        }
        
        .otp-modal-content h2 {
            color: #1f2937;
            margin-bottom: 0.5rem;
            font-size: 1.75rem;
        }
        
        .otp-modal-content p {
            color: #6b7280;
            margin-bottom: 2rem;
            line-height: 1.6;
            font-size: 0.95rem;
        }
        
        .otp-input {
            width: 100%;
            padding: 1rem;
            font-size: 2rem;
            letter-spacing: 0.5rem;
            text-align: center;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-family: 'Courier New', monospace;
            transition: all 0.2s ease;
        }
        
        .otp-input:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
        }
        
        .otp-timer {
            font-size: 0.95rem;
            color: #6b7280;
            margin-bottom: 1.5rem;
        }
        
        .otp-timer #otp-time-remaining {
            font-weight: 700;
            color: #ef4444;
            font-size: 1.1rem;
        }
        
        .otp-buttons {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .otp-buttons .btn {
            flex: 1;
            padding: 0.875rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            text-transform: uppercase;
            font-size: 0.9rem;
            letter-spacing: 0.5px;
        }
        
        .otp-buttons .btn-primary {
            background: #2563eb;
            color: white;
        }
        
        .otp-buttons .btn-primary:hover:not(:disabled) {
            background: #1d4ed8;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }
        
        .otp-buttons .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .otp-buttons .btn-secondary {
            background: #ef4444;
            color: white;
        }
        
        .otp-buttons .btn-secondary:hover {
            background: #dc2626;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        }
        
        .otp-error {
            color: #ef4444;
            font-size: 0.9rem;
            margin-top: 1rem;
            padding: 0.75rem;
            background: #fecaca;
            border-radius: 6px;
        }
        
        .otp-success {
            color: #10b981;
            font-size: 0.9rem;
            margin-top: 1rem;
            padding: 0.75rem;
            background: #d1fae5;
            border-radius: 6px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
    `;
    
    document.head.appendChild(styles);
}

// ============================================
// SESSION END (Logout)
// ============================================

async function endSession() {
    /**
     * Call backend to end session
     * - Aggregate LOW-risk snapshots
     * - Extract final features
     * - Apply training logic
     * - Retrain if needed
     */
    
    if (!currentUserId || !sessionId) {
        console.log("ℹ️ No active session to end");
        return;
    }
    
    console.log(`\n${'='.repeat(70)}`);
    console.log(`🏁 Ending session: ${sessionId}`);
    console.log(`${'='.repeat(70)}`);
    
    stopMonitoring();
    detachEventListeners();
    
    try {
        const response = await fetch(`${API_BASE_URL}/session/end`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUserId,
                session_id: sessionId
            })
        });
        
        const result = await response.json();
        
        console.log(`✅ Session ended`);
        console.log(`   Status: ${result.status}`);
        console.log(`   Message: ${result.message}`);
        
        if (result.status === 'MODEL_TRAINED') {
            console.log(`🎯 MODEL TRAINED - Version ${result.model_version}`);
        } else if (result.status === 'MODEL_RETRAINED') {
            console.log(`🎯 MODEL RETRAINED - Version ${result.model_version}`);
        }
        
    } catch (err) {
        console.error(`❌ Error ending session:`, err);
    } finally {
        // Clear session
        sessionId = null;
        currentUserId = null;
        isMonitoring = false;
        eventBuffer = {
            key_events: [],
            mouse_events: [],
            scroll_events: [],
            summary: { total_keys: 0, total_mouse_moves: 0, total_scrolls: 0 }
        };
    }
}

// ============================================
// EXPORTS
// ============================================

window.initializeSession = initializeSession;
window.endSession = endSession;
window.updateDashboardIndicator = updateDashboardIndicator;

console.log(`✅ COGNIVEX Behavior Monitor v2.0 Ready`);