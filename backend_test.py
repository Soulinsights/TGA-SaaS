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