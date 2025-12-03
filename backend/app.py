# app_with_models.py — ChatLaw Backend with AI Models (Stable Loading)
import os
import re
import uuid
import logging
import glob
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Logging
logger = logging.getLogger("chatlaw")
logging.basicConfig(level=logging.INFO)

# -------------------------
# Safe Model Loading
# -------------------------
embedder = None
llm_model = None
llm_tokenizer = None
llm_name = None

def safe_import():
    """Import ML libraries safely"""
    global embedder, llm_model, llm_tokenizer, llm_name
    
    try:
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {device}")
        
        # Load embeddings model
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model...")
            embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device=device)
            logger.info("✓ Embedding model loaded")
        except Exception as e:
            logger.warning(f"Embedding model failed: {e}")
            embedder = None
        
        # Load LLM (small, stable model)
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            # Try small, stable models that work well on CPU
            models_to_try = [
                "distilgpt2",  # Very small, stable
                "gpt2",        # Slightly larger backup
            ]
            
            for model_name in models_to_try:
                try:
                    logger.info(f"Attempting to load LLM: {model_name}")
                    llm_tokenizer = AutoTokenizer.from_pretrained(model_name)
                    llm_model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=torch.float32
                    ).to(device)
                    llm_name = model_name
                    logger.info(f"✓ LLM loaded: {model_name}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"LLM loading failed: {e}")
            llm_model = None
            
    except Exception as e:
        logger.error(f"Failed to import ML libraries: {e}")

# Try to load models
safe_import()

# Import other dependencies
try:
    import pandas as pd
    import numpy as np
    import faiss
    HAS_FAISS = True
except:
    HAS_FAISS = False
    logger.warning("FAISS not available, search disabled")

# -------------------------
# Pydantic models (API)
# -------------------------
class ConsultationStartRequest(BaseModel):
    query: str
    max_turns: Optional[int] = 7

class ConsultationStartResponse(BaseModel):
    session_id: str
    next_action: str
    question: Optional[str] = None
    partial_report: Optional[str] = None

class ConsultationAnswerRequest(BaseModel):
    session_id: str
    answer: str

class ConsultationFinalResponse(BaseModel):
    session_id: str
    report: str
    structured: Dict
    timestamp: str

# -------------------------
# Knowledge Graph
# -------------------------
class KnowledgeGraph:
    def __init__(self):
        self.entities = defaultdict(list)
        self.relations = []
        self.context = {}

    def add_entity(self, entity_type: str, value: str):
        if value and value.strip() and value not in self.entities[entity_type]:
            self.entities[entity_type].append(value.strip())

    def set_context(self, key: str, value: str):
        self.context[key] = value

    def get_summary(self) -> str:
        parts = []
        for entity_type, values in self.entities.items():
            if values:
                parts.append(f"{entity_type.upper()}: {', '.join(values[:3])}")
        if self.context.get('situation'):
            parts.append(f"SITUATION: {self.context['situation'][:200]}")
        return " | ".join(parts) if parts else "Knowledge graph empty"

# -------------------------
# Smart Classifier Agent
# -------------------------
class SmartClassifierAgent:
    def __init__(self):
        self.case_keywords = {
            'criminal': ['theft','stolen','robbery','assault','murder','rape','dacoity','fir','police','crime','burglar','pickpocket','extortion','blackmail'],
            'family': ['divorce','marriage','custody','alimony','maintenance','dowry','wife','husband','domestic','separation','child','guardian'],
            'property': ['land','boundary','inheritance','encroachment','tenant','landlord','eviction','deed','title','plot','mutation'],
            'contract': ['agreement','breach','contract','payment','outstanding','invoice','debt','loan','delivery','default']
        }

    def initial_classify(self, query: str) -> tuple:
        q = query.lower()
        scores = {}
        for case_type, keywords in self.case_keywords.items():
            match_count = sum(1 for kw in keywords if kw in q)
            scores[case_type] = match_count

        if max(scores.values()) == 0:
            return 'general', 0.5

        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type] / 5.0, 1.0)
        return best_type, confidence

# -------------------------
# Entity Extraction Agent (Regex-based)
# -------------------------
class EntityExtractionAgent:
    def extract(self, text: str):
        out = {'dates': [], 'locations': [], 'values': [], 'items': [], 'parties': []}

        # Extract dates
        out['dates'] = re.findall(r'\b\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}\b', text)[:3]
        months = re.findall(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?', text, flags=re.I)
        out['dates'] += months
        
        # Extract values
        out['values'] = re.findall(r'\b(?:Rs\.?|₹)\s*[\d,]+\b', text)[:3]
        
        # Extract locations (capitalized words)
        caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b', text)
        out['locations'] = caps[:4]
        
        # Extract items
        keywords = ['phone','laptop','car','house','land','jewelry','money','document','agreement','FIR','complaint']
        out['items'] = [kw for kw in keywords if kw.lower() in text.lower()][:4]
        
        return {k:list(dict.fromkeys(v)) for k,v in out.items()}

# -------------------------
# Adaptive Question Generator (FIXED)
# -------------------------
class AdaptiveQuestionGenerator:
    OFFENSE_KEYWORDS = {
        'murder':  ['murder','killed','homicide','stabbed','shot','strangled','burned','ipc 302','302'],
        'theft':   ['theft','stolen','pickpocket','burglary','phone was stolen','ipc 379','379'],
        'robbery': ['robbery','dacoity','snatched','armed','weapon','force','ipc 392','392','395','396'],
        'assault': ['assault','beat','injury','attack','fight','ipc 323','324','325','326'],
    }

    QUESTION_TEMPLATES = {
        # CRIMINAL CASES
        'murder': {
            'time':       ['When did the incident occur?', 'Approximate time of death known?'],
            'location':   ['Where did the incident happen?', 'Where was the body found?'],
            'relationship':['What was the relationship between accused and victim?', 'Any prior dispute?'],
            'weapon':     ['What weapon was used? (knife/firearm/blunt object)', 'Was the weapon recovered?'],
            'evidence':   ['Post-mortem report available?', 'Any CCTV or eyewitnesses?'],
            'police':     ['FIR filed? Which police station?', 'Any arrests made?'],
        },
        'robbery': {
            'time':     ['When did the robbery occur?'],
            'location': ['Where exactly did it happen? (street / shop / home)'],
            'force':    ['Was a weapon or threat used?', 'Any injuries?'],
            'property': ['What items or money were taken?'],
            'evidence': ['Any CCTV or witnesses?', 'Police informed? FIR filed?']
        },
        'theft': {
            'time':     ['When was the item last seen?', 'When did you notice it missing?'],
            'location': ['Where was the theft location?'],
            'property': ['What item was stolen? (model/serial/IMEI)'],
            'evidence': ['CCTV or witnesses?', 'Proof of ownership available?'],
            'police':   ['FIR filed? Which station?']
        },
        'assault': {
            'time':     ['When did the assault occur?'],
            'location': ['Where did it happen?'],
            'injury':   ['What injuries occurred? Medical report available?'],
            'cause':    ['Was there a dispute or trigger?'],
            'evidence': ['CCTV or witnesses?', 'Any hospital or police report?']
        },
        
        # PROPERTY CASES
        'property': {
            'type':     ['What type of property dispute? (land/house/inheritance/tenant)'],
            'location': ['Where is the property located? (address/survey number)'],
            'ownership':['Do you have ownership documents? (sale deed/title deed)'],
            'dispute':  ['What is the exact nature of the dispute?'],
            'timeline': ['When did the dispute start?'],
            'parties':  ['Who are the other parties involved?'],
            'documents':['Do you have: mutation records, property tax receipts, court orders?']
        },
        
        # FAMILY CASES
        'family': {
            'type':     ['What is the family matter? (divorce/custody/maintenance/inheritance)'],
            'marriage': ['When and where did the marriage take place?'],
            'duration': ['How long have you been married/separated?'],
            'children': ['Do you have children? If yes, their ages?'],
            'grounds':  ['What are the grounds for divorce/dispute?'],
            'attempts': ['Have you tried mediation or counseling?'],
            'documents':['Do you have: marriage certificate, proof of income, other relevant documents?']
        },
        
        # CONTRACT CASES
        'contract': {
            'type':     ['What type of agreement? (sale/loan/service/employment)'],
            'date':     ['When was the contract signed?'],
            'amount':   ['What is the contract value/amount involved?'],
            'breach':   ['How has the contract been breached?'],
            'timeline': ['When did the breach occur?'],
            'written':  ['Do you have a written agreement?'],
            'remedy':   ['What remedy are you seeking? (refund/specific performance/damages)']
        },
        
        # GENERAL
        'general': {
            'issue':    ['Please describe your legal issue in detail'],
            'parties':  ['Who are the parties involved?'],
            'timeline': ['When did this issue arise?'],
            'documents':['Do you have any relevant documents?'],
            'urgency':  ['Is this matter urgent?']
        }
    }

    def detect_crime_subtype(self, text: str) -> str:
        t = text.lower()
        best = 'theft'
        best_score = 0
        for subtype, keywords in self.OFFENSE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in t)
            if score > best_score:
                best = subtype
                best_score = score
        return best

    def generate_next(self, case_type: str, kg: KnowledgeGraph, asked: List[str]) -> Optional[str]:
        """Generate next question based on case type, ensuring no repeats"""
        situation = kg.context.get('situation', '')
        
        # Determine which template to use
        if case_type == 'criminal':
            subtype = kg.context.get('criminal_subtype') or self.detect_crime_subtype(situation)
            templates = self.QUESTION_TEMPLATES.get(subtype, self.QUESTION_TEMPLATES['theft'])
        else:
            # For non-criminal cases, use case_type directly
            templates = self.QUESTION_TEMPLATES.get(case_type, self.QUESTION_TEMPLATES['general'])

        # Iterate through all question categories
        for category, questions in templates.items():
            # Find questions that haven't been asked yet
            missing_questions = [q for q in questions if q not in asked]
            if missing_questions:
                logger.info(f"Next question from category '{category}': {missing_questions[0]}")
                return missing_questions[0]

        logger.info("All questions exhausted")
        return None

# -------------------------
# AI-Powered Analyzer with LLM
# -------------------------
class AIAnalyzer:
    def __init__(self):
        self.has_llm = llm_model is not None
        
    def analyze(self, case_type: str, kg: KnowledgeGraph) -> str:
        situation = kg.context.get('situation', '')
        
        # Get appropriate subtype based on case_type
        if case_type == 'criminal':
            subtype = kg.context.get('criminal_subtype', 'Unknown')
        else:
            subtype = case_type  # For non-criminal, use the case_type itself
        
        # Build fact summary
        fact_text = "\n".join([
            f"{k.upper()}: {', '.join(v)}" 
            for k, v in kg.entities.items() if v
        ])
        
        # For now, use enhanced template-based analysis
        # (distilgpt2 is too small for quality legal analysis)
        logger.info(f"🤖 Generating enhanced legal analysis for {case_type}/{subtype}...")
        return self._generate_enhanced_report(case_type, subtype, situation, fact_text, kg)
    
    def _format_report(self, case_type, subtype, situation, facts, analysis):
        return f"""═══════════════════════════════════════════════════
LEGAL CONSULTATION REPORT
═══════════════════════════════════════════════════

Case Type: {case_type.upper()}
Subtype: {subtype}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

─────────────────────────────────────────────────
CLIENT STATEMENT:
{situation}

─────────────────────────────────────────────────
FACTS EXTRACTED:
{facts if facts else 'Limited information available'}

─────────────────────────────────────────────────
AI LEGAL ANALYSIS:
{analysis}

─────────────────────────────────────────────────
DISCLAIMER:
This is an AI-generated preliminary analysis. Please consult
a qualified legal professional for authoritative advice.
═══════════════════════════════════════════════════"""
    
    def _generate_enhanced_report(self, case_type, subtype, situation, facts, kg: KnowledgeGraph):
        """Generate intelligent analysis based on case facts"""
        
        # Get collected information
        dates = kg.entities.get('dates', [])
        locations = kg.entities.get('locations', [])
        values = kg.entities.get('values', [])
        items = kg.entities.get('items', [])
        
        # Analyze based on case type and facts
        if case_type == 'criminal' and subtype == 'robbery':
            return self._analyze_robbery_case(situation, dates, locations, values, items, facts)
        elif case_type == 'criminal' and subtype == 'theft':
            return self._analyze_theft_case(situation, dates, locations, values, items, facts)
        elif case_type == 'criminal' and subtype == 'murder':
            return self._analyze_murder_case(situation, dates, locations, facts)
        elif case_type == 'criminal' and subtype == 'assault':
            return self._analyze_assault_case(situation, dates, locations, facts)
        elif case_type == 'property':
            return self._analyze_property_case(situation, dates, locations, values, facts)
        elif case_type == 'family':
            return self._analyze_family_case(situation, dates, facts)
        elif case_type == 'contract':
            return self._analyze_contract_case(situation, dates, values, facts)
        else:
            return self._generate_template_report(case_type, subtype, situation, facts)
    
    def _analyze_robbery_case(self, situation, dates, locations, values, items, facts):
        """Detailed robbery case analysis"""
        
        # Build context-aware analysis
        analysis = []
        
        analysis.append("CASE OVERVIEW:")
        analysis.append(f"This is a robbery case under IPC Section 390-392 (Robbery and Dacoity).")
        
        if dates:
            analysis.append(f"The incident occurred on {dates[0]}. Time is crucial - report immediately.")
        
        if locations:
            analysis.append(f"Location: {locations[0]}. Evidence collection at the crime scene is vital.")
        
        if values:
            analysis.append(f"Value involved: {values[0]}. Higher amounts may lead to more severe charges.")
        
        if items:
            analysis.append(f"Items taken: {', '.join(items)}. Document with purchase receipts/serial numbers.")
        
        analysis.append("\nAPPLICABLE LAWS:")
        analysis.append("• IPC Section 390: Definition of Robbery (theft with force/threat)")
        analysis.append("• IPC Section 392: Punishment for robbery (up to 10 years + fine)")
        analysis.append("• If weapon used: IPC Section 397 (robbery with deadly weapon) - up to 14 years")
        analysis.append("• If injury caused: Enhanced punishment under relevant sections")
        
        analysis.append("\nIMMEDIATE ACTIONS REQUIRED:")
        analysis.append("1. File FIR immediately at the nearest police station (jurisdiction based on crime location)")
        analysis.append("2. Provide detailed description of perpetrators if seen")
        analysis.append("3. Request police to preserve CCTV footage from the area")
        analysis.append("4. Get medical examination done if any injuries sustained")
        analysis.append("5. Prepare list of stolen items with proof of ownership")
        analysis.append("6. Identify and contact witnesses immediately")
        
        analysis.append("\nEVIDENCE TO COLLECT:")
        analysis.append("• CCTV footage from crime scene and surrounding areas")
        analysis.append("• Witness statements (get written statements if possible)")
        analysis.append("• Photos of crime scene and any damage")
        analysis.append("• Medical reports if injuries present")
        analysis.append("• Purchase receipts/serial numbers of stolen items")
        analysis.append("• Bank statements showing cash withdrawal (if cash stolen)")
        
        analysis.append("\nLEGAL TIMELINE:")
        analysis.append("• FIR should be filed within 24 hours for best results")
        analysis.append("• CCTV footage may be overwritten after 7-30 days")
        analysis.append("• Witness memory fades - record statements quickly")
        
        analysis.append("\nNEXT STEPS:")
        analysis.append("1. File FIR today if not already done")
        analysis.append("2. Engage a criminal lawyer to follow up on investigation")
        analysis.append("3. Monitor police investigation progress")
        analysis.append("4. Be prepared to identify accused if caught")
        analysis.append("5. Keep all evidence organized for trial")
        
        return f"""═══════════════════════════════════════════════════
LEGAL CONSULTATION REPORT - ROBBERY CASE
═══════════════════════════════════════════════════

Case Type: CRIMINAL - ROBBERY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

─────────────────────────────────────────────────
CLIENT STATEMENT:
{situation}

─────────────────────────────────────────────────
FACTS COLLECTED:
{facts if facts else 'Limited information - answer all questions for detailed analysis'}

─────────────────────────────────────────────────
LEGAL ANALYSIS:

{chr(10).join(analysis)}

─────────────────────────────────────────────────
CRITICAL REMINDERS:
⚠ Time is of the essence - evidence deteriorates quickly
⚠ FIR must be filed immediately
⚠ This is a serious offense - professional legal representation recommended
⚠ Cooperate fully with police investigation

─────────────────────────────────────────────────
DISCLAIMER:
This is a preliminary legal analysis based on the information provided.
For case-specific advice and representation, please consult a qualified
criminal lawyer immediately. Laws and procedures may vary by state.
═══════════════════════════════════════════════════"""
    
    def _analyze_theft_case(self, situation, dates, locations, values, items, facts):
        """Similar detailed analysis for theft"""
        return self._generate_template_report('criminal', 'theft', situation, facts)
    
    def _analyze_murder_case(self, situation, dates, locations, facts):
        """Similar detailed analysis for murder"""
        return self._generate_template_report('criminal', 'murder', situation, facts)
    
    def _analyze_assault_case(self, situation, dates, locations, facts):
        """Similar detailed analysis for assault"""
        return self._generate_template_report('criminal', 'assault', situation, facts)
    
    def _analyze_property_case(self, situation, dates, locations, values, facts):
        """Detailed property dispute analysis"""
        
        analysis = []
        
        analysis.append("CASE OVERVIEW:")
        analysis.append("This is a property dispute case under relevant civil/property laws.")
        
        if locations:
            analysis.append(f"Property location: {locations[0]}. Survey records and mutation documents are crucial.")
        
        if values:
            analysis.append(f"Estimated value: {values[0]}. Property valuation report recommended.")
        
        analysis.append("\nAPPLICABLE LAWS:")
        analysis.append("• Transfer of Property Act, 1882")
        analysis.append("• Indian Succession Act, 1925 (if inheritance dispute)")
        analysis.append("• Specific Relief Act, 1963 (for specific performance)")
        analysis.append("• Registration Act, 1908 (for property registration)")
        analysis.append("• State-specific Land Revenue Acts")
        
        analysis.append("\nIMMEDIATE ACTIONS REQUIRED:")
        analysis.append("1. Collect all property documents (sale deed, title deed, mutation records)")
        analysis.append("2. Get property survey done to verify boundaries")
        analysis.append("3. Check encumbrance certificate from sub-registrar office")
        analysis.append("4. Verify ownership chain - trace back 30 years minimum")
        analysis.append("5. Check for any pending litigation on the property")
        analysis.append("6. Document any illegal occupation or encroachment with photos/videos")
        
        analysis.append("\nDOCUMENTS TO COLLECT:")
        analysis.append("• Sale/Purchase deed")
        analysis.append("• Title deed and ownership chain")
        analysis.append("• Mutation records (7/12 extract, khasra, etc.)")
        analysis.append("• Property tax receipts")
        analysis.append("• Encumbrance certificate")
        analysis.append("• Survey/plot plan")
        analysis.append("• Building plan approval (if applicable)")
        analysis.append("• Will/succession certificate (if inheritance case)")
        
        analysis.append("\nRESOLUTION OPTIONS:")
        analysis.append("1. Negotiation and settlement (fastest and cheapest)")
        analysis.append("2. Mediation through court or private mediator")
        analysis.append("3. Civil suit in appropriate court")
        analysis.append("4. Partition suit (if co-owned property)")
        analysis.append("5. Injunction to prevent alienation/damage")
        
        analysis.append("\nNEXT STEPS:")
        analysis.append("1. Consult a property lawyer with all documents")
        analysis.append("2. Get legal opinion on ownership status")
        analysis.append("3. Attempt amicable settlement first")
        analysis.append("4. If settlement fails, file appropriate civil suit")
        analysis.append("5. Apply for interim injunction if urgent")
        
        return f"""═══════════════════════════════════════════════════
LEGAL CONSULTATION REPORT - PROPERTY DISPUTE
═══════════════════════════════════════════════════

Case Type: PROPERTY DISPUTE
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

─────────────────────────────────────────────────
CLIENT STATEMENT:
{situation}

─────────────────────────────────────────────────
FACTS COLLECTED:
{facts if facts else 'Limited information - answer all questions for detailed analysis'}

─────────────────────────────────────────────────
LEGAL ANALYSIS:

{chr(10).join(analysis)}

─────────────────────────────────────────────────
CRITICAL REMINDERS:
⚠ Property disputes can take years - document everything
⚠ Verify all documents before making any payment
⚠ Get title search done by professional lawyer
⚠ Do not make any physical changes to disputed property

─────────────────────────────────────────────────
DISCLAIMER:
This is a preliminary legal analysis based on the information provided.
Property laws vary by state. Please consult a qualified property lawyer
for case-specific advice and representation.
═══════════════════════════════════════════════════"""
    
    def _analyze_family_case(self, situation, dates, facts):
        """Detailed family law analysis"""
        return self._generate_template_report('family', 'family', situation, facts)
    
    def _analyze_contract_case(self, situation, dates, values, facts):
        """Detailed contract dispute analysis"""
        return self._generate_template_report('contract', 'contract', situation, facts)
    
    def _generate_template_report(self, case_type, subtype, situation, facts):
        # Fallback template when LLM unavailable
        if case_type == 'criminal':
            steps = """1. File FIR immediately at the nearest police station
2. Collect and preserve all evidence (photos, documents, CCTV)
3. Get witness statements recorded
4. Obtain medical examination report if injuries present
5. Consult a criminal lawyer for detailed legal strategy"""
        elif case_type == 'family':
            steps = """1. Attempt mediation/counseling first if applicable
2. Gather all relevant documents (marriage certificate, financial records)
3. Document any incidents with dates and evidence
4. Consult a family law specialist
5. Consider filing petition in family court if mediation fails"""
        else:
            steps = """1. Gather all relevant documents and evidence
2. Document timeline of events
3. Identify witnesses if any
4. Consult appropriate legal specialist
5. File case in appropriate court if required"""
        
        return f"""═══════════════════════════════════════════════════
LEGAL CONSULTATION REPORT
═══════════════════════════════════════════════════

Case Type: {case_type.upper()}
Subtype: {subtype}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

─────────────────────────────────────────────────
CLIENT STATEMENT:
{situation}

─────────────────────────────────────────────────
FACTS EXTRACTED:
{facts if facts else 'Limited information available'}

─────────────────────────────────────────────────
LEGAL ANALYSIS:

Based on the information provided, this appears to be a {case_type} 
matter requiring immediate attention.

RECOMMENDED LEGAL STEPS:
{steps}

IMPORTANT NOTES:
• Act promptly - legal timelines are strict
• Document everything thoroughly
• Preserve all evidence
• Consult a qualified lawyer immediately for case-specific advice

─────────────────────────────────────────────────
DISCLAIMER:
This is a preliminary analysis based on limited information.
Please consult a qualified legal professional for authoritative advice.
═══════════════════════════════════════════════════"""

# -------------------------
# Agentic Legal System with AI Models
# -------------------------
class AgenticLegalSystem:
    def __init__(self):
        self.classifier = SmartClassifierAgent()
        self.extractor = EntityExtractionAgent()
        self.qgen = AdaptiveQuestionGenerator()
        self.analyzer = AIAnalyzer()
        self.sessions = {}
        self.lock = Lock()

    def start_session(self, query: str, max_turns: int = 7) -> Dict:
        session_id = str(uuid.uuid4())
        case_type, conf = self.classifier.initial_classify(query)
        
        logger.info(f"New session {session_id}: {case_type} (confidence: {conf:.2f})")
        
        kg = KnowledgeGraph()
        kg.set_context('situation', query)
        kg.set_context('case_type', case_type)
        kg.set_context('criminal_subtype', self.qgen.detect_crime_subtype(query))

        # Extract initial entities
        extracted = self.extractor.extract(query)
        for k, vals in extracted.items():
            for v in vals:
                kg.add_entity(k, v)

        # Store session with asked questions list
        with self.lock:
            self.sessions[session_id] = {
                'query_history': [query],
                'kg': kg,
                'case_type': case_type,
                'turns_done': 0,
                'max_turns': max_turns,
                'asked_questions': [],  # ✅ TRACK ASKED QUESTIONS
                'finished': False
            }

        # Generate first question
        q = self.qgen.generate_next(case_type, kg, [])
        if q and max_turns > 0:
            with self.lock:
                self.sessions[session_id]['asked_questions'].append(q)  # ✅ MARK AS ASKED
            
            # Generate partial report with AI
            report = self.analyzer.analyze(case_type, kg)
            logger.info(f"First question: {q}")
            return {
                'session_id': session_id,
                'next_action': 'ask',
                'question': q,
                'partial_report': report
            }

        with self.lock:
            self.sessions[session_id]['finished'] = True
        report = self.analyzer.analyze(case_type, kg)
        return {
            'session_id': session_id,
            'next_action': 'final',
            'question': None,
            'partial_report': report
        }

    def answer_session(self, session_id: str, answer: str) -> Dict:
        with self.lock:
            state = self.sessions.get(session_id)
        
        if not state:
            raise KeyError("session not found")

        logger.info(f"Session {session_id} turn {state['turns_done']}: {answer[:50]}...")

        # Add answer to history
        state['query_history'].append(answer)
        state['turns_done'] += 1

        # Extract entities from answer
        extracted = self.extractor.extract(answer)
        for k, vals in extracted.items():
            for v in vals:
                state['kg'].add_entity(k, v)

        # Update subtype based on accumulated facts
        state['kg'].set_context('criminal_subtype', self.qgen.detect_crime_subtype(
            state['kg'].context.get('situation', '') + " " +
            " ".join([x for vals in state['kg'].entities.values() for x in vals])
        ))

        # Generate AI analysis with updated facts
        report = self.analyzer.analyze(state['case_type'], state['kg'])

        # Check if we should ask more questions
        if state['turns_done'] < state['max_turns']:
            # ✅ PASS THE LIST OF ASKED QUESTIONS
            logger.info(f"Asked questions so far: {state['asked_questions']}")
            q = self.qgen.generate_next(state['case_type'], state['kg'], state['asked_questions'])
            if q:
                with self.lock:
                    state['asked_questions'].append(q)  # ✅ MARK AS ASKED
                    self.sessions[session_id] = state
                logger.info(f"Next question: {q}")
                return {
                    'next_action': 'ask',
                    'question': q,
                    'partial_report': report
                }

        # No more questions - finalize
        logger.info(f"Session {session_id} complete")
        with self.lock:
            state['finished'] = True
            self.sessions[session_id] = state

        return {
            'next_action': 'final',
            'report': report,
            'structured': {}
        }

# Create system instance
system = AgenticLegalSystem()
logger.info(f"Agentic Legal System ready | LLM: {llm_name or 'Not loaded'} | Embeddings: {'Loaded' if embedder else 'Not loaded'}")

# -------------------------
# FastAPI App
# -------------------------
app = FastAPI(title="ChatLaw Legal Consultation API with AI Models")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "ChatLaw API is running with AI models",
        "llm_loaded": llm_model is not None,
        "llm_name": llm_name,
        "embeddings_loaded": embedder is not None
    }

@app.post("/consult/start", response_model=ConsultationStartResponse)
def consult_start(req: ConsultationStartRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")
    
    out = system.start_session(req.query.strip(), max_turns=req.max_turns or 7)
    return ConsultationStartResponse(
        session_id=out['session_id'],
        next_action=out['next_action'],
        question=out.get('question'),
        partial_report=out.get('partial_report')
    )

@app.post("/consult/answer")
def consult_answer(req: ConsultationAnswerRequest):
    try:
        out = system.answer_session(req.session_id, req.answer)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    
    if out['next_action'] == 'ask':
        return {
            "next_action": "ask",
            "question": out['question'],
            "partial_report": out.get('partial_report')
        }
    else:
        return ConsultationFinalResponse(
            session_id=req.session_id,
            report=out['report'],
            structured=out.get('structured', {}),
            timestamp=datetime.now().isoformat()
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
