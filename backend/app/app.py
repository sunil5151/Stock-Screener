import pandas as pd
from fastapi import FastAPI, Request, Response, Form, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import numpy as np 
from dotenv import load_dotenv
from io import StringIO

from .user_storage import register_user, validate_user, get_user_data
# Import your existing trading logic
from .main import TradingSystem
from .technical_indicators import EnhancedSRDetector
from .data_processor import DataProcessor
from .technical_indicators import TechnicalIndicators
from .signal_generator import SignalGenerator
from .backtester import Backtester
from .chart_builder import ChartBuilder
from .signal_table import SignalTable
from starlette.middleware.sessions import SessionMiddleware
# Add these imports at the top
from .history_storage import (
    add_history_entry, update_history_entry, load_user_history,
    get_history_entry, delete_history_entry
)
import datetime
import uuid
# Add these imports at the top
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, BaseModel
from typing import List

# Email configuration
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@tradingapp.com")
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")

mail_config = ConnectionConfig(
    MAIL_USERNAME="your_email@gmail.com",
    MAIL_PASSWORD="your_app_password",
    MAIL_FROM="your_email@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,       # ✅ replaces MAIL_TLS
    MAIL_SSL_TLS=False,       # ✅ replaces MAIL_SSL
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key",  # Use your value from .env or hardcoded for now
    session_cookie="session"
)
# Load environment variables
load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Create uploads directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create charts directory
CHART_DIR = os.path.join(os.path.dirname(__file__), "charts")
os.makedirs(CHART_DIR, exist_ok=True)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_logged_in_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user

# Helper function to convert numpy types to Python native types
def convert_numpy_types(obj):
    """Recursively convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):  # Handle both numpy and Python booleans
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert arrays to lists
    else:
        return obj

# Basic health check route
@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "Trading Signals API is running"
    }

# Test route to ensure your trading modules are imported correctly
@app.get("/test-imports")
def test_imports():
    return {
        "status": "ok",
        "available_modules": [
            "TradingSystem",
            "DataProcessor",
            "TechnicalIndicators",
            "SignalGenerator",
            "Backtester",
            "ChartBuilder"
        ]
    }
# Register endpoint
@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    ok, msg = register_user(username, password)
    if ok:
        return {"success": True, "message": msg}
    else:
        return JSONResponse(status_code=400, content={"success": False, "message": msg})

# Login endpoint
@app.post("/login")
async def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    if validate_user(username, password):
        request.session["user"] = username
        return {"success": True, "message": "Login successful", "username": username}
    else:
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid username or password"})

# Logout endpoint
@app.post("/upload-csv")
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    user: str = Depends(get_logged_in_user)
):
    # Save uploaded CSV with the username as prefix
    filename = f"{user}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Add to user history
    upload_id = add_history_entry(user, file.filename, file_path)
    
    # Store uploaded file path and upload ID in session
    request.session["uploaded_csv"] = file_path
    request.session["current_upload_id"] = upload_id

    return {"success": True, "message": "File uploaded", "file_path": file_path, "upload_id": upload_id}

@app.post("/process-csv")
async def process_csv(request: Request, user: str = Depends(get_logged_in_user)):
    file_path = request.session.get("uploaded_csv")
    upload_id = request.session.get("current_upload_id")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No CSV file uploaded")

    trading_system = TradingSystem()
    try:
        # Run your pipeline (no charts shown, just results)
        results = trading_system.run_complete_analysis(
            file_path=file_path,
            lookahead_bars=5,
            confirmation_bars=7,
            ema_fast=9,
            ema_slow=15,
            big_candle_multiplier=2.5,
            big_candle_lookback=10,
            volume_multiplier=2.5,
            volume_lookback=10,
            show_chart=False,
        )
        
        # Use the helper function to convert all numpy types
        clean_results = convert_numpy_types(results)
        
        # Store results in session
        request.session["last_results"] = {
            "accuracy": clean_results["accuracy_results"],
            "signals": clean_results["signals"],
        }
        
        # Update history entry with results
        if upload_id:
            update_history_entry(user, upload_id, {
                "processed": True,
                "results": {
                    "accuracy": clean_results["accuracy_results"],
                    "signals_count": len(clean_results["signals"]),
                }
            })
            
            # Send email notification if user has email
            await send_completion_email(user, upload_id, clean_results)
        
        return {
            "success": True,
            "results": clean_results["accuracy_results"],
            "signals_count": len(clean_results["signals"]),
            "upload_id": upload_id
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"success": True, "message": "Logged out successfully"}

# Info endpoint
@app.get("/me")
async def me(request: Request):
    user = request.session.get("user")
    if user:
        return {"logged_in": True, "username": user}
    else:
        return {"logged_in": False}

# Helper function to get logged in user


# CSV Upload endpoint
@app.post("/upload-csv")
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    user: str = Depends(get_logged_in_user)
):
    # Save uploaded CSV with the username as prefix
    filename = f"{user}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Store uploaded file path in session
    request.session["uploaded_csv"] = file_path

    return {"success": True, "message": "File uploaded", "file_path": file_path}

# Process CSV endpoint
@app.post("/process-csv")
async def process_csv(request: Request, user: str = Depends(get_logged_in_user)):
    file_path = request.session.get("uploaded_csv")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No CSV file uploaded")

    trading_system = TradingSystem()
    try:
        # Run your pipeline (no charts shown, just results)
        results = trading_system.run_complete_analysis(
            file_path=file_path,
            lookahead_bars=5,
            confirmation_bars=7,
            ema_fast=9,
            ema_slow=15,
            big_candle_multiplier=2.5,
            big_candle_lookback=10,
            volume_multiplier=2.5,
            volume_lookback=10,
            show_chart=False,
        )
        
        # Use the helper function to convert all numpy types
        clean_results = convert_numpy_types(results)
        
        # Store results in session
        request.session["last_results"] = {
            "accuracy": clean_results["accuracy_results"],
            "signals": clean_results["signals"],
        }
        return {
            "success": True,
            "results": clean_results["accuracy_results"],
            "signals_count": len(clean_results["signals"]),
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

# Fetch results endpoint
@app.get("/results")
async def get_results(request: Request, user: str = Depends(get_logged_in_user)):
    results = request.session.get("last_results")
    if not results:
        raise HTTPException(status_code=404, detail="No results available. Please process a CSV first.")
    return results["accuracy"]

@app.get("/chart-html")
async def get_chart_html(
    request: Request, 
    user: str = Depends(get_logged_in_user),
    upload_id: str = None
):
    """Return chart HTML content directly for embedding in frontend"""
    
    # If upload_id is provided, get file path from history
    if upload_id:
        entry = get_history_entry(user, upload_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Analysis not found")
        file_path = entry["file_path"]
        
        # Check if chart already exists
        if "html" in entry.get("chart_paths", {}):
            chart_path = entry["chart_paths"]["html"]
            if os.path.exists(chart_path):
                with open(chart_path, "r", encoding="utf-8") as f:
                    return {"success": True, "html_content": f.read()}
    else:
        # Use current session data
        file_path = request.session.get("uploaded_csv")
        upload_id = request.session.get("current_upload_id")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No processed data for chart.")
    
    # Re-run analysis to generate chart
    trading_system = TradingSystem()
    try:
        # Use same parameters as before
        output = trading_system.run_complete_analysis(
            file_path=file_path,
            lookahead_bars=5,
            confirmation_bars=7,
            ema_fast=9,
            ema_slow=15,
            big_candle_multiplier=2.5,
            big_candle_lookback=10,
            volume_multiplier=2.5,
            volume_lookback=10,
            show_chart=False,
        )
        fig, table_fig = trading_system.create_chart(show_chart=False)
        
        # Generate HTML content
        html_content = fig.to_html(
            include_plotlyjs='cdn',  # Use CDN for Plotly.js
            div_id="trading-chart",
            config={'displayModeBar': True, 'responsive': True}
        )
        
        # Save chart for future use
        if upload_id:
            filename = f"{user}_chart_{upload_id}.html"
            chart_path = os.path.join(CHART_DIR, filename)
            with open(chart_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Update history entry
            entry = get_history_entry(user, upload_id)
            if entry:
                if "chart_paths" not in entry:
                    entry["chart_paths"] = {}
                entry["chart_paths"]["html"] = chart_path
                update_history_entry(user, upload_id, {"chart_paths": entry["chart_paths"]})
        
        return {"success": True, "html_content": html_content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {e}")
# Alternative endpoint to serve chart as iframe source
# Alternative endpoint to serve chart as iframe source
@app.get("/chart-iframe")
async def get_chart_iframe(
    request: Request, 
    user: str = Depends(get_logged_in_user),
    upload_id: str = None
):
    """Serve chart HTML for iframe embedding"""
    
    # If upload_id is provided, get file path from history
    if upload_id:
        entry = get_history_entry(user, upload_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Analysis not found")
        file_path = entry["file_path"]
        
        # Check if chart already exists
        if "html" in entry.get("chart_paths", {}):
            chart_path = entry["chart_paths"]["html"]
            if os.path.exists(chart_path):
                return StreamingResponse(
                    open(chart_path, "rb"), 
                    media_type="text/html"
                )
    else:
        # Use current session data
        file_path = request.session.get("uploaded_csv")
        upload_id = request.session.get("current_upload_id")
    
    if not file_path or not os.path.exists(file_path):
        # Return a message when no data is available
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Chart</title>
            <style>
                body {{
                    margin: 0;
                    padding: 10px;
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }}
                .message {{
                    text-align: center;
                    color: #666;
                    font-size: 16px;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #f9f9f9;
                }}
            </style>
        </head>
        <body>
            <div class="message">
                <p>No chart data available. Please upload and process a CSV file first.</p>
            </div>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")
    
    # If we have a file path, generate the chart
    trading_system = TradingSystem()
    try:
        # Use same parameters as before
        output = trading_system.run_complete_analysis(
            file_path=file_path,
            lookahead_bars=5,
            confirmation_bars=7,
            ema_fast=9,
            ema_slow=15,
            big_candle_multiplier=2.5,
            big_candle_lookback=10,
            volume_multiplier=2.5,
            volume_lookback=10,
            show_chart=False,
        )
        fig, table_fig = trading_system.create_chart(show_chart=False)
        
        # Generate full HTML page for iframe
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Chart</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 10px;
                    font-family: Arial, sans-serif;
                    overflow: hidden;
                }}
                #chart-container {{
                    width: 100%;
                    height: 90vh;
                    overflow: visible;
                }}
            </style>
        </head>
        <body>
            <div id="chart-container">
                {fig.to_html(include_plotlyjs=False, div_id="trading-chart", config={{'displayModeBar': True, 'responsive': True, 'scrollZoom': True}})}  
            </div>
            <script>
                // Force redraw of chart after load to ensure all elements are visible
                document.addEventListener('DOMContentLoaded', function() {{
                    setTimeout(function() {{
                        window.dispatchEvent(new Event('resize'));
                    }}, 100);
                }});
            </script>
        </body>
        </html>
        """
        
        # Save chart for future use
        if upload_id:
            filename = f"{user}_chart_{upload_id}.html"
            chart_path = os.path.join(CHART_DIR, filename)
            with open(chart_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Update history entry
            entry = get_history_entry(user, upload_id)
            if entry:
                if "chart_paths" not in entry:
                    entry["chart_paths"] = {}
                entry["chart_paths"]["html"] = chart_path
                update_history_entry(user, upload_id, {"chart_paths": entry["chart_paths"]})
        
        return Response(content=html_content, media_type="text/html")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {e}")


# Add this new endpoint after the chart-iframe endpoint
@app.get("/chart-status")
async def get_chart_status(
    request: Request,
    user: str = Depends(get_logged_in_user),
    upload_id: str = None
):
    """Check if chart data is available for the current session or upload ID"""
    
    # If upload_id is provided, check history entry
    if upload_id:
        entry = get_history_entry(user, upload_id)
        if not entry:
            return {"chart_available": False, "message": "Analysis not found"}
        
        # Check if chart exists in history
        if "chart_paths" in entry and "html" in entry["chart_paths"]:
            chart_path = entry["chart_paths"]["html"]
            if os.path.exists(chart_path):
                return {"chart_available": True}
    else:
        # Check current session
        file_path = request.session.get("uploaded_csv")
        if file_path and os.path.exists(file_path):
            return {"chart_available": True}
    
    return {"chart_available": False, "message": "No chart data available"}
# Fetch signals endpoint
@app.get("/signals")
async def get_signals(request: Request, user: str = Depends(get_logged_in_user)):
    results = request.session.get("last_results")
    if not results:
        raise HTTPException(status_code=404, detail="No signals found. Please process a CSV first.")
    return results["signals"]

# Export signals as CSV endpoint
@app.get("/export-signals")
async def export_signals(request: Request, user: str = Depends(get_logged_in_user)):
    results = request.session.get("last_results")
    if not results or not results.get("signals"):
        raise HTTPException(status_code=404, detail="No signals to export.")
    df = pd.DataFrame(results["signals"])
    stream = StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)
    return StreamingResponse(
        stream, 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename={user}_signals.csv"}
    )
@app.get("/history")
async def get_history(request: Request, user: str = Depends(get_logged_in_user)):
    history = load_user_history(user)
    # Sort by timestamp (newest first)
    history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"success": True, "history": history}

@app.get("/history/{upload_id}")
async def get_history_detail(upload_id: str, request: Request, user: str = Depends(get_logged_in_user)):
    entry = get_history_entry(user, upload_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"success": True, "entry": entry}

@app.delete("/history/{upload_id}")
async def delete_history(upload_id: str, request: Request, user: str = Depends(get_logged_in_user)):
    success = delete_history_entry(user, upload_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"success": True, "message": "Analysis deleted"}
# Generate and download chart endpoint
@app.get("/generate-chart")
async def generate_chart(
    request: Request, 
    user: str = Depends(get_logged_in_user), 
    format: str = "html",
    upload_id: str = None
):
    # If upload_id is provided, get file path from history
    if upload_id:
        entry = get_history_entry(user, upload_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Analysis not found")
        file_path = entry["file_path"]
        
        # Check if chart already exists
        if format in entry.get("chart_paths", {}):
            chart_path = entry["chart_paths"][format]
            if os.path.exists(chart_path):
                return StreamingResponse(
                    open(chart_path, "rb"), 
                    media_type="text/html" if format == "html" else "image/png", 
                    headers={"Content-Disposition": f"attachment; filename={user}_chart_{upload_id}.{format}"}
                )
    else:
        # Use current session data
        file_path = request.session.get("uploaded_csv")
        upload_id = request.session.get("current_upload_id")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No processed data for chart.")
    
    # Re-run analysis, but don't show charts
    trading_system = TradingSystem()
    try:
        # Use same parameters as before
        output = trading_system.run_complete_analysis(
            file_path=file_path,
            lookahead_bars=5,
            confirmation_bars=7,
            ema_fast=9,
            ema_slow=15,
            big_candle_multiplier=2.5,
            big_candle_lookback=10,
            volume_multiplier=2.5,
            volume_lookback=10,
            show_chart=False,
        )
        fig, table_fig = trading_system.create_chart(show_chart=False)
        
        # Create a unique filename with upload_id if available
        filename = f"{user}_chart_{upload_id if upload_id else 'latest'}.{format}"
        chart_path = os.path.join(CHART_DIR, filename)
        
        if format == "html":
            fig.write_html(chart_path)
            media_type = "text/html"
        elif format == "png":
            fig.write_image(chart_path)
            media_type = "image/png"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'html' or 'png'.")
        
        # Update history entry with chart path
        if upload_id:
            entry = get_history_entry(user, upload_id)
            if entry:
                if "chart_paths" not in entry:
                    entry["chart_paths"] = {}
                entry["chart_paths"][format] = chart_path
                update_history_entry(user, upload_id, {"chart_paths": entry["chart_paths"]})

        return StreamingResponse(
            open(chart_path, "rb"), 
            media_type=media_type, 
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {e}")

# Email sending function
async def send_completion_email(username, upload_id, results):
    # Get user data to check if they have an email
    user_data = get_user_data(username)
    if not user_data or not user_data.get("email"):
        return False
    
    email = user_data["email"]
    entry = get_history_entry(username, upload_id)
    if not entry:
        return False
    
    # Create email content
    accuracy = results["accuracy_results"].get("accuracy_rate", 0)
    signals_count = len(results.get("signals", []))
    
    html_content = f"""
    <html>
    <body>
        <h2>Your Trading Analysis is Ready</h2>
        <p>Hello {username},</p>
        <p>Your analysis of <b>{entry['original_filename']}</b> is complete!</p>
        <h3>Summary:</h3>
        <ul>
            <li>Accuracy Rate: {accuracy:.2f}%</li>
            <li>Total Signals: {signals_count}</li>
        </ul>
        <p>You can view your results by logging into the platform.</p>
        <p>Download links:</p>
        <ul>
            <li><a href="{FRONTEND_URL}/api/generate-chart?upload_id={upload_id}&format=html">HTML Chart</a></li>
            <li><a href="{FRONTEND_URL}/api/generate-chart?upload_id={upload_id}&format=png">PNG Chart</a></li>
            <li><a href="{FRONTEND_URL}/api/export-signals?upload_id={upload_id}">Export Signals (CSV)</a></li>
        </ul>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Your Trading Analysis is Ready",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    try:
        fm = FastMail(mail_config)
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# Add admin dependency
def get_admin_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user

# Admin endpoints
@app.get("/admin/users")
async def admin_list_users(request: Request, admin: str = Depends(get_admin_user)):
    users = load_users()
    # Remove password hashes for security
    user_list = []
    for username, data in users.items():
        if isinstance(data, str):  # Old format
            user_list.append({
                "username": username,
                "email": None,
                "is_admin": False
            })
        else:  # New format
            user_list.append({
                "username": username,
                "email": data.get("email"),
                "is_admin": data.get("is_admin", False)
            })
    
    return {"success": True, "users": user_list}

@app.get("/admin/user/{username}/history")
async def admin_user_history(username: str, request: Request, admin: str = Depends(get_admin_user)):
    # Check if user exists
    user_data = get_user_data(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    history = load_user_history(username)
    # Sort by timestamp (newest first)
    history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {"success": True, "username": username, "history": history}

@app.post("/admin/user/{username}/delete")
async def admin_delete_user(username: str, request: Request, admin: str = Depends(get_admin_user)):
    # Prevent admin from deleting themselves
    if username == admin:
        return JSONResponse(
            status_code=400, 
            content={"success": False, "message": "Cannot delete your own admin account"}
        )
    
    # Check if user exists
    user_data = get_user_data(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user history to delete associated files
    history = load_user_history(username)
    
    # Delete all user files
    for entry in history:
        # Delete CSV file
        if os.path.exists(entry.get("file_path", "")):
            os.remove(entry["file_path"])
        
        # Delete chart files
        for format_type, path in entry.get("chart_paths", {}).items():
            if os.path.exists(path):
                os.remove(path)
    
    # Delete history file
    history_path = get_user_history_path(username)
    if os.path.exists(history_path):
        os.remove(history_path)
    
    # Delete user from users.json
    success = delete_user(username)
    
    if success:
        return {"success": True, "message": f"User {username} and all associated data deleted"}
    else:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "message": "Failed to delete user"}
        )

@app.post("/admin/make-admin/{username}")
async def make_user_admin(username: str, request: Request, admin: str = Depends(get_admin_user)):
    # Check if user exists
    users = load_users()
    if username not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user to admin
    if isinstance(users[username], str):  # Old format
        password_hash = users[username]
        users[username] = {
            "password": password_hash,
            "email": None,
            "is_admin": True
        }
    else:  # New format
        users[username]["is_admin"] = True
    
    save_users(users)
    
    return {"success": True, "message": f"User {username} is now an admin"}