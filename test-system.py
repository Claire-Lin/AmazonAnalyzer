#!/usr/bin/env python3
"""
Quick test script for Amazon Product Analyzer
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_environment():
    """Test environment setup"""
    print("🔧 Testing Environment Setup...")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print(f"✅ OpenAI API Key: {api_key[:20]}...")
    return True

def test_scraper():
    """Test Amazon scraper"""
    print("\n🕷️ Testing Amazon Scraper...")
    
    try:
        from utils.amazon_scraper import AmazonScraper
        
        # Test with the provided URL
        url = "https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL"
        
        scraper = AmazonScraper(headless=True)
        result = scraper.scrape_product(url)
        
        if result and result.get('success'):
            print(f"✅ Successfully scraped: {result.get('title', 'Unknown')[:50]}...")
            print(f"   Price: {result.get('price', 'N/A')} {result.get('currency', '')}")
            print(f"   ASIN: {result.get('asin', 'N/A')}")
            return True
        else:
            print("❌ Scraping failed or returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\n🗄️ Testing Database...")
    
    try:
        from models.database import init_db
        
        asyncio.run(init_db())
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_api():
    """Test FastAPI application"""
    print("\n🌐 Testing API...")
    
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_analysis_flow():
    """Test complete analysis flow"""
    print("\n🤖 Testing Analysis Flow...")
    
    try:
        from agents.supervisor import analyze_product
        
        url = "https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL"
        
        print("   Starting analysis (this may take a moment)...")
        result = analyze_product(url, session_id="test-123")
        
        if result and result.get('success'):
            print("✅ Analysis workflow completed successfully")
            print(f"   Session ID: {result.get('session_id', 'N/A')}")
            return True
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis flow test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Amazon Product Analyzer - System Test")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Scraper", test_scraper),
        ("Database", test_database),
        ("API", test_api),
        # ("Analysis Flow", test_analysis_flow),  # Skip for quick test
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except KeyboardInterrupt:
            print("\n\n🛑 Tests interrupted by user")
            break
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready!")
        print("\n🚀 Quick Start:")
        print("1. cd /Users/clairelin/Documents/TransBiz/AmazonAnalyzer")
        print("2. ./run-local.sh  # Start backend")
        print("3. Open http://localhost:8000/docs")
        print("4. Test with: https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    sys.exit(0 if main() else 1)