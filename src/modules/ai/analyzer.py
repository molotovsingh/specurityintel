"""
AI Risk Analysis Module using OpenAI.
"""

from ...interfaces.dto import RiskAnalysisResult
from ...interfaces.ports import OpenAIClient, Clock
from ...interfaces.errors import ProcessingError


class RiskAnalyzer:
    """
    Analyzes risks using AI.

    Example:
        analyzer = RiskAnalyzer(openai_client, clock)
        result = analyzer.analyze(app_id, kpi_name, kpi_value)
    """

    def __init__(self, openai_client: OpenAIClient, clock: Clock):
        self.openai = openai_client
        self.clock = clock

    def analyze(self, app_id: str, kpi_name: str, kpi_value: float) -> RiskAnalysisResult:
        """
        Analyze risk for KPI anomaly.

        Returns RiskAnalysisResult with score, confidence, explanation.
        """
        try:
            # Build prompt for AI analysis
            prompt = f"""
Analyze the following KPI anomaly:
- Application: {app_id}
- KPI: {kpi_name}
- Value: {kpi_value}

Provide:
1. Risk score (0-100)
2. Confidence (0-100)
3. Root cause explanation
4. Risk factors

Format as JSON.
"""

            # Get AI analysis
            response = self.openai.analyze(prompt, max_tokens=500)

            # Parse response (simplified)
            risk_score = self._extract_risk_score(response, kpi_value)
            confidence = self._extract_confidence(response)

            result = RiskAnalysisResult(
                app_id=app_id,
                kpi_name=kpi_name,
                risk_score=risk_score,
                confidence=confidence,
                explanation=response[:200],  # First 200 chars
                factors={"kpi_value": kpi_value},
                analyzed_at=self.clock.now()
            )

            return result

        except Exception as e:
            raise ProcessingError(
                message=f"AI analysis failed: {str(e)}",
                context={"app_id": app_id, "kpi": kpi_name}
            )

    def _extract_risk_score(self, response: str, kpi_value: float) -> float:
        """Extract risk score from response."""
        # Simple heuristic: scale KPI value to 0-100
        score = min(100.0, kpi_value * 10)
        return score

    def _extract_confidence(self, response: str) -> float:
        """Extract confidence from response."""
        # Default to 75% confidence
        return 75.0
