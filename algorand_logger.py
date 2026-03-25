import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from algosdk import account, mnemonic
from algosdk.transaction import PaymentTxn
from algosdk.v2client import algod


class AlgorandLogger:
    def __init__(
        self,
        simulate: bool = True,
        algod_address: str = "",
        algod_token: str = "",
        sender_mnemonic: str = "",
    ) -> None:
        # Public Algod nodes (e.g. Algonode) use an empty API token — do not require non-empty token.
        has_endpoint = bool(str(algod_address or "").strip())
        has_mnemonic = bool(str(sender_mnemonic or "").strip())
        can_use_real_chain = has_endpoint and has_mnemonic
        self.simulate = simulate or not can_use_real_chain
        self.client = None
        self.private_key = ""
        self.address = ""
        self.connected = False
        self.status_message = (
            "Simulation mode: alerts saved locally (SIM-ALGO-...). "
            "For real testnet: set SIMULATE_ALGORAND=false, ALGOD_ADDRESS, ALGORAND_MNEMONIC."
        )
        self.local_log = Path("algorand_alert_log.jsonl")

        if not self.simulate:
            try:
                self.client = algod.AlgodClient(algod_token, algod_address)
                self.private_key = mnemonic.to_private_key(sender_mnemonic.strip())
                self.address = account.address_from_private_key(self.private_key)
                self.connected = True
                self.status_message = f"Connected to Algorand ({self.address[:8]}...)"
            except Exception:
                self.simulate = True
                self.connected = False
                self.status_message = (
                    "Blockchain not connected: invalid mnemonic or unreachable node. "
                    "Using simulation + local log."
                )

    def log_alert(self, alert_payload: Dict[str, str]) -> str:
        if self.simulate:
            tx_id = f"SIM-ALGO-{random.randint(100000, 999999)}"
            self._write_local_record(tx_id, alert_payload, simulated=True)
            return tx_id

        try:
            params = self.client.suggested_params()
            note = json.dumps(alert_payload).encode("utf-8")[:900]
            # 0 amount self-payment transaction with note for transparency.
            txn = PaymentTxn(
                sender=self.address,
                sp=params,
                receiver=self.address,
                amt=0,
                note=note,
            )
            signed_txn = txn.sign(self.private_key)
            tx_id = self.client.send_transaction(signed_txn)
            self._write_local_record(tx_id, alert_payload, simulated=False)
            return tx_id
        except Exception:
            # Fallback to simulation if network/account not ready
            tx_id = f"SIM-ALGO-{random.randint(100000, 999999)}"
            self._write_local_record(tx_id, alert_payload, simulated=True)
            return tx_id

    def _write_local_record(self, tx_id: str, payload: Dict[str, str], simulated: bool) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tx_id": tx_id,
            "simulated": simulated,
            "payload": payload,
        }
        with self.local_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
