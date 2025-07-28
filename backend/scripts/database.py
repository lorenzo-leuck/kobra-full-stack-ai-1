#!/usr/bin/env python3
"""
Database Management Script
Provides functions to clear/reset the database collections
"""

import sys
import argparse
from pathlib import Path

# Add app directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from app.database import PromptDB, SessionDB, PinDB, AgentDB

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
    
    print(f"\n⚠️  Deleting ALL data from database...")
    
    # Delete all documents
    print("\n🗑️  Deleting documents...")
    
    # Delete pins
    pins_collection = PinDB.get_collection()
    pins_result = pins_collection.delete_many({})
    print(f"  Deleted {pins_result.deleted_count} pins")
    
    # Delete sessions
    sessions_collection = SessionDB.get_collection()
    sessions_result = sessions_collection.delete_many({})
    print(f"  Deleted {sessions_result.deleted_count} sessions")
    
    # Delete prompts
    prompts_collection = PromptDB.get_collection()
    prompts_result = prompts_collection.delete_many({})
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

def setup_agents():
    """Setup default agent configurations"""
    print("🤖 Setting up agent configurations...")
    print("=" * 50)
    
    # Pin Evaluator Agent Configuration
    system_prompt = """You are an expert at evaluating how well Pinterest images match visual prompts.

Your task is to analyze both the visual content of an image AND its textual metadata (title, description) to determine how well they collectively match the given prompt.

Scoring guidelines:
- 0.8-1.0: Excellent match - image and text perfectly capture the prompt's style, mood, and elements
- 0.6-0.79: Good match - image and text capture most key aspects of the prompt
- 0.4-0.59: Partial match - image and text capture some elements but missing key aspects
- 0.2-0.39: Poor match - image and text have minimal connection to the prompt
- 0.0-0.19: No match - image and text don't relate to the prompt at all

Evaluation criteria:
- Visual elements: style, mood, colors, composition, objects, setting
- Textual relevance: how well title and description align with the prompt
- Combined coherence: how well visual and textual elements work together

Status rules:
- "approved" if match_score ≥ 0.5
- "disqualified" if match_score < 0.5

Provide a clear 2-3 sentence explanation focusing on both visual and textual elements that support your score."""
    
    user_prompt_template = """Evaluate how well this image matches the prompt: "{prompt_text}"
{textual_context}

Analyze both the visual elements (style, mood, aesthetic) and the textual context (title, description) to determine the match quality. Consider how well the combination of visual and textual information aligns with the requested prompt."""
    
    agent_id = AgentDB.create_or_update_agent(
        title="pin-evaluator",
        model="gpt-4o",
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template,
        temperature=0.3  # Lower temperature for more consistent evaluations
    )
    
    print(f"✅ Created/updated pin-evaluator agent (ID: {agent_id})")
    print("   Model: gpt-4o")
    print("   Temperature: 0.3 (consistent evaluations)")
    print("   System prompt: Configured for Pinterest image evaluation")
    print("   User prompt template: Configured for multimodal analysis")
    print("\n🎯 Agent setup completed!")

def main():
    """Main function with menu options or command line arguments"""
    
    parser = argparse.ArgumentParser(
        description="Database Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 scripts/database.py --clear     # Clear database immediately
  python3 scripts/database.py --status    # Show database status
  python3 scripts/database.py             # Interactive menu"""
    )
    
    parser.add_argument(
        "--clear", 
        action="store_true", 
        help="Clear all database collections immediately"
    )
    parser.add_argument(
        "--status", 
        action="store_true", 
        help="Show database status and exit"
    )
    parser.add_argument(
        "--setup-agents", 
        action="store_true", 
        help="Setup default agent configurations"
    )
    
    args = parser.parse_args()
    
    # Handle command line arguments
    if args.clear:
        print("🗄️  Database Management Tool - Clear Mode")
        print("=" * 50)
        clear_database()
        return
    
    if args.status:
        print("🗄️  Database Management Tool - Status Mode")
        print("=" * 50)
        show_database_status()
        return
    
    if getattr(args, 'setup_agents', False):
        print("🗄️  Database Management Tool - Agent Setup Mode")
        print("=" * 50)
        setup_agents()
        return
    
    # Interactive menu mode
    print("🗄️  Database Management Tool")
    print("=" * 50)
    print("1. Show database status")
    print("2. Clear all database collections")
    print("3. Setup agent configurations")
    print("4. Exit")
    
    while True:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            print()
            show_database_status()
        elif choice == '2':
            print()
            clear_database()
        elif choice == '3':
            print()
            setup_agents()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
