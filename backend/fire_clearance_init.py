"""
Initialize fire clearance database tables and seed data
"""

import asyncio
import asyncpg
import os
import json
from datetime import datetime, timezone

async def init_fire_clearance_tables():
    """Initialize database tables for fire clearance configurator"""
    
    postgres_url = os.environ.get('POSTGRES_URL')
    conn = await asyncpg.connect(postgres_url)
    
    try:
        # Create manufacturers table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS manufacturers (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                country VARCHAR DEFAULT 'DE',
                website VARCHAR,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Create products table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                manufacturer_id INTEGER REFERENCES manufacturers(id),
                name VARCHAR NOT NULL,
                material VARCHAR NOT NULL,
                system_code VARCHAR,
                description TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Create approvals table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS approvals (
                id SERIAL PRIMARY KEY,
                type VARCHAR NOT NULL CHECK(type IN ('AbP', 'AbZ', 'ETA')),
                number VARCHAR NOT NULL,
                issuer VARCHAR,
                product_id INTEGER REFERENCES products(id),
                version VARCHAR,
                valid_from DATE,
                valid_to DATE,
                jurisdiction VARCHAR,
                pdf_key VARCHAR,
                url VARCHAR,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Create rules table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS rules (
                id SERIAL PRIMARY KEY,
                approval_id INTEGER REFERENCES approvals(id),
                scope VARCHAR NOT NULL DEFAULT 'pipe_to_pipe',
                priority INTEGER DEFAULT 50,
                conditions_json JSONB NOT NULL,
                result_json JSONB NOT NULL,
                anchors JSONB,
                valid_from DATE DEFAULT CURRENT_DATE,
                valid_to DATE,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Create insulations table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS insulations (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                class VARCHAR NOT NULL,
                thickness_min INTEGER,
                thickness_max INTEGER,
                wrap_required BOOLEAN DEFAULT FALSE,
                description TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Create jurisdictions table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS jurisdictions (
                id SERIAL PRIMARY KEY,
                state VARCHAR NOT NULL,
                mlr_version VARCHAR,
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        
        # Create indexes
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_rules_scope ON rules(scope)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_rules_priority ON rules(priority)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_rules_valid_to ON rules(valid_to)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_approvals_type ON approvals(type)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_products_material ON products(material)')
        
        print("✅ Fire clearance tables created successfully")
        
        # Insert seed data
        await insert_seed_data(conn)
        
    finally:
        await conn.close()

async def insert_seed_data(conn):
    """Insert seed data for demo purposes"""
    
    # Insert manufacturers
    manufacturers = [
        ("TROX GmbH", "DE", "https://www.trox.de"),
        ("Viega GmbH", "DE", "https://www.viega.de"),
        ("Geberit AG", "CH", "https://www.geberit.de"),
        ("OBO Bettermann", "DE", "https://www.obo.de")
    ]
    
    for name, country, website in manufacturers:
        await conn.execute(
            "INSERT INTO manufacturers (name, country, website) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            name, country, website
        )
    
    # Get manufacturer IDs
    trox_id = await conn.fetchval("SELECT id FROM manufacturers WHERE name = 'TROX GmbH'")
    viega_id = await conn.fetchval("SELECT id FROM manufacturers WHERE name = 'Viega GmbH'")
    
    # Insert products
    products = [
        (trox_id, "S-INOX Edelstahlrohr", "stainless_steel", "S-INOX-DN", "Edelstahl-Rohrleitungssystem für HLK-Anlagen"),
        (viega_id, "Prestabo System", "stainless_steel", "PRESTABO", "Press-Verbindungssystem aus Edelstahl"),
        (viega_id, "Sanpress Inox", "stainless_steel", "SANPRESS", "Press-System für Trinkwasserinstallation")
    ]
    
    product_ids = []
    for mfg_id, name, material, code, desc in products:
        product_id = await conn.fetchval(
            """INSERT INTO products (manufacturer_id, name, material, system_code, description) 
               VALUES ($1, $2, $3, $4, $5) 
               ON CONFLICT DO NOTHING 
               RETURNING id""",
            mfg_id, name, material, code, desc
        )
        if product_id:
            product_ids.append(product_id)
    
    # Get first product ID for approval
    if product_ids:
        product_id = product_ids[0]
    else:
        product_id = await conn.fetchval("SELECT id FROM products LIMIT 1")
    
    # Insert sample approval
    approval_id = await conn.fetchval(
        """INSERT INTO approvals (type, number, issuer, product_id, version, valid_from, valid_to, jurisdiction, url)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
           ON CONFLICT DO NOTHING
           RETURNING id""",
        'AbP', 'ABP-2024-INOX-001', 'DIBt', product_id, '1.0', 
        datetime(2024, 1, 1).date(), datetime(2026, 12, 31).date(), 'BY',
        'https://www.dibt.de/de/zulassungen/abp-2024-inox-001'
    )
    
    if not approval_id:
        approval_id = await conn.fetchval("SELECT id FROM approvals LIMIT 1")
    
    # Insert approval-based rule (0mm clearance with conditions)
    approval_rule = {
        "scope": "pipe_to_pipe",
        "priority": 100,
        "conditions_json": {
            "material_in": ["stainless_steel"],
            "DN_max": 200,
            "insulation_class_in": ["A1", "A2"],
            "layout_in": ["parallel"],
            "bundle_count_max": 2,
            "clamp_spacing_m_max": 1.5,
            "requires_wrap": ["metal_wrap_Z"]
        },
        "result_json": {
            "min_clearance_mm": 0,
            "status": "zulässig",
            "must_have": ["metal_wrap_Z"],
            "notes": "0 mm zulässig bis DN 200 mit A1/A2 Dämmung und Metallummantelung Z. Befestigungsabstand max. 1,5 m beachten.",
            "source": {
                "type": "AbP",
                "number": "ABP-2024-INOX-001",
                "anchor": "sec-3.2",
                "url": "https://www.dibt.de/de/zulassungen/abp-2024-inox-001#sec-3.2"
            }
        }
    }
    
    await conn.execute(
        """INSERT INTO rules (approval_id, scope, priority, conditions_json, result_json, valid_from, valid_to)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT DO NOTHING""",
        approval_id, approval_rule["scope"], approval_rule["priority"],
        json.dumps(approval_rule["conditions_json"]), json.dumps(approval_rule["result_json"]),
        datetime(2024, 1, 1).date(), datetime(2026, 12, 31).date()
    )
    
    # Insert MLAR fallback rule
    mlar_rule = {
        "scope": "pipe_to_pipe", 
        "priority": 10,
        "conditions_json": {
            "applies_if_no_abp_match": True
        },
        "result_json": {
            "min_clearance_mm": 50,
            "status": "default",
            "notes": "MLAR Standardregelung - 50mm Mindestabstand für Rohrleitungen ohne spezifische Zulassung",
            "source": {
                "type": "MLAR",
                "ref": "Kapitel 3.2.1",
                "anchor": "mlar-3.2.1",
                "url": "https://www.mlar-brandschutz.de/kapitel-3.2.1"
            }
        }
    }
    
    await conn.execute(
        """INSERT INTO rules (approval_id, scope, priority, conditions_json, result_json)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT DO NOTHING""",
        None, mlar_rule["scope"], mlar_rule["priority"],
        json.dumps(mlar_rule["conditions_json"]), json.dumps(mlar_rule["result_json"])
    )
    
    # Insert insulation types
    insulation_types = [
        ("Mineralwolle A1", "A1", 20, 100, False, "Nicht brennbare Mineralfaserdämmung"),
        ("Mineralwolle A2", "A2", 20, 100, False, "Nicht brennbare Mineralfaserdämmung mit begrenzten organischen Anteilen"),
        ("PU-Schaum B", "B", 10, 50, True, "Schwer entflammbare Polyurethan-Dämmung"),
        ("Elastomer C", "C", 5, 30, True, "Normal entflammbare Elastomer-Dämmung")
    ]
    
    for name, class_val, thick_min, thick_max, wrap_req, desc in insulation_types:
        await conn.execute(
            """INSERT INTO insulations (name, class, thickness_min, thickness_max, wrap_required, description)
               VALUES ($1, $2, $3, $4, $5, $6)
               ON CONFLICT DO NOTHING""",
            name, class_val, thick_min, thick_max, wrap_req, desc
        )
    
    # Insert jurisdictions
    jurisdictions = [
        ("BY", "2024.1", "Bayern - Bayerische Bauordnung"),
        ("BW", "2024.1", "Baden-Württemberg"),
        ("NW", "2024.1", "Nordrhein-Westfalen"),
        ("HE", "2024.1", "Hessen")
    ]
    
    for state, version, notes in jurisdictions:
        await conn.execute(
            """INSERT INTO jurisdictions (state, mlr_version, notes)
               VALUES ($1, $2, $3)
               ON CONFLICT DO NOTHING""",
            state, version, notes
        )
    
    print("✅ Seed data inserted successfully")

if __name__ == "__main__":
    asyncio.run(init_fire_clearance_tables())