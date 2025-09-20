#!/usr/bin/env python3
"""
Debug version of document processing with detailed logging
"""

import asyncio
import sys
import os 
from pathlib import Path
import uuid
import hashlib

# Add the backend directory to the Python path
sys.path.append('/app/backend')

# Import our server functions
from server import (
    extract_text_from_txt, get_embeddings, get_db_pool, 
    create_document_slug, create_anchor_id
)

async def debug_process_single_document():
    """Debug process a single document with detailed logging"""
    print("=== Debug Processing Single Document ===")
    
    # Use the TROX document
    doc_id = "394e3135-7233-40ac-9d29-80f7b392585f"
    file_path = Path("/app/uploads/394e3135-7233-40ac-9d29-80f7b392585f_trox_brandschutzklappen_fkrs_eu_anleitung.txt")
    file_type = "text/plain"
    doc_slug = "trox-brandschutzklappen-fkrs-eu-montage-und-betrie"
    
    print(f"Document ID: {doc_id}")
    print(f"File path: {file_path}")
    print(f"File exists: {file_path.exists()}")
    print(f"File type: {file_type}")
    print(f"Document slug: {doc_slug}")
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as db:
            print("\n1. Database connection established")
            
            # Update status to processing
            await db.execute(
                "UPDATE documents SET processing_status = 'processing' WHERE id = $1",
                doc_id
            )
            print("2. Status updated to 'processing'")
            
            # Extract text
            with open(file_path, 'rb') as f:
                file_content = f.read()
            print(f"3. File content loaded: {len(file_content)} bytes")
            
            sections = extract_text_from_txt(file_content, str(file_path.name))
            print(f"4. Text extraction completed: {len(sections)} sections")
            
            if not sections:
                print("❌ No sections extracted!")
                await db.execute(
                    "UPDATE documents SET processing_status = 'failed' WHERE id = $1",
                    doc_id
                )
                return
            
            # Show section details
            for i, section in enumerate(sections[:3]):
                print(f"   Section {i+1}: '{section['title']}' ({len(section['content'])} chars)")
            
            # Generate embeddings
            section_texts = [s['content'] for s in sections]
            print(f"5. Generating embeddings for {len(section_texts)} sections...")
            
            embeddings = await get_embeddings(section_texts)
            print(f"6. Embeddings generated: {len(embeddings)} vectors of {len(embeddings[0]) if embeddings else 0} dimensions")
            
            # Save sections to database
            print("7. Saving sections to database...")
            sections_saved = 0
            
            for i, section in enumerate(sections):
                try:
                    section_id = str(uuid.uuid4())
                    anchor_id = create_anchor_id(
                        doc_slug, 
                        section['section_hierarchy'], 
                        section['page_number'], 
                        section['content']
                    )
                    content_hash = hashlib.md5(section['content'].encode()).hexdigest()
                    
                    print(f"   Saving section {i+1}: {section_id}")
                    print(f"     Anchor ID: {anchor_id}")
                    print(f"     Content hash: {content_hash[:8]}...")
                    print(f"     Embedding length: {len(embeddings[i])}")
                    
                    await db.execute('''
                        INSERT INTO document_sections (
                            id, document_id, anchor_id, title, content, page_number,
                            section_hierarchy, content_hash, embedding
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ''', section_id, doc_id, anchor_id, section['title'], section['content'],
                         section['page_number'], section['section_hierarchy'], content_hash,
                         embeddings[i])
                    
                    sections_saved += 1
                    print(f"     ✅ Section {i+1} saved successfully")
                    
                except Exception as section_error:
                    print(f"     ❌ Error saving section {i+1}: {section_error}")
            
            print(f"8. Sections saved: {sections_saved}/{len(sections)}")
            
            # Update document status
            await db.execute(
                "UPDATE documents SET processing_status = 'completed', page_count = $2 WHERE id = $1",
                doc_id, len(sections)
            )
            print("9. Document status updated to 'completed'")
            
            # Verify the result
            doc_status = await db.fetchrow(
                "SELECT processing_status, page_count FROM documents WHERE id = $1",
                doc_id
            )
            print(f"10. Final document status: {doc_status['processing_status']}, pages: {doc_status['page_count']}")
            
            section_count = await db.fetchval(
                "SELECT COUNT(*) FROM document_sections WHERE document_id = $1",
                doc_id
            )
            print(f"11. Sections in database for this document: {section_count}")
            
        await pool.close()
        print("\n✅ Debug processing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Debug processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_process_single_document())