import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import joblib
import os

from django.conf import settings
import os

MODEL_DIR = os.path.join(settings.APP_DATA_DIR, 'models')
CLASSIFIER_PATH = os.path.join(MODEL_DIR, 'delay_classifier.joblib')
REGRESSOR_PATH = os.path.join(MODEL_DIR, 'delay_regressor.joblib')

class DelayPredictor:
    def __init__(self):
        self.classifier = None
        self.regressor = None
        self.load_models()

    def load_models(self):
        if os.path.exists(CLASSIFIER_PATH) and os.path.exists(REGRESSOR_PATH):
            self.classifier = joblib.load(CLASSIFIER_PATH)
            self.regressor = joblib.load(REGRESSOR_PATH)
        else:
            # Fallback for demo: Initialize with dummy models if not trained
            self.classifier = None
            self.regressor = None

    def predict(self, features_dict):
        """
        Predicts delay probability and days.
        Expected features: supplier_rating, est_delivery_days, historical_delay_rate, etc.
        """
        if self.classifier is None or self.regressor is None:
            # Simple heuristic fallback if models don't exist
            # This is used for the initial setup/demo
            rating = features_dict.get('supplier_rating', 5.0)
            est_days = features_dict.get('estimated_delivery_days', 10)
            delay_rate = features_dict.get('historical_supplier_delay_rate', 0.1)
            
            # Rough probability: Higher delay rate and lower rating -> higher probability
            prob = min(0.9, max(0.05, delay_rate * (6.0 - rating)))
            days = int(est_days * prob)
            
            return prob, days

        # In a real system, we'd convert features_dict to DataFrame and use model.predict
        # df = pd.DataFrame([features_dict])
        # prob = self.classifier.predict_proba(df)[0][1]
        # days = self.regressor.predict(df)[0]
        # return prob, days
        
        return 0.1, 1 # Dummy return for now if model exists but logic not fully implemented

    def train_mock(self):
        """
        Creates and saves dummy models for testing the integration.
        """
        # Training logic would go here
        pass

# Singleton instance
predictor = DelayPredictor()
