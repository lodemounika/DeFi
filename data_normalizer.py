"""
Data Normalizer — single schema for dashboard + risk engine.
"""
from typing import Dict, List

from event_listener import extract_events_from_token_transfers, flag_liquidation_risk_proxy, summarize_events
from transaction_parser import parse_transaction_batch, summarize_parsed


def normalize_processing_output(
    txlist: List[dict],
    tokentx: List[dict],
) -> dict:
    """
    Converts raw explorer payloads into a versioned, structured bundle.
    """
    parsed_txs = parse_transaction_batch(txlist)
    events = extract_events_from_token_transfers(tokentx)
    tx_summary = summarize_parsed(parsed_txs)
    ev_summary = summarize_events(events)
    flags = flag_liquidation_risk_proxy(events)

    return {
        "schema_version": "1.0",
        "transactions_structured": parsed_txs,
        "token_events": events,
        "summary": {
            "transaction_actions": tx_summary,
            "event_types": ev_summary,
            "counts": {
                "parsed_tx": len(parsed_txs),
                "token_events": len(events),
            },
        },
        "risk_hints": flags,
    }


def empty_processing_bundle() -> dict:
    return {
        "schema_version": "1.0",
        "transactions_structured": [],
        "token_events": [],
        "summary": {"transaction_actions": {}, "event_types": {}, "counts": {"parsed_tx": 0, "token_events": 0}},
        "risk_hints": {"high_dex_activity": False, "lending_touch": False},
    }
