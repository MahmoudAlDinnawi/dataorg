#!/usr/bin/env python3
import os
import re
import random
from datetime import datetime
from pathlib import Path
import json

class ConversationAnalyzer:
    def __init__(self, chat_directory):
        self.chat_directory = Path(chat_directory)
        self.conversations = []
        
    def analyze_conversation_quality(self, file_path):
        """Analyze the quality of a conversation based on multiple criteria"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                return 0, {}
            
            lines = content.strip().split('\n')
            messages = []
            
            # Parse messages with timestamps
            for line in lines:
                timestamp_match = re.match(r'\[([^\]]+)\]', line)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)
                    message_text = line[len(timestamp_match.group(0)):].strip()
                    if message_text:
                        messages.append({
                            'timestamp': timestamp,
                            'text': message_text
                        })
            
            if len(messages) < 2:
                return 0, {}
            
            quality_score = 0
            analysis = {
                'message_count': len(messages),
                'avg_message_length': 0,
                'has_questions': False,
                'conversation_flow': False,
                'template_ratio': 0,
                'unique_content_ratio': 0,
                'time_span_hours': 0
            }
            
            # 1. Message count (more messages = better conversation)
            analysis['message_count'] = len(messages)
            if len(messages) >= 10:
                quality_score += 20
            elif len(messages) >= 5:
                quality_score += 10
            elif len(messages) >= 3:
                quality_score += 5
            
            # 2. Average message length (avoid too short or too long)
            total_length = sum(len(msg['text']) for msg in messages)
            analysis['avg_message_length'] = total_length / len(messages)
            if 20 <= analysis['avg_message_length'] <= 200:
                quality_score += 15
            elif 10 <= analysis['avg_message_length'] <= 300:
                quality_score += 10
            
            # 3. Check for questions (indicates engagement)
            question_words = ['?', 'how', 'what', 'when', 'where', 'why', 'can', 'could', 'would', 'هل', 'كيف', 'ماذا', 'متى', 'أين', 'لماذا']
            question_count = 0
            for msg in messages:
                text_lower = msg['text'].lower()
                if any(word in text_lower for word in question_words):
                    question_count += 1
            
            if question_count > 0:
                analysis['has_questions'] = True
                quality_score += min(question_count * 5, 20)
            
            # 4. Template detection (lower score for high template ratio)
            template_indicators = [
                'template', 'verification code', 'your code is', 'was sent',
                'نرحب بك', 'رمز التحقق', 'تم إرسال', 'مطعم', 'حجز'
            ]
            
            template_count = 0
            for msg in messages:
                text_lower = msg['text'].lower()
                if any(indicator in text_lower for indicator in template_indicators):
                    template_count += 1
            
            analysis['template_ratio'] = template_count / len(messages)
            if analysis['template_ratio'] < 0.3:
                quality_score += 15
            elif analysis['template_ratio'] < 0.5:
                quality_score += 10
            else:
                quality_score -= 10
            
            # 5. Conversation flow (check for back-and-forth pattern)
            if len(messages) >= 4:
                flow_score = 0
                message_lengths = [len(msg['text']) for msg in messages]
                
                # Check for variety in message lengths (indicates natural conversation)
                length_variance = max(message_lengths) - min(message_lengths)
                if length_variance > 50:
                    flow_score += 10
                    analysis['conversation_flow'] = True
                
                quality_score += flow_score
            
            # 6. Unique content ratio
            unique_messages = set(msg['text'] for msg in messages)
            analysis['unique_content_ratio'] = len(unique_messages) / len(messages)
            if analysis['unique_content_ratio'] > 0.8:
                quality_score += 10
            elif analysis['unique_content_ratio'] > 0.6:
                quality_score += 5
            
            # 7. Time span analysis
            try:
                timestamps = []
                for msg in messages:
                    # Try different timestamp formats
                    timestamp_str = msg['timestamp']
                    for fmt in ['%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                        try:
                            ts = datetime.strptime(timestamp_str, fmt)
                            timestamps.append(ts)
                            break
                        except ValueError:
                            continue
                
                if len(timestamps) >= 2:
                    time_span = max(timestamps) - min(timestamps)
                    analysis['time_span_hours'] = time_span.total_seconds() / 3600
                    
                    # Prefer conversations spanning reasonable time (not too quick, not too long)
                    if 0.5 <= analysis['time_span_hours'] <= 48:
                        quality_score += 10
                    elif 0.1 <= analysis['time_span_hours'] <= 168:  # up to a week
                        quality_score += 5
            
            except Exception:
                pass
            
            return max(0, quality_score), analysis
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return 0, {}
    
    def scan_all_conversations(self):
        """Scan all conversation files and analyze their quality"""
        print("Scanning conversations for quality analysis...")
        
        txt_files = list(self.chat_directory.glob("*.txt"))
        total_files = len(txt_files)
        print(f"Found {total_files} conversation files")
        
        processed = 0
        for file_path in txt_files:
            try:
                quality_score, analysis = self.analyze_conversation_quality(file_path)
                
                if quality_score > 0:  # Only include conversations with some quality
                    self.conversations.append({
                        'file_path': str(file_path),
                        'filename': file_path.name,
                        'quality_score': quality_score,
                        'analysis': analysis
                    })
                
                processed += 1
                if processed % 10000 == 0:
                    print(f"Processed {processed}/{total_files} files...")
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        print(f"Analysis complete. Found {len(self.conversations)} quality conversations")
        
        # Sort by quality score
        self.conversations.sort(key=lambda x: x['quality_score'], reverse=True)
        
    def get_top_conversations(self, count=5000):
        """Get the top N conversations by quality"""
        return self.conversations[:count]
    
    def format_conversation_for_team(self, file_path):
        """Format a conversation file for team review with proper agent/guest/template/bot classification"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            formatted_messages = []
            
            # Known agent names (add more as needed)
            agent_names = {
                'rona daghistani', 'rona', 'soha suliman', 'soha', 'modi', 
                'sarah call center', 'sarah', 'sara mohamad', 'sara', 
                'it departments', 'it department', 'sarah alothman', 
                'shourouk', 'salman outhman', 'salman', 'bot'
            }
            
            # Template/Bot indicators
            template_indicators = [
                'template', 'verification code', 'your code is', 'was sent',
                'نرحب بك', 'رمز التحقق', 'تم إرسال', 'نود أن نعرف رأيكم',
                'استمتع بليلة موسيقية', 'إنه لمن دواعي سرورنا', 'نعتذر في حال',
                'your verification code', 'code is', 'enjoy a unique'
            ]
            
            bot_indicators = [
                'bot:', '_اهلا ومرحبا بكم في مطعم', 'ماذا تريد ان تفعل',
                'تم تحويلك الى احد مندوبي', 'اختر اللغة المفضلة'
            ]
            
            for line in lines:
                timestamp_match = re.match(r'\[([^\]]+)\]', line)
                if timestamp_match:
                    message_text = line[len(timestamp_match.group(0)):].strip()
                    
                    if message_text:
                        # Extract sender name if present (format: "Name: message")
                        sender_match = re.match(r'^([^:]+):\s*(.+)', message_text)
                        sender_name = ""
                        actual_message = message_text
                        
                        if sender_match:
                            sender_name = sender_match.group(1).strip().lower()
                            actual_message = sender_match.group(2).strip()
                        
                        # Classify the role
                        role = "guest"  # default
                        
                        # Check for bot messages first
                        if any(indicator in message_text.lower() for indicator in bot_indicators):
                            role = "bot"
                        # Check for template messages
                        elif any(indicator in message_text.lower() for indicator in template_indicators):
                            role = "template"
                        # Check if sender is a known agent
                        elif sender_name and any(agent_name in sender_name for agent_name in agent_names):
                            role = "agent"
                        # Check message content for agent-like patterns
                        elif any(name in message_text.lower() for name in agent_names):
                            role = "agent"
                        
                        # Format without timestamp
                        formatted_messages.append(f"{role}: {message_text}")
            
            return formatted_messages
            
        except Exception as e:
            print(f"Error formatting {file_path}: {e}")
            return []
    
    def save_top_conversations(self, output_dir, count=5000):
        """Save the top conversations to organized files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        top_conversations = self.get_top_conversations(count)
        
        # Save quality analysis report
        quality_report = []
        for conv in top_conversations:
            quality_report.append({
                'filename': conv['filename'],
                'quality_score': conv['quality_score'],
                'message_count': conv['analysis']['message_count'],
                'avg_message_length': round(conv['analysis']['avg_message_length'], 2),
                'has_questions': conv['analysis']['has_questions'],
                'template_ratio': round(conv['analysis']['template_ratio'], 2),
                'unique_content_ratio': round(conv['analysis']['unique_content_ratio'], 2)
            })
        
        with open(output_path / 'quality_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(quality_report, f, indent=2, ensure_ascii=False)
        
        # Create batches for team review (500 conversations per file for manageable chunks)
        batch_size = 500
        batch_num = 1
        
        for i in range(0, len(top_conversations), batch_size):
            batch = top_conversations[i:i + batch_size]
            batch_file = output_path / f'conversations_batch_{batch_num:02d}.txt'
            
            with open(batch_file, 'w', encoding='utf-8') as f:
                f.write(f"=== BATCH {batch_num} - TOP QUALITY WHATSAPP CONVERSATIONS ===\n")
                f.write(f"Total conversations in this batch: {len(batch)}\n")
                f.write(f"Quality score range: {batch[-1]['quality_score']} - {batch[0]['quality_score']}\n")
                f.write(f"\nCLASSIFICATION LEGEND:\n")
                f.write(f"• agent: Staff members (Rona, Soha, Modi, Sarah Call Center, etc.)\n")
                f.write(f"• guest: Customer/client messages\n") 
                f.write(f"• template: Automated template messages (booking confirmations, etc.)\n")
                f.write(f"• bot: Automated bot responses\n\n")
                
                for j, conv in enumerate(batch, 1):
                    f.write(f"\n{'='*80}\n")
                    f.write(f"CONVERSATION {i + j} - File: {conv['filename']}\n")
                    f.write(f"Quality Score: {conv['quality_score']}\n")
                    f.write(f"Messages: {conv['analysis']['message_count']}, ")
                    f.write(f"Avg Length: {conv['analysis']['avg_message_length']:.1f}, ")
                    f.write(f"Questions: {conv['analysis']['has_questions']}\n")
                    f.write(f"{'='*80}\n")
                    
                    formatted_messages = self.format_conversation_for_team(conv['file_path'])
                    for message in formatted_messages:
                        f.write(f"{message}\n")
                    f.write(f"\n")
            
            batch_num += 1
        
        print(f"Saved {len(top_conversations)} top quality conversations to {output_path}")
        print(f"Created {batch_num - 1} batch files for team review")
        
        return len(top_conversations)

def main():
    # Configuration
    chat_directory = "/Users/mahmouddinnawi/Desktop/chats"
    output_directory = "/Users/mahmouddinnawi/Data_Org/organized_whatsapp_conversations"
    target_conversations = 5000
    
    print("=== WhatsApp Conversation Quality Analyzer ===")
    print(f"Source directory: {chat_directory}")
    print(f"Output directory: {output_directory}")
    print(f"Target conversations: {target_conversations}")
    print()
    
    # Initialize analyzer
    analyzer = ConversationAnalyzer(chat_directory)
    
    # Scan and analyze all conversations
    analyzer.scan_all_conversations()
    
    if len(analyzer.conversations) < target_conversations:
        print(f"Warning: Only found {len(analyzer.conversations)} quality conversations")
        print(f"Will use all available quality conversations")
        target_conversations = len(analyzer.conversations)
    
    # Save top quality conversations
    saved_count = analyzer.save_top_conversations(output_directory, target_conversations)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total conversations analyzed: {len(analyzer.conversations)}")
    print(f"Top conversations saved: {saved_count}")
    print(f"Output location: {output_directory}")
    print(f"Ready for team manual organization!")

if __name__ == "__main__":
    main()