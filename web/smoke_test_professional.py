#!/usr/bin/env python3
"""
Smoke Test for Professional Audio Mixer
Tests the newly deployed professional mixer endpoints
"""

import requests
import json
import time
import sys
from datetime import datetime

class ProfessionalMixerSmokeTest:
    def __init__(self, base_url="https://6dnp3ugbc8.execute-api.us-east-1.amazonaws.com/dev"):
        self.base_url = base_url
        self.test_results = []
    
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
    
    def test_professional_health(self):
        """Test professional mixer health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health-pro", timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "Professional Health", 
                    "PASS", 
                    "Professional mixer health check passed"
                )
                return True
            else:
                self.log_test("Professional Health", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Professional Health", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_professional_mix_endpoint(self):
        """Test professional mixing endpoint"""
        try:
            payload = {
                "episode_url": "https://op3.dev/e/mp3s.nashownotes.com/NA-1779-2025-07-06-Final.mp3",
                "theme": "Best Of",
                "target_duration": 60  # Short test
            }
            
            response = requests.post(
                f"{self.base_url}/mix/professional-lite",
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_test(
                        "Professional Mixing", 
                        "PASS", 
                        "Professional mix created successfully",
                        f"Theme: {data.get('theme')}, Type: {data.get('processing_type')}"
                    )
                    return True
                else:
                    self.log_test("Professional Mixing", "FAIL", "Mix creation failed")
                    return False
            else:
                self.log_test("Professional Mixing", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Professional Mixing", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_cors_professional(self):
        """Test CORS on professional endpoints"""
        try:
            response = requests.options(f"{self.base_url}/mix/professional-lite", timeout=10)
            
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
                    "Professional CORS", 
                    "PASS", 
                    "All CORS headers present"
                )
                return True
            else:
                self.log_test(
                    "Professional CORS", 
                    "FAIL", 
                    f"Missing headers: {missing_headers}"
                )
                return False
                
        except Exception as e:
            self.log_test("Professional CORS", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_performance_professional(self):
        """Test professional mixer performance"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health-pro", timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ms
            
            if response.status_code == 200 and response_time < 3000:  # Under 3 seconds
                self.log_test(
                    "Professional Performance", 
                    "PASS", 
                    f"Response time acceptable",
                    f"{response_time:.0f}ms"
                )
                return True
            else:
                self.log_test(
                    "Professional Performance", 
                    "WARN", 
                    f"Slow response",
                    f"{response_time:.0f}ms"
                )
                return False
                
        except Exception as e:
            self.log_test("Professional Performance", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all professional mixer tests"""
        print("🎧 Starting Professional Audio Mixer Smoke Tests")
        print("=" * 60)
        
        tests = [
            self.test_professional_health,
            self.test_cors_professional,
            self.test_performance_professional,
            self.test_professional_mix_endpoint
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
        print("🎯 PROFESSIONAL MIXER TEST RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"📊 Total: {len(self.test_results)}")
        
        if failed == 0:
            print("\n🎉 ALL PROFESSIONAL MIXER TESTS PASSED!")
            return True
        else:
            print(f"\n⚠️  {failed} tests failed. Professional mixer needs attention.")
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
        
        with open('professional_mixer_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Professional mixer report saved to: professional_mixer_test_report.json")
        return report

def main():
    """Main function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://6dnp3ugbc8.execute-api.us-east-1.amazonaws.com/dev"
    
    print(f"🎧 Testing Professional Audio Mixer")
    print(f"🌐 Base URL: {base_url}")
    print()
    
    tester = ProfessionalMixerSmokeTest(base_url)
    success = tester.run_all_tests()
    tester.generate_report()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()