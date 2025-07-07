#!/usr/bin/env python3
"""
Comprehensive Smoke Test for No Agenda Professional Mixer
Tests all endpoints and functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

class NoAgendaMixerSmokeTest:
    def __init__(self, base_url="https://4as1uxx25a.execute-api.us-east-1.amazonaws.com/dev"):
        self.base_url = base_url
        self.test_results = []
        self.session_id = None
    
    def log_test(self, test_name, status, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} {test_name}: {message}")
        
        if details:
            print(f"   Details: {details}")
    
    def test_health_endpoint(self):
        """Test system health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test(
                        "Health Check", 
                        "PASS", 
                        "System is healthy",
                        f"GROK: {data.get('has_grok_key')}, FAL: {data.get('has_fal_key')}"
                    )
                    return True
                else:
                    self.log_test("Health Check", "FAIL", "System reports unhealthy")
                    return False
            else:
                self.log_test("Health Check", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_session_creation(self):
        """Test session creation"""
        try:
            payload = {
                "episode_number": 1779,
                "theme": "Best Of"
            }
            
            response = requests.post(
                f"{self.base_url}/api/start_session",
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'session_id' in data:
                    self.session_id = data['session_id']
                    self.log_test(
                        "Session Creation", 
                        "PASS", 
                        "Session created successfully",
                        f"ID: {self.session_id[:8]}..."
                    )
                    return True
                else:
                    self.log_test("Session Creation", "FAIL", "No session ID returned")
                    return False
            else:
                self.log_test("Session Creation", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Session Creation", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_ideas_generation(self):
        """Test AI ideas generation"""
        if not self.session_id:
            self.log_test("Ideas Generation", "SKIP", "No session ID available")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate_ideas/{self.session_id}",
                headers={'Content-Type': 'application/json'},
                json={},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    ideas = data.get('ideas', {})
                    segments = ideas.get('ideas', {}).get('segments', [])
                    self.log_test(
                        "Ideas Generation", 
                        "PASS", 
                        "Ideas generated successfully",
                        f"Generated {len(segments)} segments"
                    )
                    return True
                else:
                    self.log_test("Ideas Generation", "FAIL", "Generation failed")
                    return False
            else:
                self.log_test("Ideas Generation", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Ideas Generation", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_music_generation(self):
        """Test music generation"""
        if not self.session_id:
            self.log_test("Music Generation", "SKIP", "No session ID available")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate_music/{self.session_id}",
                headers={'Content-Type': 'application/json'},
                json={},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    music = data.get('music', {})
                    self.log_test(
                        "Music Generation", 
                        "PASS", 
                        "Music generated successfully",
                        f"Prompt: {music.get('prompt', 'N/A')[:50]}..."
                    )
                    return True
                else:
                    self.log_test("Music Generation", "FAIL", "Generation failed")
                    return False
            else:
                self.log_test("Music Generation", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Music Generation", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_session_retrieval(self):
        """Test session data retrieval"""
        if not self.session_id:
            self.log_test("Session Retrieval", "SKIP", "No session ID available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/session/{self.session_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'session_id' in data:
                    ideas_count = len(data.get('ideas', []))
                    music_count = len(data.get('music_generations', []))
                    self.log_test(
                        "Session Retrieval", 
                        "PASS", 
                        "Session retrieved successfully",
                        f"Ideas: {ideas_count}, Music: {music_count}"
                    )
                    return True
                else:
                    self.log_test("Session Retrieval", "FAIL", "Invalid session data")
                    return False
            else:
                self.log_test("Session Retrieval", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Session Retrieval", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_cors_compliance(self):
        """Test CORS headers"""
        try:
            response = requests.options(f"{self.base_url}/health", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            missing_headers = []
            for header in cors_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            if not missing_headers:
                self.log_test(
                    "CORS Compliance", 
                    "PASS", 
                    "All CORS headers present"
                )
                return True
            else:
                self.log_test(
                    "CORS Compliance", 
                    "FAIL", 
                    f"Missing headers: {missing_headers}"
                )
                return False
                
        except Exception as e:
            self.log_test("CORS Compliance", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling"""
        try:
            # Test invalid endpoint
            response = requests.get(f"{self.base_url}/invalid/endpoint", timeout=10)
            
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        self.log_test(
                            "Error Handling", 
                            "PASS", 
                            "Proper error responses"
                        )
                        return True
                except:
                    pass
            
            self.log_test("Error Handling", "FAIL", "Invalid error response format")
            return False
            
        except Exception as e:
            self.log_test("Error Handling", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_performance(self):
        """Test basic performance"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ms
            
            if response.status_code == 200 and response_time < 2000:  # Under 2 seconds
                self.log_test(
                    "Performance", 
                    "PASS", 
                    f"Response time acceptable",
                    f"{response_time:.0f}ms"
                )
                return True
            else:
                self.log_test(
                    "Performance", 
                    "WARN", 
                    f"Slow response",
                    f"{response_time:.0f}ms"
                )
                return False
                
        except Exception as e:
            self.log_test("Performance", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive smoke tests"""
        print("🧪 Starting No Agenda Professional Mixer Smoke Tests")
        print("=" * 60)
        
        tests = [
            self.test_health_endpoint,
            self.test_cors_compliance,
            self.test_performance,
            self.test_session_creation,
            self.test_ideas_generation,
            self.test_music_generation,
            self.test_session_retrieval,
            self.test_error_handling
        ]
        
        passed = 0
        failed = 0
        warnings = 0
        
        for test in tests:
            try:
                result = test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_test(test.__name__, "FAIL", f"Test execution failed: {str(e)}")
                failed += 1
            
            time.sleep(1)  # Brief pause between tests
        
        # Count warnings
        warnings = sum(1 for r in self.test_results if r['status'] == 'WARN')
        
        print("\n" + "=" * 60)
        print("🎯 SMOKE TEST RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"📊 Total: {len(self.test_results)}")
        
        if failed == 0:
            print("\n🎉 ALL SMOKE TESTS PASSED! System is ready for production.")
            return True
        else:
            print(f"\n⚠️  {failed} tests failed. System needs attention before production.")
            return False
    
    def generate_report(self):
        """Generate detailed test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'warnings': sum(1 for r in self.test_results if r['status'] == 'WARN'),
            'tests': self.test_results
        }
        
        with open('smoke_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Detailed report saved to: smoke_test_report.json")
        return report

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://4as1uxx25a.execute-api.us-east-1.amazonaws.com/dev"
    
    print(f"🎧 Testing No Agenda Professional Mixer")
    print(f"🌐 Base URL: {base_url}")
    print()
    
    tester = NoAgendaMixerSmokeTest(base_url)
    success = tester.run_all_tests()
    tester.generate_report()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()