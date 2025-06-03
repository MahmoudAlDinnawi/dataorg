#!/usr/bin/env python3
import json
import re
from pathlib import Path

def format_conversation_for_team(file_path):
    """Format a conversation file with proper agent/guest/template/bot classification"""
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
            'shourouk', 'salman outhman', 'salman'
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
                    
                    if sender_match:
                        sender_name = sender_match.group(1).strip().lower()
                    
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

def main():
    # Load the quality analysis report
    quality_report_path = "/Users/mahmouddinnawi/Data_Org/organized_whatsapp_conversations/quality_analysis_report.json"
    output_directory = "/Users/mahmouddinnawi/Data_Org/organized_whatsapp_conversations"
    chat_directory = "/Users/mahmouddinnawi/Desktop/chats"
    
    print("Loading quality analysis report...")
    try:
        with open(quality_report_path, 'r', encoding='utf-8') as f:
            quality_data = json.load(f)
    except FileNotFoundError:
        print("Quality analysis report not found. Please run the main analyzer first.")
        return
    
    print(f"Reformatting {len(quality_data)} conversations with improved classification...")
    
    # Create batches for team review (500 conversations per file)
    batch_size = 500
    batch_num = 1
    
    for i in range(0, len(quality_data), batch_size):
        batch = quality_data[i:i + batch_size]
        batch_file = Path(output_directory) / f'conversations_batch_{batch_num:02d}.txt'
        
        print(f"Creating batch {batch_num}...")
        
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
                f.write(f"Messages: {conv['message_count']}, ")
                f.write(f"Avg Length: {conv['avg_message_length']:.1f}, ")
                f.write(f"Questions: {conv['has_questions']}\n")
                f.write(f"{'='*80}\n")
                
                # Format the conversation
                file_path = Path(chat_directory) / conv['filename']
                formatted_messages = format_conversation_for_team(file_path)
                
                for message in formatted_messages:
                    f.write(f"{message}\n")
                f.write(f"\n")
        
        batch_num += 1
    
    print(f"Successfully reformatted {len(quality_data)} conversations into {batch_num - 1} batch files")
    print("✅ Improved classification complete!")

if __name__ == "__main__":
    main()