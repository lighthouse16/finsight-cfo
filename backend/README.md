# FinSight CFO Backend

Initial backend skeleton.

## Setup

Use Windows PowerShell commands to setup the backend locally:

```powershell
cd D:\projects\finsight-cfo\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

## Testing

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/market-watch/rates-liquidity"
```
