"""
Fire Separation Clearance Configurator Backend
Computes minimum clearance between services based on German fire protection regulations
"""

from fastapi import APIRouter, HTTPException, Depends
import asyncpg
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

# Router for fire clearance endpoints
fire_router = APIRouter(prefix="/fire", tags=["fire_clearance"])

# Pydantic Models
class InsulationData(BaseModel):
    class_type: str = Field(..., alias="class", description="Insulation class (A1, A2, B, etc.)")
    thickness_mm: int = Field(..., description="Insulation thickness in mm")
    wrap: List[str] = Field(default=[], description="Wrapping types (e.g., metal_wrap_Z)")

class MountData(BaseModel):
    clamp_spacing_m: float = Field(..., description="Clamp spacing in meters")

class Context(BaseModel):
    location: str = Field(..., description="Location (shaft, wall, ceiling)")
    jurisdiction: str = Field(..., description="State code (BY, BW, etc.)")
    building_class: str = Field(..., description="Building class (Hochhaus, etc.)")

class ClearanceRequest(BaseModel):
    product_id: str = Field(..., description="Product identifier")
    material: str = Field(..., description="Material type (stainless_steel, copper, plastic)")
    DN: int = Field(..., description="Nominal diameter")
    insulation: InsulationData
    layout: str = Field(..., description="Layout (parallel, bundled, single)")
    bundle_count: int = Field(default=1, description="Number of pipes in bundle")
    mount: MountData
    context: Context

class ClearanceSource(BaseModel):
    type: str = Field(..., description="Source type (AbP, AbZ, MLAR)")
    number: Optional[str] = Field(None, description="Approval number")
    anchor: str = Field(..., description="Anchor reference")
    url: str = Field(..., description="Deep link to source")
    ref: Optional[str] = Field(None, description="Reference text")

class ClearanceResponse(BaseModel):
    min_clearance_mm: int = Field(..., description="Minimum clearance in mm")
    status: str = Field(..., description="Status (zulässig, bedingt zulässig, nicht zulässig)")
    conditions_unmet: List[str] = Field(default=[], description="List of unmet conditions")
    sources: List[ClearanceSource] = Field(..., description="Source citations")
    notes: str = Field(..., description="Additional notes and requirements")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Debug information")

# Database helper
async def get_db_connection():
    """Get database connection - reuse existing connection logic"""
    import os
    postgres_url = os.environ.get('POSTGRES_URL')
    return await asyncpg.connect(postgres_url)

class FireClearanceEngine:
    """Rule engine for computing fire separation clearances"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    async def compute_clearance(self, request: ClearanceRequest, debug: bool = False) -> ClearanceResponse:
        """Compute minimum clearance based on rules and approvals"""
        
        debug_info = {} if debug else None
        
        try:
            # Step 1: Load candidate rules
            rules = await self._load_matching_rules(request)
            if debug_info is not None:
                debug_info['rules_loaded'] = len(rules)
                debug_info['rules'] = rules
            
            # Step 2: Evaluate approval-based rules first
            approval_results = []
            for rule in rules:
                if rule.get('approval_id'):
                    result = await self._evaluate_rule(rule, request)
                    if result['matches']:
                        approval_results.append(result)
            
            if debug_info is not None:
                debug_info['approval_matches'] = len(approval_results)
            
            # Step 3: Apply rule precedence
            if approval_results:
                # Choose strictest approval (max clearance)
                best_result = max(approval_results, key=lambda x: x['min_clearance_mm'])
                
                # Union all conditions from matching approvals
                all_conditions = []
                all_sources = []
                for result in approval_results:
                    all_conditions.extend(result.get('must_have', []))
                    all_sources.append(result['source'])
                
                return ClearanceResponse(
                    min_clearance_mm=best_result['min_clearance_mm'],
                    status=best_result['status'],
                    conditions_unmet=self._check_unmet_conditions(all_conditions, request),
                    sources=all_sources,
                    notes=best_result.get('notes', ''),
                    debug_info=debug_info
                )
            
            # Step 4: Fall back to MLAR default
            mlar_rule = await self._get_mlar_fallback(request)
            if mlar_rule:
                return ClearanceResponse(
                    min_clearance_mm=mlar_rule['min_clearance_mm'],
                    status="default",
                    conditions_unmet=[],
                    sources=[mlar_rule['source']],
                    notes="MLAR Standardregelung angewendet - keine spezifische Zulassung gefunden.",
                    debug_info=debug_info
                )
            
            # Step 5: No applicable rules found
            return ClearanceResponse(
                min_clearance_mm=100,  # Conservative fallback
                status="nicht zulässig",
                conditions_unmet=["Keine anwendbare Regel gefunden"],
                sources=[],
                notes="Keine anwendbare Brandschutzregel für diese Konfiguration gefunden. Bitte Einzelfallprüfung durchführen.",
                debug_info=debug_info
            )
            
        except Exception as e:
            logger.error(f"Error computing clearance: {e}")
            raise HTTPException(status_code=500, detail=f"Fehler bei der Berechnung: {str(e)}")
    
    async def _load_matching_rules(self, request: ClearanceRequest) -> List[Dict]:
        """Load rules matching the basic criteria"""
        query = """
            SELECT r.*, a.number as approval_number, a.type as approval_type, a.url as approval_url
            FROM rules r
            LEFT JOIN approvals a ON r.approval_id = a.id
            WHERE r.scope = 'pipe_to_pipe'
              AND (r.valid_to IS NULL OR r.valid_to > NOW())
              AND (
                r.conditions_json->>'material_in' IS NULL 
                OR $1 = ANY(string_to_array(trim(r.conditions_json->>'material_in', '[]"'), '","'))
              )
              AND (
                r.conditions_json->>'DN_max' IS NULL 
                OR $2::int <= (r.conditions_json->>'DN_max')::int
              )
            ORDER BY r.priority DESC
        """
        
        rows = await self.db.fetch(query, request.material, request.DN)
        return [dict(row) for row in rows]
    
    async def _evaluate_rule(self, rule: Dict, request: ClearanceRequest) -> Dict:
        """Evaluate if a rule matches and compute result"""
        conditions = rule.get('conditions_json', {})
        if isinstance(conditions, str):
            conditions = json.loads(conditions)
        
        result_data = rule.get('result_json', {})
        if isinstance(result_data, str):
            result_data = json.loads(result_data)
        
        # Check all conditions
        matches = True
        reasons = []
        
        # Material check
        if 'material_in' in conditions:
            if request.material not in conditions['material_in']:
                matches = False
                reasons.append(f"Material {request.material} nicht in erlaubten Materialien")
        
        # DN check
        if 'DN_max' in conditions:
            if request.DN > conditions['DN_max']:
                matches = False
                reasons.append(f"DN {request.DN} > max erlaubte {conditions['DN_max']}")
        
        # Insulation class check
        if 'insulation_class_in' in conditions:
            if request.insulation.class_type not in conditions['insulation_class_in']:
                matches = False
                reasons.append(f"Dämmklasse {request.insulation.class_type} nicht erlaubt")
        
        # Layout check
        if 'layout_in' in conditions:
            if request.layout not in conditions['layout_in']:
                matches = False
                reasons.append(f"Layout {request.layout} nicht erlaubt")
        
        # Bundle count check
        if 'bundle_count_max' in conditions:
            if request.bundle_count > conditions['bundle_count_max']:
                matches = False
                reasons.append(f"Bündelanzahl {request.bundle_count} > max {conditions['bundle_count_max']}")
        
        # Clamp spacing check
        if 'clamp_spacing_m_max' in conditions:
            if request.mount.clamp_spacing_m > conditions['clamp_spacing_m_max']:
                matches = False
                reasons.append(f"Befestigungsabstand {request.mount.clamp_spacing_m}m > max {conditions['clamp_spacing_m_max']}m")
        
        # Wrapping requirements check
        if 'requires_wrap' in conditions:
            required_wraps = conditions['requires_wrap']
            if not all(wrap in request.insulation.wrap for wrap in required_wraps):
                matches = False
                missing_wraps = [w for w in required_wraps if w not in request.insulation.wrap]
                reasons.append(f"Fehlende Ummantelung: {', '.join(missing_wraps)}")
        
        # Build source information
        source = ClearanceSource(
            type=rule.get('approval_type', 'Rule'),
            number=rule.get('approval_number'),
            anchor=result_data.get('source', {}).get('anchor', f"rule-{rule['id']}"),
            url=rule.get('approval_url', '#'),
            ref=result_data.get('source', {}).get('ref')
        )
        
        return {
            'matches': matches,
            'reasons': reasons,
            'min_clearance_mm': result_data.get('min_clearance_mm', 0),
            'status': result_data.get('status', 'unknown'),
            'must_have': result_data.get('must_have', []),
            'notes': result_data.get('notes', ''),
            'source': source
        }
    
    async def _get_mlar_fallback(self, request: ClearanceRequest) -> Optional[Dict]:
        """Get MLAR fallback rule"""
        # Simple MLAR fallback - in real implementation, this would be jurisdiction-specific
        return {
            'min_clearance_mm': 50,
            'status': 'default',
            'notes': 'MLAR Standardregelung - 50mm Mindestabstand für Rohrleitungen ohne spezifische Zulassung',
            'source': ClearanceSource(
                type='MLAR',
                number=None,
                anchor='mlar-3.2.1',
                url='https://www.mlar-brandschutz.de/kapitel-3',
                ref='Kapitel 3.2.1 - Mindestabstände für Rohrleitungen'
            )
        }
    
    def _check_unmet_conditions(self, required_conditions: List[str], request: ClearanceRequest) -> List[str]:
        """Check which required conditions are not met"""
        unmet = []
        
        for condition in required_conditions:
            if condition.startswith('metal_wrap_'):
                if condition not in request.insulation.wrap:
                    unmet.append(f"Metallummantelung {condition} erforderlich")
            # Add more condition checks as needed
        
        return unmet

# API Endpoints
@fire_router.post("/clearance/compute", response_model=ClearanceResponse)
async def compute_clearance(
    request: ClearanceRequest,
    debug: bool = False
):
    """Compute minimum fire separation clearance"""
    
    async with await get_db_connection() as db:
        engine = FireClearanceEngine(db)
        return await engine.compute_clearance(request, debug)

@fire_router.get("/products")
async def get_products():
    """Get available products for selection"""
    conn = await get_db_connection()
    try:
        query = """
            SELECT p.id, p.name, p.manufacturer_id, p.material, p.system_code,
                   m.name as manufacturer_name
            FROM products p
            LEFT JOIN manufacturers m ON p.manufacturer_id = m.id
            ORDER BY m.name, p.name
        """
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]
    finally:
        await conn.close()

@fire_router.get("/materials")
async def get_materials():
    """Get available materials"""
    return [
        {"value": "stainless_steel", "label": "Edelstahl"},
        {"value": "copper", "label": "Kupfer"},
        {"value": "plastic", "label": "Kunststoff"},
        {"value": "steel", "label": "Stahl"},
        {"value": "cast_iron", "label": "Gusseisen"}
    ]

@fire_router.get("/insulation-classes")
async def get_insulation_classes():
    """Get available insulation classes"""
    return [
        {"value": "A1", "label": "A1 - Nicht brennbar"},
        {"value": "A2", "label": "A2 - Nicht brennbar (begrenzte Anteile organischer Stoffe)"},
        {"value": "B", "label": "B - Schwer entflammbar"},
        {"value": "C", "label": "C - Normal entflammbar"},
        {"value": "D", "label": "D - Leicht entflammbar"},
        {"value": "E", "label": "E - Sehr leicht entflammbar"},
        {"value": "F", "label": "F - Nicht klassifiziert"}
    ]

@fire_router.get("/wrapping-types")
async def get_wrapping_types():
    """Get available wrapping types"""
    return [
        {"value": "metal_wrap_Z", "label": "Metallummantelung Typ Z"},
        {"value": "metal_wrap_Y", "label": "Metallummantelung Typ Y"},
        {"value": "ceramic_wrap", "label": "Keramikummantelung"},
        {"value": "mineral_wrap", "label": "Mineralfaserummantelung"}
    ]

@fire_router.get("/jurisdictions")
async def get_jurisdictions():
    """Get available jurisdictions"""
    return [
        {"value": "BY", "label": "Bayern"},
        {"value": "BW", "label": "Baden-Württemberg"},
        {"value": "NW", "label": "Nordrhein-Westfalen"},
        {"value": "HE", "label": "Hessen"},
        {"value": "NI", "label": "Niedersachsen"},
        {"value": "BE", "label": "Berlin"},
        {"value": "HH", "label": "Hamburg"},
        {"value": "SN", "label": "Sachsen"},
        {"value": "TH", "label": "Thüringen"},
        {"value": "ST", "label": "Sachsen-Anhalt"},
        {"value": "BB", "label": "Brandenburg"},
        {"value": "MV", "label": "Mecklenburg-Vorpommern"},
        {"value": "SL", "label": "Saarland"},
        {"value": "RP", "label": "Rheinland-Pfalz"},
        {"value": "SH", "label": "Schleswig-Holstein"},
        {"value": "HB", "label": "Bremen"}
    ]