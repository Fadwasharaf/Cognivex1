/**
 * COGNIVEX - Supabase Configuration
 */

const SUPABASE_URL = 'https://helbztxyefzojgujunoh.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhlbGJ6dHh5ZWZ6b2pndWp1bm9oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwMjU0OTUsImV4cCI6MjA4NzYwMTQ5NX0.RJ3_sg7OGool3dv2nEC4DpzFB0C3k5MfD81Kc3E4BU4';

function initSupabase() {
    if (typeof window.supabase === 'undefined' || typeof window.supabase.createClient !== 'function') {
        console.warn('⏳ Supabase CDN not ready, retrying...');
        setTimeout(initSupabase, 50);
        return;
    }

    try {
        window.supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        console.log('✅ Supabase client initialized');
        window.dispatchEvent(new Event('supabaseReady'));
    } catch (err) {
        console.error('❌ Failed to create Supabase client:', err);
    }
}

initSupabase();