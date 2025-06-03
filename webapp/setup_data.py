#!/usr/bin/env python3
"""
Setup script to organize data for the WhatsApp Conversation Organizer
Run this before starting the web app
"""
import os
import shutil
import json
from pathlib import Path

def setup_data_structure():
    """Set up the data structure for the web app"""
    
    # Get the current directory (where the web app is)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("🔧 Setting up WhatsApp Conversation Organizer...")
    print(f"📁 Base directory: {base_dir}")
    
    # Create necessary directories
    directories = [
        os.path.join(base_dir, "organized_whatsapp_conversations"),
        os.path.join(base_dir, "chats"),
        os.path.join(base_dir, "templates")
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Check if we need to copy data
    chat_dir = os.path.join(base_dir, "chats")
    organized_dir = os.path.join(base_dir, "organized_whatsapp_conversations")
    
    # Instructions for data setup
    print("\n📋 DATA SETUP INSTRUCTIONS:")
    print("=" * 50)
    
    # Check if chat files exist
    chat_files = list(Path(chat_dir).glob("*.txt"))
    if not chat_files:
        print(f"❌ No chat files found in: {chat_dir}")
        print(f"📥 Please copy your WhatsApp conversation files (.txt) to: {chat_dir}")
        print(f"   Example: cp /path/to/your/chats/*.txt {chat_dir}/")
    else:
        print(f"✅ Found {len(chat_files)} chat files in {chat_dir}")
    
    # Check if quality analysis report exists
    quality_report = os.path.join(organized_dir, "quality_analysis_report.json")
    if not os.path.exists(quality_report):
        print(f"❌ Quality analysis report not found: {quality_report}")
        print(f"📥 Please copy the quality_analysis_report.json to: {organized_dir}/")
        print(f"   Example: cp /path/to/organized_whatsapp_conversations/quality_analysis_report.json {organized_dir}/")
        
        # Create a sample quality report if none exists
        create_sample_quality_report(quality_report, chat_files)
    else:
        print(f"✅ Quality analysis report found: {quality_report}")
    
    print("\n🚀 AUTOMATED DATA COPY:")
    print("=" * 50)
    print("If you have the organized_whatsapp_conversations folder from the original analysis:")
    print("🔧 Run: python3 copy_data.py")
    print("   This will automatically find and copy your data files")
    
    print("\n📋 MANUAL STEPS (if automated copy doesn't work):")
    print("=" * 50)
    print("1. Copy your WhatsApp conversation files (.txt) to the 'chats' directory")
    print("2. Copy the quality_analysis_report.json to the 'organized_whatsapp_conversations' directory")
    print("3. Run: python3 start.py")
    print("4. Open browser to: http://localhost:5001")
    
    return True

def create_sample_quality_report(report_path, chat_files):
    """Create a sample quality report if chat files exist but no report"""
    if not chat_files:
        return
    
    print(f"📝 Creating sample quality report with {len(chat_files)} files...")
    
    sample_data = []
    for i, chat_file in enumerate(chat_files[:100]):  # Limit to first 100 files for demo
        sample_data.append({
            "filename": chat_file.name,
            "quality_score": 95 - (i % 20),  # Sample scores 75-95
            "message_count": 10 + (i % 15),  # Sample message counts 10-25
            "avg_message_length": 45.5,
            "has_questions": True,
            "template_ratio": 0.2,
            "unique_content_ratio": 0.8
        })
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created sample quality report: {report_path}")

def check_requirements():
    """Check if required Python packages are installed"""
    required_packages = ['flask']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"📥 Install with: pip install {' '.join(missing_packages)}")
        return False
    else:
        print(f"✅ All required packages installed")
        return True

if __name__ == '__main__':
    print("🚀 WhatsApp Conversation Organizer Setup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please install missing packages first")
        exit(1)
    
    # Setup data structure
    if setup_data_structure():
        print("\n✅ Setup completed successfully!")
        print("📋 Follow the instructions above to complete the data setup")
    else:
        print("\n❌ Setup failed")
        exit(1)