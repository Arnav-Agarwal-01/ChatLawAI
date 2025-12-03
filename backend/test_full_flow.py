#!/usr/bin/env python3
"""Test full consultation flow with final report"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_full_consultation():
    print("=" * 60)
    print("Testing Full Consultation Flow with AI Models")
    print("=" * 60)
    
    # 1. Start consultation
    print("\n1. Starting consultation...")
    response = requests.post(
        f"{BASE_URL}/consult/start",
        json={"query": "robbery happened yesterday at my shop", "max_turns": 3}
    )
    data = response.json()
    session_id = data['session_id']
    print(f"   Session ID: {session_id}")
    print(f"   First question: {data['question']}")
    print(f"   Has partial_report: {'partial_report' in data}")
    
    # 2. Answer first question
    print("\n2. Answering Q1...")
    response = requests.post(
        f"{BASE_URL}/consult/answer",
        json={"session_id": session_id, "answer": "around 5pm yesterday"}
    )
    data = response.json()
    print(f"   Next action: {data['next_action']}")
    print(f"   Next question: {data.get('question', 'N/A')}")
    
    # 3. Answer second question
    print("\n3. Answering Q2...")
    response = requests.post(
        f"{BASE_URL}/consult/answer",
        json={"session_id": session_id, "answer": "in my electronics shop"}
    )
    data = response.json()
    print(f"   Next action: {data['next_action']}")
    print(f"   Next question: {data.get('question', 'N/A')}")
    
    # 4. Answer third question (should trigger final)
    print("\n4. Answering Q3 (final)...")
    response = requests.post(
        f"{BASE_URL}/consult/answer",
        json={"session_id": session_id, "answer": "yes knife was used"}
    )
    data = response.json()
    print(f"   Response keys: {list(data.keys())}")
    print(f"   Next action: {data.get('next_action', 'NOT IN RESPONSE')}")
    
    # Check if final based on response structure
    is_final = 'report' in data or data.get('next_action') == 'final'
    
    if is_final:
        print("   ✅ Got final response!")
        if 'report' in data:
            print(f"   ✅ Has 'report' field (length: {len(data['report'])} chars)")
            print("\n   Report preview:")
            print("   " + data['report'][:300].replace('\n', '\n   '))
            print("   ...")
        else:
            print("   ❌ No 'report' field in response!")
            print(f"   Response data: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"   ❌ Expected final response but got: {data}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_consultation()
