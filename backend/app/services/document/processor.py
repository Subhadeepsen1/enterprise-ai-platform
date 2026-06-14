"""
Intelligent Document Processing Service.
Handles text extraction, cleaning, classification, and entity extraction.
"""

import logging
import re
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Core document processing pipeline."""

    DOCUMENT_KEYWORDS = {
        "invoice": ["invoice", "bill", "billing", "payment due", "invoice number", "inv#", "amount due"],
        "contract": ["agreement", "contract", "terms and conditions", "party", "whereas", "hereinafter", "obligations"],
        "report": ["report", "analysis", "findings", "summary", "quarterly", "annual", "performance"],
        "policy": ["policy", "procedure", "guideline", "compliance", "regulation", "shall", "must not"],
        "purchase_order": ["purchase order", "po number", "order number", "delivery", "ship to", "vendor"],
    }

    def extract_text_from_file(self, file_path: str, mime_type: str) -> str:
        """Extract raw text from uploaded file."""
        path = Path(file_path)
        
        try:
            if mime_type == "text/plain" or path.suffix.lower() == ".txt":
                return self._extract_from_txt(path)
            elif mime_type == "application/pdf" or path.suffix.lower() == ".pdf":
                return self._extract_from_pdf(path)
            elif mime_type in [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
            ] or path.suffix.lower() in [".docx", ".doc"]:
                return self._extract_from_docx(path)
            else:
                raise ValueError(f"Unsupported file type: {mime_type}")
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            raise

    def _extract_from_txt(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")

    def _extract_from_pdf(self, path: Path) -> str:
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n\n".join(text_parts)
        except ImportError:
            # Fallback to PyPDF2
            import PyPDF2
            text_parts = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n\n".join(text_parts)

    def _extract_from_docx(self, path: Path) -> str:
        from docx import Document
        doc = Document(path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)

    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove non-printable characters
        text = re.sub(r"[^\x20-\x7E\n\t]", "", text)
        # Normalize line breaks
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip leading/trailing whitespace
        return text.strip()

    def classify_document(self, text: str) -> tuple[str, float]:
        """
        Classify document type based on keyword analysis.
        Returns (document_type, confidence_score).
        """
        text_lower = text.lower()
        scores = {}
        
        for doc_type, keywords in self.DOCUMENT_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in text_lower)
            scores[doc_type] = hits / len(keywords)
        
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        if best_score < 0.1:
            return "unknown", 0.3
        
        confidence = min(0.5 + best_score * 2, 0.99)
        return best_type, round(confidence, 2)

    def extract_entities(self, text: str, doc_type: str) -> dict:
        """
        Extract structured entities using pattern matching + heuristics.
        In production, this would call an LLM for higher accuracy.
        """
        entities = {}
        
        # Universal extractors
        entities["dates"] = self._extract_dates(text)
        entities["amounts"] = self._extract_amounts(text)
        entities["emails"] = self._extract_emails(text)
        entities["phone_numbers"] = self._extract_phones(text)
        
        # Type-specific extractors
        if doc_type == "invoice":
            entities.update(self._extract_invoice_entities(text))
        elif doc_type == "contract":
            entities.update(self._extract_contract_entities(text))
        elif doc_type == "purchase_order":
            entities.update(self._extract_po_entities(text))
        
        # General entities
        entities["company_names"] = self._extract_company_names(text)
        entities["action_items"] = self._extract_action_items(text)
        
        return entities

    def _extract_dates(self, text: str) -> list[str]:
        patterns = [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
            r"\b\d{4}-\d{2}-\d{2}\b",
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(dates))[:10]

    def _extract_amounts(self, text: str) -> list[str]:
        patterns = [
            r"\$[\d,]+(?:\.\d{2})?",
            r"USD\s*[\d,]+(?:\.\d{2})?",
            r"EUR\s*[\d,]+(?:\.\d{2})?",
            r"[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|INR)",
        ]
        amounts = []
        for pattern in patterns:
            amounts.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(amounts))[:10]

    def _extract_emails(self, text: str) -> list[str]:
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        return list(set(re.findall(pattern, text)))[:5]

    def _extract_phones(self, text: str) -> list[str]:
        pattern = r"(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        return list(set(re.findall(pattern, text)))[:5]

    def _extract_company_names(self, text: str) -> list[str]:
        pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Ltd|Corp|GmbH|AG|SE|Co|Limited|Corporation|Group)\.?))\b"
        names = re.findall(pattern, text)
        return list(set(names))[:10]

    def _extract_invoice_entities(self, text: str) -> dict:
        entities = {}
        
        inv_match = re.search(r"(?:Invoice|Inv)[\s#:.-]*([A-Z0-9-]+)", text, re.IGNORECASE)
        entities["invoice_number"] = inv_match.group(1) if inv_match else None
        
        due_match = re.search(r"(?:Due|Payment Due|Net)[\s:]*(\d+)\s*(?:days?)?", text, re.IGNORECASE)
        entities["payment_terms"] = f"Net {due_match.group(1)}" if due_match else None
        
        vendor_match = re.search(r"(?:From|Vendor|Supplier|Bill From)[\s:]+([^\n]+)", text, re.IGNORECASE)
        entities["vendor_name"] = vendor_match.group(1).strip() if vendor_match else None
        
        total_match = re.search(r"(?:Total|Amount Due|Grand Total)[\s:$]*([0-9,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        entities["total_amount"] = total_match.group(1) if total_match else None
        
        return entities

    def _extract_contract_entities(self, text: str) -> dict:
        entities = {}
        
        party_pattern = r"(?:between|party of the first part|party of the second part)[\s:]+([^\n,]+)"
        parties = re.findall(party_pattern, text, re.IGNORECASE)
        entities["parties"] = [p.strip() for p in parties[:4]]
        
        term_match = re.search(r"(?:term|duration|period)[\s:]*(?:of\s+)?(\d+)\s*(years?|months?|days?)", text, re.IGNORECASE)
        entities["contract_term"] = f"{term_match.group(1)} {term_match.group(2)}" if term_match else None
        
        value_match = re.search(r"(?:contract value|total value|consideration)[\s:$]*([0-9,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        entities["contract_value"] = value_match.group(1) if value_match else None
        
        entities["has_termination_clause"] = bool(re.search(r"termination|terminate", text, re.IGNORECASE))
        entities["has_penalty_clause"] = bool(re.search(r"penalty|liquidated damage", text, re.IGNORECASE))
        
        return entities

    def _extract_po_entities(self, text: str) -> dict:
        entities = {}
        
        po_match = re.search(r"(?:PO|Purchase Order)[\s#:.-]*([A-Z0-9-]+)", text, re.IGNORECASE)
        entities["po_number"] = po_match.group(1) if po_match else None
        
        delivery_match = re.search(r"(?:Deliver|Ship)[\s\w]*(?:by|on|before)[\s:]*([^\n]+)", text, re.IGNORECASE)
        entities["delivery_date"] = delivery_match.group(1).strip() if delivery_match else None
        
        return entities

    def _extract_action_items(self, text: str) -> list[str]:
        patterns = [
            r"(?:must|should|shall|required to|needs to)\s+([^.!?]+[.!?])",
            r"(?:action required|please|kindly)\s*:?\s*([^.!?\n]+)",
        ]
        items = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            items.extend(m.strip() for m in matches[:3])
        return items[:5]

    def analyze_risk(self, text: str, entities: dict, doc_type: str) -> dict:
        """
        Analyze document for risks and compliance issues.
        Returns risk score (0-100) and risk factors.
        """
        risk_factors = []
        risk_score = 0

        # Missing field checks
        if doc_type == "invoice":
            if not entities.get("invoice_number"):
                risk_factors.append({"severity": "high", "issue": "Missing invoice number", "recommendation": "Request invoice number from vendor"})
                risk_score += 25
            if not entities.get("payment_terms"):
                risk_factors.append({"severity": "medium", "issue": "Payment terms not specified", "recommendation": "Clarify payment terms before approval"})
                risk_score += 15
            if not entities.get("vendor_name"):
                risk_factors.append({"severity": "high", "issue": "Vendor name not identified", "recommendation": "Verify vendor identity before processing"})
                risk_score += 20

        elif doc_type == "contract":
            if not entities.get("has_termination_clause"):
                risk_factors.append({"severity": "high", "issue": "Termination clause missing", "recommendation": "Add termination conditions before approval"})
                risk_score += 30
            if not entities.get("contract_term"):
                risk_factors.append({"severity": "medium", "issue": "Contract duration not specified", "recommendation": "Define explicit contract period"})
                risk_score += 15
            if not entities.get("parties"):
                risk_factors.append({"severity": "high", "issue": "Contracting parties not clearly identified", "recommendation": "Clearly identify all parties"})
                risk_score += 25

        # Universal risk checks
        risky_words = ["immediately", "urgent", "no liability", "waive", "as-is", "no warranty"]
        for word in risky_words:
            if word.lower() in text.lower():
                risk_factors.append({"severity": "medium", "issue": f"Risky clause detected: '{word}'", "recommendation": "Legal review recommended"})
                risk_score += 10

        # Unusually high amounts
        amounts = entities.get("amounts", [])
        for amount_str in amounts:
            try:
                clean = re.sub(r"[,$USD EUR]", "", amount_str).strip()
                if float(clean.replace(",", "")) > 500000:
                    risk_factors.append({"severity": "high", "issue": f"High-value transaction: {amount_str}", "recommendation": "Requires CFO approval"})
                    risk_score += 20
                    break
            except ValueError:
                pass

        risk_score = min(risk_score, 100)
        
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 40:
            risk_level = "high"
        elif risk_score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
        }

    def generate_summary(self, text: str, doc_type: str, entities: dict) -> str:
        """Generate a brief human-readable summary."""
        summary_parts = [f"Document Type: {doc_type.replace('_', ' ').title()}"]
        
        if entities.get("dates"):
            summary_parts.append(f"Key Dates: {', '.join(entities['dates'][:2])}")
        if entities.get("amounts"):
            summary_parts.append(f"Amounts: {', '.join(entities['amounts'][:2])}")
        if entities.get("company_names"):
            summary_parts.append(f"Companies: {', '.join(entities['company_names'][:2])}")
        if doc_type == "invoice":
            if entities.get("invoice_number"):
                summary_parts.append(f"Invoice #: {entities['invoice_number']}")
            if entities.get("vendor_name"):
                summary_parts.append(f"Vendor: {entities['vendor_name']}")
        
        word_count = len(text.split())
        summary_parts.append(f"Document Length: {word_count} words")
        
        return " | ".join(summary_parts)


# Singleton instance
document_processor = DocumentProcessor()
