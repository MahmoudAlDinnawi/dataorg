# Quick Start Guide for Tawabel Server

## 🚀 Setup Instructions

### 1. First Time Setup
```bash
cd ~/projects/dataorg
python3 setup_data.py
```

### 2. Copy Your Data Files

#### Option A: Automated Copy (Recommended)
```bash
# This will automatically find and copy your existing organized data
python3 copy_data.py
```

#### Option B: Manual Copy
```bash
# Copy all your .txt conversation files to the chats directory
cp /path/to/your/original/chats/*.txt ./chats/

# Copy the quality analysis report
cp /path/to/organized_whatsapp_conversations/quality_analysis_report.json ./organized_whatsapp_conversations/

# Copy batch files (optional)
cp /path/to/organized_whatsapp_conversations/conversations_batch_*.txt ./organized_whatsapp_conversations/
```

### 3. Start the Application
```bash
python3 start.py
```

### 4. Access the Web App
- Open browser to: `http://your-server-ip:5001`
- Or if running locally: `http://localhost:5001`

## 📁 Expected Directory Structure
```
~/projects/dataorg/
├── app.py                              # Main Flask application
├── start.py                           # Startup script
├── setup_data.py                      # Data setup helper
├── requirements.txt                   # Python dependencies
├── conversations.db                   # SQLite database (auto-created)
├── chats/                            # Your WhatsApp conversation files
│   ├── conversation1.txt
│   ├── conversation2.txt
│   └── ...
├── organized_whatsapp_conversations/ # Quality analysis data
│   └── quality_analysis_report.json
└── templates/                        # HTML templates
    ├── base.html
    ├── dashboard.html
    ├── review.html
    └── conversation.html
```

## 🔧 Troubleshooting

### Permission Errors
If you get permission errors:
```bash
chmod +x setup_data.py
chmod +x start.py
```

### Port Already in Use
If port 5001 is in use, edit `app.py` line 367:
```python
app.run(debug=True, host='0.0.0.0', port=5002)  # Change to available port
```

### Missing Data Files
If you see warnings about missing files:
1. Run `python3 setup_data.py` again
2. Follow the instructions to copy your data files
3. Restart with `python3 start.py`

### Flask Not Found
```bash
pip install flask
# or
pip3 install flask
```

## 🎯 Usage

1. **Dashboard**: View team progress and statistics
2. **Review Interface**: Accept/reject conversations for training
3. **Conversation Editor**: 
   - Edit message classifications
   - Add/remove/reorder messages
   - Fix conversation flow
4. **Export**: Download training data in JSONL format

## 👥 Team Workflow

### Team Member 1
Visit: `http://your-server:5001/review?reviewer=Team%20Member%201`

### Team Member 2  
Visit: `http://your-server:5001/review?reviewer=Team%20Member%202`

## 📞 Need Help?

If you encounter any issues:
1. Check the console output for error messages
2. Ensure all data files are in the correct directories
3. Verify Flask is installed: `python3 -c "import flask; print('Flask OK')"`
4. Check if the port is available: `netstat -an | grep 5001`

---
**Ready to organize your fine-tuning data!** 🚀