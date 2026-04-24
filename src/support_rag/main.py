from __future__ import annotations

import argparse
from pathlib import Path

from .config import get_config
from .ingest import ingest_pdf
from .workflow import run_support_graph


def ingest_command(pdf: str) -> None:
    config = get_config()
    chunk_count = ingest_pdf(Path(pdf), config)
    print(f"Ingested {chunk_count} chunks from {pdf}")


def chat_command() -> None:
    config = get_config()
    print("Customer Support Assistant")
    print("Type 'exit' to stop.\n")

    while True:
        query = input("Customer> ").strip()
        if query.lower() in {"exit", "quit"}:
            break
        if not query:
            continue

        state = run_support_graph(query, config)
        print(f"\nIntent: {state['intent']}")
        print(f"Confidence: {state['confidence']}")
        print(f"Route: {state['route']}\n")
        if state["route"] == "escalate":
            print(state["human_response"])
        else:
            print(state["answer"])
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG-based customer support assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a PDF knowledge base")
    ingest_parser.add_argument("--pdf", required=True, help="Path to the PDF file")

    subparsers.add_parser("chat", help="Start the CLI support assistant")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "ingest":
        ingest_command(args.pdf)
    elif args.command == "chat":
        chat_command()


if __name__ == "__main__":
    main()
