# 🏗️ TGA Knowledge Platform

**📋 Pull Request: Fire Clearance Configurator Implementation**
This pull request implements the complete fire separation clearance configurator and ingestion pipeline, including the 3-step wizard, rule engine, and German regulatory compliance features.

A professional SaaS platform for the German TGA (Technical Building Equipment) sector, providing engineers, architects, and facility managers with comprehensive access to TGA norms, fire safety rules, product data, and compliance tools.

## 🌟 Overview
The TGA Knowledge Platform is a comprehensive German TGA knowledge management system that functions as an MCP-style knowledge server. It provides centralized access to technical building equipment information with advanced search capabilities, AI-powered Q&A, and professional compliance tools.

**🔗 Live Demo:** [https://buildingsage.preview.emergentagent.com](https://buildingsage.preview.emergentagent.com)

## ✨ Key Features
### 📚 Knowledge Management
- **Hybrid Search Engine**: Combined full-text and semantic vector search (45% FTS + 55% vector)
- **AI-Powered Q&A**: RAG-based question answering with precise citations
- **Document Processing**: Automatic OCR, text extraction, chunking, and embedding generation
- **License Compliance**: Automatic DIN/VDI detection with metadata-only display + deep-links

### 🔥 Fire Separation Clearance Configurator *(NEW)*
- **Professional 3-step wizard** for brandschutz compliance calculations
- **Rule engine** with AbP/AbZ approval precedence over MLAR defaults
- **German regulatory compliance** with proper citation system
- **Minimum clearance computation** for pipe-to-pipe installations
- **Product integration** with TROX, Viega, and other German manufacturers

### 🏢 Industry-Specific Features
- **German TGA Focus**: Complete German localization with professional terminology
- **Manufacturer Integration**: TROX, Wolf, Wilo, Grundfos, Viega, Geberit, OBO, Hilti, Bosch
- **Jurisdiction Support**: All 16 German states with specific regulations
- **Project Profiles**: Context-aware search based on building type and location

## 🏛️ Technical Architecture
### Backend
- **FastAPI** with async/await patterns
- **PostgreSQL + pgvector** for vector similarity search
- **Emergent LLM Integration** (OpenAI text-embedding-3-large, GPT-4o-mini)
- **Hybrid search** with German full-text indexing
- **Rule engine** for fire protection compliance

### Frontend
- **React 19** with modern component architecture
- **Professional German TGA styling** with glassmorphism design
