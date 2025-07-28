#!/usr/bin/env python3
"""
Database Management Script
Provides functions to clear/reset the database collections
"""

import sys
from pathlib import Path

# Add app directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from app.database import PromptDB, SessionDB, PinDB

def clear_database():
    """Clear all data from pins, sessions, and prompts collections"""
    
    print("🗑️  Clearing database collections...")
    print("=" * 50)
    
    # Get counts before deletion
    pins_count = len(PinDB.get_many())
    sessions_count = len(SessionDB.get_many())
    prompts_count = len(PromptDB.get_many())
    
    print(f"Before deletion:")
    print(f"  Pins: {pins_count}")
    print(f"  Sessions: {sessions_count}")
    print(f"  Prompts: {prompts_count}")
    
    if pins_count == 0 and sessions_count == 0 and prompts_count == 0:
        print("\n✅ Database is already empty!")
        return
    
    # Confirm deletion
    print(f"\n⚠️  This will permanently delete ALL data from the database!")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm != 'DELETE':
        print("❌ Operation cancelled")
        return
    
    # Delete all documents
    print("\n🗑️  Deleting documents...")
    
    # Delete pins
    pins_result = PinDB.collection.delete_many({})
    print(f"  Deleted {pins_result.deleted_count} pins")
    
    # Delete sessions
    sessions_result = SessionDB.collection.delete_many({})
    print(f"  Deleted {sessions_result.deleted_count} sessions")
    
    # Delete prompts
    prompts_result = PromptDB.collection.delete_many({})
    print(f"  Deleted {prompts_result.deleted_count} prompts")
    
    # Verify deletion
    remaining_pins = len(PinDB.get_many())
    remaining_sessions = len(SessionDB.get_many())
    remaining_prompts = len(PromptDB.get_many())
    
    print(f"\nAfter deletion:")
    print(f"  Pins: {remaining_pins}")
    print(f"  Sessions: {remaining_sessions}")
    print(f"  Prompts: {remaining_prompts}")
    
    if remaining_pins == 0 and remaining_sessions == 0 and remaining_prompts == 0:
        print("\n✅ Database cleared successfully!")
    else:
        print("\n⚠️  Some documents may not have been deleted")

def show_database_status():
    """Show current database status and document counts"""
    
    print("📊 Database Status")
    print("=" * 50)
    
    # Get all documents
    pins = PinDB.get_many()
    sessions = SessionDB.get_many()
    prompts = PromptDB.get_many()
    
    print(f"Total Documents:")
    print(f"  📌 Pins: {len(pins)}")
    print(f"  🔄 Sessions: {len(sessions)}")
    print(f"  💭 Prompts: {len(prompts)}")
    
    if pins:
        # Show pin status breakdown
        status_counts = {}
        for pin in pins:
            status = pin.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\nPin Status Breakdown:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
    
    if sessions:
        # Show session status breakdown
        session_status_counts = {}
        for session in sessions:
            status = session.get('status', 'unknown')
            session_status_counts[status] = session_status_counts.get(status, 0) + 1
        
        print(f"\nSession Status Breakdown:")
        for status, count in session_status_counts.items():
            print(f"  {status}: {count}")
    
    if prompts:
        # Show prompt status breakdown
        prompt_status_counts = {}
        for prompt in prompts:
            status = prompt.get('status', 'unknown')
            prompt_status_counts[status] = prompt_status_counts.get(status, 0) + 1
        
        print(f"\nPrompt Status Breakdown:")
        for status, count in prompt_status_counts.items():
            print(f"  {status}: {count}")
        
        # Show recent prompts
        print(f"\nRecent Prompts:")
        recent_prompts = sorted(prompts, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        for i, prompt in enumerate(recent_prompts, 1):
            created_at = prompt.get('created_at', 'Unknown')
            text = prompt.get('text', 'No text')[:50]
            status = prompt.get('status', 'unknown')
            print(f"  {i}. {text}... ({status}) - {created_at}")

def main():
    """Main function with menu options"""
    
    print("🗄️  Database Management Tool")
    print("=" * 50)
    print("1. Show database status")
    print("2. Clear all database collections")
    print("3. Exit")
    
    while True:
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            print()
            show_database_status()
        elif choice == '2':
            print()
            clear_database()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()
