"""
Workflow Automation Engine.
Orchestrates document processing, risk assessment, and approval recommendations.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    AI-driven workflow automation engine.
    Analyzes documents and generates approval recommendations.
    """

    RISK_THRESHOLDS = {
        "auto_approve": 20,
        "manager_review": 50,
        "escalate": 70,
    }

    def generate_recommendation(
        self,
        risk_score: float,
        risk_factors: list,
        doc_type: str,
        entities: dict,
        missing_fields: list,
    ) -> dict:
        """
        Generate an AI approval recommendation based on risk analysis.
        Returns recommendation, status, reasoning, and action items.
        """
        actions = []
        
        # Determine recommendation
        if missing_fields and len(missing_fields) > 2:
            recommendation = "manual_review"
            status = "on_hold"
            reason = f"Document is missing {len(missing_fields)} required fields: {', '.join(missing_fields[:3])}"
        elif risk_score <= self.RISK_THRESHOLDS["auto_approve"]:
            recommendation = "approve"
            status = "in_review"
            reason = "Low risk score. Document appears complete and compliant."
        elif risk_score <= self.RISK_THRESHOLDS["manager_review"]:
            recommendation = "manual_review"
            status = "in_review"
            reason = f"Moderate risk ({risk_score:.0f}/100). Manager review recommended."
        elif risk_score <= self.RISK_THRESHOLDS["escalate"]:
            recommendation = "escalate"
            status = "escalated"
            reason = f"High risk ({risk_score:.0f}/100). Escalation to senior management required."
        else:
            recommendation = "reject"
            status = "in_review"
            reason = f"Critical risk ({risk_score:.0f}/100). Multiple compliance issues detected."
        
        # Generate specific action items
        for factor in risk_factors:
            actions.append({
                "priority": factor.get("severity", "medium"),
                "action": factor.get("recommendation", "Review required"),
                "issue": factor.get("issue", ""),
            })
        
        # Doc type specific actions
        if doc_type == "invoice":
            if entities.get("total_amount"):
                try:
                    amount = float(str(entities["total_amount"]).replace(",", ""))
                    if amount > 100000:
                        actions.append({
                            "priority": "high",
                            "action": "CFO approval required for amounts exceeding $100,000",
                            "issue": f"Invoice amount: ${entities['total_amount']}",
                        })
                except (ValueError, TypeError):
                    pass
        
        return {
            "recommendation": recommendation,
            "workflow_status": status,
            "reason": reason,
            "action_items": actions,
            "risk_score": risk_score,
            "confidence": self._calculate_confidence(risk_score, len(risk_factors)),
            "auto_processable": risk_score <= self.RISK_THRESHOLDS["auto_approve"],
        }

    def detect_missing_fields(self, doc_type: str, entities: dict) -> list[str]:
        """Detect required fields that are missing from the document."""
        required_fields = {
            "invoice": ["invoice_number", "vendor_name", "total_amount", "payment_terms"],
            "contract": ["parties", "contract_term", "has_termination_clause"],
            "purchase_order": ["po_number", "vendor_name", "total_amount"],
            "report": ["dates", "company_names"],
            "policy": [],
        }
        
        missing = []
        fields = required_fields.get(doc_type, [])
        
        for field in fields:
            value = entities.get(field)
            if not value or value == [] or value is False:
                missing.append(field.replace("_", " ").title())
        
        return missing

    def _calculate_confidence(self, risk_score: float, num_issues: int) -> float:
        """Calculate confidence in the AI recommendation."""
        base_confidence = 0.85
        
        if num_issues == 0:
            confidence = base_confidence + 0.10
        elif num_issues > 5:
            confidence = base_confidence - 0.15
        else:
            confidence = base_confidence - (num_issues * 0.03)
        
        if 20 <= risk_score <= 80:
            confidence -= 0.05
        
        return round(max(0.50, min(0.99, confidence)), 2)

    def get_workflow_stats(self, workflows: list) -> dict:
        """Aggregate workflow statistics for analytics."""
        stats = {
            "total": len(workflows),
            "pending": 0,
            "in_review": 0,
            "approved": 0,
            "rejected": 0,
            "escalated": 0,
            "on_hold": 0,
            "avg_risk_score": 0.0,
            "high_risk_count": 0,
        }
        
        risk_scores = []
        for wf in workflows:
            status = getattr(wf, "status", "pending")
            stats[status] = stats.get(status, 0) + 1
            
            risk = getattr(wf, "risk_score", None)
            if risk is not None:
                risk_scores.append(risk)
                if risk >= 70:
                    stats["high_risk_count"] += 1
        
        if risk_scores:
            stats["avg_risk_score"] = round(sum(risk_scores) / len(risk_scores), 1)
        
        return stats


# Singleton
workflow_engine = WorkflowEngine()
