import os
from typing import Dict, List

import requests


class LLMReasoner:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def summarize(self, decision: Dict, observation: Dict, portfolio: Dict, alert_history: List[Dict]) -> str:
        if not self.api_key:
            return self._fallback_summary(decision, portfolio)

        prompt = (
            "You are a DeFi risk assistant. Provide a short, actionable summary with:\n"
            "1) risk diagnosis,\n2) what user should do now,\n3) next 1-2 checks.\n"
            "Keep it under 90 words.\n\n"
            f"Decision: {decision}\n"
            f"Portfolio: {portfolio}\n"
            f"Observation: tx_frequency={observation.get('tx_frequency')}, prices={observation.get('prices')}\n"
            f"Recent Alerts Count: {len(alert_history)}"
        )

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You explain DeFi risks clearly."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            return content or self._fallback_summary(decision, portfolio)
        except Exception:
            return self._fallback_summary(decision, portfolio)

    def _fallback_summary(self, decision: Dict, portfolio: Dict) -> str:
        level = decision["risk_level"]
        score = decision["risk_score"]
        value = portfolio.get("total_value_usd", 0.0)
        if level == "HIGH":
            action = "Reduce exposure and watch wallet activity closely."
        elif level == "MEDIUM":
            action = "Hold position and monitor for another cycle."
        else:
            action = "Continue monitoring; market risk is currently contained."
        return f"LLM fallback: Risk is {level} (score {score}). Portfolio value is ${value:,.2f}. {action}"
