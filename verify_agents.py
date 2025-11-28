#!/usr/bin/env python3
"""
Verify that all agents are properly set up and can be imported.
Run this before testing with ADK.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def verify_imports():
    """Verify all agents can be imported."""
    print("Verifying agent imports...")
    print("=" * 60)
    
    # Check if google-adk is installed
    try:
        import google.adk
        print("✅ google-adk package is installed")
    except ImportError:
        print("❌ google-adk package not found")
        print("   Install it with: pip install google-adk")
        return False
    
    errors = []
    
    # Test root agent
    try:
        from utsava_agent.agent import root_agent
        print("✅ root_agent imported successfully")
        print(f"   Name: {root_agent.name}")
        print(f"   Tools: {len(root_agent.tools)}")
    except Exception as e:
        print(f"❌ root_agent import failed: {e}")
        errors.append("root_agent")
    
    # Test coordinator agent
    try:
        from utsava_agent.coordinator import coordinator_agent
        print("✅ coordinator_agent imported successfully")
        print(f"   Name: {coordinator_agent.name}")
        print(f"   Tools: {len(coordinator_agent.tools)}")
        print(f"   Tool names: {[getattr(t, '__name__', str(t)) for t in coordinator_agent.tools[:5]]}")
    except Exception as e:
        print(f"❌ coordinator_agent import failed: {e}")
        errors.append("coordinator_agent")
    
    # Test specialized agents
    agents_to_test = [
        ("research_agent", "utsava_agent.agents.research_agent"),
        ("preparation_agent", "utsava_agent.agents.preparation_agent"),
        ("experience_agent", "utsava_agent.agents.experience_agent"),
        ("content_agent", "utsava_agent.agents.content_agent"),
    ]
    
    for agent_name, module_path in agents_to_test:
        try:
            module = __import__(module_path, fromlist=[agent_name])
            agent = getattr(module, agent_name)
            print(f"✅ {agent_name} imported successfully")
            print(f"   Name: {agent.name}")
            print(f"   Tools: {len(agent.tools)}")
        except Exception as e:
            print(f"❌ {agent_name} import failed: {e}")
            errors.append(agent_name)
    
    print("=" * 60)
    
    if errors:
        print(f"\n❌ {len(errors)} agent(s) failed to import:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("\n✅ All agents imported successfully!")
        print("\nYou can now test with ADK:")
        print("   ./test_adk.sh")
        print("   or")
        print("   adk web --port 8000")
        return True

if __name__ == "__main__":
    success = verify_imports()
    sys.exit(0 if success else 1)

