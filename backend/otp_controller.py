"""
COGNIVEX - OTP Controller (SIMPLE - In Memory)
Generates OTP in-memory, no database issues
"""

import random
import string
from datetime import datetime, timedelta

COOLDOWN_MINUTES = 10

class OTPController:
    
    def __init__(self, supabase):
        self.supabase = supabase
        self.otp_storage = {}  # In-memory storage: {session_id: {'code': '1234', 'expires_at': time, 'verified': False}}
    
    def createOTP(self, user_id: str, session_id: str) -> str:
        """
        Generate OTP in memory
        NO database involved
        """
        
        print(f"   Creating OTP in memory...")
        
        # Check cooldown in database
        isInCooldown = self.supabase.check_cooldown(user_id, session_id)
        
        if isInCooldown:
            print(f"   ⏳ User in OTP cooldown - not asking again")
            return None
        
        # Generate random 4-digit OTP
        otpCode = ''.join(random.choices(string.digits, k=4))
        
        # Store in memory (not database)
        expires_at = datetime.now() + timedelta(minutes=2)
        
        self.otp_storage[session_id] = {
            'user_id': user_id,
            'code': otpCode,
            'expires_at': expires_at,
            'verified': False
        }
        
        print(f"   ✅ OTP generated in memory")
        print(f"   📧 OTP Code: {otpCode}")
        print(f"   Expires at: {expires_at.strftime('%H:%M:%S')}")
        
        return otpCode
    
    def verifyOTP(self, user_id: str, session_id: str, provided_code: str) -> bool:
        """
        Verify OTP from memory
        NO database involved
        """
        
        print(f"   Verifying OTP...")
        print(f"   User provided: {provided_code}")
        print(f"   Session ID: {session_id}")
        
        # Check if OTP exists for this session
        if session_id not in self.otp_storage:
            print(f"   ❌ No OTP generated for this session")
            return False
        
        otp_data = self.otp_storage[session_id]
        stored_code = otp_data['code']
        expires_at = otp_data['expires_at']
        
        print(f"   Stored code: {stored_code}")
        print(f"   Stored code type: {type(stored_code)}")
        print(f"   Provided code type: {type(provided_code)}")
        
        # Check expiry
        if datetime.now() > expires_at:
            print(f"   ⏰ OTP expired")
            del self.otp_storage[session_id]  # Clean up
            return False
        
        # Check code - exact match
        if str(stored_code) == str(provided_code).strip():
            print(f"   ✅ OTP MATCHES!")
            
            # Mark as verified
            otp_data['verified'] = True
            
            # Set cooldown in database
            print(f"   Setting cooldown for {COOLDOWN_MINUTES} minutes...")
            self.supabase.set_cooldown(user_id, session_id, COOLDOWN_MINUTES)
            
            print(f"   ✅ OTP verification successful!")
            
            # Clean up
            del self.otp_storage[session_id]
            
            return True
        else:
            print(f"   ❌ OTP does not match")
            print(f"      Expected: '{stored_code}'")
            print(f"      Got: '{str(provided_code).strip()}'")
            return False
    
    def checkCooldown(self, user_id: str, session_id: str) -> bool:
        """Check if in cooldown (from database)"""
        return self.supabase.check_cooldown(user_id, session_id)
    
    def getOTPStorage(self):
        """Debug: see what's in memory (DO NOT USE IN PRODUCTION)"""
        return self.otp_storage