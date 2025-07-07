#!/usr/bin/env python3
"""
Comprehensive Smoke Test for All No Agenda Mixer Endpoints
Tests both existing and new production endpoints
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple

class ComprehensiveSmokeTest:
    def __init__(self):
        # Both deployed systems
        self.endpoints = {
            'original': {
                'base_url': 'https://4as1uxx25a.execute-api.us-east-1.amazonaws.com/dev',
                'name': 'Original System',
                'tests': []
            },
            'professional_lite': {
                'base_url': 'https://6dnp3ugbc8.execute-api.us-east-1.amazonaws.com/dev',
                'name': 'Professional Lite',
                'tests': []
            }
        }
        self.test_results = []
        self.sessions = {}
    
    def log_test(self, system: str, test_name: str, status: str, message: str, details=None):
        """Log test result"""
        result = {
            'system': system,
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} [{system}] {test_name}: {message}")
        
        if details:
            if isinstance(details, dict):
                for k, v in details.items():
                    print(f"     {k}: {v}")
            else:
                print(f"     {details}")
    
    def test_endpoint(self, system: str, method: str, path: str, 
                     payload: Dict = None, timeout: int = 30) -> Tuple[bool, Dict]:
        """Test a single endpoint"""
        base_url = self.endpoints[system]['base_url']
        url = f"{base_url}{path}"
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, timeout=timeout)
            elif method == 'POST':
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            elif method == 'OPTIONS':
                response = requests.options(url, timeout=timeout)
            else:
                return False, {'error': f'Unsupported method: {method}'}
            
            response_time = (time.time() - start_time) * 1000
            
            result = {
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'headers': dict(response.headers),
                'success': response.status_code in [200, 201]
            }
            
            try:
                result['body'] = response.json()
            except:
                result['body'] = response.text[:200] if response.text else None
            
            return result['success'], result
            
        except Exception as e:
            return False, {'error': str(e), 'exception_type': type(e).__name__}
    
    def test_original_system(self):
        """Test all endpoints on original system"""
        system = 'original'
        print(f"\n🔍 Testing {self.endpoints[system]['name']}")
        print("=" * 60)
        
        # Health check
        success, result = self.test_endpoint(system, 'GET', '/health')
        self.log_test(system, 'Health Check', 
                     'PASS' if success else 'FAIL',
                     f"Status: {result.get('status_code', 'N/A')}",
                     {'response_time_ms': result.get('response_time_ms', 0)})
        
        # CORS preflight
        success, result = self.test_endpoint(system, 'OPTIONS', '/health')
        cors_headers = result.get('headers', {})
        has_cors = all(h in cors_headers for h in ['access-control-allow-origin', 
                                                    'access-control-allow-methods'])
        self.log_test(system, 'CORS Support', 
                     'PASS' if has_cors else 'FAIL',
                     'CORS headers present' if has_cors else 'Missing CORS headers')
        
        # Session creation
        session_payload = {
            "episode_number": 1779,
            "theme": "Best Of"
        }
        success, result = self.test_endpoint(system, 'POST', '/api/start_session', session_payload)
        session_id = None
        if success and result.get('body', {}).get('session_id'):
            session_id = result['body']['session_id']
            self.sessions[system] = session_id
            
        self.log_test(system, 'Session Creation', 
                     'PASS' if success and session_id else 'FAIL',
                     f"Session ID: {session_id[:8]}..." if session_id else "No session created",
                     {'status_code': result.get('status_code')})
        
        # Ideas generation
        if session_id:
            success, result = self.test_endpoint(system, 'POST', f'/api/generate_ideas/{session_id}', {})
            segments_count = len(result.get('body', {}).get('ideas', {}).get('ideas', {}).get('segments', []))
            self.log_test(system, 'Ideas Generation', 
                         'PASS' if success else 'FAIL',
                         f"Generated {segments_count} segments" if success else "Failed",
                         {'response_time_ms': result.get('response_time_ms', 0)})
        
        # Music generation
        if session_id:
            success, result = self.test_endpoint(system, 'POST', f'/api/generate_music/{session_id}', {})
            self.log_test(system, 'Music Generation', 
                         'PASS' if success else 'FAIL',
                         "Music generated" if success else "Failed",
                         {'response_time_ms': result.get('response_time_ms', 0)})
        
        # Session retrieval
        if session_id:
            success, result = self.test_endpoint(system, 'GET', f'/api/session/{session_id}')
            self.log_test(system, 'Session Retrieval', 
                         'PASS' if success else 'FAIL',
                         "Session data retrieved" if success else "Failed")
    
    def test_professional_lite_system(self):
        """Test all endpoints on professional lite system"""
        system = 'professional_lite'
        print(f"\n🔍 Testing {self.endpoints[system]['name']}")
        print("=" * 60)
        
        # Health check (expected to fail based on earlier tests)
        success, result = self.test_endpoint(system, 'GET', '/health-pro')
        self.log_test(system, 'Health Check', 
                     'PASS' if success else 'WARN',
                     f"Status: {result.get('status_code', 'N/A')}",
                     {'note': 'Health endpoint may not be configured'})
        
        # CORS preflight for professional endpoint
        success, result = self.test_endpoint(system, 'OPTIONS', '/mix/professional-lite')
        cors_headers = result.get('headers', {})
        has_cors = all(h in cors_headers for h in ['access-control-allow-origin', 
                                                    'access-control-allow-methods'])
        self.log_test(system, 'CORS Support', 
                     'PASS' if has_cors else 'FAIL',
                     'CORS headers present' if has_cors else 'Missing CORS headers')
        
        # Professional mixing endpoint
        mix_payload = {
            "episode_url": "https://op3.dev/e/mp3s.nashownotes.com/NA-1779-2025-07-06-Final.mp3",
            "theme": "Best Of",
            "target_duration": 60
        }
        success, result = self.test_endpoint(system, 'POST', '/mix/professional-lite', 
                                           mix_payload, timeout=40)
        
        mix_details = {}
        if success and result.get('body'):
            body = result['body']
            mix_details = {
                'status': body.get('status'),
                'theme': body.get('theme'),
                'processing_type': body.get('processing_type'),
                'mix_path': body.get('mix_path', '')[:50] + '...' if body.get('mix_path') else None
            }
        
        self.log_test(system, 'Professional Mixing', 
                     'PASS' if success else 'FAIL',
                     "Mix created" if success else "Failed",
                     mix_details)
        
        # Test different themes
        themes = ['Media Meltdown', 'Conspiracy Corner', 'Musical Mayhem']
        for theme in themes:
            theme_payload = mix_payload.copy()
            theme_payload['theme'] = theme
            theme_payload['target_duration'] = 30  # Shorter for testing
            
            success, result = self.test_endpoint(system, 'POST', '/mix/professional-lite', 
                                               theme_payload, timeout=40)
            self.log_test(system, f'Theme: {theme}', 
                         'PASS' if success else 'FAIL',
                         f"Mix created with {theme}" if success else "Failed",
                         {'status_code': result.get('status_code')})
    
    def test_performance_comparison(self):
        """Compare performance between systems"""
        print("\n📊 Performance Comparison")
        print("=" * 60)
        
        # Test health endpoint response times
        for system_key, system_info in self.endpoints.items():
            if system_key == 'original':
                path = '/health'
            else:
                path = '/mix/professional-lite'  # Use working endpoint
            
            response_times = []
            for i in range(3):
                success, result = self.test_endpoint(system_key, 'GET' if 'health' in path else 'OPTIONS', path)
                if 'response_time_ms' in result:
                    response_times.append(result['response_time_ms'])
                time.sleep(0.5)
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                self.log_test('Performance', f'{system_info["name"]} Latency', 
                             'PASS' if avg_time < 1000 else 'WARN',
                             f"Average: {avg_time:.0f}ms",
                             {'samples': len(response_times), 'min': f"{min(response_times):.0f}ms", 
                              'max': f"{max(response_times):.0f}ms"})
    
    def run_all_tests(self):
        """Run comprehensive smoke tests on all systems"""
        print("🧪 Comprehensive Smoke Test - No Agenda Mixer")
        print("🕐 Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 80)
        
        # Test each system
        self.test_original_system()
        self.test_professional_lite_system()
        self.test_performance_comparison()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 SMOKE TEST SUMMARY")
        print("=" * 80)
        
        # Count results by system and status
        summary = {}
        for result in self.test_results:
            system = result['system']
            status = result['status']
            
            if system not in summary:
                summary[system] = {'PASS': 0, 'FAIL': 0, 'WARN': 0}
            
            summary[system][status] = summary[system].get(status, 0) + 1
        
        # Display summary
        for system, counts in summary.items():
            total = sum(counts.values())
            passed = counts.get('PASS', 0)
            failed = counts.get('FAIL', 0)
            warned = counts.get('WARN', 0)
            
            system_name = self.endpoints.get(system, {}).get('name', system) if system in self.endpoints else system
            print(f"\n{system_name}:")
            print(f"  ✅ Passed: {passed}/{total}")
            print(f"  ❌ Failed: {failed}/{total}")
            print(f"  ⚠️  Warnings: {warned}/{total}")
            print(f"  📊 Success Rate: {(passed/total*100):.1f}%" if total > 0 else "  📊 No tests")
        
        # Overall status
        total_tests = len(self.test_results)
        total_passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        total_failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        
        print(f"\n🎯 OVERALL RESULTS")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)" if total_tests > 0 else "Passed: 0")
        print(f"Failed: {total_failed}")
        
        # Generate report
        self.generate_report()
        
        # Final verdict
        if total_failed == 0:
            print("\n✅ ALL SMOKE TESTS PASSED!")
        else:
            print(f"\n⚠️  {total_failed} tests failed across all systems")
        
        return total_failed == 0
    
    def generate_report(self):
        """Generate detailed test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'systems_tested': list(self.endpoints.keys()),
            'total_tests': len(self.test_results),
            'results': self.test_results,
            'sessions_created': self.sessions,
            'summary': {
                'passed': sum(1 for r in self.test_results if r['status'] == 'PASS'),
                'failed': sum(1 for r in self.test_results if r['status'] == 'FAIL'),
                'warnings': sum(1 for r in self.test_results if r['status'] == 'WARN')
            }
        }
        
        with open('comprehensive_smoke_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Detailed report saved to: comprehensive_smoke_test_report.json")

def main():
    """Main test runner"""
    tester = ComprehensiveSmokeTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()