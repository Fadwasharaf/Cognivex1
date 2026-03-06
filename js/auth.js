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

            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 500);

        } catch (error) {
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