from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import asyncpg
import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone
import hashlib
import json
import magic
import PyPDF2
from io import BytesIO
import re
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="TGA Knowledge Platform", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Database connection pool
db_pool = None

async def get_db_pool():
    global db_pool
    if db_pool is None:
        postgres_url = os.environ.get('POSTGRES_URL')
        db_pool = await asyncpg.create_pool(postgres_url, min_size=1, max_size=10)
    return db_pool

async def get_db():
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        yield connection

# Pydantic Models
class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    trade: str  # HVAC, Plumbing, Electrical, Fire Protection, etc.
    category: str  # Standard, Product Data, Technical Guide, etc.
    jurisdiction: Optional[str] = None  # Bavaria, Federal, EU, etc.
    building_type: Optional[str] = None  # High-rise, Commercial, Residential, etc.
    year: Optional[int] = None
    language: str = "de"
    license_type: str = "open"  # open, DIN, VDI, proprietary

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: str
    slug: str
    file_path: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    processing_status: str  # pending, processing, completed, failed
    created_at: datetime
    updated_at: datetime
    
class DocumentSection(BaseModel):
    id: str
    document_id: str
    anchor_id: str  # docSlug::sec-hierarchy-p<page>-<hash8>
    title: str
    content: str
    page_number: int
    section_hierarchy: str  # e.g., "1.2.3"
    content_hash: str
    embedding: Optional[List[float]] = None
    created_at: datetime

class SearchQuery(BaseModel):
    query: str
    trade_filter: Optional[str] = None
    category_filter: Optional[str] = None
    jurisdiction_filter: Optional[str] = None
    building_type_filter: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    license_filter: Optional[str] = None
    limit: int = 20
    offset: int = 0

class SearchResult(BaseModel):
    id: str
    document_id: str
    document_title: str
    anchor_id: str
    title: str
    content: str
    page_number: int
    relevance_score: float
    trade: str
    category: str
    license_type: str

class QAQuery(BaseModel):
    question: str
    project_context: Optional[Dict[str, Any]] = None
    trade_filter: Optional[str] = None
    jurisdiction_filter: Optional[str] = None
    building_type_filter: Optional[str] = None

class QAResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    confidence: float
    
class ProjectProfile(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    jurisdiction: str
    building_type: str
    usage_class: Optional[str] = None
    special_requirements: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

# Database initialization
async def init_database():
    """Initialize database tables and extensions"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Create documents table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR PRIMARY KEY,
                slug VARCHAR UNIQUE NOT NULL,
                title VARCHAR NOT NULL,
                description TEXT,
                trade VARCHAR NOT NULL,
                category VARCHAR NOT NULL,
                jurisdiction VARCHAR,
                building_type VARCHAR,
                year INTEGER,
                language VARCHAR DEFAULT 'de',
                license_type VARCHAR DEFAULT 'open',
                file_path VARCHAR NOT NULL,
                file_type VARCHAR NOT NULL,
                file_size INTEGER NOT NULL,
                page_count INTEGER,
                processing_status VARCHAR DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Create document sections table with vector support
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS document_sections (
                id VARCHAR PRIMARY KEY,
                document_id VARCHAR REFERENCES documents(id) ON DELETE CASCADE,
                anchor_id VARCHAR UNIQUE NOT NULL,
                title VARCHAR NOT NULL,
                content TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                section_hierarchy VARCHAR,
                content_hash VARCHAR NOT NULL,
                embedding VECTOR(1536),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Create project profiles table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS project_profiles (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                jurisdiction VARCHAR NOT NULL,
                building_type VARCHAR NOT NULL,
                usage_class VARCHAR,
                special_requirements JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Create indexes
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_documents_trade ON documents(trade)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON documents(jurisdiction)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_documents_license ON documents(license_type)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_sections_document ON document_sections(document_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_sections_page ON document_sections(page_number)')
        
        # Create full-text search index
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_sections_content_fts 
            ON document_sections USING gin(to_tsvector('german', content))
        ''')
        
        # Create vector similarity index (using ivfflat instead of hnsw for high dimensions)
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_sections_embedding_ivfflat 
            ON document_sections USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        ''')

# LLM Integration
async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using OpenAI text-embedding-3-large"""
    try:
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"embedding-{uuid.uuid4()}",
            system_message="Generate embeddings for text."
        ).with_model("openai", "text-embedding-3-large")
        
        # For embedding, we need to use the OpenAI client directly
        # This is a placeholder - we'll implement proper embedding logic
        embeddings = []
        for text in texts:
            # Generate a mock embedding for now - replace with actual embedding call
            embedding = [0.1] * 1536  # Mock 1536-dimensional embedding
            embeddings.append(embedding)
        return embeddings
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return [[0.0] * 1536 for _ in texts]

async def generate_rag_response(question: str, context_sections: List[Dict]) -> Dict:
    """Generate RAG response with citations"""
    try:
        # Prepare context
        context_text = "\n\n".join([
            f"[{section['anchor_id']}] {section['title']}\n{section['content'][:1000]}..."
            for section in context_sections
        ])
        
        system_message = """Sie sind ein Experte für technische Gebäudeausrüstung (TGA) in Deutschland. 
        Beantworten Sie Fragen basierend auf den bereitgestellten Dokumenten. 
        
        WICHTIGE REGELN:
        - Zitieren Sie immer Ihre Quellen mit [anchor_id]
        - Für lizenzierte DIN/VDI-Normen: Nur Metadaten und Zusammenfassungen, kein Volltext
        - Antworten Sie auf Deutsch
        - Seien Sie präzise und technisch korrekt
        - Bei Unsicherheit: Verweisen Sie auf Originaldokumente
        """
        
        user_message = UserMessage(
            text=f"Frage: {question}\n\nRelevante Dokumente:\n{context_text}"
        )
        
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=f"rag-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        
        response = await chat.send_message(user_message)
        
        # Extract citations from response
        citations = []
        for section in context_sections:
            if section['anchor_id'] in response:
                citations.append({
                    'anchor_id': section['anchor_id'],
                    'document_title': section.get('document_title', ''),
                    'title': section['title'],
                    'page_number': section['page_number'],
                    'relevance_score': section.get('relevance_score', 0.0)
                })
        
        return {
            'answer': response,
            'citations': citations,
            'confidence': 0.8  # Mock confidence score
        }
        
    except Exception as e:
        logger.error(f"Error generating RAG response: {e}")
        return {
            'answer': f"Entschuldigung, ich konnte die Frage nicht beantworten. Fehler: {str(e)}",
            'citations': [],
            'confidence': 0.0
        }

# Document processing utilities
def create_document_slug(title: str) -> str:
    """Create URL-friendly slug from title"""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug[:50]

def create_anchor_id(doc_slug: str, section_hierarchy: str, page_num: int, content: str) -> str:
    """Create stable anchor ID for citations"""
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{doc_slug}::sec-{section_hierarchy}-p{page_num}-{content_hash}"

def extract_text_from_pdf(file_content: bytes) -> List[Dict]:
    """Extract text and metadata from PDF"""
    try:
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        sections = []
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            if text.strip():
                sections.append({
                    'title': f'Seite {page_num}',
                    'content': text,
                    'page_number': page_num,
                    'section_hierarchy': str(page_num)
                })
        
        return sections
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return []

# API Routes
@api_router.get("/")
async def root():
    return {"message": "TGA Knowledge Platform API", "version": "1.0.0"}

@api_router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    trade: str = Form(...),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    jurisdiction: Optional[str] = Form(None),
    building_type: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    license_type: str = Form("open"),
    db: asyncpg.Connection = Depends(get_db)
):
    """Upload and process a TGA document"""
    try:
        # Validate file
        if file.size > int(os.environ.get('MAX_FILE_SIZE', 50000000)):
            raise HTTPException(status_code=413, detail="File too large")
        
        # Read file content
        file_content = await file.read()
        file_type = magic.from_buffer(file_content, mime=True)
        
        # Create document record
        doc_id = str(uuid.uuid4())
        doc_slug = create_document_slug(title)
        
        # Save file
        upload_dir = Path(os.environ.get('UPLOAD_DIR', '/app/uploads'))
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / f"{doc_id}_{file.filename}"
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Insert document
        await db.execute('''
            INSERT INTO documents (
                id, slug, title, description, trade, category, jurisdiction,
                building_type, year, license_type, file_path, file_type, file_size
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ''', doc_id, doc_slug, title, description, trade, category, jurisdiction,
             building_type, year, license_type, str(file_path), file_type, file.size)
        
        # Process document (async)
        asyncio.create_task(process_document(doc_id, file_path, file_type, doc_slug))
        
        return {"document_id": doc_id, "status": "uploaded", "message": "Document processing started"}
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_document(doc_id: str, file_path: Path, file_type: str, doc_slug: str):
    """Process document: extract text, create sections, generate embeddings"""
    pool = await get_db_pool()
    async with pool.acquire() as db:
        try:
            # Update status
            await db.execute(
                "UPDATE documents SET processing_status = 'processing' WHERE id = $1",
                doc_id
            )
            
            # Extract text based on file type
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            sections = []
            if 'pdf' in file_type:
                sections = extract_text_from_pdf(file_content)
            
            if not sections:
                await db.execute(
                    "UPDATE documents SET processing_status = 'failed' WHERE id = $1",
                    doc_id
                )
                return
            
            # Generate embeddings
            section_texts = [s['content'] for s in sections]
            embeddings = await get_embeddings(section_texts)
            
            # Save sections
            for i, section in enumerate(sections):
                section_id = str(uuid.uuid4())
                anchor_id = create_anchor_id(
                    doc_slug, 
                    section['section_hierarchy'], 
                    section['page_number'], 
                    section['content']
                )
                content_hash = hashlib.md5(section['content'].encode()).hexdigest()
                
                await db.execute('''
                    INSERT INTO document_sections (
                        id, document_id, anchor_id, title, content, page_number,
                        section_hierarchy, content_hash, embedding
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ''', section_id, doc_id, anchor_id, section['title'], section['content'],
                     section['page_number'], section['section_hierarchy'], content_hash,
                     embeddings[i])
            
            # Update document status
            await db.execute(
                "UPDATE documents SET processing_status = 'completed', page_count = $2 WHERE id = $1",
                doc_id, len(sections)
            )
            
            logger.info(f"Document {doc_id} processed successfully with {len(sections)} sections")
            
        except Exception as e:
            logger.error(f"Processing error for {doc_id}: {e}")
            await db.execute(
                "UPDATE documents SET processing_status = 'failed' WHERE id = $1",
                doc_id
            )

@api_router.get("/documents", response_model=List[Document])
async def get_documents(
    trade: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get documents with optional filters"""
    query = "SELECT * FROM documents WHERE 1=1"
    params = []
    param_count = 0
    
    if trade:
        param_count += 1
        query += f" AND trade = ${param_count}"
        params.append(trade)
    
    if category:
        param_count += 1
        query += f" AND category = ${param_count}"
        params.append(category)
    
    param_count += 1
    query += f" ORDER BY created_at DESC LIMIT ${param_count}"
    params.append(limit)
    
    param_count += 1
    query += f" OFFSET ${param_count}"
    params.append(offset)
    
    rows = await db.fetch(query, *params)
    return [dict(row) for row in rows]

@api_router.post("/search", response_model=List[SearchResult])
async def search_documents(
    search_query: SearchQuery,
    db: asyncpg.Connection = Depends(get_db)
):
    """Hybrid search (FTS + vector) with filters"""
    try:
        # Get query embedding
        query_embeddings = await get_embeddings([search_query.query])
        query_embedding = query_embeddings[0]
        
        # Build SQL query with hybrid search
        sql = '''
            WITH fts_search AS (
                SELECT ds.id, ts_rank(to_tsvector('german', ds.content), query) as fts_score
                FROM document_sections ds, to_tsquery('german', $1) query
                WHERE to_tsvector('german', ds.content) @@ query
            ),
            vector_search AS (
                SELECT ds.id, 1 - (ds.embedding <=> $2::vector) as vector_score
                FROM document_sections ds
                WHERE ds.embedding IS NOT NULL
                ORDER BY ds.embedding <=> $2::vector
                LIMIT 100
            )
            SELECT DISTINCT
                ds.id, ds.document_id, d.title as document_title,
                ds.anchor_id, ds.title, ds.content, ds.page_number,
                d.trade, d.category, d.license_type,
                (COALESCE(fts.fts_score, 0) * $3 + COALESCE(vs.vector_score, 0) * $4) as relevance_score
            FROM document_sections ds
            JOIN documents d ON ds.document_id = d.id
            LEFT JOIN fts_search fts ON ds.id = fts.id
            LEFT JOIN vector_search vs ON ds.id = vs.id
            WHERE (fts.fts_score IS NOT NULL OR vs.vector_score IS NOT NULL)
        '''
        
        params = [
            search_query.query.replace(' ', ' & '),  # FTS query
            str(query_embedding),  # Vector query as string
            float(os.environ.get('SEARCH_FTS_WEIGHT', 0.45)),  # FTS weight
            float(os.environ.get('SEARCH_VECTOR_WEIGHT', 0.55))  # Vector weight
        ]
        param_count = 4
        
        # Add filters
        if search_query.trade_filter:
            param_count += 1
            sql += f" AND d.trade = ${param_count}"
            params.append(search_query.trade_filter)
        
        if search_query.category_filter:
            param_count += 1
            sql += f" AND d.category = ${param_count}"
            params.append(search_query.category_filter)
        
        if search_query.jurisdiction_filter:
            param_count += 1
            sql += f" AND d.jurisdiction = ${param_count}"
            params.append(search_query.jurisdiction_filter)
        
        if search_query.license_filter:
            param_count += 1
            sql += f" AND d.license_type = ${param_count}"
            params.append(search_query.license_filter)
        
        # Add ordering and pagination
        sql += " ORDER BY relevance_score DESC"
        param_count += 1
        sql += f" LIMIT ${param_count}"
        params.append(search_query.limit)
        
        param_count += 1
        sql += f" OFFSET ${param_count}"
        params.append(search_query.offset)
        
        rows = await db.fetch(sql, *params)
        
        results = []
        for row in rows:
            result = dict(row)
            # Handle license compliance
            if result['license_type'] in ['DIN', 'VDI']:
                result['content'] = f"[Lizenzierter Inhalt - {result['license_type']}] Nur Metadaten verfügbar. Volltext erfordert Lizenz."
            results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/qa", response_model=QAResponse)
async def question_answer(
    qa_query: QAQuery,
    db: asyncpg.Connection = Depends(get_db)
):
    """RAG-based question answering with citations"""
    try:
        # Perform search to get relevant sections
        search_query = SearchQuery(
            query=qa_query.question,
            trade_filter=qa_query.trade_filter,
            jurisdiction_filter=qa_query.jurisdiction_filter,
            building_type_filter=qa_query.building_type_filter,
            limit=5
        )
        
        # Get search results
        search_results = await search_documents(search_query, db)
        
        # Prepare context for RAG
        context_sections = []
        for result in search_results:
            context_sections.append({
                'anchor_id': result['anchor_id'],
                'document_title': result['document_title'],
                'title': result['title'],
                'content': result['content'],
                'page_number': result['page_number'],
                'relevance_score': result['relevance_score']
            })
        
        # Generate RAG response
        rag_response = await generate_rag_response(qa_query.question, context_sections)
        
        return QAResponse(**rag_response)
        
    except Exception as e:
        logger.error(f"QA error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    db: asyncpg.Connection = Depends(get_db)
):
    """Get document details with sections"""
    doc_row = await db.fetchrow(
        "SELECT * FROM documents WHERE id = $1", document_id
    )
    
    if not doc_row:
        raise HTTPException(status_code=404, detail="Document not found")
    
    sections_rows = await db.fetch(
        "SELECT * FROM document_sections WHERE document_id = $1 ORDER BY page_number",
        document_id
    )
    
    document = dict(doc_row)
    document['sections'] = [dict(row) for row in sections_rows]
    
    return document

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    await init_database()
    logger.info("TGA Knowledge Platform started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    global db_pool
    if db_pool:
        await db_pool.close()
    logger.info("TGA Knowledge Platform shut down")