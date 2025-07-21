import os
from fastapi import FastAPI, Query, HTTPException, Request, Body, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
import httpx
from datetime import datetime, timedelta
from typing import Optional
from pytz import timezone
from collections import deque
import numpy as np
from fastapi import status
import traceback
from dateutil import parser
from fastapi.staticfiles import StaticFiles
import joblib
from .ml_inference import (
    predict_bias, predict_market_style, predict_trap, predict_reversal, predict_sr, predict_entry_logic
)

load_dotenv()

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["samarth"]
tokens_col = db["tokens"]

# Upstox OAuth endpoints
@app.get("/auth-url")
def get_auth_url(user: str = Query(..., enum=["emperor", "king"])):
    if user == "emperor":
        api_key = os.getenv("UPSTOX_EMPEROR_API_KEY")
        redirect_uri = os.getenv("UPSTOX_EMPEROR_REDIRECT_URI")
    else:
        api_key = os.getenv("UPSTOX_KING_API_KEY")
        redirect_uri = os.getenv("UPSTOX_KING_REDIRECT_URI")
    
    base_url = "https://api.upstox.com/v2/login/authorization/dialog"
    auth_url = f"{base_url}?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}&state=xyz"
    return {"auth_url": auth_url}

class TokenRequest(BaseModel):
    user: str  # 'emperor' or 'king'
    code: str

@app.post("/generate-token")
async def generate_token(req: TokenRequest):
    if req.user == "emperor":
        api_key = os.getenv("UPSTOX_EMPEROR_API_KEY")
        api_secret = os.getenv("UPSTOX_EMPEROR_API_SECRET")
        redirect_uri = os.getenv("UPSTOX_EMPEROR_REDIRECT_URI")
    else:
        api_key = os.getenv("UPSTOX_KING_API_KEY")
        api_secret = os.getenv("UPSTOX_KING_API_SECRET")
        redirect_uri = os.getenv("UPSTOX_KING_REDIRECT_URI")

    token_url = "https://api.upstox.com/v2/login/authorization/token"
    payload = {
        "code": req.code,
        "client_id": api_key,
        "client_secret": api_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get access token from Upstox.")
    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token in response.")
    # Remove any previous token for this user
    tokens_col.delete_many({"user": req.user})
    # Store in DB with expiry (24 hours from now)
    tokens_col.insert_one({
        "user": req.user,
        "access_token": access_token,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    })
    return {"success": True, "access_token": access_token} 

@app.get("/check-token")
def check_token(user: str):
    token_doc = tokens_col.find_one({"user": user})
    if not token_doc or not token_doc.get("access_token"):
        return {"valid": False}
    if token_doc.get("expires_at") < datetime.utcnow():
        return {"valid": False}
    return {"valid": True}

@app.get("/option-chain")
async def get_option_chain(user: str, expiry: str, request: Request):
    # Get access token from DB
    token_doc = tokens_col.find_one({"user": user})
    if not token_doc or not token_doc.get("access_token"):
        raise HTTPException(status_code=401, detail="No access token found. Please login again.")
    access_token = token_doc["access_token"]

    # Fetch option chain from Upstox
    url = "https://api.upstox.com/v2/option/chain"
    params = {
        "instrument_key": "NSE_INDEX|Nifty 50",
        "expiry_date": expiry
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch option chain from Upstox.")
    data = response.json()
    if data.get("status") != "success" or not data.get("data"):
        raise HTTPException(status_code=400, detail="No option chain data returned.")

    # Flatten and structure the data
    strikes = []
    for item in data["data"]:
        strike = {
            "expiry": item.get("expiry"),
            "strike_price": item.get("strike_price"),
            "underlying_key": item.get("underlying_key"),
            "underlying_spot_price": item.get("underlying_spot_price"),
            "pcr": item.get("pcr"),
        }
        # Call option fields
        call = item.get("call_options", {})
        call_md = call.get("market_data", {})
        call_greeks = call.get("option_greeks", {})
        for k, v in call_md.items():
            strike[f"call_{k}"] = v
        for k, v in call_greeks.items():
            strike[f"call_{k}"] = v
        # Put option fields
        put = item.get("put_options", {})
        put_md = put.get("market_data", {})
        put_greeks = put.get("option_greeks", {})
        for k, v in put_md.items():
            strike[f"put_{k}"] = v
        for k, v in put_greeks.items():
            strike[f"put_{k}"] = v
        strikes.append(strike)

    # Store snapshot in DB (overwrite previous for user+expiry)
    db["option_chain_snapshots"].update_one(
        {"user": user, "expiry": expiry},
        {"$set": {
            "timestamp": datetime.utcnow(),
            "strikes": strikes
        }},
        upsert=True
    )
    return {"strikes": strikes} 

@app.get("/bias-identifier")
async def bias_identifier(user: str, expiry: str):
    # Fetch latest option chain snapshot for user+expiry
    doc = db["option_chain_snapshots"].find_one({"user": user, "expiry": expiry}, sort=[("timestamp", -1)])
    if not doc or not doc.get("strikes"):
        raise HTTPException(status_code=404, detail="No option chain data found for user/expiry.")
    strikes = doc["strikes"]
    # Find ATM strike (closest to underlying_spot_price)
    if not strikes:
        raise HTTPException(status_code=404, detail="No strikes data available.")
    spot = strikes[0].get("underlying_spot_price")
    if spot is None:
        raise HTTPException(status_code=400, detail="No underlying_spot_price in data.")
    atm_strike = min((row["strike_price"] for row in strikes if row.get("strike_price") is not None), key=lambda x: abs(x - spot))
    # Add option_type_zone to each row (in DB only)
    for row in strikes:
        strike = row.get("strike_price")
        if strike is None:
            row["option_type_zone"] = None
            continue
        # Calls
        if strike == atm_strike:
            row["call_option_type_zone"] = "ATM"
        elif strike > atm_strike:
            row["call_option_type_zone"] = "OTM"
        else:
            row["call_option_type_zone"] = "ITM"
        # Puts
        if strike == atm_strike:
            row["put_option_type_zone"] = "ATM"
        elif strike < atm_strike:
            row["put_option_type_zone"] = "OTM"
        else:
            row["put_option_type_zone"] = "ITM"
    # Update DB with zones
    db["option_chain_snapshots"].update_one({"_id": doc["_id"]}, {"$set": {"strikes": strikes}})
    # Filter ATM+OTM rows for calls and puts
    call_rows = [r for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM")]
    put_rows = [r for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM")]
    # Columns to aggregate
    agg_cols = [
        ("volume", "call_volume", "put_volume"),
        ("openInterest", "call_oi", "put_oi"),
        ("iv", "call_iv", "put_iv"),
    ]
    def agg(rows, call_or_put):
        result = {}
        for label, call_key, put_key in agg_cols:
            key = call_key if call_or_put == "call" else put_key
            total = sum(r.get(key, 0) or 0 for r in rows)
            result[label] = total
        return result
    call_totals = agg(call_rows, "call")
    put_totals = agg(put_rows, "put")

    # --- Rolling 10-min window for OI, IV, Volume ---
    from datetime import datetime, timedelta
    rolling_col = db["option_chain_rolling"]
    now = datetime.utcnow()
    # Insert current snapshot
    rolling_col.insert_one({
                "user": user,
                "expiry": expiry,
        "timestamp": now,
        "call_oi": call_totals["openInterest"],
        "put_oi": put_totals["openInterest"],
        "call_iv": call_totals["iv"],
        "put_iv": put_totals["iv"],
        "call_volume": call_totals["volume"],
        "put_volume": put_totals["volume"]
    })
    # Find snapshot from ~10 minutes ago
    ten_min_ago = now - timedelta(minutes=10)
    old_doc = rolling_col.find_one(
        {"user": user, "expiry": expiry, "timestamp": {"$lte": ten_min_ago}},
        sort=[("timestamp", -1)]
    )
    if old_doc:
        rolling_deltas = {
            "call_oi": call_totals["openInterest"] - old_doc["call_oi"],
            "put_oi": put_totals["openInterest"] - old_doc["put_oi"],
            "call_iv": call_totals["iv"] - old_doc["call_iv"],
            "put_iv": put_totals["iv"] - old_doc["put_iv"],
            "call_volume": call_totals["volume"] - old_doc["call_volume"],
            "put_volume": put_totals["volume"] - old_doc["put_volume"],
        }
        rolling_pct = {
            k: (rolling_deltas[k] / old_doc[k]) * 100 if old_doc[k] else 0
            for k in rolling_deltas
        }
    else:
        rolling_deltas = None
        rolling_pct = None
    # Purge old data (>15 min)
    rolling_col.delete_many({"user": user, "expiry": expiry, "timestamp": {"$lt": now - timedelta(minutes=15)}})

    # --- Rolling spot price logic for dynamic price_direction ---
    spot_rolling_col = db["spot_price_rolling"]
    rolling_doc = spot_rolling_col.find_one({"user": user, "expiry": expiry})
    if rolling_doc and "spots" in rolling_doc:
        spots = rolling_doc["spots"]
    else:
        spots = []
    # Append current spot, keep maxlen=120 (10 minutes)
    spots.append(spot)
    if len(spots) > 120:
        spots = spots[-120:]
    # Save back to DB
    spot_rolling_col.update_one(
        {"user": user, "expiry": expiry},
        {"$set": {"user": user, "expiry": expiry, "spots": spots, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    # Compute rolling average
    if len(spots) >= 2:
        rolling_avg = sum(spots) / len(spots)
        if spot > rolling_avg:
            price_direction = "up"
        elif spot < rolling_avg:
            price_direction = "down"
        else:
            price_direction = "flat"
    else:
        price_direction = None

    # --- Participant and Bias Classification (refined, using rolling window) ---
    call_position = None
    put_position = None
    bias = None
    # Only classify if we have all three rolling % metrics and price direction
    if (
        rolling_pct is not None and price_direction is not None and
        all(k in rolling_pct for k in ("call_oi", "call_volume", "call_iv", "put_oi", "put_volume", "put_iv"))
    ):
        call_oi = rolling_pct["call_oi"]
        call_vol = rolling_pct["call_volume"]
        call_iv = rolling_pct["call_iv"]
        put_oi = rolling_pct["put_oi"]
        put_vol = rolling_pct["put_volume"]
        put_iv = rolling_pct["put_iv"]
        # Calls classification
        if call_oi > 0 and call_iv > 0 and call_vol > 0 and price_direction == "up":
            call_position = "Long Buildup"
        elif call_oi > 0 and call_iv > 0 and call_vol > 0 and price_direction == "down":
            call_position = "Short Buildup"
        elif call_oi < 0 and call_iv < 0 and call_vol > 0 and price_direction == "up":
            call_position = "Short Covering"
        elif call_oi < 0 and call_iv < 0 and call_vol > 0 and price_direction == "down":
            call_position = "Long Unwinding"
        else:
            call_position = "Neutral / Noise"
        # Puts classification
        if put_oi > 0 and put_iv > 0 and put_vol > 0 and price_direction == "up":
            put_position = "Long Buildup"
        elif put_oi > 0 and put_iv > 0 and put_vol > 0 and price_direction == "down":
            put_position = "Short Buildup"
        elif put_oi < 0 and put_iv < 0 and put_vol > 0 and price_direction == "up":
            put_position = "Short Covering"
        elif put_oi < 0 and put_iv < 0 and put_vol > 0 and price_direction == "down":
            put_position = "Long Unwinding"
        else:
            put_position = "Neutral / Noise"
        # Bias logic
        if (
            (call_position in ("Long Buildup", "Short Covering")) and
            (put_position in ("Long Unwinding", "Short Covering"))
        ):
            bias = "Bullish"
        elif (
            (call_position in ("Short Buildup", "Long Unwinding")) and
            (put_position in ("Long Buildup", "Long Unwinding"))
        ):
            bias = "Bearish"
        elif (
            call_position == "Neutral / Noise" and put_position == "Neutral / Noise"
        ):
            bias = "Sideways"
        else:
            bias = "Sideways"

    output = {
        "calls": call_totals,
        "puts": put_totals,
        "rolling_deltas": rolling_deltas,
        "rolling_pct": rolling_pct,
        "price_direction": price_direction,
        "spot": spot,
        "call_participant": call_position,
        "put_participant": put_position,
        "bias": bias
    } 
    # ML inference
    ml_features = [
        output['rolling_pct'].get('call_oi'), output['rolling_pct'].get('call_iv'), output['rolling_pct'].get('call_volume'),
        output['rolling_pct'].get('put_oi'), output['rolling_pct'].get('put_iv'), output['rolling_pct'].get('put_volume'),
        output['spot'], output['price_direction'], output['call_participant'], output['put_participant'], output['bias']
    ]
    try:
        ml_result = predict_bias(ml_features)
        output['ml_predicted_bias'] = ml_result['predicted']
        output['ml_probabilities'] = ml_result['probabilities']
        output['ml_confidence'] = ml_result['confidence']
    except Exception as e:
        output['ml_error'] = str(e)
    # Persist output for ML/audit
    db["bias_identifier_snapshots"].insert_one({
        **output,
        "user": user,
        "expiry": expiry,
        "timestamp": datetime.utcnow(),
        "trigger": "poll"
    })
    return output 

@app.get("/market-style-identifier")
async def market_style_identifier(user: str, expiry: str, mode: str = Query("adaptive", enum=["strict", "adaptive"])):
    # Fetch latest option chain snapshot for user+expiry
    doc = db["option_chain_snapshots"].find_one({"user": user, "expiry": expiry}, sort=[("timestamp", -1)])
    if not doc or not doc.get("strikes"):
        raise HTTPException(status_code=404, detail="No option chain data found for user/expiry.")
    strikes = doc["strikes"]
    spot = strikes[0].get("underlying_spot_price")
    if spot is None:
        raise HTTPException(status_code=400, detail="No underlying_spot_price in data.")
    # Find ATM strike
    atm_strike = min((row["strike_price"] for row in strikes if row.get("strike_price") is not None), key=lambda x: abs(x - spot))
    for row in strikes:
        strike = row.get("strike_price")
        if strike is None:
            row["option_type_zone"] = None
            continue
        if strike == atm_strike:
            row["call_option_type_zone"] = "ATM"
        elif strike > atm_strike:
            row["call_option_type_zone"] = "OTM"
        else:
            row["call_option_type_zone"] = "ITM"
        if strike == atm_strike:
            row["put_option_type_zone"] = "ATM"
        elif strike < atm_strike:
            row["put_option_type_zone"] = "OTM"
        else:
            row["put_option_type_zone"] = "ITM"
    call_rows = [r for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM")]
    put_rows = [r for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM")]
    agg_cols = [
        ("volume", "call_volume", "put_volume"),
        ("openInterest", "call_oi", "put_oi"),
        ("iv", "call_iv", "put_iv"),
    ]
    def agg(rows, call_or_put):
        result = {}
        for label, call_key, put_key in agg_cols:
            key = call_key if call_or_put == "call" else put_key
            total = sum(r.get(key, 0) or 0 for r in rows)
            result[label] = total
        return result
    call_totals = agg(call_rows, "call")
    put_totals = agg(put_rows, "put")
    total_volume = call_totals["volume"] + put_totals["volume"]
    total_oi = call_totals["openInterest"] + put_totals["openInterest"]
    # --- Baseline logic ---
    ist = timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    today_str = now_ist.strftime('%Y-%m-%d')
    nine_fifteen = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    eleven_thirty = now_ist.replace(hour=11, minute=30, second=0, microsecond=0)
    # Get morning baseline
    baseline_col = db["otm_baseline_snapshots"]
    morning_baseline = baseline_col.find_one({"user": user, "expiry": expiry, "date": today_str})
    # Get midday baseline
    midday_col = db["midday_baseline_snapshots"]
    midday_baseline = midday_col.find_one({"user": user, "expiry": expiry, "date": today_str})
    baseline_used = "morning"
    baseline_doc = morning_baseline
    # --- Adaptive mode: dynamic midday baseline trigger ---
    if mode == "adaptive" and now_ist >= eleven_thirty and morning_baseline:
        # Check IV/spot change from morning baseline
        iv_morning = morning_baseline["calls"].get("iv", 0) + morning_baseline["puts"].get("iv", 0)
        iv_now = call_totals["iv"] + put_totals["iv"]
        spot_morning = morning_baseline.get("spot", spot)
        iv_change = abs((iv_now - iv_morning) / (iv_morning or 1)) * 100
        spot_change = abs((spot - spot_morning) / (spot_morning or 1)) * 100
        # Only one midday baseline per day
        if not midday_baseline and (iv_change > 2.5 or spot_change > 1.5):
            midday_baseline_doc = {
                "user": user,
                "expiry": expiry,
                "date": today_str,
                "calls": call_totals,
                "puts": put_totals,
                "spot": spot,
                "created_at": now_ist
            }
            midday_col.insert_one(midday_baseline_doc)
            midday_baseline = midday_baseline_doc
        if midday_baseline:
            baseline_doc = midday_baseline
            baseline_used = "midday"
    # --- Strict mode: always use morning baseline ---
    if not baseline_doc:
        return {"market_style": None, "oi_diff": None, "vol_diff": None, "iv_diff": None, "price_direction": None, "volatility_state": None, "baseline_used": None, "spot_trend_strength": None, "total_volume": total_volume, "total_oi": total_oi, "mode": mode}
    # --- Compute % changes ---
    def pct_change(current, base):
        if base == 0:
            return 0
        return ((current - base) / base) * 100
    pct_calls = {
        "openInterest": pct_change(call_totals["openInterest"], baseline_doc["calls"].get("openInterest", 1)),
        "volume": pct_change(call_totals["volume"], baseline_doc["calls"].get("volume", 1)),
        "iv": pct_change(call_totals["iv"], baseline_doc["calls"].get("iv", 1)),
    }
    pct_puts = {
        "openInterest": pct_change(put_totals["openInterest"], baseline_doc["puts"].get("openInterest", 1)),
        "volume": pct_change(put_totals["volume"], baseline_doc["puts"].get("volume", 1)),
        "iv": pct_change(put_totals["iv"], baseline_doc["puts"].get("iv", 1)),
    }
    # --- Compute diffs ---
    oi_diff = pct_calls["openInterest"] - pct_puts["openInterest"]
    vol_diff = pct_calls["volume"] - pct_puts["volume"]
    iv_diff = pct_calls["iv"] - pct_puts["iv"]
    # --- Volatility state ---
    if iv_diff > 5:
        volatility_state = "High"
    elif iv_diff < -5:
        volatility_state = "Low"
    else:
        volatility_state = "Stable"
    # --- Rolling spot trend with EMA ---
    spot_rolling_col = db["spot_price_rolling"]
    rolling_doc = spot_rolling_col.find_one({"user": user, "expiry": expiry})
    price_direction = None
    spot_trend_strength = None
    if rolling_doc and "spots" in rolling_doc:
        spots = rolling_doc["spots"]
        if len(spots) >= 2:
            # EMA calculation
            alpha = 2 / (min(len(spots), 120) + 1)
            ema = spots[0]
            for s in spots[1:]:
                ema = alpha * s + (1 - alpha) * ema
            # Slope/strength: difference between last and first EMA over window
            ema_start = spots[0]
            ema_end = ema
            spot_trend_strength = ema_end - ema_start
            if spot > ema:
                price_direction = "up"
            elif spot < ema:
                price_direction = "down"
            else:
                price_direction = "flat"
    # --- Low liquidity fallback ---
    min_liquidity = 100000
    if total_volume < min_liquidity or total_oi < min_liquidity:
        return {"market_style": "Low Liquidity", "price_direction": price_direction, "oi_diff": oi_diff, "vol_diff": vol_diff, "iv_diff": iv_diff, "volatility_state": volatility_state, "baseline_used": baseline_used, "spot_trend_strength": spot_trend_strength, "total_volume": total_volume, "total_oi": total_oi, "mode": mode}
    # --- Market style logic ---
    if mode == "strict":
        # Use fixed thresholds and simple average for spot trend
        if oi_diff > 5 and vol_diff > 5 and price_direction == "up":
            market_style = "Trending Up"
        elif oi_diff < -5 and vol_diff < -5 and price_direction == "down":
            market_style = "Trending Down"
        elif abs(oi_diff) < 3 and abs(vol_diff) < 3:
            market_style = "Sideways"
        else:
            market_style = "Volatile / Choppy"
    else:
        # Adaptive logic: use relative/normalized/z-score logic if available (future), else use diffs and EMA
        # Use IV diff for momentum/breakout/choppy
        if oi_diff > 0 and vol_diff > 0 and iv_diff > 5 and price_direction == "up":
            market_style = "Trending Up"
        elif oi_diff < 0 and vol_diff < 0 and iv_diff < -5 and price_direction == "down":
            market_style = "Trending Down"
        elif abs(oi_diff) < 2 and abs(vol_diff) < 2 and abs(iv_diff) < 2:
            market_style = "Sideways"
        elif volatility_state == "High":
            market_style = "Volatile / Choppy"
        else:
            market_style = "Volatile / Choppy"
    output = {
        "market_style": market_style,
        "price_direction": price_direction,
        "oi_diff": oi_diff,
        "vol_diff": vol_diff,
        "iv_diff": iv_diff,
        "volatility_state": volatility_state,
        "baseline_used": baseline_used,
        "spot_trend_strength": spot_trend_strength,
        "total_volume": total_volume,
        "total_oi": total_oi,
        "mode": mode
    } 
    # ML inference
    ml_features = [
        output['price_direction'], output['oi_diff'], output['vol_diff'], output['iv_diff'], output['volatility_state'],
        output['baseline_used'], output['spot_trend_strength'], output['total_volume'], output['total_oi'], output['mode']
    ]
    try:
        ml_result = predict_market_style(ml_features)
        output['ml_predicted_market_style'] = ml_result['predicted']
        output['ml_probabilities'] = ml_result['probabilities']
        output['ml_confidence'] = ml_result['confidence']
    except Exception as e:
        output['ml_error'] = str(e)
    db["market_style_snapshots"].insert_one({
        **output,
        "user": user,
        "expiry": expiry,
        "timestamp": datetime.utcnow(),
        "trigger": "poll"
    })
    return output 

@app.get("/reversal-probability-finder")
async def reversal_probability_finder(user: str, expiry: str):
    ist = timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    today_str = now_ist.strftime('%Y-%m-%d')
    window_minutes = 10
    window_points = 120  # 10 min at 5s intervals

    # --- Get rolling spot prices ---
    spot_rolling_col = db["spot_price_rolling"]
    rolling_doc = spot_rolling_col.find_one({"user": user, "expiry": expiry})
    spots = rolling_doc["spots"] if rolling_doc and "spots" in rolling_doc else []
    if len(spots) < 2:
        return {"reversal_probability": 0.0, "reversal_type": None, "bias_cluster_flipped": False, "iv_oi_support_flip": False, "price_vs_bias_conflict": False, "liquidity_ok": False, "structural_context": None, "volatility_phase": None, "reasoning": "Not enough spot data"}
    # --- Higher timeframe trend ---
    spot_start = spots[0]
    spot_end = spots[-1]
    spot_change = (spot_end - spot_start) / (spot_start or 1) * 100
    if spot_change > 0.3:
        higher_tf_trend = "up"
    elif spot_change < -0.3:
        higher_tf_trend = "down"
    else:
        higher_tf_trend = "sideways"

    # --- Get bias_state history (simulate from bias snapshots or store in a collection) ---
    bias_col = db["bias_state_history"]
    bias_doc = bias_col.find_one({"user": user, "expiry": expiry})
    bias_history = bias_doc["biases"][-window_points:] if bias_doc and "biases" in bias_doc else []
    # --- Bias flip cluster detection ---
    bias_flips = 0
    last_bias = None
    for b in bias_history:
        if last_bias is not None and b != last_bias:
            bias_flips += 1
        last_bias = b
    bias_cluster_flipped = bias_flips >= 2

    # --- Get rolling option chain snapshots ---
    oc_col = db["option_chain_snapshots"]
    oc_docs = list(oc_col.find({"user": user, "expiry": expiry}).sort("timestamp", -1).limit(window_points))
    oc_docs = oc_docs[::-1]  # oldest to newest
    if not oc_docs:
        return {"reversal_probability": 0.0, "reversal_type": None, "bias_cluster_flipped": False, "iv_oi_support_flip": False, "price_vs_bias_conflict": False, "liquidity_ok": False, "structural_context": None, "volatility_phase": None, "reasoning": "No option chain data"}
    # --- IV & OI shift tracking ---
    def get_agg(doc):
        strikes = doc.get("strikes", [])
        call_oi = sum(r.get("call_oi", 0) or 0 for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM"))
        put_oi = sum(r.get("put_oi", 0) or 0 for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM"))
        call_iv = sum(r.get("call_iv", 0) or 0 for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM"))
        put_iv = sum(r.get("put_iv", 0) or 0 for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM"))
        call_vol = sum(r.get("call_volume", 0) or 0 for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM"))
        put_vol = sum(r.get("put_volume", 0) or 0 for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM"))
        return call_oi, put_oi, call_iv, put_iv, call_vol, put_vol
    call_oi_start, put_oi_start, call_iv_start, put_iv_start, call_vol_start, put_vol_start = get_agg(oc_docs[0])
    call_oi_end, put_oi_end, call_iv_end, put_iv_end, call_vol_end, put_vol_end = get_agg(oc_docs[-1])
    # Detect IV/OI support flip
    oi_shift = (call_oi_end - call_oi_start) - (put_oi_end - put_oi_start)
    iv_shift = (call_iv_end - call_iv_start) - (put_iv_end - put_iv_start)
    iv_oi_support_flip = abs(oi_shift) > 0 and abs(iv_shift) > 0 and (np.sign(oi_shift) == np.sign(iv_shift))
    # --- Price vs OI/IV divergence ---
    price_trend = np.sign(spot_end - spot_start)
    bias_trend = 0
    if bias_history:
        bias_trend = 1 if bias_history[-1] == "Bullish" else -1 if bias_history[-1] == "Bearish" else 0
    price_vs_bias_conflict = (price_trend != 0 and bias_trend != 0 and price_trend != bias_trend)
    # --- Liquidity check ---
    liquidity_ok = (call_oi_end + put_oi_end) > 100000 and (call_vol_end + put_vol_end) > 100000
    # --- Volatility filter ---
    iv_series = [(get_agg(doc)[2] + get_agg(doc)[3]) for doc in oc_docs]
    iv_range = max(iv_series) - min(iv_series) if iv_series else 0
    volatility_phase = "expanding" if iv_range > 5 else "normal"
    # --- Structural context ---
    structural_context = "counter_trend" if (higher_tf_trend == "down" and bias_trend == 1) or (higher_tf_trend == "up" and bias_trend == -1) else "trend_continuation"

    # --- Market Style & Trap Detector Integration ---
    style_fn = app.routes[[r.path for r in app.routes].index("/market-style-identifier")].endpoint
    trap_fn = app.routes[[r.path for r in app.routes].index("/trap-detector")].endpoint
    style = await style_fn(user, expiry, "adaptive")
    trap = await trap_fn(user, expiry)
    market_style = style.get("market_style") if style else None
    trap_call = trap.get("call") if trap else None
    trap_put = trap.get("put") if trap else None
    trap_detected = (trap_call and trap_call.get("trap_detected")) or (trap_put and trap_put.get("trap_detected"))
    trap_comment = "Trap detected by Trap Detector. Increases reversal probability." if trap_detected else ""

    # --- Reversal probability calculation ---
    score = 0
    if bias_cluster_flipped: score += 0.25
    if iv_oi_support_flip: score += 0.25
    if price_vs_bias_conflict: score += 0.2
    if liquidity_ok: score += 0.1
    if structural_context == "counter_trend": score += 0.1
    if volatility_phase == "expanding": score += 0.1
    if trap_detected: score += 0.15
    # Market style sensitivity
    style_comment = ""
    if market_style:
        if "Trending" in market_style:
            score *= 0.8  # require stronger confirmation
            style_comment = "Trending market: reversal probability down-weighted."
        elif "Sideways" in market_style:
            score *= 1.2  # more sensitive
            style_comment = "Sideways market: reversal probability up-weighted."
        elif "Volatile" in market_style:
            score *= 1.1  # slightly more sensitive
            style_comment = "Volatile market: reversal probability slightly up-weighted."
    reversal_probability = min(1.0, score)
    reversal_type = None
    if reversal_probability > 0.5:
        if bias_history and bias_history[-1] == "Bullish":
            reversal_type = "bullish"
        elif bias_history and bias_history[-1] == "Bearish":
            reversal_type = "bearish"
    reasoning = f"Bias flips: {bias_flips}, IV/OI flip: {iv_oi_support_flip}, Price vs Bias: {price_vs_bias_conflict}, Liquidity: {liquidity_ok}, Volatility: {volatility_phase}, Context: {structural_context}. {trap_comment} {style_comment}"
    output = {
        "reversal_probability": round(float(reversal_probability), 2),
        "reversal_type": reversal_type,
        "bias_cluster_flipped": bool(bias_cluster_flipped),
        "iv_oi_support_flip": bool(iv_oi_support_flip),
        "price_vs_bias_conflict": bool(price_vs_bias_conflict),
        "liquidity_ok": bool(liquidity_ok),
        "structural_context": structural_context,
        "volatility_phase": volatility_phase,
        "market_style": market_style,
        "trap_detected": bool(trap_detected),
        "reasoning": reasoning
    } 
    # ML inference
    ml_features = [
        output['reversal_probability'], output['bias_cluster_flipped'], output['iv_oi_support_flip'], output['price_vs_bias_conflict'],
        output['liquidity_ok'], output['structural_context'], output['volatility_phase'], output['market_style'], output['trap_detected']
    ]
    try:
        ml_result = predict_reversal(ml_features)
        output['ml_predicted_reversal'] = ml_result['predicted']
        output['ml_probabilities'] = ml_result['probabilities']
        output['ml_confidence'] = ml_result['confidence']
    except Exception as e:
        output['ml_error'] = str(e)
    db["reversal_probability_snapshots"].insert_one({
        **output,
        "user": user,
        "expiry": expiry,
        "timestamp": datetime.utcnow(),
        "trigger": "poll"
    })
    return output 

@app.get("/trap-detector")
async def trap_detector(user: str, expiry: str):
    from fastapi import Request
    from datetime import datetime
    import calendar
    ist = timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    window_points = 120  # 10 min at 5s intervals

    # --- Get rolling spot prices ---
    spot_rolling_col = db["spot_price_rolling"]
    rolling_doc = spot_rolling_col.find_one({"user": user, "expiry": expiry})
    spots = rolling_doc["spots"] if rolling_doc and "spots" in rolling_doc else []
    if len(spots) < 2:
        return {"call": {"trap_detected": False, "trap_type": "None", "deception_score": 0, "confidence_level": "Low", "comment": "Not enough spot data"},
                "put": {"trap_detected": False, "trap_type": "None", "deception_score": 0, "confidence_level": "Low", "comment": "Not enough spot data"}}
    # --- Get rolling option chain snapshots ---
    oc_col = db["option_chain_snapshots"]
    oc_docs = list(oc_col.find({"user": user, "expiry": expiry}).sort("timestamp", -1).limit(window_points))
    oc_docs = oc_docs[::-1]  # oldest to newest
    if not oc_docs:
        return {"call": {"trap_detected": False, "trap_type": "None", "deception_score": 0, "confidence_level": "Low", "comment": "No option chain data"},
                "put": {"trap_detected": False, "trap_type": "None", "deception_score": 0, "confidence_level": "Low", "comment": "No option chain data"}}
    # --- Helper: rolling avg ---
    def rolling_avg(series):
        return sum(series) / len(series) if series else 0
    # --- Helper: get per-leg series ---
    def get_leg_series(leg):
        oi = []
        iv = []
        vol = []
        for doc in oc_docs:
            strikes = doc.get("strikes", [])
            if leg == "call":
                oi.append(sum(r.get("call_oi", 0) or 0 for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM")))
                iv.append(sum(r.get("call_iv", 0) or 0 for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM")))
                vol.append(sum(r.get("call_volume", 0) or 0 for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM")))
            else:
                oi.append(sum(r.get("put_oi", 0) or 0 for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM")))
                iv.append(sum(r.get("put_iv", 0) or 0 for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM")))
                vol.append(sum(r.get("put_volume", 0) or 0 for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM")))
        return oi, iv, vol
    ce_oi, ce_iv, ce_vol = get_leg_series("call")
    pe_oi, pe_iv, pe_vol = get_leg_series("put")
    # --- Price stalling ---
    ema_slope = (spots[-1] - spots[0]) / (len(spots) or 1)
    price_stalling = abs(ema_slope) < 0.05  # configurable threshold
    # --- Rolling IV avg ---
    ce_iv_avg = rolling_avg(ce_iv[:-3]) if len(ce_iv) > 3 else rolling_avg(ce_iv)
    pe_iv_avg = rolling_avg(pe_iv[:-3]) if len(pe_iv) > 3 else rolling_avg(pe_iv)
    # --- Current deltas ---
    ce_oi_delta = ce_oi[-1] - ce_oi[0]
    ce_iv_delta = ce_iv[-1] - ce_iv_avg
    ce_vol_delta = ce_vol[-1] - ce_vol[0]
    pe_oi_delta = pe_oi[-1] - pe_oi[0]
    pe_iv_delta = pe_iv[-1] - pe_iv_avg
    pe_vol_delta = pe_vol[-1] - pe_vol[0]
    # --- Price direction ---
    price_direction = "up" if spots[-1] > rolling_avg(spots) else "down" if spots[-1] < rolling_avg(spots) else "flat"
    # --- Leg divergence ---
    ce_vs_pe_div = (ce_oi_delta > 0 and pe_oi_delta > 0 and pe_iv_delta > 0)
    pe_vs_ce_div = (pe_oi_delta > 0 and ce_oi_delta > 0 and ce_iv_delta > 0)
    # --- Reversal confirmation (next 3 points) ---
    def reversal_confirm(leg_iv, leg_vol):
        if len(leg_iv) < 4 or len(leg_vol) < 4:
            return False
        # Look for IV rising and volume stalling in last 3 points
        return any(leg_iv[-i] > leg_iv[-i-1] for i in range(1, 4)) and all(leg_vol[-i] < leg_vol[-i-1] for i in range(1, 4))

    # --- S/R Guard Integration ---
    sr_fn = app.routes[[r.path for r in app.routes].index("/support-resistance-guard")].endpoint
    sr_zones = await sr_fn(user, expiry)
    sr_trap_signals = []
    for z in sr_zones:
        if z.get("trap_risk") and z.get("zone_state") == "Active":
            sr_trap_signals.append(f"Trap risk at {z['zone_type']} {z['zone_level']}")
        if z.get("zone_state") == "Active" and z.get("bias_suggestion") == "Trap":
            sr_trap_signals.append(f"Trap bias at {z['zone_type']} {z['zone_level']}")
        if z.get("zone_state") == "Active" and z.get("bias_suggestion") == "Bounce" and z.get("confidence") == "Medium":
            sr_trap_signals.append(f"Wick rejection at {z['zone_type']} {z['zone_level']}")
        if z.get("zone_state") == "Active" and z.get("bias_suggestion") == "Break" and z.get("confidence") == "High":
            sr_trap_signals.append(f"Fakeout at {z['zone_type']} {z['zone_level']}")

    # --- Trap Memory (Historical Context) ---
    trap_memory_col = db["trap_memory"]
    trap_level = round(spots[-1], -1)  # round to nearest 10 for grouping
    trap_mem_doc = trap_memory_col.find_one({"user": user, "expiry": expiry, "level": trap_level})
    trap_count = trap_mem_doc["count"] if trap_mem_doc else 0

    # --- Expiry/Event Sensitivity ---
    is_expiry = now_ist.weekday() == 3  # Thursday
    is_friday = now_ist.weekday() == 4
    is_event_day = is_expiry or is_friday
    min_signals_required = 2 if is_event_day else 1
    event_comment = "Expiry/Event day: IV spikes may be event-driven. Require more signals for trap confirmation." if is_event_day else ""

    # --- Call Trap Logic ---
    call_score = 0
    call_comment = []
    trap_signals = 0
    if price_direction == "up" and ce_oi_delta > 0 and ce_iv_delta < -0.5 * abs(ce_iv_avg):
        call_score += 20
        call_comment.append("Price up, CE OI up, CE IV down vs avg")
        trap_signals += 1
    if price_stalling:
        call_score += 20
        call_comment.append("Price stalling/flat")
        trap_signals += 1
    if ce_vs_pe_div:
        call_score += 20
        call_comment.append("PE also building OI/IV (hedge/fade)")
        trap_signals += 1
    if ce_iv_delta < -0.5 * abs(ce_iv_avg):
        call_score += 20
        call_comment.append("CE IV drop significant vs regime")
        trap_signals += 1
    if reversal_confirm(ce_iv, ce_vol):
        call_score += 20
        call_comment.append("Reversal confirmation in last 3 points")
        trap_signals += 1
    # S/R signals
    for s in sr_trap_signals:
        call_score += 10
        call_comment.append(f"S/R: {s}")
        trap_signals += 1
    # Trap memory
    if trap_count > 0:
        call_score += min(20, trap_count * 5)
        call_comment.append(f"Trap memory: {trap_count} prior traps at this level")
    # Event/expiry sensitivity
    if event_comment:
        call_comment.append(event_comment)
    call_conf = "High" if call_score >= 80 else "Medium" if call_score >= 60 else "Low"
    call_trap = trap_signals >= min_signals_required and call_score >= 60
    # Update trap memory if trap detected
    if call_trap:
        trap_memory_col.update_one({"user": user, "expiry": expiry, "level": trap_level}, {"$inc": {"count": 1}}, upsert=True)

    # --- Put Trap Logic ---
    put_score = 0
    put_comment = []
    trap_signals = 0
    if price_direction == "down" and pe_oi_delta > 0 and pe_iv_delta < -0.5 * abs(pe_iv_avg):
        put_score += 20
        put_comment.append("Price down, PE OI up, PE IV down vs avg")
        trap_signals += 1
    if price_stalling:
        put_score += 20
        put_comment.append("Price stalling/flat")
        trap_signals += 1
    if pe_vs_ce_div:
        put_score += 20
        put_comment.append("CE also building OI/IV (hedge/fade)")
        trap_signals += 1
    if pe_iv_delta < -0.5 * abs(pe_iv_avg):
        put_score += 20
        put_comment.append("PE IV drop significant vs regime")
        trap_signals += 1
    if reversal_confirm(pe_iv, pe_vol):
        put_score += 20
        put_comment.append("Reversal confirmation in last 3 points")
        trap_signals += 1
    # S/R signals
    for s in sr_trap_signals:
        put_score += 10
        put_comment.append(f"S/R: {s}")
        trap_signals += 1
    # Trap memory
    if trap_count > 0:
        put_score += min(20, trap_count * 5)
        put_comment.append(f"Trap memory: {trap_count} prior traps at this level")
    # Event/expiry sensitivity
    if event_comment:
        put_comment.append(event_comment)
    put_conf = "High" if put_score >= 80 else "Medium" if put_score >= 60 else "Low"
    put_trap = trap_signals >= min_signals_required and put_score >= 60
    # Update trap memory if trap detected
    if put_trap:
        trap_memory_col.update_one({"user": user, "expiry": expiry, "level": trap_level}, {"$inc": {"count": 1}}, upsert=True)

    output = {
        "call": {
            "trap_detected": bool(call_trap),
            "trap_type": "Call Trap" if call_trap else "None",
            "deception_score": int(call_score),
            "confidence_level": call_conf,
            "comment": "; ".join(call_comment) or "No trap detected",
            "trap_memory": trap_count
        },
        "put": {
            "trap_detected": bool(put_trap),
            "trap_type": "Put Trap" if put_trap else "None",
            "deception_score": int(put_score),
            "confidence_level": put_conf,
            "comment": "; ".join(put_comment) or "No trap detected",
            "trap_memory": trap_count
        }
    } 
    # ML inference
    ml_features = [
        output['call']['trap_detected'], output['put']['trap_detected'], output['call']['deception_score'], output['put']['deception_score'],
        output['call']['confidence_level'], output['put']['confidence_level'], output['call']['comment'], output['put']['comment']
    ]
    try:
        ml_result = predict_trap(ml_features)
        output['ml_predicted_trap'] = ml_result['predicted']
        output['ml_probabilities'] = ml_result['probabilities']
        output['ml_confidence'] = ml_result['confidence']
    except Exception as e:
        output['ml_error'] = str(e)
    db["trap_detector_snapshots"].insert_one({
        **output,
        "user": user,
        "expiry": expiry,
        "timestamp": datetime.utcnow(),
        "trigger": "poll"
    })
    return output 

@app.get("/support-resistance-guard")
async def support_resistance_guard(user: str, expiry: str):
    ist = timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    window_points = 120  # 10 min at 5s intervals
    recent_window_sec = 600  # 10 min

    # --- Get latest spot price ---
    spot_rolling_col = db["spot_price_rolling"]
    rolling_doc = spot_rolling_col.find_one({"user": user, "expiry": expiry})
    spots = rolling_doc["spots"] if rolling_doc and "spots" in rolling_doc else []
    spot = spots[-1] if spots else None
    if not spot:
        return []

    # --- Get option chain snapshots (last 10 min) ---
    oc_col = db["option_chain_snapshots"]
    oc_docs = list(oc_col.find({"user": user, "expiry": expiry}).sort("timestamp", -1).limit(window_points))
    oc_docs = oc_docs[::-1]  # oldest to newest
    if not oc_docs:
        return []

    # --- Get bias from Bias Identifier ---
    bias_col = db["bias_state_history"]
    bias_doc = bias_col.find_one({"user": user, "expiry": expiry})
    global_bias = bias_doc["biases"][-1] if bias_doc and "biases" in bias_doc and bias_doc["biases"] else None

    # --- VWAP, PDH, PDL (placeholders, replace with real values if available) ---
    vwap = sum(spots) / len(spots) if spots else spot
    pdh = spot + 100  # placeholder
    pdl = spot - 100  # placeholder

    # --- Auto-detect round levels ---
    round_levels = set()
    for inc in [100, 50]:
        base = int(spot // inc) * inc
        for offset in range(-400, 401, inc):
            lvl = base + offset
            if lvl > 0:
                round_levels.add(lvl)
    round_levels = sorted(round_levels)
    # Only keep those within ±400 of spot
    round_levels = [lvl for lvl in round_levels if abs(lvl - spot) <= 400]

    # --- Manual zones from config ---
    manual_zones_col = db["manual_zones"]
    manual_zones_doc = manual_zones_col.find_one({"user": user, "expiry": expiry})
    manual_zones = manual_zones_doc["zones"] if manual_zones_doc and "zones" in manual_zones_doc else []
    # manual_zones: list of {"zone_type": "Manual", "zone_level": float}

    # --- Build zones list ---
    zones = [
        {"zone_type": "VWAP", "zone_level": vwap},
        {"zone_type": "PDH", "zone_level": pdh},
        {"zone_type": "PDL", "zone_level": pdl},
    ] + [{"zone_type": "Round", "zone_level": lvl} for lvl in round_levels]
    # Add manual zones
    zones += [{"zone_type": z.get("zone_type", "Manual"), "zone_level": z["zone_level"]} for z in manual_zones if "zone_level" in z]

    # --- Volatility regime (iv_range) ---
    def get_agg(doc):
        strikes = doc.get("strikes", [])
        ce_iv = sum(r.get("call_iv", 0) or 0 for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM"))
        pe_iv = sum(r.get("put_iv", 0) or 0 for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM"))
        return ce_iv, pe_iv
    iv_series = [(get_agg(doc)[0] + get_agg(doc)[1]) for doc in oc_docs]
    iv_range = max(iv_series) - min(iv_series) if iv_series else 0
    volatility_regime = "high" if iv_range > 5 else "normal"

    # --- For each zone, evaluate state and signals ---
    results = []
    for zone in zones:
        zlvl = zone["zone_level"]
        ztype = zone["zone_type"]
        # Find last test time (price within 0.1% or 20 points)
        last_test_time = None
        for doc in reversed(oc_docs):
            ts = doc.get("timestamp")
            strikes = doc.get("strikes", [])
            s = strikes[0].get("underlying_spot_price") if strikes and strikes[0].get("underlying_spot_price") else None
            if not s: continue
            if abs(s - zlvl) <= max(20, 0.001 * zlvl):
                last_test_time = ts
                break
        # Zone state
        if last_test_time:
            if isinstance(last_test_time, str):
                try:
                    last_test_time_dt = parser.parse(last_test_time)
                except Exception:
                    last_test_time_dt = None
            else:
                last_test_time_dt = last_test_time
            if last_test_time_dt is not None:
                if last_test_time_dt.tzinfo is None:
                    last_test_time_dt = timezone('Asia/Kolkata').localize(last_test_time_dt)
                if now_ist.tzinfo is None:
                    now_ist_aware = timezone('Asia/Kolkata').localize(now_ist)
                else:
                    now_ist_aware = now_ist
                tdelta = (now_ist_aware - last_test_time_dt).total_seconds()
            else:
                tdelta = recent_window_sec + 1
            if tdelta < recent_window_sec:
                zone_state = "Active"
            elif tdelta < 2 * recent_window_sec:
                zone_state = "Decaying"
            else:
                zone_state = "Ignored"
        else:
            zone_state = "Ignored"
        # Price action & wick structure (placeholder logic)
        wick_reject = abs(spot - zlvl) > 10 and abs(spots[-1] - zlvl) < 20
        body_break = abs(spot - zlvl) < 10
        # OI/IV/Volume analysis (use last doc)
        strikes = oc_docs[-1].get("strikes", [])
        ce_oi = sum(r.get("call_oi", 0) or 0 for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM"))
        pe_oi = sum(r.get("put_oi", 0) or 0 for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM"))
        ce_iv = sum(r.get("call_iv", 0) or 0 for r in strikes if r.get("call_option_type_zone") in ("ATM", "OTM"))
        pe_iv = sum(r.get("put_iv", 0) or 0 for r in strikes if r.get("put_option_type_zone") in ("ATM", "OTM"))
        # Bias suggestion and confidence logic
        bias_suggestion = "Bounce"
        confidence = "Low"
        confidence_score = 0.3
        trap_risk = False
        if zone_state == "Active":
            if wick_reject:
                bias_suggestion = "Bounce"
                confidence = "Medium"
                confidence_score = 0.6
            elif body_break:
                bias_suggestion = "Break"
                confidence = "High"
                confidence_score = 0.9
            # Trap risk: CE unwinding + IV spike near resistance (or PE for support)
            if (ztype in ["VWAP", "PDH", "Round", "Manual"] and ce_oi < 0 and ce_iv > 0.05 * ce_iv) or (ztype in ["VWAP", "PDL", "Round", "Manual"] and pe_oi < 0 and pe_iv > 0.05 * pe_iv):
                bias_suggestion = "Trap"
                trap_risk = True
                confidence = "Medium"
                confidence_score = 0.8
        elif zone_state == "Decaying":
            confidence = "Low"
            confidence_score = 0.3
        # Volatility regime adjustment
        if volatility_regime == "high":
            if bias_suggestion == "Trap":
                confidence_score = min(1.0, confidence_score + 0.1)
            elif bias_suggestion in ["Break", "Bounce"]:
                confidence_score = max(0.1, confidence_score - 0.2)
                confidence = "Low" if confidence_score < 0.5 else confidence
        # Signal disagreement
        signal_disagreement = (global_bias and ((bias_suggestion == "Bounce" and global_bias == "Bearish") or (bias_suggestion == "Break" and global_bias == "Bullish") or (bias_suggestion == "Trap")))
        results.append({
            "zone_level": zlvl,
            "zone_type": ztype,
            "zone_state": zone_state,
            "bias_suggestion": bias_suggestion,
            "confidence": confidence,
            "confidence_score": round(confidence_score, 2),
            "volatility_regime": volatility_regime,
            "trap_risk": bool(trap_risk),
            "last_test_time": str(last_test_time) if last_test_time else None,
            "signal_disagreement": bool(signal_disagreement)
        })
    output = results
    # ML inference
    ml_features = [
        output['zone_state'], output['bias_suggestion'], output['confidence'], output['confidence_score'],
        output['volatility_regime'], output['trap_risk'], output['last_test_time'], output['signal_disagreement']
    ]
    try:
        ml_result = predict_sr(ml_features)
        output['ml_predicted_sr'] = ml_result['predicted']
        output['ml_probabilities'] = ml_result['probabilities']
        output['ml_confidence'] = ml_result['confidence']
    except Exception as e:
        output['ml_error'] = str(e)
    db["support_resistance_snapshots"].insert_one({
        "zones": results,
        "user": user,
        "expiry": expiry,
        "timestamp": datetime.utcnow(),
        "trigger": "poll"
    })
    return output 

# Internal logging collection for transparency
entry_engine_log_col = db["entry_logic_engine_logs"]

@app.get("/entry-logic-engine")
async def entry_logic_engine(user: str, expiry: str, mode: str = Query("adaptive", enum=["strict", "adaptive"])):
    """
    Fuses signals from Bias Identifier, Market Style Identifier, Trap Detector, Reversal Probability Finder, and Support/Resistance Guard
    to produce real-time entry recommendations.
    """
    now = datetime.utcnow()
    log_entry = {
        "user": user,
        "expiry": expiry,
        "mode": mode,
        "timestamp": now,
        "rejections": [],
        "conflicts": [],
        "raw_signals": {},
    }
    # Helper to log and fallback
    async def safe_call(fn, name, *args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            log_entry["rejections"].append({"module": name, "error": str(e), "trace": tb})
            return None
    # Import endpoints as callables
    from fastapi import Request
    # Get app dependency-injected endpoints
    bias_fn = app.routes[[r.path for r in app.routes].index("/bias-identifier")].endpoint
    style_fn = app.routes[[r.path for r in app.routes].index("/market-style-identifier")].endpoint
    reversal_fn = app.routes[[r.path for r in app.routes].index("/reversal-probability-finder")].endpoint
    trap_fn = app.routes[[r.path for r in app.routes].index("/trap-detector")].endpoint
    sr_fn = app.routes[[r.path for r in app.routes].index("/support-resistance-guard")].endpoint
    # Call all modules (serially for now)
    bias = await safe_call(bias_fn, "bias_identifier", user, expiry)
    style = await safe_call(style_fn, "market_style_identifier", user, expiry, mode)
    reversal = await safe_call(reversal_fn, "reversal_probability_finder", user, expiry)
    trap = await safe_call(trap_fn, "trap_detector", user, expiry)
    sr = await safe_call(sr_fn, "support_resistance_guard", user, expiry)
    log_entry["raw_signals"] = {"bias": bias, "style": style, "reversal": reversal, "trap": trap, "sr": sr}
    # Fallbacks if any module fails
    must_avoid = False
    reasons = []
    entry_direction = "avoid"
    entry_zone = None
    confidence = "low"
    reason = ""
    trade_type = None
    entry_score = 0.0
    # --- Directional agreement (bias + reversal) ---
    bias_dir = bias["bias"] if bias and "bias" in bias else None
    reversal_type = reversal["reversal_type"] if reversal and "reversal_type" in reversal else None
    reversal_prob = reversal["reversal_probability"] if reversal and "reversal_probability" in reversal else 0
    # --- Market style ---
    market_style = style["market_style"] if style and "market_style" in style else None
    # --- Trap risk ---
    trap_call = trap["call"] if trap and "call" in trap else {"trap_detected": False, "deception_score": 0}
    trap_put = trap["put"] if trap and "put" in trap else {"trap_detected": False, "deception_score": 0}
    # --- Support/Resistance ---
    sr_zones = sr if isinstance(sr, list) else []
    # --- Entry logic fusion ---
    # 1. If trap risk is high (deception_score >= 80), must_avoid
    if trap_call.get("deception_score", 0) >= 80 or trap_put.get("deception_score", 0) >= 80:
        must_avoid = True
        reasons.append("High deception score detected by Trap Detector.")
    # 2. If bias and reversal are in strong disagreement, must_avoid
    if bias_dir and reversal_type and ((bias_dir == "Bullish" and reversal_type == "bearish" and reversal_prob > 0.5) or (bias_dir == "Bearish" and reversal_type == "bullish" and reversal_prob > 0.5)):
        must_avoid = True
        reasons.append("Bias and Reversal signals are in strong disagreement.")
        log_entry["conflicts"].append({"type": "bias_reversal_disagreement", "bias": bias_dir, "reversal": reversal_type, "reversal_prob": reversal_prob})
    # 3. If market style is Volatile/Choppy or Low Liquidity, avoid
    if market_style in ["Volatile / Choppy", "Low Liquidity"]:
        must_avoid = True
        reasons.append(f"Market style is {market_style}.")
    # 4. If all modules fail, must_avoid
    if not any([bias, style, reversal, trap, sr]):
        must_avoid = True
        reasons.append("All modules failed to provide signals.")
    # 5. Otherwise, determine entry direction
    if not must_avoid:
        # If bias is Bullish and reversal is not bearish, and no call trap, consider long
        if bias_dir == "Bullish" and (not reversal_type or reversal_type != "bearish" or reversal_prob < 0.5) and not trap_call.get("trap_detected", False):
            entry_direction = "long"
            confidence = "high" if not trap_call.get("trap_detected", False) and market_style == "Trending Up" else "medium"
            reasons.append("Bias is Bullish, no strong reversal or call trap, market style supports long.")
        # If bias is Bearish and reversal is not bullish, and no put trap, consider short
        elif bias_dir == "Bearish" and (not reversal_type or reversal_type != "bullish" or reversal_prob < 0.5) and not trap_put.get("trap_detected", False):
            entry_direction = "short"
            confidence = "high" if not trap_put.get("trap_detected", False) and market_style == "Trending Down" else "medium"
            reasons.append("Bias is Bearish, no strong reversal or put trap, market style supports short.")
        else:
            entry_direction = "avoid"
            confidence = "low"
            reasons.append("No clear directional edge or traps detected.")
    # 6. Entry zone: pick the most confident active support/resistance zone matching direction
    if entry_direction in ["long", "short"] and sr_zones:
        # For long, look for support zones with Bounce, for short, resistance with Break
        if entry_direction == "long":
            candidates = [z for z in sr_zones if z["zone_state"] == "Active" and z["bias_suggestion"] == "Bounce" and not z["trap_risk"]]
        else:
            candidates = [z for z in sr_zones if z["zone_state"] == "Active" and z["bias_suggestion"] == "Break" and not z["trap_risk"]]
        if candidates:
            # Pick highest confidence
            best = max(candidates, key=lambda z: (z["confidence"] == "High", z["confidence"] == "Medium"))
            entry_zone = {"zone_level": best["zone_level"], "zone_type": best["zone_type"], "confidence": best["confidence"]}
            reasons.append(f"Entry zone: {best['zone_type']} at {best['zone_level']} with {best['confidence']} confidence.")
    # 7. If any zone has signal_disagreement or trap_risk, log it
    for z in sr_zones:
        if z.get("signal_disagreement") or z.get("trap_risk"):
            log_entry["conflicts"].append({"type": "zone_conflict", "zone": z})
    # --- trade_type logic ---
    if entry_direction == "long" and market_style and "Trending" in market_style:
        trade_type = "trend_follow"
    elif entry_direction == "short" and market_style and "Trending" in market_style:
        trade_type = "trend_follow"
    elif entry_direction in ["long", "short"] and market_style and "Range" in market_style:
        trade_type = "fade"
    elif entry_direction in ["long", "short"] and market_style and "Volatile" in market_style:
        trade_type = "breakout"
    # --- score weighting ---
    # reversal=40%, trap=30%, bias=20%, sr=10%
    reversal_score = reversal["reversal_probability"] if reversal and "reversal_probability" in reversal else 0
    trap_score = max(trap_call.get("deception_score", 0), trap_put.get("deception_score", 0)) / 100 if trap_call or trap_put else 0
    bias_score = 1.0 if (bias_dir == "Bullish" and entry_direction == "long") or (bias_dir == "Bearish" and entry_direction == "short") else 0.5 if bias_dir else 0
    sr_score = 0
    if entry_zone and "confidence" in entry_zone:
        sr_score = 1.0 if entry_zone["confidence"] == "High" else 0.7 if entry_zone["confidence"] == "Medium" else 0.4
    entry_score = 0.4 * reversal_score + 0.3 * (1 - trap_score) + 0.2 * bias_score + 0.1 * sr_score
    # --- time-decay logic ---
    # If any module's most recent signal is older than 5 min, reduce confidence and entry_score
    latest_times = []
    for mod in [bias, style, reversal, trap, sr]:
        if mod and isinstance(mod, dict) and "timestamp" in mod:
            try:
                t = parser.parse(mod["timestamp"]) if isinstance(mod["timestamp"], str) else mod["timestamp"]
                latest_times.append(t)
            except Exception:
                continue
    if latest_times:
        most_recent = max(latest_times)
        if (now - most_recent).total_seconds() > 300:
            # Reduce confidence by one level and entry_score by 0.2
            if confidence == "high":
                confidence = "medium"
            elif confidence == "medium":
                confidence = "low"
            entry_score = max(0, entry_score - 0.2)
            reasons.append("Signal is older than 5 minutes, confidence and score reduced.")
    # --- set confidence from entry_score ---
    if entry_score >= 0.8:
        confidence = "high"
    elif entry_score >= 0.6:
        confidence = "medium"
    else:
        confidence = "low"
    reason = " ".join(reasons)
    log_entry["final_decision"] = {"entry_direction": entry_direction, "entry_zone": entry_zone, "confidence": confidence, "reason": reason, "must_avoid": must_avoid, "trade_type": trade_type, "entry_score": round(entry_score, 2)}
    entry_engine_log_col.insert_one(log_entry)
    db["entry_logic_snapshots"].insert_one({
        **log_entry["final_decision"],
        "user": user,
        "expiry": expiry,
        "timestamp": datetime.utcnow(),
        "trigger": "entry_decision"
    })
    # ML inference
    ml_features = [
        entry_direction, trade_type, entry_score, confidence, must_avoid,
        entry_zone["zone_type"] if entry_zone else None,
        entry_zone["confidence"] if entry_zone else None,
        entry_zone["zone_level"] if entry_zone else None
    ]
    try:
        ml_result = predict_entry_logic(ml_features)
        ml_pred = ml_result['predicted']
        ml_probs = ml_result['probabilities']
        ml_conf = ml_result['confidence']
    except Exception as e:
        ml_pred = None
        ml_probs = None
        ml_conf = str(e)
    return {
        "entry_direction": entry_direction,
        "entry_zone": entry_zone,
        "confidence": confidence,
        "reason": reason,
        "must_avoid": must_avoid,
        "trade_type": trade_type,
        "entry_score": round(entry_score, 2),
        "ml_predicted_entry": ml_pred,
        "ml_probabilities": ml_probs,
        "ml_confidence": ml_conf,
        "raw_signals": log_entry["raw_signals"],
        "rejections": log_entry["rejections"],
        "conflicts": log_entry["conflicts"]
    } 

@app.post("/clear-analytics")
def clear_analytics(user: str, expiry: str):
    # Remove analytics/calculated data for this user/expiry
    # Do NOT remove option chain data or tokens
    # Remove analytics from relevant collections
    db["otm_baseline_snapshots"].delete_many({"user": user, "expiry": expiry})
    db["otm_difference_snapshots"].delete_many({"user": user, "expiry": expiry})
    db["otm_percentage_change_snapshots"].delete_many({"user": user, "expiry": expiry})
    db["market_style_snapshots"].delete_many({"user": user, "expiry": expiry})
    db["reversal_probability_snapshots"].delete_many({"user": user, "expiry": expiry})
    db["trap_detector_snapshots"].delete_many({"user": user, "expiry": expiry})
    db["support_resistance_snapshots"].delete_many({"user": user, "expiry": expiry})
    db["entry_logic_snapshots"].delete_many({"user": user, "expiry": expiry})
    # You can add more collections here if needed
    return {"success": True, "message": "Analytics/calculated data cleared for user/expiry."} 

# Serve React build as static files
frontend_build_path = os.path.join(os.path.dirname(__file__), '../../frontend/build')
app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static") 