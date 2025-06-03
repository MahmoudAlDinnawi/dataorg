#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import re
from pathlib import Path
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# Configuration - Use relative paths that work on any system
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "organized_whatsapp_conversations") 
CHAT_DIR = os.path.join(BASE_DIR, "chats")
DB_PATH = os.path.join(BASE_DIR, "conversations.db")

class ConversationManager:
    def __init__(self):
        self.init_database()
        self.load_conversations()
    
    def init_database(self):
        """Initialize SQLite database for tracking progress"""
        # Ensure the database directory exists
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:  # Only create directory if DB_PATH has a directory component
            os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY,
                filename TEXT UNIQUE,
                quality_score INTEGER,
                message_count INTEGER,
                status TEXT DEFAULT 'pending',
                reviewer TEXT,
                reviewed_at TIMESTAMP,
                accepted BOOLEAN,
                notes TEXT,
                corrected_messages TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_progress (
                reviewer TEXT PRIMARY KEY,
                total_reviewed INTEGER DEFAULT 0,
                accepted INTEGER DEFAULT 0,
                rejected INTEGER DEFAULT 0,
                last_active TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_conversations(self):
        """Load conversations from quality report if not already in database"""
        quality_report_path = os.path.join(DATA_DIR, "quality_analysis_report.json")
        
        if not os.path.exists(quality_report_path):
            print(f"⚠️  Quality analysis report not found: {quality_report_path}")
            print(f"📋 Run 'python3 setup_data.py' to set up your data first")
            return
        
        try:
            with open(quality_report_path, 'r', encoding='utf-8') as f:
                quality_data = json.load(f)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            for conv in quality_data:
                cursor.execute('''
                    INSERT OR IGNORE INTO conversations 
                    (filename, quality_score, message_count)
                    VALUES (?, ?, ?)
                ''', (conv['filename'], conv['quality_score'], conv['message_count']))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Loaded {len(quality_data)} conversations into database")
            
        except Exception as e:
            print(f"❌ Error loading conversations: {e}")
            print(f"📋 Please check your data setup and run 'python3 setup_data.py'")
    
    def get_conversation_content(self, filename):
        """Load and parse a specific conversation file"""
        try:
            file_path = Path(CHAT_DIR) / filename
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            messages = []
            
            # Known agent names
            agent_names = {
                'rona daghistani', 'rona', 'soha suliman', 'soha', 'modi', 
                'sarah call center', 'sarah', 'sara mohamad', 'sara', 
                'it departments', 'it department', 'sarah alothman', 
                'shourouk', 'salman outhman', 'salman'
            }
            
            # Template/Bot indicators
            template_indicators = [
                'template', 'verification code', 'your code is', 'was sent',
                'نرحب بك', 'رمز التحقق', 'تم إرسال', 'نود أن نعرف رأيكم',
                'استمتع بليلة موسيقية', 'إنه لمن دواعي سرورنا', 'نعتذر في حال'
            ]
            
            bot_indicators = [
                'bot:', '_اهلا ومرحبا بكم في مطعم', 'ماذا تريد ان تفعل',
                'تم تحويلك الى احد مندوبي', 'اختر اللغة المفضلة'
            ]
            
            for i, line in enumerate(lines):
                timestamp_match = re.match(r'\[([^\]]+)\]', line)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)
                    message_text = line[len(timestamp_match.group(0)):].strip()
                    
                    if message_text:
                        # Extract sender name if present
                        sender_match = re.match(r'^([^:]+):\s*(.+)', message_text)
                        sender_name = ""
                        actual_message = message_text
                        
                        if sender_match:
                            sender_name = sender_match.group(1).strip().lower()
                            actual_message = sender_match.group(2).strip()
                        
                        # Classify the role
                        role = "guest"  # default
                        
                        if any(indicator in message_text.lower() for indicator in bot_indicators):
                            role = "bot"
                        elif any(indicator in message_text.lower() for indicator in template_indicators):
                            role = "template"
                        elif sender_name and any(agent_name in sender_name for agent_name in agent_names):
                            role = "agent"
                        elif any(name in message_text.lower() for name in agent_names):
                            role = "agent"
                        
                        messages.append({
                            'id': i,
                            'timestamp': timestamp,
                            'role': role,
                            'text': message_text,
                            'sender_name': sender_name,
                            'actual_message': actual_message
                        })
            
            return messages
            
        except Exception as e:
            print(f"Error loading conversation {filename}: {e}")
            return []
    
    def get_conversations_for_review(self, reviewer=None, status='pending', limit=50, offset=0):
        """Get conversations for review with pagination"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = '''
            SELECT filename, quality_score, message_count, status, reviewer, notes, accepted
            FROM conversations 
            WHERE status = ? 
            ORDER BY quality_score DESC, message_count DESC
            LIMIT ? OFFSET ?
        '''
        
        cursor.execute(query, (status, limit, offset))
        results = cursor.fetchall()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM conversations WHERE status = ?', (status,))
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        conversations = []
        for row in results:
            conversations.append({
                'filename': row[0],
                'quality_score': row[1],
                'message_count': row[2],
                'status': row[3],
                'reviewer': row[4],
                'notes': row[5],
                'accepted': row[6]
            })
        
        return conversations, total_count
    
    def update_conversation_status(self, filename, reviewer, accepted, notes="", corrected_messages=None):
        """Update conversation review status"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        status = 'reviewed'
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE conversations 
            SET status = ?, reviewer = ?, reviewed_at = ?, accepted = ?, notes = ?, corrected_messages = ?
            WHERE filename = ?
        ''', (status, reviewer, timestamp, accepted, notes, corrected_messages, filename))
        
        # Update team progress
        cursor.execute('''
            INSERT OR REPLACE INTO team_progress 
            (reviewer, total_reviewed, accepted, rejected, last_active)
            VALUES (?, 
                COALESCE((SELECT total_reviewed FROM team_progress WHERE reviewer = ?), 0) + 1,
                COALESCE((SELECT accepted FROM team_progress WHERE reviewer = ?), 0) + ?,
                COALESCE((SELECT rejected FROM team_progress WHERE reviewer = ?), 0) + ?,
                ?)
        ''', (reviewer, reviewer, reviewer, 1 if accepted else 0, reviewer, 0 if accepted else 1, timestamp))
        
        conn.commit()
        conn.close()
    
    def get_team_progress(self):
        """Get progress statistics for both team members"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM team_progress')
        progress = cursor.fetchall()
        
        # Get overall statistics
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM conversations WHERE status = "reviewed"')
        total_reviewed = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM conversations WHERE accepted = 1')
        total_accepted = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'team_stats': [{'reviewer': row[0], 'total_reviewed': row[1], 'accepted': row[2], 'rejected': row[3], 'last_active': row[4]} for row in progress],
            'overall': {
                'total_conversations': total_conversations,
                'total_reviewed': total_reviewed,
                'total_accepted': total_accepted,
                'progress_percentage': round((total_reviewed / total_conversations) * 100, 1) if total_conversations > 0 else 0
            }
        }

# Initialize conversation manager
conv_manager = ConversationManager()

@app.route('/')
def index():
    """Main dashboard"""
    progress = conv_manager.get_team_progress()
    return render_template('dashboard.html', progress=progress)

@app.route('/review')
def review():
    """Conversation review interface"""
    page = int(request.args.get('page', 1))
    reviewer = request.args.get('reviewer', 'Team Member')
    limit = 10
    offset = (page - 1) * limit
    
    conversations, total_count = conv_manager.get_conversations_for_review(
        reviewer=reviewer, 
        status='pending', 
        limit=limit, 
        offset=offset
    )
    
    total_pages = (total_count + limit - 1) // limit
    
    return render_template('review.html', 
                         conversations=conversations,
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         reviewer=reviewer)

@app.route('/conversation/<filename>')
def view_conversation(filename):
    """View individual conversation for detailed review"""
    messages = conv_manager.get_conversation_content(filename)
    return render_template('conversation.html', filename=filename, messages=messages)

@app.route('/api/review', methods=['POST'])
def api_review():
    """API endpoint to submit conversation review"""
    data = request.json
    filename = data.get('filename')
    reviewer = data.get('reviewer')
    accepted = data.get('accepted')
    notes = data.get('notes', '')
    corrected_messages = data.get('corrected_messages')
    
    if corrected_messages:
        corrected_messages = json.dumps(corrected_messages)
    
    conv_manager.update_conversation_status(filename, reviewer, accepted, notes, corrected_messages)
    
    return jsonify({'status': 'success'})

@app.route('/api/export')
def api_export():
    """Export accepted conversations in fine-tuning format"""
    format_type = request.args.get('format', 'jsonl')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT filename, corrected_messages FROM conversations 
        WHERE accepted = 1 AND status = "reviewed"
    ''')
    
    accepted_conversations = cursor.fetchall()
    conn.close()
    
    # Generate fine-tuning format
    training_data = []
    
    for filename, corrected_messages_json in accepted_conversations:
        if corrected_messages_json:
            # Use corrected messages
            messages = json.loads(corrected_messages_json)
        else:
            # Use original messages
            messages = conv_manager.get_conversation_content(filename)
        
        # Convert to training format (customize based on your fine-tuning needs)
        conversation_pairs = []
        for i in range(len(messages) - 1):
            current_msg = messages[i]
            next_msg = messages[i + 1]
            
            if current_msg['role'] in ['guest'] and next_msg['role'] in ['agent']:
                conversation_pairs.append({
                    "messages": [
                        {"role": "user", "content": current_msg['actual_message']},
                        {"role": "assistant", "content": next_msg['actual_message']}
                    ]
                })
        
        training_data.extend(conversation_pairs)
    
    if format_type == 'jsonl':
        import io
        from flask import Response
        
        def generate():
            for item in training_data:
                yield json.dumps(item, ensure_ascii=False) + '\n'
        
        return Response(generate(), 
                       mimetype='application/jsonl',
                       headers={'Content-Disposition': 'attachment; filename=fine_tuning_data.jsonl'})
    
    return jsonify(training_data)

@app.route('/api/progress')
def api_progress():
    """Get current team progress"""
    return jsonify(conv_manager.get_team_progress())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)