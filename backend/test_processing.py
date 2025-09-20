#!/usr/bin/env python3
"""
Test script to debug document processing pipeline
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append('/app/backend')

# Import our server functions
from server import extract_text_from_txt, get_embeddings, get_db_pool, init_database

async def test_text_extraction():
    """Test text extraction from our uploaded files"""
    print("=== Testing Text Extraction ===")
    
    # Test with one of our uploaded files
    test_file = "/app/uploads/394e3135-7233-40ac-9d29-80f7b392585f_trox_brandschutzklappen_fkrs_eu_anleitung.txt"
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return False
    
    try:
        with open(test_file, 'rb') as f:
            file_content = f.read()
        
        print(f"File size: {len(file_content)} bytes")
        
        # Extract sections
        sections = extract_text_from_txt(file_content, "test_document.txt")
        print(f"Extracted {len(sections)} sections")
        
        for i, section in enumerate(sections[:3]):  # Show first 3 sections
            print(f"\nSection {i+1}:")
            print(f"  Title: {section['title']}")
            print(f"  Page: {section['page_number']}")
            print(f"  Hierarchy: {section['section_hierarchy']}")
            print(f"  Content length: {len(section['content'])} chars")
            print(f"  Content preview: {section['content'][:200]}...")
            
        return sections
        
    except Exception as e:
        print(f"Text extraction error: {e}")
        return False

async def test_embeddings():
    """Test embedding generation"""
    print("\n=== Testing Embedding Generation ===")
    
    test_texts = [
        "Brandschutzklappen sind wichtige Komponenten in Lüftungsanlagen.",
        "Die Installation erfolgt nach den technischen Richtlinien.",
        "Wartung und Prüfung sind regelmäßig durchzuführen."
    ]
    
    try:
        embeddings = await get_embeddings(test_texts)
        print(f"Generated {len(embeddings)} embeddings")
        
        for i, embedding in enumerate(embeddings):
            print(f"Embedding {i+1}: dimension {len(embedding)}, sample values: {embedding[:5]}")
            
        return embeddings
        
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return False

async def test_database_connection():
    """Test database connection and table structure"""
    print("\n=== Testing Database Connection ===")
    
    try:
        # Initialize database
        await init_database()
        print("Database initialized successfully")
        
        # Test connection
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check if tables exist
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN ('documents', 'document_sections')
            """)
            
            print(f"Found tables: {[row['table_name'] for row in tables]}")
            
            # Check document count
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
            print(f"Documents in database: {doc_count}")
            
            # Check section count
            section_count = await conn.fetchval("SELECT COUNT(*) FROM document_sections")
            print(f"Sections in database: {section_count}")
            
        await pool.close()
        return True
        
    except Exception as e:
        print(f"Database test error: {e}")
        return False

async def main():
    """Run all tests"""
    print("Starting document processing pipeline tests...\n")
    
    # Test 1: Text extraction
    sections = await test_text_extraction()
    if not sections:
        print("❌ Text extraction failed")
        return
    else:
        print("✅ Text extraction successful")
    
    # Test 2: Embedding generation
    embeddings = await test_embeddings()
    if not embeddings:
        print("❌ Embedding generation failed")
        return
    else:
        print("✅ Embedding generation successful")
    
    # Test 3: Database connection
    db_ok = await test_database_connection()
    if not db_ok:
        print("❌ Database test failed")
        return
    else:
        print("✅ Database test successful")
    
    print("\n🎉 All pipeline components are working!")
    print("\nNext step: Test full document processing...")

if __name__ == "__main__":
    asyncio.run(main())