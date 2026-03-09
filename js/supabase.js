/**
 * COGNIVEX - Supabase Configuration
 */

const SUPABASE_URL = 'https://lphoncgiccuvifprggvr.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_wkA2MCbEjTlolsVHaTFGuQ_GIZwPabE';

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
