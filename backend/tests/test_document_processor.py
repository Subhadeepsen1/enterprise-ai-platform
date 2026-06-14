"""Unit tests for Document Processing Service."""

import pytest
from app.services.document.processor import DocumentProcessor


@pytest.fixture
def processor():
    return DocumentProcessor()


class TestDocumentClassification:
    def test_classify_invoice(self, processor):
        text = "Invoice #INV-2024-001 from Acme Corp. Payment due within 30 days. Amount: $5,000.00"
        doc_type, confidence = processor.classify_document(text)
        assert doc_type == "invoice"
        assert confidence > 0.5

    def test_classify_contract(self, processor):
        text = "This Agreement is entered into between Party A and Party B. Whereas the parties agree to the terms and conditions hereinafter."
        doc_type, confidence = processor.classify_document(text)
        assert doc_type == "contract"
        assert confidence > 0.5

    def test_classify_purchase_order(self, processor):
        text = "Purchase Order PO-2024-999. Ship to: 123 Main St. Vendor delivery required by end of month."
        doc_type, confidence = processor.classify_document(text)
        assert doc_type == "purchase_order"

    def test_classify_unknown(self, processor):
        text = "Lorem ipsum dolor sit amet consectetur adipiscing elit."
        doc_type, confidence = processor.classify_document(text)
        assert doc_type == "unknown"


class TestEntityExtraction:
    def test_extract_dates(self, processor):
        text = "Invoice dated 2024-01-15. Payment due by January 31, 2024."
        entities = processor.extract_entities(text, "invoice")
        assert len(entities["dates"]) > 0

    def test_extract_amounts(self, processor):
        text = "Total Amount Due: $12,500.00. Discount: $500.00"
        entities = processor.extract_entities(text, "invoice")
        assert len(entities["amounts"]) > 0
        assert any("12,500" in amt for amt in entities["amounts"])

    def test_extract_invoice_number(self, processor):
        text = "Invoice #INV-2024-0042 from TechCorp Solutions."
        entities = processor.extract_entities(text, "invoice")
        assert entities.get("invoice_number") is not None

    def test_extract_emails(self, processor):
        text = "Contact us at billing@enterprise.com or support@company.org"
        entities = processor.extract_entities(text, "invoice")
        assert len(entities["emails"]) >= 1


class TestRiskAnalysis:
    def test_low_risk_complete_invoice(self, processor):
        text = "Invoice #INV-001 from Acme Inc. Total: $5,000. Payment terms: Net 30."
        entities = {
            "invoice_number": "INV-001",
            "vendor_name": "Acme Inc",
            "total_amount": "5000",
            "payment_terms": "Net 30",
            "amounts": ["$5,000.00"],
        }
        risk = processor.analyze_risk(text, entities, "invoice")
        assert risk["risk_level"] in ["low", "medium"]
        assert risk["risk_score"] < 50

    def test_high_risk_missing_fields(self, processor):
        text = "Invoice amount $750,000. Immediately payable. No liability assumed."
        entities = {
            "invoice_number": None,
            "vendor_name": None,
            "amounts": ["$750,000"],
        }
        risk = processor.analyze_risk(text, entities, "invoice")
        assert risk["risk_score"] > 40
        assert len(risk["risk_factors"]) > 0

    def test_contract_missing_termination_clause(self, processor):
        text = "Contract between Party A and Party B. No termination specified."
        entities = {
            "parties": ["Party A", "Party B"],
            "contract_term": "2 years",
            "has_termination_clause": False,
            "has_penalty_clause": False,
        }
        risk = processor.analyze_risk(text, entities, "contract")
        assert any("termination" in str(f.get("issue", "")).lower() for f in risk["risk_factors"])


class TestTextCleaning:
    def test_clean_excessive_whitespace(self, processor):
        text = "Hello   World\n\n\n\nFoo"
        cleaned = processor.clean_text(text)
        assert "   " not in cleaned
        assert "\n\n\n" not in cleaned

    def test_clean_preserves_content(self, processor):
        text = "Invoice $5,000 due on 2024-01-15"
        cleaned = processor.clean_text(text)
        assert "5,000" in cleaned
        assert "2024-01-15" in cleaned


class TestWorkflowEngine:
    def test_low_risk_recommendation(self):
        from app.services.workflow.engine import WorkflowEngine
        engine = WorkflowEngine()
        result = engine.generate_recommendation(
            risk_score=10,
            risk_factors=[],
            doc_type="invoice",
            entities={"invoice_number": "INV-001", "vendor_name": "Acme"},
            missing_fields=[],
        )
        assert result["recommendation"] == "approve"

    def test_high_risk_escalation(self):
        from app.services.workflow.engine import WorkflowEngine
        engine = WorkflowEngine()
        result = engine.generate_recommendation(
            risk_score=75,
            risk_factors=[{"severity": "high", "issue": "Missing clause", "recommendation": "Add clause"}],
            doc_type="contract",
            entities={},
            missing_fields=["Termination Clause", "Contract Term"],
        )
        assert result["recommendation"] in ["escalate", "reject"]
