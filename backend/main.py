"""
COGNIVEX v2.0 - FastAPI Server
Behavioral Biometrics with ML Anomaly Detection

CORRECT ARCHITECTURE:
- Sessions 1-14: Collect data (no scoring, no model)
- Session 15: Train Isolation Forest model
- Sessions 16+: Score behavior, detect anomalies, OTP challenges
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

from supabase_client import SupabaseClient
from feature_extractor import FeatureExtractor
from model_engine import ModelEngine
from otp_controller import OTPController

# ===== INITIALIZE =====

app = FastAPI(title="COGNIVEX v2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = SupabaseClient()
featureExtractor = FeatureExtractor()
modelEngine = ModelEngine(supabase)
otpController = OTPController(supabase)

print("\n" + "="*70)
print("✅ All components initialized")
print("="*70 + "\n")

# ===== REQUEST MODELS =====

class SnapshotRequest(BaseModel):
    user_id: str
    session_id: str
    raw_data: Dict[str, Any]

class SessionEndRequest(BaseModel):
    user_id: str
    session_id: str

class OTPVerifyRequest(BaseModel):
    user_id: str
    session_id: str
    otp_code: str

# ===== ROUTES =====

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "✅ COGNIVEX v2.0 Running",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/session/snapshot")
async def sessionSnapshot(req: SnapshotRequest):
    """
    30-second behavioral snapshot
    
    Sessions 1-14: Just store (no model exists yet)
    Sessions 15+: Store + Score + Check risk
    """
    
    user_id = req.user_id
    session_id = req.session_id
    raw_data = req.raw_data
    
    print(f"\n📤 [SNAPSHOT] User {user_id}, Session {session_id}")
    
    try:
        # Step 1: Store raw snapshot
        print(f"   Step 1: Storing raw data to behavior_logs...")
        snapshot_id = supabase.store_snapshot(user_id, session_id, raw_data)
        print(f"   ✅ Stored snapshot ID: {snapshot_id}")
        
        # Step 2: Check if model exists
        print(f"   Step 2: Checking if model exists...")
        modelInfo = modelEngine.getModel(user_id)
        
        if not modelInfo:
            # ===== SESSIONS 1-14: COLLECTING DATA =====
            print(f"   ℹ️ No model yet (Sessions 1-14 - Collecting phase)")
            print(f"   Marking as LOW (no scoring, just collecting)")
            
            supabase.update_snapshot_risk(snapshot_id, 'LOW', 0)
            
            return {
                "status": "COLLECTING_DATA",
                "risk_level": "LOW",
                "message": "📊 Data collection in progress (no model yet)"
            }
        
        # ===== SESSIONS 15+: MODEL EXISTS, SCORE BEHAVIOR =====
        print(f"   Step 3: Model exists! Extracting features...")
        
        # Extract features in-memory
        features = featureExtractor.extract(raw_data)
        print(f"   Features extracted:")
        print(f"      typing_speed: {features['typing_speed']:.2f}")
        print(f"      mouse_speed: {features['avg_mouse_speed']:.2f}")
        print(f"      keystroke_interval: {features['avg_keystroke_interval']:.4f}")
        
        # Score with model
        model = modelInfo['model']
        modelVersion = modelInfo['model_version']
        
        print(f"   Step 4: Scoring with model v{modelVersion}...")
        score = modelEngine.predict(model, features)
        riskLevel = modelEngine.scoreToRiskLevel(score)
        
        print(f"   Score: {score:.4f}")
        print(f"   Risk Level: {riskLevel}")
        
        # Update snapshot with risk level
        supabase.update_snapshot_risk(snapshot_id, riskLevel, modelVersion)
        
        # ===== HANDLE BASED ON RISK LEVEL =====
        
        if riskLevel == 'LOW':
            print(f"   ✅ LOW risk - Behavior is normal")
            return {
                "status": "OK",
                "risk_level": "LOW",
                "message": "✅ Normal Activity"
            }
        
        elif riskLevel == 'MEDIUM':
            print(f"   ⚠️ MEDIUM risk - Unusual behavior detected")
    
    # ===== CRITICAL: CHECK COOLDOWN FIRST =====
            print(f"   Step 5: Checking OTP cooldown...")
            if otpController.checkCooldown(user_id, session_id):
                print(f"   ⏳ Cooldown ACTIVE - NOT asking for OTP")
                return {
                  "status": "OK",
                  "risk_level": "MEDIUM",
                  "message": "⚠️ Unusual but recently verified. Continuing without OTP..."
        }
            else:
                print(f"   ✅ Cooldown expired or doesn't exist - ASK FOR OTP")
    
    # Create and ask for OTP
            print(f"   Step 6: Creating OTP challenge...")
            otpCode = otpController.createOTP(user_id, session_id)
    
            if otpCode:
                print(f"   📧 OTP created: {otpCode}")
                return {
                    "status": "OTP_REQUIRED",
                    "risk_level": "MEDIUM",
                    "session_id": session_id,
                    "message": f"⚠️ Unusual behavior detected. OTP: {otpCode}"
        }
            else:
                print(f"   ⏳ Cooldown check returned None - continuing without OTP")
                return {
                  "status": "OK",
                  "risk_level": "MEDIUM",
                  "message": "⚠️ Unusual but OTP cooldown active"
        }
        
        elif riskLevel == 'HIGH':
            print(f"   🚨 HIGH risk - Suspicious activity!")
            return {
                "status": "SESSION_TERMINATED",
                "risk_level": "HIGH",
                "message": "🚨 Suspicious activity detected. Session terminated."
            }
    
    except Exception as e:
        print(f"❌ Error in /session/snapshot: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-otp")
async def verifyOTP(req: OTPVerifyRequest):
    """
    Verify OTP code (Simple In-Memory Version)
    If correct: Set cooldown and continue
    If wrong: Terminate session
    """
    
    user_id = req.user_id
    session_id = req.session_id
    provided_otp = str(req.otp_code).strip()  # Convert to string and strip whitespace
    
    print(f"\n{'='*70}")
    print(f"🔐 [OTP VERIFY]")
    print(f"   User: {user_id}")
    print(f"   Session: {session_id}")
    print(f"   Code: {provided_otp}")
    print(f"{'='*70}")
    
    try:
        # Verify using in-memory storage
        is_valid = otpController.verifyOTP(user_id, session_id, provided_otp)
        
        if is_valid:
            print(f"\n✅ OTP VERIFICATION SUCCESSFUL\n")
            return {
                "status": "OTP_VERIFIED",
                "message": "✅ OTP verified. Session continues."
            }
        else:
            print(f"\n❌ OTP VERIFICATION FAILED\n")
            # Mark session as HIGH risk
            supabase.mark_otp_failed(user_id, session_id)
            return {
                "status": "SESSION_TERMINATED",
                "message": "❌ Invalid or expired OTP. Session terminated."
            }
    
    except Exception as e:
        print(f"\n❌ Error in /verify-otp: {e}\n")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/session/end")
async def sessionEnd(req: SessionEndRequest):
    """
    Session ended by user (logout)
    
    1. Aggregate features from all snapshots
    2. Store to behavior_features
    3. Check if should train/retrain model
    """
    
    user_id = req.user_id
    session_id = req.session_id
    
    print(f"\n{'='*70}")
    print(f"🏁 [SESSION END]")
    print(f"   User: {user_id}")
    print(f"   Session: {session_id}")
    print(f"{'='*70}")
    
    try:
        # Step 1: Get ALL snapshots from this session
        print(f"Step 1: Fetching all snapshots from this session...")
        response = supabase.client.table('behavior_logs').select('*').eq(
            'user_id', user_id
        ).eq('session_id', session_id).execute()
        
        allSnapshots = response.data
        print(f"   Found {len(allSnapshots)} snapshots")
        
        if len(allSnapshots) == 0:
            print(f"⚠️ No snapshots in this session")
            return {
                "status": "SESSION_STORED",
                "message": "No behavioral data in session"
            }
        
        # Step 2: Aggregate features from ALL snapshots
        print(f"Step 2: Aggregating features from {len(allSnapshots)} snapshots...")
        aggregatedFeatures = featureExtractor.aggregateFeatures(allSnapshots)
        
        print(f"   Aggregated features:")
        print(f"      typing_speed: {aggregatedFeatures['typing_speed']:.2f}")
        print(f"      backspace_ratio: {aggregatedFeatures['backspace_ratio']:.4f}")
        print(f"      mouse_speed: {aggregatedFeatures['avg_mouse_speed']:.2f}")
        
        # Step 3: Store aggregated features to behavior_features
        print(f"Step 3: Storing to behavior_features table...")
        supabase.store_session_features(user_id, session_id, aggregatedFeatures)
        print(f"   ✅ Stored!")
        
        # Step 4: Get total session count
        print(f"Step 4: Counting total sessions for this user...")
        totalSessions = supabase.count_sessions(user_id)
        print(f"   📊 Session Number: {totalSessions}")
        print(f"   Total sessions for user: {totalSessions}")
        
        # Step 5: Apply training logic based on session count
        print(f"Step 5: Applying training logic...")
        
        if totalSessions == 15:
            # ===== FIRST TIME: TRAIN MODEL V1 =====
            print(f"\n   🎯 SESSION 15 REACHED! Training first model...")
            print(f"   {'='*60}")
            
            result = modelEngine.trainModelV1(user_id)
            
            print(f"   {'='*60}")
            print(f"   ✅ MODEL v1 TRAINED SUCCESSFULLY!")
            print(f"   🎉 From session 16 onwards:")
            print(f"      - Anomaly detection is ACTIVE")
            print(f"      - Unusual behavior will trigger OTP challenges")
            print(f"      - HIGH risk will terminate session")
            print(f"   {'='*60}\n")
            
            return {
                "status": "MODEL_TRAINED",
                "model_version": 1,
                "sessions_collected": 15,
                "message": "🎉 Model v1 trained! Anomaly detection now ACTIVE (session 16+)"
            }
        
        elif totalSessions > 15:
            # ===== CHECK IF RETRAINING NEEDED =====
            modelMetadata = modelEngine.getModelMetadata(user_id)
            lastTrained = modelMetadata['last_trained_count']
            sessionsSinceTrain = totalSessions - lastTrained
            
            print(f"   Last trained at: {lastTrained} sessions")
            print(f"   Sessions since train: {sessionsSinceTrain}")
            
            if sessionsSinceTrain >= 20:
                # ===== RETRAIN MODEL =====
                print(f"\n   🎯 {sessionsSinceTrain} SESSIONS SINCE TRAINING! Retraining...")
                print(f"   {'='*60}")
                
                result = modelEngine.retrainModel(user_id, totalSessions)
                
                print(f"   {'='*60}")
                print(f"   ✅ MODEL v{result['model_version']} RETRAINED!")
                print(f"   {'='*60}\n")
                
                return {
                    "status": "MODEL_RETRAINED",
                    "model_version": result['model_version'],
                    "sessions_total": totalSessions,
                    "message": f"✅ Model retrained to v{result['model_version']}"
                }
            else:
                # Not yet time to retrain
                sessionsTillRetrain = 20 - sessionsSinceTrain
                print(f"   ℹ️ {sessionsTillRetrain} more sessions needed to retrain")
                
                return {
                    "status": "SESSION_STORED",
                    "sessions_total": totalSessions,
                    "sessions_till_retrain": sessionsTillRetrain,
                    "message": f"Session {totalSessions} stored. {sessionsTillRetrain} more for retrain."
                }
        
        else:
            # ===== STILL COLLECTING (Sessions 1-14) =====
            sessionsTillTraining = 15 - totalSessions
            print(f"   ℹ️ Collecting data ({totalSessions}/15)")
            print(f"   Sessions till training: {sessionsTillTraining}")
            
            return {
                "status": "COLLECTING_DATA",
                "sessions_collected": totalSessions,
                "sessions_needed": 15,
                "sessions_remaining": sessionsTillTraining,
                "message": f"✅ Session {totalSessions}/15 collected. {sessionsTillTraining} more to train model!"
            }
    
    except Exception as e:
        print(f"❌ Error in /session/end: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{user_id}")
async def getStatus(user_id: str):
    """Get user's training status and model info"""
    try:
        totalSessions = supabase.count_sessions(user_id)
        modelInfo = modelEngine.getModelMetadata(user_id)
        
        if modelInfo and totalSessions >= 15:
            status = "READY - Anomaly detection ACTIVE"
            model_version = modelInfo['model_version']
        else:
            status = f"COLLECTING - Need {15 - totalSessions} more sessions"
            model_version = 0
        
        return {
            "user_id": user_id,
            "total_sessions": totalSessions,
            "model_version": model_version,
            "status": status,
            "details": {
                "sessions_collected": totalSessions,
                "sessions_needed_for_training": max(0, 15 - totalSessions),
                "anomaly_detection_active": totalSessions >= 15
            }
        }
    
    except Exception as e:
        print(f"❌ Error in /status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== STARTUP =====

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🚀 COGNIVEX v2.0 - BEHAVIORAL BIOMETRICS")
    print("="*70)
    print("\n📋 Architecture:")
    print("   Sessions 1-14: Data Collection (no scoring)")
    print("   Session 15: Model Training")
    print("   Sessions 16+: Anomaly Detection + OTP Challenges")
    print("\n📍 API: http://localhost:5000")
    print("📍 Health: http://localhost:5000/health")
    print("📍 Docs: http://localhost:5000/docs")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5000)