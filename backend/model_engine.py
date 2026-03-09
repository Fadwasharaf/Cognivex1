"""
COGNIVEX - Model Engine (CORRECTED)
ML Training, Prediction, Retraining
"""

import pickle
from sklearn.ensemble import IsolationForest
import numpy as np
from typing import Dict, Optional, List

class ModelEngine:
    
    # Risk thresholds
    SCORE_LOW = -0.1
    SCORE_MEDIUM = -0.3
    
    def __init__(self, supabase):
        self.supabase = supabase
        self.model_cache = {}
    
    def getModel(self, user_id: str) -> Optional[Dict]:
        """Get model from cache or load from DB - CORRECTED"""
        
        # Check cache first
        if user_id in self.model_cache:
            print(f"   ✅ Model loaded from cache (v{self.model_cache[user_id]['model_version']})")
            return self.model_cache[user_id]
        
        # Load from database
        modelBinary = self.supabase.get_model_data(user_id)
        
        if not modelBinary:
            print(f"   ℹ️ No model in database")
            return None
        
        try:
            print(f"   Deserializing model...")
            model = pickle.loads(modelBinary)
            print(f"   ✅ Model deserialized successfully")
            
            metadata = self.supabase.get_model_metadata(user_id)
            
            if not metadata:
                print(f"   ❌ Could not get model metadata")
                return None
            
            result = {
                'model': model,
                'model_version': metadata['model_version']
            }
            
            # Cache it
            self.model_cache[user_id] = result
            print(f"   ✅ Model cached (v{metadata['model_version']})")
            
            return result
        
        except Exception as e:
            print(f"   ❌ Error loading model: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def predict(self, model: IsolationForest, features: Dict[str, float]) -> float:
        """Score features with model - CORRECTED"""
        
        try:
            featureArray = np.array([
                float(features['typing_speed']),
                float(features['backspace_ratio']),
                float(features['avg_keystroke_interval']),
                float(features['keystroke_variance']),
                float(features['avg_mouse_speed']),
                float(features['mouse_move_variance']),
                float(features['scroll_frequency']),
                float(features['idle_ratio'])
            ]).reshape(1, -1)
            
            score = model.decision_function(featureArray)[0]
            return float(score)
        
        except Exception as e:
            print(f"   ❌ Error predicting: {e}")
            return 0.0
    
    def scoreToRiskLevel(self, score: float) -> str:
        """Convert score to risk level - CORRECTED"""
        
        print(f"      Score: {score:.4f}")
        
        if score > self.SCORE_LOW:  # > -0.1
            print(f"      Threshold: > {self.SCORE_LOW} → LOW RISK")
            return 'LOW'
        elif score > self.SCORE_MEDIUM:  # > -0.3 (but <= -0.1)
            print(f"      Threshold: > {self.SCORE_MEDIUM} → MEDIUM RISK")
            return 'MEDIUM'
        else:  # <= -0.3
            print(f"      Threshold: <= {self.SCORE_MEDIUM} → HIGH RISK")
            return 'HIGH'
    
    def trainModelV1(self, user_id: str) -> Dict:
        """Train first model on 15 sessions - CORRECTED"""
        
        print(f"\n{'='*70}")
        print(f"🤖 Training Model v1 for user {user_id}")
        print(f"{'='*70}")
        
        sessions = self.supabase.get_latest_sessions(user_id, 15)
        
        if len(sessions) < 15:
            raise Exception(f"Not enough sessions: {len(sessions)} < 15")
        
        print(f"   Fetched {len(sessions)} sessions")
        
        # Extract features
        featureMatrix = []
        for i, session in enumerate(sessions):
            try:
                features = [
                    float(session['typing_speed']),
                    float(session['backspace_ratio']),
                    float(session['avg_keystroke_interval']),
                    float(session['keystroke_variance']),
                    float(session['avg_mouse_speed']),
                    float(session['mouse_move_variance']),
                    float(session['scroll_frequency']),
                    float(session['idle_ratio'])
                ]
                featureMatrix.append(features)
                print(f"   Session {i+1}: Features extracted ✅")
            except Exception as e:
                print(f"   Session {i+1}: Error - {e}")
        
        featureMatrix = np.array(featureMatrix)
        
        print(f"   Training on {len(sessions)} sessions")
        print(f"   Feature matrix shape: {featureMatrix.shape}")
        print(f"   Data type: {featureMatrix.dtype}")
        
        # Train
        try:
            model = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            model.fit(featureMatrix)
            print(f"✅ Model trained successfully")
        except Exception as e:
            print(f"❌ Error training model: {e}")
            raise
        
        # Serialize to binary
        try:
            print(f"   Pickling model...")
            modelBinary = pickle.dumps(model)
            print(f"   ✅ Model pickled: {len(modelBinary)} bytes")
        except Exception as e:
            print(f"   ❌ Error pickling: {e}")
            raise
        
        # Save to database
        self.supabase.save_model(user_id, modelBinary, model_version=1, total_sessions=15)
        
        # Clear cache
        if user_id in self.model_cache:
            del self.model_cache[user_id]
            print(f"   Cache cleared")
        
        return {'model_version': 1, 'total_sessions': 15}
    
    def retrainModel(self, user_id: str, totalSessions: int) -> Dict:
        """Retrain model on latest 15 sessions - CORRECTED"""
        
        print(f"\n{'='*70}")
        print(f"🤖 Retraining Model for user {user_id} (total: {totalSessions})")
        print(f"{'='*70}")
        
        sessions = self.supabase.get_latest_sessions(user_id, 15)
        
        print(f"   Fetched {len(sessions)} sessions for retraining")
        
        # Extract features
        featureMatrix = []
        for i, session in enumerate(sessions):
            try:
                features = [
                    float(session['typing_speed']),
                    float(session['backspace_ratio']),
                    float(session['avg_keystroke_interval']),
                    float(session['keystroke_variance']),
                    float(session['avg_mouse_speed']),
                    float(session['mouse_move_variance']),
                    float(session['scroll_frequency']),
                    float(session['idle_ratio'])
                ]
                featureMatrix.append(features)
            except Exception as e:
                print(f"   Session {i+1}: Error - {e}")
        
        featureMatrix = np.array(featureMatrix)
        
        print(f"   Retraining on latest {len(sessions)} sessions")
        print(f"   Feature matrix shape: {featureMatrix.shape}")
        
        # Get current version
        metadata = self.supabase.get_model_metadata(user_id)
        newVersion = metadata['model_version'] + 1
        print(f"   Current version: {metadata['model_version']}")
        print(f"   New version: {newVersion}")
        
        # Train
        try:
            model = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            model.fit(featureMatrix)
            print(f"✅ Model retrained successfully (v{newVersion})")
        except Exception as e:
            print(f"❌ Error retraining: {e}")
            raise
        
        # Serialize
        try:
            modelBinary = pickle.dumps(model)
            print(f"   ✅ Model pickled: {len(modelBinary)} bytes")
        except Exception as e:
            print(f"   ❌ Error pickling: {e}")
            raise
        
        # Save
        self.supabase.save_model(user_id, modelBinary, model_version=newVersion, total_sessions=totalSessions)
        
        # Clear cache
        if user_id in self.model_cache:
            del self.model_cache[user_id]
        
        return {'model_version': newVersion, 'total_sessions': totalSessions}
    
    def getModelMetadata(self, user_id: str) -> Dict:
        """Get model metadata - CORRECTED"""
        metadata = self.supabase.get_model_metadata(user_id)
        if metadata:
            print(f"   Model metadata: v{metadata['model_version']}, trained at session {metadata['last_trained_count']}")
        return metadata