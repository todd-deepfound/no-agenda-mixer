#!/usr/bin/env python3
"""
Production Test Suite for No Agenda Professional Mixer
Tests the complete production pipeline with real audio processing
"""

import json
import time
import sys
import requests
from datetime import datetime
from typing import Dict, Any

class ProductionTestSuite:
    """Complete test suite for production system"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or "https://your-production-url.execute-api.us-east-1.amazonaws.com/dev"
        self.test_results = []
        self.session_data = {}
    
    def log_test(self, test_name: str, status: str, message: str, details: Any = None):
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
        
        if details and isinstance(details, dict):
            for key, value in details.items():
                print(f"   {key}: {value}")
        elif details:
            print(f"   Details: {details}")
    
    def test_production_health(self) -> bool:
        """Test production health endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=30)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Production Health Check",
                    "PASS",
                    "System is healthy",
                    {
                        "response_time_ms": f"{response_time:.0f}",
                        "system_type": data.get('system_type'),
                        "version": data.get('version')
                    }
                )
                return True
            else:
                self.log_test("Production Health Check", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Production Health Check", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_mixer_health(self) -> bool:
        """Test professional mixer health endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/mix/health", timeout=30)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                components = data.get('components', {})
                
                self.log_test(
                    "Professional Mixer Health",
                    "PASS",
                    "Mixer system is healthy",
                    {
                        "response_time_ms": f"{response_time:.0f}",
                        "s3_bucket": components.get('s3_bucket'),
                        "librosa_available": components.get('librosa_available'),
                        "ffmpeg_available": components.get('ffmpeg_available'),
                        "themes_count": len(data.get('themes_available', []))
                    }
                )
                return True
            else:
                self.log_test("Professional Mixer Health", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Professional Mixer Health", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_professional_mixing(self) -> bool:
        """Test the complete professional mixing pipeline"""
        try:
            payload = {
                "episode_url": "https://op3.dev/e/mp3s.nashownotes.com/NA-1779-2025-07-06-Final.mp3",
                "theme": "Best Of",
                "target_duration": 90,  # 1.5 minutes for faster testing
                "session_id": f"test_{int(time.time())}"
            }
            
            print(f"🎧 Starting professional mixing test (this may take 2-5 minutes)...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/mix/professional",
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=600  # 10 minutes timeout
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    mix_meta = data.get('mix_metadata', {})
                    download = data.get('download', {})
                    analysis = data.get('analysis', {})
                    
                    self.session_data = {
                        'session_id': data.get('session_id'),
                        'download_url': download.get('url'),
                        's3_key': download.get('s3_key')
                    }
                    
                    self.log_test(
                        "Professional Mixing Pipeline",
                        "PASS",
                        "Complete mix created successfully",
                        {
                            "processing_time_minutes": f"{processing_time/60:.2f}",
                            "file_size_mb": mix_meta.get('file_size_mb'),
                            "segments_processed": analysis.get('segments_selected'),
                            "audio_duration": f"{analysis.get('audio_duration', 0):.1f}s",
                            "selection_method": analysis.get('selection_method'),
                            "confidence_score": f"{analysis.get('average_confidence', 0):.2f}",
                            "s3_key": download.get('s3_key')
                        }
                    )
                    return True
                else:
                    self.log_test("Professional Mixing Pipeline", "FAIL", 
                                f"Mix creation failed: {data.get('message')}")
                    return False
            else:
                self.log_test("Professional Mixing Pipeline", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Professional Mixing Pipeline", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_download_functionality(self) -> bool:
        """Test the download functionality of created mix"""
        if not self.session_data.get('download_url'):
            self.log_test("Download Functionality", "SKIP", "No download URL available")
            return False
        
        try:
            # Test download URL (HEAD request to avoid downloading full file)
            response = requests.head(self.session_data['download_url'], timeout=30)
            
            if response.status_code == 200:
                content_length = response.headers.get('Content-Length', 'unknown')
                content_type = response.headers.get('Content-Type', 'unknown')
                
                self.log_test(
                    "Download Functionality",
                    "PASS",
                    "Download URL is accessible",
                    {
                        "content_length": content_length,
                        "content_type": content_type,
                        "s3_key": self.session_data.get('s3_key')
                    }
                )
                return True
            else:
                self.log_test("Download Functionality", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Download Functionality", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_mix_history(self) -> bool:
        """Test mix history endpoint"""
        try:
            response = requests.get(f"{self.base_url}/mix/history", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                mixes = data.get('mixes', [])
                
                self.log_test(
                    "Mix History",
                    "PASS",
                    "History retrieved successfully",
                    {
                        "total_mixes": len(mixes),
                        "history_status": data.get('status')
                    }
                )
                return True
            else:
                self.log_test("Mix History", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Mix History", "FAIL", f"Request failed: {str(e)}")
            return False
    
    def test_cors_compliance(self) -> bool:
        """Test CORS compliance across endpoints"""
        endpoints = ['/health', '/mix/health', '/mix/professional', '/mix/history']
        
        all_passed = True
        for endpoint in endpoints:
            try:
                response = requests.options(f"{self.base_url}{endpoint}", timeout=10)
                
                required_headers = [
                    'Access-Control-Allow-Origin',
                    'Access-Control-Allow-Methods',
                    'Access-Control-Allow-Headers'
                ]
                
                missing_headers = [h for h in required_headers if h not in response.headers]
                
                if not missing_headers and response.status_code == 200:
                    continue  # This endpoint passed
                else:
                    all_passed = False
                    break
                    
            except Exception:
                all_passed = False
                break
        
        if all_passed:
            self.log_test("CORS Compliance", "PASS", "All endpoints support CORS")
            return True
        else:
            self.log_test("CORS Compliance", "FAIL", "CORS issues detected")
            return False
    
    def run_full_production_test(self) -> bool:
        """Run complete production test suite"""
        print("🧪 Starting Production Test Suite for No Agenda Professional Mixer")
        print("=" * 80)
        
        tests = [
            ("Basic Health", self.test_production_health),
            ("Mixer Health", self.test_mixer_health),
            ("CORS Compliance", self.test_cors_compliance),
            ("Professional Mixing", self.test_professional_mixing),
            ("Download Functionality", self.test_download_functionality),
            ("Mix History", self.test_mix_history)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔄 Running {test_name}...")
            try:
                if test_func():
                    passed += 1
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Test execution failed: {str(e)}")
        
        print("\n" + "=" * 80)
        print("🎯 PRODUCTION TEST RESULTS")
        print("=" * 80)
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}")
        
        success_rate = (passed / total) * 100
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL PRODUCTION TESTS PASSED!")
            print("🚀 System is ready for production use!")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed.")
            print("🔧 System needs attention before production deployment.")
            return False
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate detailed test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
            'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
            'skipped': sum(1 for r in self.test_results if r['status'] == 'SKIP'),
            'test_results': self.test_results,
            'session_data': self.session_data
        }
        
        with open('production_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Detailed test report saved to: production_test_report.json")
        return report

def main():
    """Main function for production testing"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not base_url:
        print("❌ Please provide the production URL:")
        print("   python3 production_test.py https://your-api-url.execute-api.us-east-1.amazonaws.com/dev")
        sys.exit(1)
    
    print(f"🎧 Testing No Agenda Professional Mixer (Production)")
    print(f"🌐 Base URL: {base_url}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = ProductionTestSuite(base_url)
    success = tester.run_full_production_test()
    tester.generate_test_report()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()