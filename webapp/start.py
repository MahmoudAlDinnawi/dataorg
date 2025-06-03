#!/usr/bin/env python3
"""
Simple script to start the WhatsApp Conversation Organizer web app
"""
import webbrowser
import time
from app import app

def start_app():
    print("🚀 Starting WhatsApp Conversation Organizer...")
    print(f"📊 Loaded conversation data successfully")
    print(f"🌐 Web app will be available at: http://localhost:5001")
    print(f"👥 Team Member 1: http://localhost:5001/review?reviewer=Team%20Member%201")
    print(f"👥 Team Member 2: http://localhost:5001/review?reviewer=Team%20Member%202")
    print(f"\n💡 Press Ctrl+C to stop the server")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:5001')
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start the Flask app
    app.run(debug=False, host='0.0.0.0', port=5001)

if __name__ == '__main__':
    start_app()