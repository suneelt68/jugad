import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
import pandas as pd
from jugaad_data.nse import index_raw

app = FastAPI(
    title="NSE Index Data REST API",
    description="Fetch historical NSE index data dynamically by date."
)

@app.get("/")
def home():
    return {"status": "active", "message": "NSE Index API is running. Go to /docs to test endpoints."}


@app.get("/api/index-data")
def get_index_data(
    date: str = Query(
        ..., 
        description="Target date in YYYY-MM-DD format (e.g., 2026-10-01)", 
        example="2026-10-01"
    ),
    to_date: Optional[str] = Query(
        None, 
        description="Optional end date for date ranges in YYYY-MM-DD format. Defaults to 'date'."
    ),
    symbol: str = Query(
        "NIFTY 50", 
        description="NSE Index symbol (e.g., NIFTY 50, NIFTY BANK, NIFTY IT)"
    )
):
    try:
        # Parse mandatory start date
        start_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        
        # Parse optional end date or default to single-day lookup
        if to_date:
            end_date = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
        else:
            end_date = start_date

        # Fetch raw historical data from NSE using jugaad-data
        raw_data = index_raw(symbol=symbol, from_date=start_date, to_date=end_date)
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(raw_data)

        if df.empty:
            return {
                "status": "success",
                "symbol": symbol,
                "from_date": str(start_date),
                "to_date": str(end_date),
                "count": 0,
                "data": [],
                "message": "No data available. The date might be a trading holiday, weekend, or in the future."
            }

        # Data formatting & cleanup
        if 'HistoricalDate' in df.columns:
            df['HistoricalDate'] = pd.to_datetime(df['HistoricalDate']).dt.strftime('%Y-%m-%d')
        
        if 'CLOSE' in df.columns:
            df['CLOSE'] = df['CLOSE'].astype(float)
            
        df = df.sort_values('HistoricalDate').reset_index(drop=True)

        # Fix NaN values to prevent JSON serialization crash
        clean_records = df.where(pd.notnull(df), None).to_dict(orient="records")

        return {
            "status": "success",
            "symbol": symbol,
            "from_date": str(start_date),
            "to_date": str(end_date),
            "count": len(clean_records),
            "data": clean_records
        }

    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date format. Please use YYYY-MM-DD (e.g., 2026-10-01)."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching data from NSE: {str(e)}"
        )
