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
        """Load conversations from quality report OR extract from batch files"""
        quality_report_path = os.path.join(DATA_DIR, "quality_analysis_report.json")
        
        # Try to load from quality report first
        if os.path.exists(quality_report_path):
            try:
                with open(quality_report_path, 'r', encoding='utf-8') as f:
                    quality_data = json.load(f)
                self._load_from_quality_data(quality_data)
                return
            except Exception as e:
                print(f"❌ Error loading quality report: {e}")
        
        # If no quality report, try to extract from batch files
        print(f"⚠️  Quality analysis report not found, extracting from batch files...")
        quality_data = self._extract_from_batch_files()
        
        if quality_data:
            self._load_from_quality_data(quality_data)
            # Save the extracted data for future use
            try:
                with open(quality_report_path, 'w', encoding='utf-8') as f:
                    json.dump(quality_data, f, indent=2, ensure_ascii=False)
                print(f"✅ Created quality_analysis_report.json with {len(quality_data)} conversations")
            except Exception as e:
                print(f"⚠️  Could not save quality report: {e}")
        else:
            print(f"❌ No data found. Please check your batch files in {DATA_DIR}")
    
    def _load_from_quality_data(self, quality_data):
        """Load conversation data into database"""
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
    
    def _extract_from_batch_files(self):
        """Extract conversation metadata from batch files"""
        batch_files = list(Path(DATA_DIR).glob("conversations_batch_*.txt"))
        
        if not batch_files:
            print(f"❌ No batch files found in {DATA_DIR}")
            return []
        
        print(f"📄 Found {len(batch_files)} batch files, extracting metadata...")
        
        conversations_data = []
        
        for batch_file in batch_files:
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract conversation metadata from batch file
                conv_data = self._parse_batch_file_metadata(content)
                conversations_data.extend(conv_data)
                
            except Exception as e:
                print(f"❌ Error processing {batch_file.name}: {e}")
        
        return conversations_data
    
    def _parse_batch_file_metadata(self, content):
        """Parse conversation metadata from batch file content"""
        conversations = []
        lines = content.split('\n')
        
        current_conv = None
        
        for line in lines:
            line = line.strip()
            
            # Look for conversation headers
            if line.startswith('CONVERSATION') and '- File:' in line:
                # Parse: CONVERSATION X - File: filename.txt
                parts = line.split('- File: ')
                if len(parts) > 1:
                    filename = parts[1].strip()
                    current_conv = {
                        'filename': filename,
                        'quality_score': 85,  # Default
                        'message_count': 10,  # Default
                        'avg_message_length': 50.0,
                        'has_questions': True,
                        'template_ratio': 0.2,
                        'unique_content_ratio': 0.8
                    }
            
            # Parse quality info
            elif line.startswith('Quality Score:') and current_conv:
                try:
                    score_part = line.split('Quality Score: ')[1]
                    score = int(score_part.split(',')[0] if ',' in score_part else score_part)
                    current_conv['quality_score'] = score
                except:
                    pass
            
            # Parse message info
            elif line.startswith('Messages:') and current_conv:
                try:
                    parts = line.split(', ')
                    msg_count = int(parts[0].split('Messages: ')[1])
                    avg_length = float(parts[1].split('Avg Length: ')[1])
                    has_questions = parts[2].split('Questions: ')[1].lower() == 'true'
                    
                    current_conv['message_count'] = msg_count
                    current_conv['avg_message_length'] = avg_length
                    current_conv['has_questions'] = has_questions
                    
                    # Add the conversation to our list
                    conversations.append(current_conv)
                    current_conv = None
                    
                except Exception as e:
                    # If parsing fails, still add the conversation with defaults
                    if current_conv:
                        conversations.append(current_conv)
                        current_conv = None
        
        return conversations
    
    def get_conversation_content(self, filename):
        """Load and parse a specific conversation from batch files"""
        try:
            # First try to load from individual chat file
            file_path = Path(CHAT_DIR) / filename
            if os.path.exists(file_path):
                return self._parse_individual_chat_file(file_path)
            
            # If individual file doesn't exist, extract from batch files
            return self._extract_conversation_from_batches(filename)
            
        except Exception as e:
            print(f"Error loading conversation {filename}: {e}")
            return []
    
    def _parse_individual_chat_file(self, file_path):
        """Parse messages from individual chat file"""
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
    
    def _extract_conversation_from_batches(self, filename):
        """Extract a specific conversation from batch files"""
        batch_files = list(Path(DATA_DIR).glob("conversations_batch_*.txt"))
        
        for batch_file in batch_files:
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find the conversation in this batch file
                messages = self._find_conversation_in_batch(content, filename)
                if messages:
                    return messages
                    
            except Exception as e:
                print(f"Error searching in {batch_file.name}: {e}")
        
        # If not found, return empty list
        print(f"Conversation {filename} not found in batch files")
        return []
    
    def _find_conversation_in_batch(self, content, target_filename):
        """Find and extract a specific conversation from batch content"""
        lines = content.split('\n')
        in_target_conversation = False
        in_messages_section = False
        messages = []
        message_id = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if we found our target conversation
            if line_stripped.startswith('CONVERSATION') and f'- File: {target_filename}' in line_stripped:
                in_target_conversation = True
                in_messages_section = False
                continue
            
            # Check if we've moved to the next conversation
            elif line_stripped.startswith('CONVERSATION') and in_target_conversation:
                break  # We've finished our target conversation
            
            # Check for message section start
            elif in_target_conversation and line_stripped == '=' * 80:
                in_messages_section = True
                continue
            
            # Parse messages
            elif in_target_conversation and in_messages_section and ':' in line_stripped:
                # Parse format: role: message
                colon_index = line_stripped.find(':')
                if colon_index > 0:
                    role = line_stripped[:colon_index].strip()
                    message_text = line_stripped[colon_index + 1:].strip()
                    
                    if role in ['agent', 'guest', 'bot', 'template'] and message_text:
                        from datetime import datetime
                        timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
                        
                        messages.append({
                            'id': message_id,
                            'timestamp': timestamp,
                            'role': role,
                            'text': f"{role}: {message_text}",
                            'sender_name': role,
                            'actual_message': message_text
                        })
                        message_id += 1
        
        return messages if in_target_conversation else []
    
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

@app.route('/approved')
def approved():
    """Approved conversations page"""
    page = int(request.args.get('page', 1))
    limit = 20
    offset = (page - 1) * limit
    
    conversations, total_count = conv_manager.get_conversations_for_review(
        status='reviewed', 
        limit=limit, 
        offset=offset
    )
    
    # Filter only accepted conversations
    approved_conversations = [conv for conv in conversations if conv.get('accepted')]
    approved_count = len(approved_conversations)
    
    # Get total approved count
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM conversations WHERE status = "reviewed" AND accepted = 1')
    total_approved = cursor.fetchone()[0]
    conn.close()
    
    total_pages = (total_approved + limit - 1) // limit
    
    return render_template('approved.html', 
                         conversations=approved_conversations,
                         current_page=page,
                         total_pages=total_pages,
                         total_count=total_approved)

@app.route('/conversation/<filename>')
def view_conversation(filename):
    """View individual conversation for detailed review"""
    # First get the original messages
    messages = conv_manager.get_conversation_content(filename)
    
    # Check if there are saved edits for this conversation
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT corrected_messages FROM conversations WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        conn.close()
        
        has_saved_edits = bool(result and result[0])
        
        # If there are saved edits, use them instead of the original messages
        if has_saved_edits and result[0]:
            try:
                edited_messages = json.loads(result[0])
                messages = edited_messages
                print(f"✅ Loaded edited version of {filename} with {len(messages)} messages")
            except Exception as e:
                print(f"⚠️  Error loading edited messages for {filename}: {e}")
                # Fall back to original messages
        
    except Exception as e:
        has_saved_edits = False
        print(f"Error checking for saved edits: {e}")
    
    return render_template('conversation.html', 
                         filename=filename, 
                         messages=messages,
                         has_saved_edits=has_saved_edits)

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

@app.route('/api/save_edits', methods=['POST'])
def api_save_edits():
    """API endpoint to save conversation edits (persistent)"""
    data = request.json
    filename = data.get('filename')
    corrected_messages = data.get('corrected_messages')
    
    if not filename or not corrected_messages:
        return jsonify({'status': 'error', 'message': 'Missing filename or messages'})
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Save the corrected messages as JSON
        cursor.execute('''
            UPDATE conversations 
            SET corrected_messages = ?
            WHERE filename = ?
        ''', (json.dumps(corrected_messages), filename))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Edits saved successfully'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/get_edits/<filename>')
def api_get_edits(filename):
    """API endpoint to get saved edits for a conversation"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT corrected_messages FROM conversations WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            corrected_messages = json.loads(result[0])
            return jsonify({'status': 'success', 'corrected_messages': corrected_messages})
        else:
            return jsonify({'status': 'success', 'corrected_messages': None})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/find_replace', methods=['POST'])
def api_find_replace():
    """API endpoint to find and replace text in conversation"""
    data = request.json
    filename = data.get('filename')
    find_text = data.get('find_text', '').strip()
    replace_text = data.get('replace_text', '').strip()
    
    if not filename or not find_text:
        return jsonify({'status': 'error', 'message': 'Missing filename or search text'})
    
    try:
        # Get current conversation content (including any saved edits)
        messages = conv_manager.get_conversation_content(filename)
        
        # Check if there are saved edits
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT corrected_messages FROM conversations WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            # Use saved edits if available
            saved_messages = json.loads(result[0])
            messages = saved_messages
        
        # Perform find and replace
        replaced_count = 0
        for message in messages:
            if find_text.lower() in message.get('text', '').lower():
                # Case-insensitive replace
                original_text = message.get('text', '')
                new_text = re.sub(re.escape(find_text), replace_text, original_text, flags=re.IGNORECASE)
                message['text'] = new_text
                
                # Also update actual_message if it exists
                if 'actual_message' in message:
                    original_actual = message.get('actual_message', '')
                    new_actual = re.sub(re.escape(find_text), replace_text, original_actual, flags=re.IGNORECASE)
                    message['actual_message'] = new_actual
                
                replaced_count += 1
        
        # Save the updated messages
        if replaced_count > 0:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversations 
                SET corrected_messages = ?
                WHERE filename = ?
            ''', (json.dumps(messages), filename))
            conn.commit()
            conn.close()
        
        return jsonify({
            'status': 'success', 
            'replaced_count': replaced_count,
            'updated_messages': messages
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/export')
def api_export():
    """Export accepted conversations in multiple formats"""
    format_type = request.args.get('format', 'jsonl')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT filename, corrected_messages FROM conversations 
        WHERE accepted = 1 AND status = "reviewed"
    ''')
    
    accepted_conversations = cursor.fetchall()
    conn.close()
    
    if format_type == 'txt_individual':
        return export_individual_txt_files(accepted_conversations)
    
    # Generate training data for JSON/JSONL formats
    training_data = []
    all_conversations = []
    
    for filename, corrected_messages_json in accepted_conversations:
        if corrected_messages_json:
            # Use corrected messages
            messages = json.loads(corrected_messages_json)
        else:
            # Use original messages
            messages = conv_manager.get_conversation_content(filename)
        
        # Store full conversation for txt format
        all_conversations.append({
            'filename': filename,
            'messages': messages
        })
        
        # Convert to training format pairs
        conversation_pairs = []
        for i in range(len(messages) - 1):
            current_msg = messages[i]
            next_msg = messages[i + 1]
            
            if current_msg.get('role') in ['guest'] and next_msg.get('role') in ['agent']:
                # Clean the message content
                user_content = extract_clean_message(current_msg)
                assistant_content = extract_clean_message(next_msg)
                
                if user_content and assistant_content:
                    conversation_pairs.append({
                        "messages": [
                            {"role": "user", "content": user_content},
                            {"role": "assistant", "content": assistant_content}
                        ]
                    })
        
        training_data.extend(conversation_pairs)
    
    if format_type == 'jsonl':
        from flask import Response
        
        def generate():
            for item in training_data:
                yield json.dumps(item, ensure_ascii=False) + '\n'
        
        return Response(generate(), 
                       mimetype='application/jsonl',
                       headers={'Content-Disposition': 'attachment; filename=fine_tuning_data.jsonl'})
    
    elif format_type == 'json':
        from flask import Response
        
        json_data = json.dumps(training_data, ensure_ascii=False, indent=2)
        return Response(json_data,
                       mimetype='application/json',
                       headers={'Content-Disposition': 'attachment; filename=fine_tuning_data.json'})
    
    elif format_type == 'txt':
        from flask import Response
        
        def generate():
            for conv in all_conversations:
                yield f"=== CONVERSATION: {conv['filename']} ===\n"
                for msg in conv['messages']:
                    clean_msg = extract_clean_message(msg)
                    if clean_msg:
                        yield f"{msg.get('role', 'unknown')}: {clean_msg}\n"
                yield "\n" + "="*80 + "\n\n"
        
        return Response(generate(),
                       mimetype='text/plain',
                       headers={'Content-Disposition': 'attachment; filename=approved_conversations.txt'})
    
    return jsonify(training_data)

def extract_clean_message(message):
    """Extract clean message content from message object"""
    # Try different message content fields
    content = message.get('actual_message') or message.get('text', '')
    
    if not content:
        return ""
    
    # Remove role prefix if it exists (e.g., "guest: message" -> "message")
    if ':' in content:
        parts = content.split(':', 1)
        if len(parts) > 1 and parts[0].strip().lower() in ['agent', 'guest', 'bot', 'template']:
            content = parts[1].strip()
    
    return content.strip()

def export_individual_txt_files(accepted_conversations):
    """Export each conversation as individual txt files in a zip"""
    import zipfile
    import io
    from flask import Response
    
    # Create zip file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, corrected_messages_json in accepted_conversations:
            if corrected_messages_json:
                messages = json.loads(corrected_messages_json)
            else:
                messages = conv_manager.get_conversation_content(filename)
            
            # Create content for individual file
            content_lines = []
            content_lines.append(f"=== CONVERSATION: {filename} ===\n")
            content_lines.append(f"Total Messages: {len(messages)}\n")
            content_lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            content_lines.append("="*50 + "\n\n")
            
            for msg in messages:
                role = msg.get('role', 'unknown')
                clean_msg = extract_clean_message(msg)
                if clean_msg:
                    content_lines.append(f"{role}: {clean_msg}\n")
            
            # Add file to zip
            file_content = ''.join(content_lines)
            safe_filename = filename.replace('.txt', '_approved.txt')
            zip_file.writestr(safe_filename, file_content.encode('utf-8'))
    
    zip_buffer.seek(0)
    
    return Response(
        zip_buffer.getvalue(),
        mimetype='application/zip',
        headers={'Content-Disposition': 'attachment; filename=approved_conversations_individual.zip'}
    )

@app.route('/api/progress')
def api_progress():
    """Get current team progress"""
    return jsonify(conv_manager.get_team_progress())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)