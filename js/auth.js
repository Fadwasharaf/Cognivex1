<<<<<<< HEAD
window.authHandler = {

    isLoginPage() {
        return window.location.pathname.includes('index.html') ||
               window.location.pathname === '/' ||
               window.location.pathname.endsWith('/');
    },

    init() {
        console.log('🔐 Auth handler initializing...');
        this.checkSession();
        
        // Check session every 60 seconds
        this.sessionInterval = setInterval(() => {
            this.checkSession();
        }, 60000);

        // Check session when tab becomes visible
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.checkSession();
            }
        });
    },

    async checkSession() {
        try {
            const supabase = window.supabaseClient;

            if (!supabase) {
                console.error('✗ Supabase client not available');
                return;
            }

            const { data, error } = await supabase.auth.getSession();
            if (error) throw error;

            const session = data.session;

            if (session) {
                console.log('✓ Active session found:', session.user.email);
                if (this.isLoginPage()) {
                    console.log('→ User already logged in, redirecting to dashboard...');
                    window.location.href = 'dashboard.html';
                }
            } else {
                console.log('✗ No active session found');
                if (!this.isLoginPage()) {
                    console.log('→ User not logged in, redirecting to login...');
                    window.location.href = 'index.html';
                }
            }

        } catch (error) {
            console.error('✗ Session check error:', error);
            if (!this.isLoginPage()) {
                window.location.href = 'index.html';
            }
        }
    },

    async login(email, password) {
        const errorMessage = document.getElementById('error-message');
        const loginButton = document.querySelector('#loginForm button[type="submit"]');
        const originalButtonText = loginButton?.textContent || 'Sign In';

        try {
            if (loginButton) {
                loginButton.disabled = true;
                loginButton.textContent = 'Signing in...';
            }

            if (errorMessage) {
                errorMessage.textContent = '';
                errorMessage.classList.remove('visible');
            }

            const supabase = window.supabaseClient;
            if (!supabase) throw new Error('Authentication service not available');

            console.log('🔐 Attempting login for:', email);

            const { data, error } = await supabase.auth.signInWithPassword({
                email: email.trim(),
                password: password
            });

            if (error) throw error;

            console.log('✓ Login successful for:', email);
            
            // Brief delay to ensure session is set
=======
/**
 * COGNIVEX - Authentication Handler
 */

class AuthHandler {
    constructor(supabase) {
        this.supabase = supabase;
        console.log('🔐 Auth Handler initialized');
    }

    async login(email, password) {
        console.log(`🔐 Attempting login for: ${email}`);
        try {
            const { data, error } = await this.supabase.auth.signInWithPassword({
                email: email,
                password: password
            });

            if (error) {
                console.error('❌ Login error:', error);
                throw new Error(error.message || 'Login failed');
            }

            console.log('✅ Login successful!');
            window.currentUserId = data.user.id;

            if (typeof window.initializeSession === 'function') {
                window.initializeSession(data.user.id);
            }

>>>>>>> bhagya/main
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 500);

        } catch (error) {
<<<<<<< HEAD
            console.error('✗ Login error:', error);

            if (errorMessage) {
                const userMessage = error.message.includes('Invalid login credentials')
                    ? '⚠ Invalid email or password. Please try again.'
                    : error.message || 'Login failed. Please try again.';
                
                errorMessage.textContent = userMessage;
                errorMessage.classList.add('visible');

                setTimeout(() => {
                    errorMessage.classList.remove('visible');
                }, 5000);
            }

        } finally {
            if (loginButton) {
                loginButton.disabled = false;
                loginButton.textContent = originalButtonText;
            }
        }
    },

    async logout() {
        try {
            console.log('🔐 Logging out...');
            const supabase = window.supabaseClient;
            
            if (!supabase) {
                window.location.href = 'index.html';
                return;
            }

            // Flush any remaining behavior data before logout
            if (window.flushBehaviorData) {
                await window.flushBehaviorData();
            }

            await supabase.auth.signOut();
            console.log('✓ Logout successful');
            
            window.location.href = 'index.html';

        } catch (error) {
            console.error('✗ Logout error:', error);
            window.location.href = 'index.html';
        }
    },

    getCurrentUser() {
        const supabase = window.supabaseClient;
        if (!supabase) return null;
        
        return supabase.auth.user();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM loaded, initializing auth...');

    const waitForSupabase = setInterval(() => {
        if (window.supabaseClient) {
            clearInterval(waitForSupabase);
            window.authHandler.init();
        }
    }, 100);

    // Timeout after 5 seconds
    setTimeout(() => {
        if (window.supabaseClient) {
            window.authHandler.init();
        } else {
            console.error('✗ Supabase client failed to initialize after 5 seconds');
        }
    }, 5000);
});
=======
            console.error('❌ Login failed:', error);
            throw error;
        }
    }

    async logout() {
        console.log('🔄 Logging out...');
        try {
            if (typeof window.endSession === 'function') {
                await window.endSession();
            }

            const { error } = await this.supabase.auth.signOut();
            if (error) throw error;

            console.log('✅ Logout successful');
            window.currentUserId = null;

            setTimeout(() => {
                window.location.href = 'index.html';
            }, 500);

        } catch (error) {
            console.error('❌ Logout failed:', error);
            window.location.href = 'index.html';
        }
    }

    async checkSession() {
        console.log('🔍 Checking session...');
        try {
            const { data: { session }, error } = await this.supabase.auth.getSession();
            if (error) throw error;

            if (session) {
                console.log('✅ Active session found, redirecting...');
                window.currentUserId = session.user.id;
                window.location.href = 'dashboard.html';
                return true;
            } else {
                console.log('ℹ️ No active session');
                return false;
            }
        } catch (error) {
            console.error('❌ Session check failed:', error);
            return false;
        }
    }

    async getCurrentUser() {
        try {
            const { data: { user }, error } = await this.supabase.auth.getUser();
            if (error) throw error;
            return user;
        } catch (error) {
            console.error('❌ Error getting user:', error);
            return null;
        }
    }
}

// Initialize auth handler — wait for supabaseReady event OR check if already ready
function setupAuthHandler() {
    if (window.supabaseClient) {
        window.authHandler = new AuthHandler(window.supabaseClient);
        console.log('✅ Auth Handler ready');
    } else {
        // Listen for the event fired by supabase.js when client is ready
        window.addEventListener('supabaseReady', () => {
            window.authHandler = new AuthHandler(window.supabaseClient);
            console.log('✅ Auth Handler ready (via supabaseReady event)');
        }, { once: true });
    }
}

setupAuthHandler();
>>>>>>> bhagya/main
