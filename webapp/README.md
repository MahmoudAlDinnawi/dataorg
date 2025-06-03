# WhatsApp Conversation Organizer Web App

## 🎯 Purpose
This web application helps your 2-person team efficiently organize 5,000 high-quality WhatsApp conversations for fine-tuning preparation.

## ✨ Features

### 📊 Dashboard
- **Team Progress Tracking** - See how many conversations each person has reviewed
- **Overall Statistics** - Total conversations, reviewed count, acceptance rate
- **Quick Actions** - Start reviewing as Team Member 1 or 2
- **Export Tools** - Download training data in JSONL or JSON format

### 📋 Review Interface
- **Batch Review** - 10 conversations per page for manageable chunks
- **Quick Preview** - Load conversation preview without opening new tab
- **Accept/Reject** - Simple buttons to approve conversations for training
- **Notes System** - Add comments for each conversation
- **Keyboard Shortcuts** - Ctrl+Enter to accept, Ctrl+Delete to reject

### 🔍 Advanced Conversation Editor
- **Full Message View** - See complete conversation with proper formatting
- **Classification Editor** - Fix agent/guest/bot/template labels with dropdowns
- **Message Management** - Add, edit, and remove individual messages
- **Drag & Drop Reordering** - Rearrange messages by dragging
- **Live Statistics** - Real-time count of message types
- **Visual Feedback** - Color-coded messages by role with hover effects
- **Keyboard Shortcuts** - Ctrl+Enter (add message), Escape (cancel), Ctrl+S (save)

### 📤 Export Features
- **JSONL Format** - Ready for OpenAI fine-tuning
- **JSON Format** - Standard JSON for other platforms
- **Filtered Data** - Only exports accepted conversations
- **Corrected Classifications** - Uses team-corrected labels

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /Users/mahmouddinnawi/Data_Org/webapp
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

### 3. Open in Browser
Navigate to: `http://localhost:5000`

## 👥 Team Workflow

### Initial Setup
1. **Team Member 1** starts reviewing at: `http://localhost:5000/review?reviewer=Team Member 1`
2. **Team Member 2** starts reviewing at: `http://localhost:5000/review?reviewer=Team Member 2`

### Review Process
1. **Load Preview** - Click to see first 5 messages
2. **View Details** - Open full conversation in new tab if needed
3. **Add Notes** - Optional comments for quality control
4. **Accept/Reject** - Choose if conversation should be used for training
5. **Auto-scroll** - Interface automatically moves to next conversation

### Quality Guidelines for Fine-Tuning
- ✅ **Accept**: Natural agent-customer exchanges
- ✅ **Accept**: Good problem resolution examples  
- ✅ **Accept**: Professional agent responses
- ❌ **Reject**: Template-heavy conversations
- ❌ **Reject**: Spam or verification codes only
- ❌ **Reject**: Poor agent responses

### Advanced Message Editing
- Click **"View Details"** to open conversation editor
- Click **"Edit Conversation"** to enable advanced editing mode
- **Change Classifications** - Use dropdowns to fix agent/guest/bot/template labels
- **Edit Message Text** - Click edit button to modify message content
- **Add New Messages** - Click "Add Message" button to insert new messages
- **Remove Messages** - Click trash button to delete unwanted messages
- **Reorder Messages** - Drag messages up/down using the grip handle
- **Save Changes** - Apply all modifications to the conversation

## 📁 Data Flow

1. **Input**: 5,000 pre-selected high-quality conversations
2. **Process**: Team reviews and accepts/rejects each conversation
3. **Output**: Clean training data in JSONL format

## 🔧 Technical Details

### Database Schema
- **conversations** table: Tracks review status and notes
- **team_progress** table: Monitors team member statistics

### Export Format (JSONL)
```json
{"messages": [{"role": "user", "content": "Customer question"}, {"role": "assistant", "content": "Agent response"}]}
{"messages": [{"role": "user", "content": "Another question"}, {"role": "assistant", "content": "Another response"}]}
```

### File Structure
```
webapp/
├── app.py                 # Flask backend
├── requirements.txt       # Dependencies
├── conversations.db       # SQLite database (auto-created)
├── templates/
│   ├── base.html         # Common layout
│   ├── dashboard.html    # Main dashboard
│   ├── review.html       # Review interface
│   └── conversation.html # Detailed view
└── README.md             # This guide
```

## 🎯 Expected Outcome

After your team completes the review:
- **High-quality training data** with corrected classifications
- **Consistent labeling** across all conversations
- **Ready-to-use JSONL file** for fine-tuning
- **Progress tracking** and quality metrics

## 🆘 Troubleshooting

**Port already in use?**
```bash
python app.py
# If error, try different port:
python -c "from app import app; app.run(port=5001)"
```

**Database errors?**
```bash
rm conversations.db  # Delete and restart app to recreate
```

**Can't see conversations?**
- Check that the original conversation files are in `/Users/mahmouddinnawi/Desktop/chats`
- Ensure `quality_analysis_report.json` exists in the organized_whatsapp_conversations folder

---

**Ready to start organizing your fine-tuning data efficiently!** 🚀