from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fastf1
import pandas as pd
from datetime import datetime
import os
import numpy as np
from fastf1.ergast import Ergast

app = FastAPI(title="F1 Data API - Complete", version="3.0")

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

# Inizializza Ergast per dati storici
ergast = Ergast()

# Mappa completa piloti
DRIVER_CODES = {
    'VER': 'Max Verstappen', 'PER': 'Sergio Perez', 'HAM': 'Lewis Hamilton',
    'RUS': 'George Russell', 'LEC': 'Charles Leclerc', 'SAI': 'Carlos Sainz',
    'NOR': 'Lando Norris', 'PIA': 'Oscar Piastri', 'ALO': 'Fernando Alonso',
    'STR': 'Lance Stroll', 'GAS': 'Pierre Gasly', 'OCO': 'Esteban Ocon',
    'TSU': 'Yuki Tsunoda', 'RIC': 'Daniel Ricciardo', 'MAG': 'Kevin Magnussen',
    'HUL': 'Nico Hulkenberg', 'BOT': 'Valtteri Bottas', 'ZHO': 'Guanyu Zhou',
    'ALB': 'Alexander Albon', 'SAR': 'Logan Sargeant', 'LAW': 'Liam Lawson',
    'BEA': 'Oliver Bearman', 'COL': 'Franco Colapinto', 'VET': 'Sebastian Vettel',
    'RAI': 'Kimi Raikkonen', 'BUT': 'Jenson Button', 'MAS': 'Felipe Massa',
    'ALO': 'Fernando Alonso', 'WEB': 'Mark Webber', 'ROS': 'Nico Rosberg',
    'BOT': 'Valtteri Bottas', 'RIC': 'Daniel Ricciardo', 'KVY': 'Daniil Kvyat'
}

# ==================== API BASE ====================

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "F1 Data API - Complete",
        "version": "3.0",
        "endpoints": "/docs",
        "data_coverage": "1950-present"
    }

@app.get("/api/seasons")
async def get_seasons():
    """Stagioni disponibili (1950-oggi)"""
    current_year = datetime.now().year
    return {"seasons": list(range(1950, current_year + 1))}

@app.get("/api/available-years")
async def get_available_years():
    """Anni per cui FastF1 ha dati"""
    current_year = datetime.now().year
    return {
        "modern_era": list(range(2018, current_year + 1)),  # Timing/Telemetria
        "historical": list(range(1950, 2018))  # Solo risultati
    }

# ==================== DATI STORICI (1950-2017) ====================

@app.get("/api/historical/races/{year}")
async def get_historical_races(year: int):
    """Lista GP di una stagione storica (1950-2017)"""
    try:
        schedule = ergast.get_race_schedule(year)
        if schedule.empty:
            raise HTTPException(404, f"Nessun dato per il {year}")
        
        races = []
        for _, race in schedule.iterrows():
            races.append({
                "round": int(race['round']),
                "name": race['raceName'],
                "circuit": race['circuitName'],
                "date": race['date'],
                "country": race.get('country', 'Unknown')
            })
        return JSONResponse(races)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/historical/results/{year}/{round}")
async def get_historical_results(year: int, round: int):
    """Risultati gara storica (1950-2017)"""
    try:
        results = ergast.get_race_results(year, round)
        if results.empty:
            raise HTTPException(404, f"Nessun risultato per GP {year} round {round}")
        
        race_results = []
        for _, result in results.iterrows():
            race_results.append({
                "position": int(result['position']) if pd.notna(result['position']) else None,
                "driver": f"{result['givenName']} {result['familyName']}",
                "constructor": result['constructorName'],
                "points": float(result['points']),
                "time": result.get('time', 'N/A'),
                "status": result['status']
            })
        return JSONResponse(race_results)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/historical/qualifying/{year}/{round}")
async def get_historical_qualifying(year: int, round: int):
    """Qualifiche storiche (1950-2017)"""
    try:
        quali = ergast.get_qualifying_results(year, round)
        if quali.empty:
            raise HTTPException(404, f"Nessuna qualifica per GP {year} round {round}")
        
        qualifying_results = []
        for _, result in quali.iterrows():
            qualifying_results.append({
                "position": int(result['position']),
                "driver": f"{result['givenName']} {result['familyName']}",
                "constructor": result['constructorName'],
                "q1": result.get('q1', 'N/A'),
                "q2": result.get('q2', 'N/A'),
                "q3": result.get('q3', 'N/A')
            })
        return JSONResponse(qualifying_results)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/historical/drivers-championship/{year}")
async def get_historical_drivers_championship(year: int):
    """Classifica piloti stagione storica"""
    try:
        standings = ergast.get_driver_standings(year)
        if standings.empty:
            raise HTTPException(404, f"Nessuna classifica per {year}")
        
        championship = []
        for _, driver in standings.iterrows():
            championship.append({
                "position": int(driver['position']),
                "driver": f"{driver['givenName']} {driver['familyName']}",
                "constructor": driver['constructorName'],
                "points": float(driver['points']),
                "wins": int(driver['wins'])
            })
        return JSONResponse(championship)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/historical/constructors-championship/{year}")
async def get_historical_constructors_championship(year: int):
    """Classifica costruttori stagione storica"""
    try:
        standings = ergast.get_constructor_standings(year)
        if standings.empty:
            raise HTTPException(404, f"Nessuna classifica per {year}")
        
        championship = []
        for _, constructor in standings.iterrows():
            championship.append({
                "position": int(constructor['position']),
                "constructor": constructor['constructorName'],
                "points": float(constructor['points']),
                "wins": int(constructor['wins'])
            })
        return JSONResponse(championship)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== GP E GARE (MODERNE 2018+) ====================

@app.get("/api/races/{year}")
async def get_races(year: int):
    """Lista tutti i GP di una stagione"""
    try:
        if year < 2018:
            return await get_historical_races(year)
        
        schedule = fastf1.get_event_schedule(year)
        races = schedule[['RoundNumber', 'EventName', 'Country', 'Location', 'EventDate']]
        return JSONResponse(races.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/race-results/{year}/{round}")
async def get_race_results(year: int, round: int):
    """Risultati completi gara"""
    try:
        if year < 2018:
            return await get_historical_results(year, round)
        
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
        if year < 2018:
            return await get_historical_qualifying(year, round)
        
        session = fastf1.get_session(year, round, 'Q')
        session.load()
        
        quali = session.results[['FullName', 'Position', 'Q1', 'Q2', 'Q3', 'TeamName']]
        quali['Position'] = quali['Position'].astype(str)
        
        return JSONResponse(quali.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Qualifiche non trovate: {str(e)}")

@app.get("/api/sprint/{year}/{round}")
async def get_sprint(year: int, round: int):
    """Risultati Sprint (se presente, solo 2021+)"""
    try:
        if year < 2021:
            return {"message": "Sprint introdotte nel 2021"}
        
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
        if year < 2018:
            results = ergast.get_driver_standings(year)
            if results.empty:
                raise HTTPException(404, f"Nessun pilota per {year}")
            
            drivers = []
            for _, driver in results.iterrows():
                drivers.append({
                    "FullName": f"{driver['givenName']} {driver['familyName']}",
                    "Abbreviation": driver.get('code', driver['familyName'][:3].upper())
                })
            return JSONResponse(drivers)
        
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
        if year < 2018:
            return {"message": "Dati telemetria disponibili solo dal 2018", "driver": driver}
        
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        laps = session.laps.pick_driver(driver)
        
        if laps.empty:
            raise HTTPException(404, f"Pilota {driver} non trovato")
        
        laps_data = laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time', 'Compound']].dropna()
        
        if not laps_data.empty and 'LapTime' in laps_data.columns:
            laps_data['LapTime_seconds'] = laps_data['LapTime'].dt.total_seconds()
        
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
        if year < 2018:
            return {"message": "Dati telemetria disponibili solo dal 2018"}
        
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

# ==================== TELEMETRIA E MAPPE ====================

@app.get("/api/telemetry/{year}/{round}/{driver}/{lap_number}")
async def get_telemetry(year: int, round: int, driver: str, lap_number: int):
    """Telemetria completa di un giro"""
    try:
        if year < 2018:
            return {"message": "Telemetria disponibile solo dal 2018"}
        
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        lap = session.laps.pick_driver(driver).pick_lap(lap_number)
        if lap.empty:
            raise HTTPException(404, "Giro non trovato")
        
        telemetry = lap.get_car_data()
        
        # Campiona i dati per ridurre la dimensione
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
        if year < 2018:
            return {"message": "Dati GPS disponibili solo dal 2018"}
        
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        lap = session.laps.pick_driver(driver).pick_lap(lap_number)
        if lap.empty:
            raise HTTPException(404, "Giro non trovato")
        
        telemetry = lap.get_telemetry()
        
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

@app.get("/api/track-map/{year}/{round}")
async def get_track_map(year: int, round: int):
    """Coordinate del tracciato per mappa"""
    try:
        if year < 2018:
            return {"message": "Mappa tracciato disponibile solo dal 2018"}
        
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        circuit_info = session.get_circuit_info()
        
        # Ottieni le coordinate del tracciato da un giro di riferimento
        reference_lap = session.laps.pick_fastest()
        telemetry = reference_lap.get_telemetry()
        
        data = {
            "circuit_name": circuit_info['CircuitName'],
            "country": circuit_info['Country'],
            "x": telemetry['X'].tolist(),
            "y": telemetry['Y'].tolist()
        }
        
        return JSONResponse(data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== CONFRONTI ====================

@app.get("/api/compare/{year}/{round}/{driver1}/{driver2}")
async def compare_drivers(year: int, round: int, driver1: str, driver2: str):
    """Confronto diretto tra due piloti"""
    try:
        if year < 2018:
            return {"message": "Confronto dettagliato disponibile solo dal 2018"}
        
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        laps1 = session.laps.pick_driver(driver1)
        laps2 = session.laps.pick_driver(driver2)
        
        if laps1.empty or laps2.empty:
            raise HTTPException(404, "Uno o entrambi i piloti non trovati")
        
        best1 = laps1['LapTime'].min().total_seconds()
        best2 = laps2['LapTime'].min().total_seconds()
        avg1 = laps1['LapTime'].dropna().apply(lambda x: x.total_seconds()).mean()
        avg2 = laps2['LapTime'].dropna().apply(lambda x: x.total_seconds()).mean()
        std1 = laps1['LapTime'].dropna().apply(lambda x: x.total_seconds()).std()
        std2 = laps2['LapTime'].dropna().apply(lambda x: x.total_seconds()).std()
        
        return {
            "driver1": {"code": driver1, "name": DRIVER_CODES.get(driver1.upper(), driver1)},
            "driver2": {"code": driver2, "name": DRIVER_CODES.get(driver2.upper(), driver2)},
            "best_lap": {driver1: round(best1, 3), driver2: round(best2, 3), "difference": round(abs(best1 - best2), 3)},
            "avg_lap": {driver1: round(avg1, 3), driver2: round(avg2, 3)},
            "consistency": {driver1: round(std1, 3), driver2: round(std2, 3)}
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== PIT STOP ====================

@app.get("/api/pitstops/{year}/{round}/{driver}")
async def get_pitstops(year: int, round: int, driver: str):
    """Tutti i pit stop di un pilota"""
    try:
        if year < 2018:
            return {"message": "Dati pit stop dettagliati disponibili solo dal 2018"}
        
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
        if year < 2018:
            results = ergast.get_driver_standings(year)
            driver_data = results[results['driverCode'] == driver.upper()]
            if driver_data.empty:
                raise HTTPException(404, f"Pilota {driver} non trovato")
            
            return {
                "driver": driver.upper(),
                "year": year,
                "position": int(driver_data['position'].iloc[0]),
                "points": float(driver_data['points'].iloc[0]),
                "wins": int(driver_data['wins'].iloc[0])
            }
        
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

@app.get("/api/drivers-list")
async def get_drivers_list():
    """Lista completa codici piloti"""
    return {"drivers": DRIVER_CODES}

# ==================== COSTRUTTORI ====================

@app.get("/api/constructors/{year}")
async def get_constructors(year: int):
    """Lista tutti i costruttori di una stagione"""
    try:
        if year < 2018:
            standings = ergast.get_constructor_standings(year)
            if standings.empty:
                raise HTTPException(404, f"Nessun costruttore per {year}")
            
            constructors = []
            for _, constructor in standings.iterrows():
                constructors.append({"TeamName": constructor['constructorName']})
            return JSONResponse(constructors)
        
        first_race = fastf1.get_session(year, 1, 'R')
        first_race.load()
        
        constructors = first_race.results[['TeamName']].drop_duplicates()
        return JSONResponse(constructors.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/constructor-standings/{year}/{round}")
async def get_constructor_standings(year: int, round: int):
    """Classifica costruttori dopo un GP"""
    try:
        if year < 2018:
            standings = ergast.get_constructor_standings(year)
            if standings.empty:
                raise HTTPException(404, f"Nessuna classifica per {year}")
            
            championship = []
            for _, constructor in standings.iterrows():
                championship.append({
                    "position": int(constructor['position']),
                    "constructor": constructor['constructorName'],
                    "points": float(constructor['points'])
                })
            return JSONResponse(championship)
        
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        standings = session.results.groupby('TeamName')['Points'].sum().reset_index()
        standings = standings.sort_values('Points', ascending=False)
        standings['Position'] = range(1, len(standings) + 1)
        
        return JSONResponse(standings.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/constructor-results/{year}/{round}/{constructor}")
async def get_constructor_results(year: int, round: int, constructor: str):
    """Risultati di un costruttore in un GP"""
    try:
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        team_results = session.results[session.results['TeamName'].str.contains(constructor, case=False)]
        
        if team_results.empty:
            raise HTTPException(404, f"Costruttore {constructor} non trovato")
        
        results = team_results[['FullName', 'Position', 'Points', 'Time']]
        results['Position'] = results['Position'].astype(str)
        
        return JSONResponse(results.to_dict(orient='records'))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/constructor-stats/{year}/{constructor}")
async def get_constructor_stats(year: int, constructor: str):
    """Statistiche complete di un costruttore per tutta la stagione"""
    try:
        schedule = fastf1.get_event_schedule(year)
        stats = []
        total_points = 0
        wins = 0
        podiums = 0
        
        for _, event in schedule.iterrows():
            round_num = event['RoundNumber']
            try:
                session = fastf1.get_session(year, round_num, 'R')
                session.load()
                
                team_data = session.results[session.results['TeamName'].str.contains(constructor, case=False)]
                
                if not team_data.empty:
                    race_points = team_data['Points'].sum()
                    total_points += race_points
                    
                    positions = team_data['Position'].astype(str)
                    if '1' in positions.values:
                        wins += 1
                    if any(pos in ['1', '2', '3'] for pos in positions.values):
                        podiums += 1
                    
                    stats.append({
                        "round": int(round_num),
                        "event": event['EventName'],
                        "points": float(race_points),
                        "drivers": team_data['FullName'].tolist(),
                        "best_position": int(team_data['Position'].min())
                    })
            except:
                continue
        
        return {
            "constructor": constructor,
            "year": year,
            "races_competed": len(stats),
            "total_points": total_points,
            "wins": wins,
            "podiums": podiums,
            "results": stats
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/constructor-head-to-head/{year}/{constructor1}/{constructor2}")
async def constructor_head_to_head(year: int, constructor1: str, constructor2: str):
    """Confronto diretto tra due costruttori"""
    try:
        schedule = fastf1.get_event_schedule(year)
        comparison = []
        points1_total = 0
        points2_total = 0
        wins1 = 0
        wins2 = 0
        
        for _, event in schedule.iterrows():
            round_num = event['RoundNumber']
            try:
                session = fastf1.get_session(year, round_num, 'R')
                session.load()
                
                team1 = session.results[session.results['TeamName'].str.contains(constructor1, case=False)]
                team2 = session.results[session.results['TeamName'].str.contains(constructor2, case=False)]
                
                if not team1.empty and not team2.empty:
                    pts1 = team1['Points'].sum()
                    pts2 = team2['Points'].sum()
                    points1_total += pts1
                    points2_total += pts2
                    
                    if pts1 > pts2:
                        wins1 += 1
                    elif pts2 > pts1:
                        wins2 += 1
                    
                    comparison.append({
                        "round": int(round_num),
                        "event": event['EventName'],
                        f"{constructor1}_points": float(pts1),
                        f"{constructor2}_points": float(pts2),
                        "winner": constructor1 if pts1 > pts2 else constructor2 if pts2 > pts1 else "draw"
                    })
            except:
                continue
        
        return {
            "year": year,
            "constructor1": constructor1,
            "constructor2": constructor2,
            "total_points": {constructor1: points1_total, constructor2: points2_total},
            "wins": {constructor1: wins1, constructor2: wins2},
            "races_compared": len(comparison),
            "comparison": comparison
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/constructor-season-progress/{year}/{constructor}")
async def constructor_season_progress(year: int, constructor: str):
    """Evoluzione punti del costruttore durante la stagione"""
    try:
        schedule = fastf1.get_event_schedule(year)
        progress = []
        cumulative_points = 0
        
        for _, event in schedule.iterrows():
            round_num = event['RoundNumber']
            try:
                session = fastf1.get_session(year, round_num, 'R')
                session.load()
                
                team_data = session.results[session.results['TeamName'].str.contains(constructor, case=False)]
                
                if not team_data.empty:
                    race_points = team_data['Points'].sum()
                    cumulative_points += race_points
                    
                    progress.append({
                        "round": int(round_num),
                        "event": event['EventName'],
                        "points_this_race": float(race_points),
                        "cumulative_points": cumulative_points
                    })
            except:
                continue
        
        return {
            "constructor": constructor,
            "year": year,
            "progress": progress,
            "final_points": cumulative_points
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== CIRCUITI ====================

@app.get("/api/circuits/{year}")
async def get_circuits(year: int):
    """Lista circuiti di una stagione"""
    try:
        schedule = fastf1.get_event_schedule(year)
        circuits = []
        
        for _, event in schedule.iterrows():
            circuits.append({
                "round": int(event['RoundNumber']),
                "name": event['EventName'],
                "location": f"{event['Location']}, {event['Country']}",
                "date": event['EventDate']
            })
        
        return JSONResponse(circuits)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ==================== UTILITY ====================

@app.get("/api/weather/{year}/{round}")
async def get_weather(year: int, round: int):
    """Dati meteo della gara (se disponibili)"""
    try:
        if year < 2018:
            return {"message": "Dati meteo disponibili solo dal 2018"}
        
        session = fastf1.get_session(year, round, 'R')
        session.load()
        
        if hasattr(session, 'weather_data') and session.weather_data is not None:
            weather = session.weather_data[['Time', 'AirTemp', 'TrackTemp', 'Humidity']]
            return JSONResponse(weather.to_dict(orient='records'))
        else:
            return {"message": "Dati meteo non disponibili per questa sessione"}
    except Exception as e:
        return {"message": f"Dati meteo non disponibili: {str(e)}"}