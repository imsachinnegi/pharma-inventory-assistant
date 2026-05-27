# 💊 Pharma Inventory Assistant

An AI-powered inventory management system for pharmaceutical companies.

## Features
- ✅ Add/Search medicines
- ✅ Track inventory levels
- ✅ Monitor expiry dates
- ✅ Low stock alerts
- ✅ AI-powered chatbot interface

## Installation

```bash
pip install -r requirements.txt
```

## Running the Application

Terminal 1 - Start MCP Server:
```bash
python server.py
```

Terminal 2 - Start Flask App:
```bash
python app.py
```

Then open: http://127.0.0.1:5000

## Commands
- `show inventory` - View all medicines
- `add medicine [details]` - Add new medicine
- `low stock` - Show low stock items
- `expiring soon` - Show medicines expiring soon
- `search [name]` - Search for medicine
- `delete [name]` - Delete medicine

## Technology Stack
- Flask (Backend)
- SQLite (Database)
- Ollama + LLaMA (AI)
- MCP (Model Context Protocol)

## Author
Sachin Negi