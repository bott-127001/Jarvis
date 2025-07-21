import joblib
import numpy as np
import os

MODEL_PATHS = {
    'bias': 'ml_models/bias_identifier_model.pkl',
    'market_style': 'ml_models/market_style_model.pkl',
    'trap': 'ml_models/trap_detector_model.pkl',
    'reversal': 'ml_models/reversal_probability_model.pkl',
    'sr': 'ml_models/support_resistance_model.pkl',
    'entry_logic': 'ml_models/entry_logic_model.pkl',
}

# Class labels for each module (must match training order)
BIAS_CLASSES = ['Bullish', 'Bearish', 'Sideways']
STYLE_CLASSES = ['Trending', 'Sideways', 'Volatile']
TRAP_CLASSES = [0, 1]  # 0 = not trap, 1 = true trap
REVERSAL_CLASSES = [0, 1]  # 0 = no reversal, 1 = true reversal
SR_CLASSES = ['Bounce', 'Break', 'Trap', 'Other']
ENTRY_CLASSES = [0, 1]  # 0 = incorrect, 1 = correct

_model_cache = {}

def load_model(module):
    if module in _model_cache:
        return _model_cache[module]
    path = MODEL_PATHS[module]
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")
    model = joblib.load(path)
    _model_cache[module] = model
    return model

def predict_bias(features):
    model = load_model('bias')
    X = np.array([features])
    probs = model.predict_proba(X)[0]
    idx = np.argmax(probs)
    return {
        'predicted': BIAS_CLASSES[idx],
        'probabilities': dict(zip(BIAS_CLASSES, probs)),
        'confidence': float(probs[idx])
    }

def predict_market_style(features):
    model = load_model('market_style')
    X = np.array([features])
    probs = model.predict_proba(X)[0]
    idx = np.argmax(probs)
    return {
        'predicted': STYLE_CLASSES[idx],
        'probabilities': dict(zip(STYLE_CLASSES, probs)),
        'confidence': float(probs[idx])
    }

def predict_trap(features):
    model = load_model('trap')
    X = np.array([features])
    probs = model.predict_proba(X)[0]
    idx = np.argmax(probs)
    return {
        'predicted': int(TRAP_CLASSES[idx]),
        'probabilities': {str(k): float(v) for k, v in zip(TRAP_CLASSES, probs)},
        'confidence': float(probs[idx])
    }

def predict_reversal(features):
    model = load_model('reversal')
    X = np.array([features])
    probs = model.predict_proba(X)[0]
    idx = np.argmax(probs)
    return {
        'predicted': int(REVERSAL_CLASSES[idx]),
        'probabilities': {str(k): float(v) for k, v in zip(REVERSAL_CLASSES, probs)},
        'confidence': float(probs[idx])
    }

def predict_sr(features):
    model = load_model('sr')
    X = np.array([features])
    probs = model.predict_proba(X)[0]
    idx = np.argmax(probs)
    return {
        'predicted': SR_CLASSES[idx],
        'probabilities': dict(zip(SR_CLASSES, probs)),
        'confidence': float(probs[idx])
    }

def predict_entry_logic(features):
    model = load_model('entry_logic')
    X = np.array([features])
    probs = model.predict_proba(X)[0]
    idx = np.argmax(probs)
    return {
        'predicted': int(ENTRY_CLASSES[idx]),
        'probabilities': {str(k): float(v) for k, v in zip(ENTRY_CLASSES, probs)},
        'confidence': float(probs[idx])
    } 