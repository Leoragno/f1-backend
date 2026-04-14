from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fastf1
import pandas as pd
from datetime import datetime
import os
import numpy as np

app = FastAPI(title="F1 Data API - Complete", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache per Render
cache_dir = '/tmp/fastf1_cache'
os.makedirs(cache_dir, exist_ok=True)
fastf1.Cache.enable_cache(cache_dir)

# Mappa codici piloti
DRIVER_CODES = {
    'VER': 'Max Verstappen', 'PER': 'Sergio Perez', 'HAM': 'Lewis Hamilton',
    'RUS': 'George Russell', 'LEC': 'Charles Leclerc', 'SAI': 'Carlos Sainz',
    'NOR': 'Lando Norris', 'PIA': 'Oscar Piastri', 'ALO': 'Fernando Alonso',
    'STR': 'Lance Stroll', 'GAS': 'Pierre Gasly', 'OCO': 'Esteban Ocon',
    'TSU': 'Yuki Tsunoda', 'RIC': 'Daniel Ricciardo', 'MAG': 'Kevin Magnussen',
    'HUL': 'Nico Hulkenberg', 'BOT': 'Valtteri Bottas', 'ZHO': 'Guanyu Zhou',
    'ALB': 'Alexander Albon', 'SAR': 'Logan Sargeant', 'LAW': 'Liam Lawson',
    'BEA': 'Oliver Bearman', 'COL': 'Franco Colapinto'
}

# ==================== API BASE ====================

@app.get("/")
async def root():
    return {"status": "online", "service": "F1 Data API - Complete", "endpoints": "/docs"}

@app.get("/api/seasons")
async def get_seasons():
    """Lista stagioni disponibili (2018-oggi)"""
    return {"seasons": list(range(2018, datetime.now().year + 1))}

# ==================== GP E GARE ====================

@app.get("/api/races/{year}")
async def get_races(year: int):
    """Lista tutti i GP di una stagione"""
    try:
        schedule = fastf1.get_event_schedule(year)
        races = schedule[['RoundNumber', 'EventName', 'Country', 'Location', 'EventDate']]
        return JSONResponse(races.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/race-results/{year}/{round}")
async def get_race_results(year: int, round: int):
    """Risultati completi gara"""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        results = session.results[['FullName', 'Position', 'Points', 'TeamName', 'Time']]
        results['Position'] = results['Position'].astype(str)
        results['Time'] = results['Time'].astype(str)
        
        return JSONResponse(results.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"GP non trovato: {str(e)}")

@app.get("/api/qualifying/{year}/{round}")
async def get_qualifying(year: int, round: int):
    """Risultati qualifiche (Q1, Q2, Q3)"""
    try:
        session = fastf1.get_session(year, round, 'Q')
        session.load()
        
        quali = session.results[['FullName', 'Position', 'Q1', 'Q2', 'Q3', 'TeamName']]
        quali['Position'] = quali['Position'].astype(str)
        
        return JSONResponse(quali.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Qualifiche non trovate: {str(e)}")

@app.get("/api/sprint/{year}/{round}")
async def get_sprint(year: int, round: int):
    """Risultati Sprint (se presente)"""
    try:
        session = fastf1.get_session(year, round, 'S')
        session.load()
        
        sprint = session.results[['FullName', 'Position', 'Points', 'TeamName']]
        sprint['Position'] = sprint['Position'].astype(str)
        
        return JSONResponse(sprint.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Sprint non disponibile: {str(e)}")

# ==================== PILOTI E TEMPI ====================

@app.get("/api/drivers/{year}")
async def get_drivers(year: int):
    """Lista piloti di una stagione"""
    try:
        schedule = fastf1.get_event_schedule(year)
        first_race = fastf1.get_session(year, 1, 'R')
        first_race.load()
        
        drivers = first_race.results[['FullName', 'TeamName', 'Abbreviation']].drop_duplicates()
        return JSONResponse(drivers.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/laptimes/{year}/{round}/{driver}")
async def get_laptimes(year: int, round: int, driver: str):
    """Tutti i tempi giro di un pilota"""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        laps = session.laps.pick_driver(driver)
        
        if laps.empty:
            raise HTTPException(404, f"Pilota {driver} non trovato")
        
        laps_data = laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time', 'Compound']].dropna()
        
        # Converti tempi in secondi
        if not laps_data.empty and 'LapTime' in laps_data.columns:
            laps_data['LapTime_seconds'] = laps_data['LapTime'].dt.total_seconds()
            laps_data['Sector1_seconds'] = laps_data['Sector1Time'].dt.total_seconds()
            laps_data['Sector2_seconds'] = laps_data['Sector2Time'].dt.total_seconds()
            laps_data['Sector3_seconds'] = laps_data['Sector3Time'].dt.total_seconds()
        
        result = {
            "driver": driver,
            "driver_name": DRIVER_CODES.get(driver.upper(), driver),
            "total_laps": len(laps_data),
            "best_lap": float(laps_data['LapTime_seconds'].min()) if not laps_data.empty else None,
            "laps": laps_data.to_dict(orient='records')
        }
        
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/best-lap/{year}/{round}")
async def get_best_lap(year: int, round: int):
    """Giro più veloce della gara"""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        fastest = session.laps.pick_fastest()
        
        return {
            "driver": fastest['Driver'],
            "driver_name": DRIVER_CODES.get(fastest['Driver'], fastest['Driver']),
            "lap_number": int(fastest['LapNumber']),
            "lap_time_seconds": float(fastest['LapTime'].total_seconds()),
            "lap_time_str": str(fastest['LapTime']),
            "compound": fastest['Compound']
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== TELEMETRIA ====================

@app.get("/api/telemetry/{year}/{round}/{driver}/{lap_number}")
async def get_telemetry(year: int, round: int, driver: str, lap_number: int):
    """Telemetria completa di un giro (velocità, gas, freno, marcia, RPM)"""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        lap = session.laps.pick_driver(driver).pick_lap(lap_number)
        if lap.empty:
            raise HTTPException(404, "Giro non trovato")
        
        telemetry = lap.get_car_data()
        
        # Campiona i dati per ridurre la dimensione (max 500 punti)
        step = max(1, len(telemetry) // 500)
        telemetry_sampled = telemetry.iloc[::step]
        
        data = {
            "driver": driver,
            "lap_number": lap_number,
            "distance": telemetry_sampled['Distance'].tolist(),
            "speed": telemetry_sampled['Speed'].tolist(),
            "throttle": telemetry_sampled['Throttle'].tolist(),
            "brake": telemetry_sampled['Brake'].tolist(),
            "gear": telemetry_sampled['nGear'].tolist(),
            "rpm": telemetry_sampled['RPM'].tolist()
        }
        
        return JSONResponse(data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/gps/{year}/{round}/{driver}/{lap_number}")
async def get_gps_position(year: int, round: int, driver: str, lap_number: int):
    """Posizione GPS del giro (per mappa tracciato)"""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        lap = session.laps.pick_driver(driver).pick_lap(lap_number)
        if lap.empty:
            raise HTTPException(404, "Giro non trovato")
        
        telemetry = lap.get_telemetry()
        
        # Campiona i dati
        step = max(1, len(telemetry) // 500)
        telemetry_sampled = telemetry.iloc[::step]
        
        data = {
            "driver": driver,
            "lap_number": lap_number,
            "x": telemetry_sampled['X'].tolist(),
            "y": telemetry_sampled['Y'].tolist(),
            "speed": telemetry_sampled['Speed'].tolist()
        }
        
        return JSONResponse(data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== CONFRONTI ====================

@app.get("/api/compare/{year}/{round}/{driver1}/{driver2}")
async def compare_drivers(year: int, round: int, driver1: str, driver2: str):
    """Confronto diretto tra due piloti"""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        laps1 = session.laps.pick_driver(driver1)
        laps2 = session.laps.pick_driver(driver2)
        
        if laps1.empty or laps2.empty:
            raise HTTPException(404, "Uno o entrambi i piloti non trovati")
        
        # Tempi migliori
        best1 = laps1['LapTime'].min().total_seconds()
        best2 = laps2['LapTime'].min().total_seconds()
        
        # Tempi medi
        avg1 = laps1['LapTime'].dropna().apply(lambda x: x.total_seconds()).mean()
        avg2 = laps2['LapTime'].dropna().apply(lambda x: x.total_seconds()).mean()
        
        # Consistenza (deviazione standard)
        std1 = laps1['LapTime'].dropna().apply(lambda x: x.total_seconds()).std()
        std2 = laps2['LapTime'].dropna().apply(lambda x: x.total_seconds()).std()
        
        return {
            "driver1": {"code": driver1, "name": DRIVER_CODES.get(driver1.upper(), driver1)},
            "driver2": {"code": driver2, "name": DRIVER_CODES.get(driver2.upper(), driver2)},
            "best_lap": {
                driver1: round(best1, 3),
                driver2: round(best2, 3),
                "difference": round(abs(best1 - best2), 3)
            },
            "avg_lap": {
                driver1: round(avg1, 3),
                driver2: round(avg2, 3)
            },
            "consistency": {
                driver1: round(std1, 3),
                driver2: round(std2, 3)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== PIT STOP ====================

@app.get("/api/pitstops/{year}/{round}/{driver}")
async def get_pitstops(year: int, round: int, driver: str):
    """Tutti i pit stop di un pilota"""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        laps = session.laps.pick_driver(driver)
        pit_stops = laps[laps['PitInTime'].notna()]
        
        if pit_stops.empty:
            return {"driver": driver, "pitstops": []}
        
        stops = []
        for _, lap in pit_stops.iterrows():
            stops.append({
                "lap_number": int(lap['LapNumber']),
                "lap_time": str(lap['LapTime']),
                "pit_in_time": str(lap['PitInTime']),
                "pit_out_time": str(lap['PitOutTime']),
                "compound": lap['Compound']
            })
        
        return {
            "driver": driver,
            "driver_name": DRIVER_CODES.get(driver.upper(), driver),
            "total_pitstops": len(stops),
            "pitstops": stops
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== STATISTICHE ====================

@app.get("/api/driver-stats/{year}/{driver}")
async def get_driver_stats(year: int, driver: str):
    """Statistiche complete di un pilota per tutta la stagione"""
    try:
        schedule = fastf1.get_event_schedule(year)
        stats = []
        
        for _, event in schedule.iterrows():
            round_num = event['RoundNumber']
            try:
                session = fastf1.get_session(year, round_num, 'R')
                session.load()
                
                driver_data = session.results[session.results['Abbreviation'] == driver.upper()]
                if not driver_data.empty:
                    stats.append({
                        "round": int(round_num),
                        "event": event['EventName'],
                        "position": int(driver_data['Position'].iloc[0]),
                        "points": float(driver_data['Points'].iloc[0])
                    })
            except:
                continue
        
        return {
            "driver": driver.upper(),
            "year": year,
            "races_completed": len(stats),
            "total_points": sum(s['points'] for s in stats),
            "results": stats
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== UTILITY ====================

@app.get("/api/drivers-list")
async def get_drivers_list():
    """Lista completa codici piloti"""
    return {"drivers": DRIVER_CODES}

@app.get("/api/available-years")
async def get_available_years():
    """Anni per cui FastF1 ha dati"""
    current_year = datetime.now().year
    return {"years": list(range(2018, current_year + 1))}