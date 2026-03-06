"""
COGNIVEX - Supabase Client (FINAL - TIMEZONE FIXED)
All database operations with proper timezone handling
"""

import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import json
import base64

load_dotenv()

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.url or not self.key:
            print("❌ Missing Supabase credentials in .env")
            exit(1)
        
        self.client = create_client(self.url, self.key)
        print("✅ Supabase connected")
    
    # ===== BEHAVIOR_LOGS =====
    
    def store_snapshot(self, user_id: str, session_id: str, raw_data: dict) -> str:
        """Store 30-sec snapshot to behavior_logs"""
        try:
            response = self.client.table('behavior_logs').insert({
                'user_id': user_id,
                'session_id': session_id,
                'key_events': raw_data.get('key_events'),
                'mouse_events': raw_data.get('mouse_events'),
                'scroll_events': raw_data.get('scroll_events'),
                'summary': raw_data.get('summary'),
                'risk_level': 'PENDING',
                'model_version': 0
            }).execute()
            
            return response.data[0]['id']
        except Exception as e:
            print(f"❌ Error storing snapshot: {e}")
            raise
    
    def update_snapshot_risk(self, snapshot_id: str, risk_level: str, model_version: int):
        """Update risk level after scoring"""
        try:
            self.client.table('behavior_logs').update({
                'risk_level': risk_level,
                'model_version': model_version
            }).eq('id', snapshot_id).execute()
        except Exception as e:
            print(f"❌ Error updating snapshot: {e}")
            raise
    
    def get_low_risk_snapshots(self, user_id: str, session_id: str) -> list:
        """Get all LOW-risk snapshots"""
        try:
            response = self.client.table('behavior_logs').select('*').eq(
                'user_id', user_id
            ).eq('session_id', session_id).eq('risk_level', 'LOW').execute()
            return response.data
        except Exception as e:
            print(f"❌ Error fetching snapshots: {e}")
            raise
    
    # ===== BEHAVIOR_FEATURES =====
    
    def store_session_features(self, user_id: str, session_id: str, features: dict):
        """Store aggregated session features"""
        try:
            print(f"   📝 Storing features for user {user_id}")
            print(f"      Session: {session_id}")
            
            # Ensure all values are floats
            clean_features = {
                'user_id': user_id,
                'session_id': session_id,
                'typing_speed': float(features.get('typing_speed', 0)),
                'backspace_ratio': float(features.get('backspace_ratio', 0)),
                'avg_keystroke_interval': float(features.get('avg_keystroke_interval', 0)),
                'keystroke_variance': float(features.get('keystroke_variance', 0)),
                'avg_mouse_speed': float(features.get('avg_mouse_speed', 0)),
                'mouse_move_variance': float(features.get('mouse_move_variance', 0)),
                'scroll_frequency': float(features.get('scroll_frequency', 0)),
                'idle_ratio': float(features.get('idle_ratio', 0))
            }
            
            response = self.client.table('behavior_features').insert(clean_features).execute()
            
            print(f"   ✅ Features stored successfully!")
            return response.data[0]['id']
        
        except Exception as e:
            print(f"❌ Error storing features: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_latest_sessions(self, user_id: str, limit: int = 15) -> list:
        """Get latest N sessions"""
        try:
            response = self.client.table('behavior_features').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).limit(limit).execute()
            
            # Reverse to get oldest first (for training)
            return list(reversed(response.data))
        except Exception as e:
            print(f"❌ Error fetching sessions: {e}")
            raise
    
    def count_sessions(self, user_id: str) -> int:
        """Count total sessions"""
        try:
            response = self.client.table('behavior_features').select(
                'id', count='exact'
            ).eq('user_id', user_id).execute()
            return response.count
        except Exception as e:
            print(f"❌ Error counting sessions: {e}")
            raise
    
    # ===== MODEL_METADATA =====
    
    def save_model(self, user_id: str, model_binary: bytes, model_version: int, total_sessions: int):
        """
        Save or update model to model_metadata
        With CORRECT base64 encoding
        """
        try:
            print(f"   💾 Saving model to database...")
            print(f"   Model size: {len(model_binary)} bytes")
            
            # Convert to base64 STRING (not storing binary data)
            model_base64 = base64.b64encode(model_binary).decode('utf-8')
            print(f"   Base64 size: {len(model_base64)} chars")
            
            # Check if record exists
            print(f"   Checking for existing model record...")
            existing = self.client.table('model_metadata').select('id').eq(
                'user_id', user_id
            ).execute()
            
            data = {
                'model_data': model_base64,  # Store as TEXT (base64 string)
                'model_version': model_version,
                'last_trained_count': total_sessions,
                'total_sessions': total_sessions,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if existing.data:
                # Update existing
                print(f"   Updating existing model record...")
                self.client.table('model_metadata').update(data).eq(
                    'user_id', user_id
                ).execute()
                print(f"   ✅ Model updated!")
            else:
                # Create new
                print(f"   Creating new model record...")
                data['user_id'] = user_id
                self.client.table('model_metadata').insert(data).execute()
                print(f"   ✅ Model created!")
        
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_model_data(self, user_id: str):
        """
        Get model binary from Supabase
        CORRECT decoding
        """
        try:
            print(f"   🔄 Fetching model from Supabase...")
            
            response = self.client.table('model_metadata').select('model_data').eq(
                'user_id', user_id
            ).single().execute()
            
            if not response.data:
                print(f"   ℹ️ No model found")
                return None
            
            model_base64 = response.data['model_data']
            print(f"   ✅ Model data retrieved: {len(model_base64)} chars")
            
            # Decode from base64
            try:
                model_binary = base64.b64decode(model_base64)
                print(f"   ✅ Model decoded successfully: {len(model_binary)} bytes")
                return model_binary
            
            except Exception as decode_err:
                print(f"   ❌ Base64 decode error: {decode_err}")
                print(f"   First 50 chars: {model_base64[:50]}")
                return None
        
        except Exception as e:
            print(f"❌ Error fetching model: {e}")
            return None
    
    def get_model_metadata(self, user_id: str):
        """Get model metadata (version, training info)"""
        try:
            response = self.client.table('model_metadata').select('*').eq(
                'user_id', user_id
            ).single().execute()
            return response.data
        except Exception as e:
            print(f"ℹ️ No model metadata found")
            return None
    
    # ===== OTP_CHALLENGES =====
    
    def create_otp_record(self, user_id: str, session_id: str, otp_code: str):
        """Create OTP challenge record"""
        try:
            expires_at = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
            
            self.client.table('otp_challenges').insert({
                'user_id': user_id,
                'session_id': session_id,
                'otp_code': otp_code,
                'status': 'PENDING',
                'expires_at': expires_at
            }).execute()
            
            print(f"   ✅ OTP record created")
        except Exception as e:
            print(f"❌ Error creating OTP: {e}")
            raise
    
    def verify_otp(self, user_id: str, session_id: str, otp_code: str) -> bool:
        """Verify OTP code"""
        try:
            response = self.client.table('otp_challenges').select('*').eq(
                'user_id', user_id
            ).eq('session_id', session_id).eq('status', 'PENDING').execute()
            
            if not response.data:
                print(f"   ℹ️ No pending OTP found")
                return False
            
            otp_record = response.data[0]
            
            # Check expiry
            expires_at = datetime.fromisoformat(otp_record['expires_at'])
            if datetime.now(timezone.utc) > expires_at:
                print(f"   ⏰ OTP expired")
                return False
            
            # Check code
            if otp_record['otp_code'] != otp_code:
                print(f"   ❌ Code mismatch")
                return False
            
            # Mark as verified
            self.client.table('otp_challenges').update({
                'status': 'VERIFIED',
                'verified_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', otp_record['id']).execute()
            
            print(f"   ✅ OTP verified")
            return True
        
        except Exception as e:
            print(f"❌ Error verifying OTP: {e}")
            return False
    
    def mark_otp_failed(self, user_id: str, session_id: str):
        """Mark OTP as failed and session as HIGH risk"""
        try:
            self.client.table('otp_challenges').update({
                'status': 'FAILED'
            }).eq('user_id', user_id).eq('session_id', session_id).execute()
            
            self.client.table('behavior_logs').update({
                'risk_level': 'HIGH'
            }).eq('user_id', user_id).eq('session_id', session_id).execute()
            
            print(f"   ✅ OTP marked as failed")
        except Exception as e:
            print(f"❌ Error marking OTP failed: {e}")
            raise
    
    # ===== OTP_COOLDOWNS =====
    
    def check_cooldown(self, user_id: str, session_id: str) -> bool:
        """
        Check if user is in OTP cooldown period
        FIXED - Handles timezone-aware datetimes from Supabase
        """
        try:
            print(f"      Checking cooldown in database...")
            
            response = self.client.table('otp_cooldowns').select('*').eq(
                'user_id', user_id
            ).eq('session_id', session_id).execute()
            
            if not response.data:
                print(f"      ℹ️ No cooldown record found")
                return False  # No cooldown record = not in cooldown
            
            cooldown_record = response.data[0]
            cooldown_until_str = cooldown_record['cooldown_until']
            
            print(f"      Cooldown until (raw): {cooldown_until_str}")
            
            # Parse the datetime - Supabase returns timezone-aware datetime
            cooldown_until = datetime.fromisoformat(cooldown_until_str)
            
            # Get current time in UTC
            now = datetime.now(timezone.utc)
            
            # Remove timezone info from both to make comparable
            if cooldown_until.tzinfo is not None:
                cooldown_until = cooldown_until.replace(tzinfo=None)
            
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            print(f"      Current time (UTC): {now}")
            print(f"      Cooldown until: {cooldown_until}")
            
            # Check if still in cooldown
            if now < cooldown_until:
                remaining_seconds = (cooldown_until - now).total_seconds()
                remaining_minutes = remaining_seconds / 60
                print(f"      ✅ COOLDOWN ACTIVE ({remaining_minutes:.1f} min remaining)")
                return True  # Still in cooldown
            else:
                print(f"      ❌ Cooldown has EXPIRED")
                return False  # Cooldown expired
        
        except Exception as e:
            print(f"      ❌ Error checking cooldown: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_cooldown(self, user_id: str, session_id: str, minutes: int):
        """Set OTP cooldown period - with UTC timezone"""
        try:
            # Use UTC timezone for consistency with Supabase
            verified_at = datetime.now(timezone.utc)
            cooldown_until = verified_at + timedelta(minutes=minutes)
            
            existing = self.client.table('otp_cooldowns').select('id').eq(
                'user_id', user_id
            ).eq('session_id', session_id).execute()
            
            data = {
                'verified_at': verified_at.isoformat(),
                'cooldown_until': cooldown_until.isoformat()
            }
            
            if existing.data:
                self.client.table('otp_cooldowns').update(data).eq(
                    'user_id', user_id
                ).eq('session_id', session_id).execute()
                print(f"      ✅ Cooldown updated: {minutes} minutes")
            else:
                data['user_id'] = user_id
                data['session_id'] = session_id
                self.client.table('otp_cooldowns').insert(data).execute()
                print(f"      ✅ Cooldown created: {minutes} minutes")
            
            print(f"      Verified at: {verified_at}")
            print(f"      Cooldown until: {cooldown_until}")
        
        except Exception as e:
            print(f"      ❌ Error setting cooldown: {e}")
            import traceback
            traceback.print_exc()
            raise