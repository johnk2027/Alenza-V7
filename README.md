# Alenza-v7 Realtor OS

An institutional-grade workstation for Canadian real estate brokerages. Built for compliance, accuracy, and agent productivity.

## Features
- **Closing Cost Engine:** Stacked Toronto MLTT/Ontario LTT and corrected BC PTT phase-out math.
- **Compliance AI Copilot:** Regex-driven risk scanning for RECO/regulatory standards.
- **Privacy-First Audit:** PII redaction (scrapes postal codes/emails/SIN from logs) with SQLite persistence.
- **Live Market Data:** Real-time integration with Bank of Canada Valet API.

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Run locally: `streamlit run app.py`
3. Default Access Key: `alenza2026`

## Security Warning
The `alenza_broker_secure.db` contains hashed interaction logs. Ensure your deployment environment has restricted file permissions.
