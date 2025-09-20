# 🏗️ TGA Knowledge Platform

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
- **Responsive design** optimized for engineering workflows
- **Real-time form validation** and user feedback

### Database
- **PostgreSQL** with vector extension (pgvector)
- **Document storage** with stable anchor IDs for citations
- **Fire clearance tables** with approval and rule management
- **German jurisdiction** and manufacturer data

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- Emergent LLM key for AI features

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tga-knowledge-platform
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Initialize databases
   python fire_clearance_init.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   yarn install
   yarn start
   ```

4. **Environment Configuration**
   ```bash
   # Backend (.env)
   POSTGRES_URL=postgresql://postgres@localhost:5432/tga_knowledge
   EMERGENT_LLM_KEY=your_emergent_key_here
   
   # Frontend (.env)
   REACT_APP_BACKEND_URL=http://localhost:8001
   ```

## 📖 API Documentation

### Core Knowledge APIs

#### Documents
```http
GET /api/documents
POST /api/documents/upload  # Multipart form data
GET /api/documents/{id}
```

#### Search & Q&A
```http
POST /api/search           # Hybrid search with filters
POST /api/qa              # RAG-based question answering
```

### Fire Clearance APIs *(NEW)*

#### Configuration Options
```http
GET /api/fire/products           # TROX, Viega products
GET /api/fire/materials          # Stainless steel, copper, etc.
GET /api/fire/insulation-classes # A1, A2, B, C, D, E, F
GET /api/fire/wrapping-types     # Metal wrap types
GET /api/fire/jurisdictions      # German states
```

#### Clearance Calculation
```http
POST /api/fire/clearance/compute
```

**Request Example:**
```json
{
  "product_id": "1",
  "material": "stainless_steel",
  "DN": 200,
  "insulation": {
    "class": "A2",
    "thickness_mm": 30,
    "wrap": ["metal_wrap_Z"]
  },
  "layout": "parallel",
  "bundle_count": 2,
  "mount": {
    "clamp_spacing_m": 1.5
  },
  "context": {
    "location": "shaft",
    "jurisdiction": "BY",
    "building_class": "Hochhaus"
  }
}
```

**Response Example:**
```json
{
  "min_clearance_mm": 0,
  "status": "zulässig",
  "conditions_unmet": [],
  "sources": [
    {
      "type": "AbP",
      "number": "ABP-2024-INOX-001",
      "anchor": "sec-3.2",
      "url": "https://www.dibt.de/de/zulassungen/abp-2024-inox-001"
    }
  ],
  "notes": "0 mm zulässig bis DN 200 mit A2 Dämmung und Metallummantelung Z."
}
```

## 🔧 Fire Clearance Rule Engine

### Rule Precedence
1. **AbP/AbZ specific approvals** (conditions met) override general rules
2. **MLAR defaults** when no applicable approval conditions are met  
3. **Multiple approvals** → choose stricter result (max clearance)
4. **Audit trail** with sources and condition tracking

### Golden Test Cases
- **With metal wrap**: 0mm clearance (AbP approval)
- **Without metal wrap**: 50mm clearance (MLAR fallback)

### Database Schema
```sql
-- Core tables
manufacturers, products, approvals, rules, insulations, jurisdictions

-- Rule structure
{
  "scope": "pipe_to_pipe",
  "conditions": {
    "material_in": ["stainless_steel"],
    "DN_max": 200,
    "insulation_class_in": ["A1", "A2"],
    "requires_wrap": ["metal_wrap_Z"]
  },
  "result": {
    "min_clearance_mm": 0,
    "status": "zulässig"
  }
}
```

## 🎯 User Interface

### Main Navigation
- **🏠 Startseite**: Homepage with feature overview
- **🔍 Suche**: Hybrid search with advanced filters
- **💬 Q&A Chat**: AI-powered TGA expert assistance
- **🧮 Brandschutz**: Fire separation clearance calculator *(NEW)*
- **📤 Upload**: Document upload and processing
- **🏢 Projekte**: Project profile management

### Fire Clearance Configurator Workflow
1. **Step 1 - System Configuration**: Product, material, DN, insulation, layout
2. **Step 2 - Project Context**: Location, jurisdiction, building class  
3. **Step 3 - Results**: Clearance value, compliance status, sources

## 🔐 Compliance & Security

### German Regulatory Compliance
- **DIN/VDI Standards**: Metadata-only display with official deep-links
- **AbP/AbZ Approvals**: Integration with DIBt approval database
- **MLAR Compliance**: Fallback rules for standard applications
- **Jurisdiction Filtering**: State-specific regulations (Bayern, BW, NW, etc.)

### License Management
- **Open Content**: Full text display and search
- **Licensed Content**: Metadata + summaries + external links only
- **Source Attribution**: Stable anchor IDs for precise citations

## 📊 Performance & Analytics

### Search Performance
- **Hybrid Algorithm**: 45% full-text + 55% vector similarity
- **German Language**: Optimized full-text search with German stemming
- **Vector Similarity**: OpenAI text-embedding-3-large embeddings
- **Query Response**: <2 seconds for most searches

### Fire Clearance Performance
- **Rule Evaluation**: <500ms for standard calculations
- **Database Queries**: Optimized with proper indexing
- **Condition Matching**: Real-time validation with instant feedback

## 🧪 Testing

### Backend Testing
```bash
cd backend
python backend_test.py
```
**Latest Results**: 15/17 tests passed (88.2% success rate)

### Frontend Testing
- React component testing with Jest
- E2E testing with Playwright
- Form validation and user workflow testing

### Fire Clearance Testing
- Golden test cases with AbP and MLAR scenarios
- Rule engine logic validation
- API contract testing

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards
- **Backend**: Black formatting, FastAPI best practices
- **Frontend**: ESLint configuration, React hooks patterns
- **Database**: PostgreSQL naming conventions
- **Testing**: Comprehensive test coverage for new features

## 📝 Changelog

### v2.0.0 - Fire Clearance Module *(Latest)*
- ✅ Added Fire Separation Clearance Configurator
- ✅ Professional 3-step wizard interface
- ✅ AbP/AbZ approval integration with rule engine
- ✅ German manufacturer product database
- ✅ MLAR fallback compliance system
- ✅ Real-time clearance calculation with citations

### v1.0.0 - TGA Knowledge Platform
- ✅ Hybrid search engine (FTS + vector)
- ✅ RAG-based Q&A with citations  
- ✅ Document upload and processing pipeline
- ✅ Project profile management
- ✅ German TGA industry localization
- ✅ License compliance system

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **German TGA Industry**: For regulatory standards and best practices
- **Emergent Platform**: For LLM integration and hosting infrastructure
- **Open Source Community**: For the excellent tools and libraries used

## 📞 Support

For questions, issues, or feature requests:
- 📧 **Email**: support@tga-knowledge-platform.de
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 📖 **Documentation**: [Wiki](https://github.com/your-repo/wiki)

---

**Built with ❤️ for the German TGA community**
