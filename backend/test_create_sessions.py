"""
COGNIVEX - Test Data Generator
Creates 15 dummy sessions with random but realistic behavior data
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import random
from datetime import datetime, timedelta

load_dotenv()

# Setup Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase credentials in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*70)
print("🧪 COGNIVEX - TEST DATA GENERATOR")
print("="*70 + "\n")

# ===== GET USER ID =====

print("Step 1: Getting your user ID from Supabase Auth...")

try:
    # List all users (needs service key)
    response = supabase.auth.admin.list_users()
    users = response.users if hasattr(response, 'users') else response
    
    if not users:
        print("❌ No users found in Supabase")
        exit(1)
    
    # Get first user (your test user)
    user = users[0]
    user_id = user.id
    user_email = user.email
    
    print(f"✅ Found user:")
    print(f"   Email: {user_email}")
    print(f"   ID: {user_id}\n")

except Exception as e:
    print(f"❌ Error getting user: {e}")
    print("Make sure SUPABASE_SERVICE_KEY is correct in .env")
    exit(1)

# ===== CREATE 15 DUMMY SESSIONS =====

print("Step 2: Creating 15 dummy sessions...\n")

def generate_random_features():
    """Generate realistic random features"""
    return {
        'typing_speed': random.uniform(3, 6),           # Keys per second
        'backspace_ratio': random.uniform(0.02, 0.15),  # % of backspaces
        'avg_keystroke_interval': random.uniform(0.08, 0.14),  # Seconds between keys
        'keystroke_variance': random.uniform(0.01, 0.04),  # Variance in timing
        'avg_mouse_speed': random.uniform(100, 200),    # Pixels per second
        'mouse_move_variance': random.uniform(50, 150), # Variance in speed
        'scroll_frequency': random.uniform(0.5, 2.5),   # Scrolls per second
        'idle_ratio': random.uniform(0.1, 0.3)          # % of idle time
    }

created_count = 0
failed_count = 0

for i in range(1, 16):
    try:
        features = generate_random_features()
        
        # Create session record
        response = supabase.table('behavior_features').insert({
            'user_id': user_id,
            'session_id': f'test_session_{i}_{datetime.now().timestamp()}',
            'typing_speed': features['typing_speed'],
            'backspace_ratio': features['backspace_ratio'],
            'avg_keystroke_interval': features['avg_keystroke_interval'],
            'keystroke_variance': features['keystroke_variance'],
            'avg_mouse_speed': features['avg_mouse_speed'],
            'mouse_move_variance': features['mouse_move_variance'],
            'scroll_frequency': features['scroll_frequency'],
            'idle_ratio': features['idle_ratio']
        }).execute()
        
        print(f"✅ Session {i:2d}/15 created")
        print(f"   typing_speed: {features['typing_speed']:.2f} keys/sec")
        print(f"   mouse_speed: {features['avg_mouse_speed']:.0f} px/sec")
        created_count += 1
        
    except Exception as e:
        print(f"❌ Session {i:2d} failed: {e}")
        failed_count += 1

# ===== SUMMARY =====

print(f"\n{'='*70}")
print(f"Results:")
print(f"  ✅ Created: {created_count}/15")
print(f"  ❌ Failed: {failed_count}/15")
print(f"{'='*70}\n")

if created_count == 15:
    print("🎉 SUCCESS! 15 test sessions created!\n")
    print("Next steps:")
    print("  1. Make sure backend is running (python main.py)")
    print("  2. In another terminal, run:")
    print("     curl http://localhost:5000/status/YOUR_USER_ID")
    print("     (Replace YOUR_USER_ID with the ID above)")
    print("  3. Should show: status READY, total_sessions 15")
    print("  4. Backend should have triggered MODEL TRAINING\n")
    print("Check your backend terminal for:")
    print("  🎯 Exactly 15 sessions - TRAINING FIRST MODEL")
    print("  ✅ MODEL TRAINED - Version 1\n")
else:
    print(f"⚠️ Only created {created_count} sessions. Check errors above.\n")