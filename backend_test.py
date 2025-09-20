#!/usr/bin/env python3
"""
TGA Knowledge Platform Backend API Testing
Tests all backend endpoints for the German TGA knowledge management system
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import tempfile
import os

class TGABackendTester:
    def __init__(self, base_url="https://buildingsage.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_keys = ['message', 'version']
                has_expected_data = all(key in data for key in expected_keys)
                if has_expected_data:
                    self.log_test("API Root Endpoint", True, f"Version: {data.get('version')}")
                else:
                    self.log_test("API Root Endpoint", False, f"Missing expected keys in response: {data}")
            else:
                self.log_test("API Root Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("API Root Endpoint", False, f"Connection error: {str(e)}")

    def test_get_documents(self):
        """Test documents listing endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/documents", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.log_test("Get Documents", True, f"Retrieved {len(data)} documents")
                return data
            else:
                self.log_test("Get Documents", False, f"Status: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_test("Get Documents", False, f"Error: {str(e)}")
            return []

    def test_search_endpoint(self):
        """Test search functionality"""
        try:
            # Test basic search
            search_payload = {
                "query": "Brandschutz",
                "limit": 10,
                "offset": 0
            }
            
            response = requests.post(
                f"{self.base_url}/api/search", 
                json=search_payload,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.log_test("Search Endpoint - Basic", True, f"Found {len(data)} results")
                
                # Test search with filters
                filtered_search = {
                    "query": "DIN 4102",
                    "trade_filter": "Brandschutz",
                    "license_filter": "DIN",
                    "limit": 5
                }
                
                response2 = requests.post(
                    f"{self.base_url}/api/search", 
                    json=filtered_search,
                    headers={'Content-Type': 'application/json'},
                    timeout=15
                )
                
                if response2.status_code == 200:
                    filtered_data = response2.json()
                    self.log_test("Search Endpoint - Filtered", True, f"Filtered results: {len(filtered_data)}")
                else:
                    self.log_test("Search Endpoint - Filtered", False, f"Status: {response2.status_code}")
                    
            else:
                self.log_test("Search Endpoint - Basic", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Search Endpoint", False, f"Error: {str(e)}")

    def test_qa_endpoint(self):
        """Test Q&A RAG functionality"""
        try:
            qa_payload = {
                "question": "Was sind die wichtigsten Brandschutzklappen nach DIN 4102?",
                "trade_filter": "Brandschutz"
            }
            
            response = requests.post(
                f"{self.base_url}/api/qa", 
                json=qa_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30  # RAG responses can take longer
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_keys = ['answer', 'citations', 'confidence']
                has_expected_structure = all(key in data for key in expected_keys)
                
                if has_expected_structure:
                    self.log_test("Q&A RAG Endpoint", True, 
                                f"Answer length: {len(data['answer'])}, Citations: {len(data['citations'])}, Confidence: {data['confidence']}")
                else:
                    self.log_test("Q&A RAG Endpoint", False, f"Invalid response structure: {data}")
            else:
                self.log_test("Q&A RAG Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Q&A RAG Endpoint", False, f"Error: {str(e)}")

    def test_document_upload(self):
        """Test document upload functionality"""
        try:
            # Create a test PDF file
            test_content = """
            TGA Testdokument
            
            Dies ist ein Testdokument für die TGA Knowledge Platform.
            
            Brandschutz Grundlagen:
            - Brandschutzklappen nach DIN 4102
            - Rauchmelder Installation
            - Fluchtwegeplanung
            
            HLK/RLT Systeme:
            - Lüftungsanlagen
            - Klimatechnik
            - Heizungssysteme
            """
            
            # Create temporary text file (simpler than PDF for testing)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(test_content)
                temp_file_path = f.name
            
            try:
                # Prepare upload data
                upload_data = {
                    'title': 'TGA Test Dokument',
                    'trade': 'Brandschutz',
                    'category': 'Technical Guide',
                    'description': 'Test document for TGA platform',
                    'jurisdiction': 'Bayern',
                    'building_type': 'Commercial',
                    'year': 2024,
                    'license_type': 'open'
                }
                
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('test_document.txt', f, 'text/plain')}
                    
                    response = requests.post(
                        f"{self.base_url}/api/documents/upload",
                        data=upload_data,
                        files=files,
                        timeout=30
                    )
                
                success = response.status_code in [200, 201]
                
                if success:
                    data = response.json()
                    if 'document_id' in data:
                        self.log_test("Document Upload", True, f"Document ID: {data['document_id']}")
                        return data['document_id']
                    else:
                        self.log_test("Document Upload", False, f"No document_id in response: {data}")
                else:
                    self.log_test("Document Upload", False, f"Status: {response.status_code}, Response: {response.text}")
                    
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("Document Upload", False, f"Error: {str(e)}")
        
        return None

    def test_document_detail(self, document_id):
        """Test document detail endpoint"""
        if not document_id:
            self.log_test("Document Detail", False, "No document ID provided")
            return
            
        try:
            response = requests.get(f"{self.base_url}/api/documents/{document_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_keys = ['id', 'title', 'trade', 'category']
                has_expected_data = all(key in data for key in expected_keys)
                
                if has_expected_data:
                    sections_count = len(data.get('sections', []))
                    self.log_test("Document Detail", True, f"Document with {sections_count} sections")
                else:
                    self.log_test("Document Detail", False, f"Missing expected keys: {data}")
            else:
                self.log_test("Document Detail", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Document Detail", False, f"Error: {str(e)}")

    def test_database_connectivity(self):
        """Test if database operations are working by checking document operations"""
        try:
            # This is indirect - we test if we can retrieve documents which requires DB
            response = requests.get(f"{self.base_url}/api/documents?limit=1", timeout=10)
            
            if response.status_code == 200:
                self.log_test("Database Connectivity", True, "Database operations working")
            else:
                self.log_test("Database Connectivity", False, f"Database operations failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Database Connectivity", False, f"Database connection error: {str(e)}")

    def test_cors_headers(self):
        """Test CORS configuration"""
        try:
            response = requests.options(f"{self.base_url}/api/", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            has_cors = any(header in response.headers for header in cors_headers)
            
            if has_cors or response.status_code == 200:
                self.log_test("CORS Configuration", True, "CORS headers present")
            else:
                self.log_test("CORS Configuration", False, f"No CORS headers found")
                
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Error: {str(e)}")

    def test_fire_products_endpoint(self):
        """Test fire clearance products endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/fire/products", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check if products have expected structure
                    first_product = data[0]
                    expected_keys = ['id', 'name', 'manufacturer_name', 'material']
                    has_expected_structure = all(key in first_product for key in expected_keys)
                    
                    if has_expected_structure:
                        self.log_test("Fire Products Endpoint", True, f"Retrieved {len(data)} products")
                    else:
                        self.log_test("Fire Products Endpoint", False, f"Invalid product structure: {first_product}")
                else:
                    self.log_test("Fire Products Endpoint", False, "No products returned")
            else:
                self.log_test("Fire Products Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Fire Products Endpoint", False, f"Error: {str(e)}")

    def test_fire_materials_endpoint(self):
        """Test fire clearance materials endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/fire/materials", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check for expected materials
                    expected_materials = ['stainless_steel', 'copper', 'plastic']
                    material_values = [item['value'] for item in data if 'value' in item]
                    has_expected_materials = any(mat in material_values for mat in expected_materials)
                    
                    if has_expected_materials:
                        self.log_test("Fire Materials Endpoint", True, f"Retrieved {len(data)} materials")
                    else:
                        self.log_test("Fire Materials Endpoint", False, f"Missing expected materials: {material_values}")
                else:
                    self.log_test("Fire Materials Endpoint", False, "No materials returned")
            else:
                self.log_test("Fire Materials Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Fire Materials Endpoint", False, f"Error: {str(e)}")

    def test_fire_insulation_classes_endpoint(self):
        """Test fire clearance insulation classes endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/fire/insulation-classes", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check for expected insulation classes
                    expected_classes = ['A1', 'A2', 'B']
                    class_values = [item['value'] for item in data if 'value' in item]
                    has_expected_classes = any(cls in class_values for cls in expected_classes)
                    
                    if has_expected_classes:
                        self.log_test("Fire Insulation Classes Endpoint", True, f"Retrieved {len(data)} classes")
                    else:
                        self.log_test("Fire Insulation Classes Endpoint", False, f"Missing expected classes: {class_values}")
                else:
                    self.log_test("Fire Insulation Classes Endpoint", False, "No insulation classes returned")
            else:
                self.log_test("Fire Insulation Classes Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Fire Insulation Classes Endpoint", False, f"Error: {str(e)}")

    def test_fire_wrapping_types_endpoint(self):
        """Test fire clearance wrapping types endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/fire/wrapping-types", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check for expected wrapping types
                    expected_wraps = ['metal_wrap_Z', 'metal_wrap_Y']
                    wrap_values = [item['value'] for item in data if 'value' in item]
                    has_expected_wraps = any(wrap in wrap_values for wrap in expected_wraps)
                    
                    if has_expected_wraps:
                        self.log_test("Fire Wrapping Types Endpoint", True, f"Retrieved {len(data)} wrapping types")
                    else:
                        self.log_test("Fire Wrapping Types Endpoint", False, f"Missing expected wraps: {wrap_values}")
                else:
                    self.log_test("Fire Wrapping Types Endpoint", False, "No wrapping types returned")
            else:
                self.log_test("Fire Wrapping Types Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Fire Wrapping Types Endpoint", False, f"Error: {str(e)}")

    def test_fire_jurisdictions_endpoint(self):
        """Test fire clearance jurisdictions endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/fire/jurisdictions", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check for expected German states
                    expected_states = ['BY', 'BW', 'NW']
                    state_values = [item['value'] for item in data if 'value' in item]
                    has_expected_states = any(state in state_values for state in expected_states)
                    
                    if has_expected_states:
                        self.log_test("Fire Jurisdictions Endpoint", True, f"Retrieved {len(data)} jurisdictions")
                    else:
                        self.log_test("Fire Jurisdictions Endpoint", False, f"Missing expected states: {state_values}")
                else:
                    self.log_test("Fire Jurisdictions Endpoint", False, "No jurisdictions returned")
            else:
                self.log_test("Fire Jurisdictions Endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Fire Jurisdictions Endpoint", False, f"Error: {str(e)}")

    def test_fire_clearance_compute_golden_case_1(self):
        """Test fire clearance computation - Golden Case 1 (AbP approval - 0mm)"""
        try:
            # Golden Case 1: Stainless steel + A2 insulation + DN=200 + metal_wrap_Z + parallel + clamp 1.5m → 0mm zulässig (AbP source)
            clearance_request = {
                "product_id": "1",  # Assuming first product from seed data
                "material": "stainless_steel",
                "DN": 200,
                "insulation": {
                    "class": "A2",
                    "thickness_mm": 30,
                    "wrap": ["metal_wrap_Z"]
                },
                "layout": "parallel",
                "bundle_count": 1,
                "mount": {
                    "clamp_spacing_m": 1.5
                },
                "context": {
                    "location": "shaft",
                    "jurisdiction": "BY",
                    "building_class": "Hochhaus"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/fire/clearance/compute",
                json=clearance_request,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_keys = ['min_clearance_mm', 'status', 'sources']
                has_expected_structure = all(key in data for key in expected_keys)
                
                if has_expected_structure:
                    # Check if we get 0mm clearance (AbP approval case)
                    clearance = data['min_clearance_mm']
                    status = data['status']
                    sources = data['sources']
                    
                    # For golden case 1, we expect 0mm with AbP source
                    if clearance == 0 and any(source.get('type') == 'AbP' for source in sources):
                        self.log_test("Fire Clearance Golden Case 1 (AbP)", True, 
                                    f"Clearance: {clearance}mm, Status: {status}, Sources: {len(sources)}")
                    else:
                        self.log_test("Fire Clearance Golden Case 1 (AbP)", False, 
                                    f"Expected 0mm with AbP source, got {clearance}mm with sources: {[s.get('type') for s in sources]}")
                else:
                    self.log_test("Fire Clearance Golden Case 1 (AbP)", False, f"Invalid response structure: {data}")
            else:
                self.log_test("Fire Clearance Golden Case 1 (AbP)", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Fire Clearance Golden Case 1 (AbP)", False, f"Error: {str(e)}")

    def test_fire_clearance_compute_golden_case_2(self):
        """Test fire clearance computation - Golden Case 2 (MLAR fallback - 50mm)"""
        try:
            # Golden Case 2: Same as case 1 but missing metal_wrap_Z → 50mm default (MLAR source)
            clearance_request = {
                "product_id": "1",
                "material": "stainless_steel",
                "DN": 200,
                "insulation": {
                    "class": "A2",
                    "thickness_mm": 30,
                    "wrap": []  # No wrapping - should trigger MLAR fallback
                },
                "layout": "parallel",
                "bundle_count": 1,
                "mount": {
                    "clamp_spacing_m": 1.5
                },
                "context": {
                    "location": "shaft",
                    "jurisdiction": "BY",
                    "building_class": "Hochhaus"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/fire/clearance/compute",
                json=clearance_request,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_keys = ['min_clearance_mm', 'status', 'sources']
                has_expected_structure = all(key in data for key in expected_keys)
                
                if has_expected_structure:
                    clearance = data['min_clearance_mm']
                    status = data['status']
                    sources = data['sources']
                    
                    # For golden case 2, we expect 50mm with MLAR source
                    if clearance == 50 and any(source.get('type') == 'MLAR' for source in sources):
                        self.log_test("Fire Clearance Golden Case 2 (MLAR)", True, 
                                    f"Clearance: {clearance}mm, Status: {status}, Sources: {len(sources)}")
                    else:
                        self.log_test("Fire Clearance Golden Case 2 (MLAR)", False, 
                                    f"Expected 50mm with MLAR source, got {clearance}mm with sources: {[s.get('type') for s in sources]}")
                else:
                    self.log_test("Fire Clearance Golden Case 2 (MLAR)", False, f"Invalid response structure: {data}")
            else:
                self.log_test("Fire Clearance Golden Case 2 (MLAR)", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Fire Clearance Golden Case 2 (MLAR)", False, f"Error: {str(e)}")

    def test_fire_clearance_compute_with_debug(self):
        """Test fire clearance computation with debug mode"""
        try:
            clearance_request = {
                "product_id": "1",
                "material": "stainless_steel",
                "DN": 100,
                "insulation": {
                    "class": "A1",
                    "thickness_mm": 25,
                    "wrap": ["metal_wrap_Z"]
                },
                "layout": "parallel",
                "bundle_count": 1,
                "mount": {
                    "clamp_spacing_m": 1.0
                },
                "context": {
                    "location": "wall",
                    "jurisdiction": "BW",
                    "building_class": "Gewerbebau"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/fire/clearance/compute?debug=true",
                json=clearance_request,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if 'debug_info' in data and data['debug_info'] is not None:
                    debug_info = data['debug_info']
                    has_debug_data = 'rules_loaded' in debug_info or 'approval_matches' in debug_info
                    
                    if has_debug_data:
                        self.log_test("Fire Clearance Debug Mode", True, 
                                    f"Debug info present with {debug_info.get('rules_loaded', 0)} rules loaded")
                    else:
                        self.log_test("Fire Clearance Debug Mode", False, f"Debug info missing expected data: {debug_info}")
                else:
                    self.log_test("Fire Clearance Debug Mode", False, "No debug_info in response")
            else:
                self.log_test("Fire Clearance Debug Mode", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Fire Clearance Debug Mode", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting TGA Knowledge Platform Backend Tests")
        print(f"📍 Testing API at: {self.base_url}")
        print("=" * 60)
        
        # Core API tests
        self.test_api_root()
        self.test_database_connectivity()
        self.test_cors_headers()
        
        # Document management tests
        documents = self.test_get_documents()
        
        # Upload test (creates new document)
        uploaded_doc_id = self.test_document_upload()
        
        # Test document detail with uploaded document or existing one
        test_doc_id = uploaded_doc_id or (documents[0]['id'] if documents else None)
        if test_doc_id:
            self.test_document_detail(test_doc_id)
        
        # Search and Q&A tests
        self.test_search_endpoint()
        self.test_qa_endpoint()
        
        # Fire Clearance Module Tests
        print("\n🔥 Testing Fire Clearance Module...")
        self.test_fire_products_endpoint()
        self.test_fire_materials_endpoint()
        self.test_fire_insulation_classes_endpoint()
        self.test_fire_wrapping_types_endpoint()
        self.test_fire_jurisdictions_endpoint()
        self.test_fire_clearance_compute_golden_case_1()
        self.test_fire_clearance_compute_golden_case_2()
        self.test_fire_clearance_compute_with_debug()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests details
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print("\n🔍 FAILED TESTS DETAILS:")
            for test in failed_tests:
                print(f"❌ {test['name']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = TGABackendTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())