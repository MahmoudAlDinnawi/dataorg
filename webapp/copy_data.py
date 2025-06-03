#!/usr/bin/env python3
"""
Script to copy organized WhatsApp conversation data to the web app directory
Run this to set up your data structure properly
"""
import os
import shutil
import json
from pathlib import Path

def copy_organized_data():
    """Copy data from the original organized_whatsapp_conversations folder"""
    
    # Current web app directory
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Possible source directories (adjust these paths for your setup)
    possible_sources = [
        "/Users/mahmouddinnawi/Data_Org/organized_whatsapp_conversations",
        "/home/tawabel/Data_Org/organized_whatsapp_conversations", 
        "../organized_whatsapp_conversations",
        "../../organized_whatsapp_conversations",
        "/path/to/your/organized_whatsapp_conversations"  # User should update this
    ]
    
    # Chat file sources
    possible_chat_sources = [
        "/Users/mahmouddinnawi/Desktop/chats",
        "/home/tawabel/Desktop/chats",
        "../chats",
        "../../chats", 
        "/path/to/your/chats"  # User should update this
    ]
    
    print("🔍 Looking for organized WhatsApp conversation data...")
    
    # Find the source data
    source_data_dir = None
    for source in possible_sources:
        if os.path.exists(source):
            quality_report = os.path.join(source, "quality_analysis_report.json")
            if os.path.exists(quality_report):
                source_data_dir = source
                print(f"✅ Found organized data at: {source}")
                break
    
    if not source_data_dir:
        print("❌ Could not find organized_whatsapp_conversations directory with quality_analysis_report.json")
        print("\n📋 Please manually specify the path:")
        print("Edit this script and update the 'possible_sources' list with your actual path")
        return False
    
    # Find chat files
    source_chat_dir = None
    for source in possible_chat_sources:
        if os.path.exists(source):
            txt_files = list(Path(source).glob("*.txt"))
            if txt_files:
                source_chat_dir = source
                print(f"✅ Found {len(txt_files)} chat files at: {source}")
                break
    
    if not source_chat_dir:
        print("❌ Could not find directory with .txt chat files")
        print("\n📋 Please manually specify the path:")
        print("Edit this script and update the 'possible_chat_sources' list with your actual path")
        return False
    
    # Create destination directories
    webapp_organized_dir = os.path.join(webapp_dir, "organized_whatsapp_conversations")
    webapp_chat_dir = os.path.join(webapp_dir, "chats")
    
    os.makedirs(webapp_organized_dir, exist_ok=True)
    os.makedirs(webapp_chat_dir, exist_ok=True)
    
    print(f"\n📁 Copying data to web app directory: {webapp_dir}")
    
    # Copy quality analysis report
    source_report = os.path.join(source_data_dir, "quality_analysis_report.json")
    dest_report = os.path.join(webapp_organized_dir, "quality_analysis_report.json")
    
    try:
        shutil.copy2(source_report, dest_report)
        print(f"✅ Copied quality_analysis_report.json")
        
        # Verify the report
        with open(dest_report, 'r', encoding='utf-8') as f:
            quality_data = json.load(f)
        print(f"📊 Quality report contains {len(quality_data)} conversations")
        
    except Exception as e:
        print(f"❌ Error copying quality report: {e}")
        return False
    
    # Copy batch files if they exist
    batch_files = list(Path(source_data_dir).glob("conversations_batch_*.txt"))
    if batch_files:
        print(f"📄 Found {len(batch_files)} batch files, copying...")
        for batch_file in batch_files:
            dest_batch = os.path.join(webapp_organized_dir, batch_file.name)
            shutil.copy2(str(batch_file), dest_batch)
        print(f"✅ Copied {len(batch_files)} batch files")
    
    # Copy chat files (sample first, then ask for confirmation for all)
    chat_files = list(Path(source_chat_dir).glob("*.txt"))
    
    if len(chat_files) > 1000:
        print(f"⚠️  Found {len(chat_files)} chat files - this is a lot!")
        print("Do you want to copy all files? This might take a while and use significant disk space.")
        response = input("Copy all files? (y/N): ").lower().strip()
        if response != 'y':
            print("📋 Copying only first 1000 files for testing...")
            chat_files = chat_files[:1000]
    
    print(f"📁 Copying {len(chat_files)} chat files...")
    copied_count = 0
    
    for i, chat_file in enumerate(chat_files):
        try:
            dest_chat = os.path.join(webapp_chat_dir, chat_file.name)
            shutil.copy2(str(chat_file), dest_chat)
            copied_count += 1
            
            if (i + 1) % 1000 == 0:
                print(f"   📝 Copied {i + 1}/{len(chat_files)} files...")
                
        except Exception as e:
            print(f"❌ Error copying {chat_file.name}: {e}")
    
    print(f"✅ Successfully copied {copied_count} chat files")
    
    return True

def verify_data_structure():
    """Verify that the data structure is correct"""
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check required files
    required_files = [
        os.path.join(webapp_dir, "organized_whatsapp_conversations", "quality_analysis_report.json"),
    ]
    
    required_dirs = [
        os.path.join(webapp_dir, "chats"),
        os.path.join(webapp_dir, "organized_whatsapp_conversations"),
        os.path.join(webapp_dir, "templates")
    ]
    
    print("\n🔍 Verifying data structure...")
    
    all_good = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {os.path.basename(file_path)}")
        else:
            print(f"❌ Missing: {file_path}")
            all_good = False
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            if dir_path.endswith('chats'):
                file_count = len(list(Path(dir_path).glob("*.txt")))
                print(f"✅ {os.path.basename(dir_path)}/ ({file_count} .txt files)")
            else:
                print(f"✅ {os.path.basename(dir_path)}/")
        else:
            print(f"❌ Missing directory: {dir_path}")
            all_good = False
    
    if all_good:
        print("\n🎉 Data structure is complete!")
        print("🚀 You can now run: python3 start.py")
    else:
        print("\n❌ Data structure is incomplete")
        print("📋 Please fix the missing files/directories")
    
    return all_good

if __name__ == '__main__':
    print("📋 WhatsApp Conversation Data Setup")
    print("=" * 50)
    
    if copy_organized_data():
        print("\n" + "=" * 50)
        verify_data_structure()
    else:
        print("\n❌ Data copy failed")
        print("📋 Please check the paths and try again")
        
        print("\n💡 Manual Steps:")
        print("1. Copy quality_analysis_report.json to: ./organized_whatsapp_conversations/")
        print("2. Copy your .txt chat files to: ./chats/")
        print("3. Run: python3 start.py")