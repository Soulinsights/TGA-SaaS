#!/usr/bin/env python3
"""
Manually process documents that failed automatic processing
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append('/app/backend')

# Import our server functions
from server import process_document, get_db_pool

async def manual_process_documents():
    """Manually process all failed documents"""
    print("=== Manually Processing Failed Documents ===")
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get all failed documents
            failed_docs = await conn.fetch("""
                SELECT id, slug, file_path, file_type 
                FROM documents 
                WHERE processing_status = 'failed'
                ORDER BY created_at DESC
            """)
            
            print(f"Found {len(failed_docs)} failed documents")
            
            for doc in failed_docs:
                print(f"\nProcessing document: {doc['slug']}")
                print(f"  ID: {doc['id']}")
                print(f"  File: {doc['file_path']}")
                print(f"  Type: {doc['file_type']}")
                
                # Check if file exists
                file_path = Path(doc['file_path'])
                if not file_path.exists():
                    print(f"  ❌ File not found: {file_path}")
                    continue
                
                try:
                    # Manually call the processing function
                    await process_document(
                        doc['id'], 
                        file_path, 
                        doc['file_type'], 
                        doc['slug']
                    )
                    print(f"  ✅ Processing completed for {doc['slug']}")
                    
                except Exception as e:
                    print(f"  ❌ Processing failed for {doc['slug']}: {e}")
            
            # Check results
            print(f"\n=== Processing Results ===")
            completed_docs = await conn.fetch("""
                SELECT id, slug, processing_status, page_count
                FROM documents 
                ORDER BY created_at DESC
            """)
            
            for doc in completed_docs:
                status_icon = "✅" if doc['processing_status'] == 'completed' else "❌"
                print(f"{status_icon} {doc['slug']}: {doc['processing_status']} ({doc['page_count']} pages)")
            
            # Check section count
            section_count = await conn.fetchval("SELECT COUNT(*) FROM document_sections")
            print(f"\nTotal sections in database: {section_count}")
            
        await pool.close()
        
    except Exception as e:
        print(f"Manual processing error: {e}")

if __name__ == "__main__":
    asyncio.run(manual_process_documents())