#!/usr/bin/env python3
"""Verify RNS result XML signatures embedded inside a results JSON file.

Python 3 port of results-verification.py.

Dependencies:
    pip install lxml xmlsec cryptography

Usage:
    python results_verification_py3.py -j results.json -c certificate.pem
    python results_verification_py3.py -j results.json -c cert1.pem -c cert2.pem
    python results_verification_py3.py -j results.json -c keys/

The -c/--cert argument accepts either a PEM file or a directory containing .pem files.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any

import xmlsec
from lxml import etree
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def create_pubkey_from_exp_mod(exponent_b64: str, modulus_b64: str) -> bytes:
    """Create an RSA public key PEM from base64 XMLDSig Exponent/Modulus values."""
    exponent = int.from_bytes(base64.b64decode(exponent_b64), byteorder="big")
    modulus = int.from_bytes(base64.b64decode(modulus_b64), byteorder="big")

    public_numbers = rsa.RSAPublicNumbers(exponent, modulus)
    public_key = public_numbers.public_key()

    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def parse_xml(xml_file: str | Path) -> etree._Element:
    return etree.parse(str(xml_file)).getroot()


def _require_node(node: etree._Element | None, name: str) -> etree._Element:
    if node is None:
        raise ValueError(f"Unable to find required XML node: {name}")
    return node


def xml_verify_self(resultxml: etree._Element) -> bool:
    """Verify the XML signature using the RSA key embedded in KeyInfo."""
    signature_node = _require_node(
        xmlsec.tree.find_node(resultxml, xmlsec.Node.SIGNATURE),
        "Signature",
    )
    keyinfo_node = _require_node(
        xmlsec.tree.find_node(resultxml, "KeyInfo"),
        "KeyInfo",
    )
    keymodulus_node = _require_node(
        xmlsec.tree.find_node(keyinfo_node, "Modulus"),
        "Modulus",
    )
    keyexponent_node = _require_node(
        xmlsec.tree.find_node(keyinfo_node, "Exponent"),
        "Exponent",
    )

    if not signature_node.tag.endswith(xmlsec.Node.SIGNATURE):
        raise ValueError(f"Unexpected signature node tag: {signature_node.tag}")

    if not keymodulus_node.text or not keyexponent_node.text:
        raise ValueError("KeyInfo Modulus/Exponent values must not be empty")

    pubkey_pem = create_pubkey_from_exp_mod(
        keyexponent_node.text,
        keymodulus_node.text,
    )

    ctx = xmlsec.SignatureContext()
    ctx.key = xmlsec.Key.from_memory(pubkey_pem, xmlsec.KeyFormat.PEM, None)

    ctx.verify(signature_node)
    return True


def xml_verify_with_certpem_file(resultxml: etree._Element, cert_pem: bytes) -> bool:
    """Verify the XML signature using a PEM certificate."""
    signature_node = _require_node(
        xmlsec.tree.find_node(resultxml, xmlsec.Node.SIGNATURE),
        "Signature",
    )

    if not signature_node.tag.endswith(xmlsec.Node.SIGNATURE):
        raise ValueError(f"Unexpected signature node tag: {signature_node.tag}")

    ctx = xmlsec.SignatureContext()
    ctx.key = xmlsec.Key.from_memory(cert_pem, xmlsec.KeyFormat.CERT_PEM, None)

    ctx.verify(signature_node)
    return True


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify RNS result XML signatures embedded in a results JSON file."
    )
    parser.add_argument(
        "-j",
        "--results-json",
        required=True,
        help="Path to the results JSON file.",
    )
    parser.add_argument(
        "-c",
        "--cert",
        action="append",
        default=[],
        help=(
            "Path to a PEM certificate or a directory containing .pem files. "
            "May be supplied multiple times."
        ),
    )
    return parser.parse_args(argv)


def find_pem_files(cert_paths: list[str]) -> list[Path]:
    """Expand -c/--cert inputs into a sorted list of PEM files.

    Each input may be either:
      * a single .pem file, or
      * a directory containing .pem files.

    Directory scanning is non-recursive by default, so passing keys/ loads keys/*.pem.
    """
    pem_files: list[Path] = []

    for cert_path in cert_paths:
        path = Path(cert_path)

        if path.is_dir():
            pem_files.extend(sorted(path.glob("*.pem")))
        elif path.is_file():
            if path.suffix.lower() != ".pem":
                raise ValueError(f"Certificate file does not end with .pem: {path}")
            pem_files.append(path)
        else:
            raise FileNotFoundError(f"Certificate path not found: {path}")

    # Deduplicate while preserving order.
    seen: set[Path] = set()
    unique_pem_files: list[Path] = []
    for pem_file in pem_files:
        resolved = pem_file.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_pem_files.append(pem_file)

    return unique_pem_files


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    pem_files = find_pem_files(args.cert)
    if not pem_files:
        print("WARNING: no PEM certificates were supplied or found.", file=sys.stderr)

    certs = []
    for path in pem_files:
        certs.append({"filename": str(path), "data": path.read_bytes()})

    print(f"loaded certificates: {len(certs)}")

    json_data = load_json(args.results_json)
    results = json_data.get("results", [])

    print("loaded json")
    print(len(results))

    for item in results:
        result = item["result"]
        result_id = result["resultId"]
        result_xml_text = result["result"]

        result_xml = etree.fromstring(result_xml_text.encode("utf-8"))

        try:
            self_verified = xml_verify_self(result_xml)
        except Exception as exc:  # xmlsec raises on invalid signatures
            print(f"WARNING: self verification failed for resultId {result_id}: {exc}", file=sys.stderr)
            self_verified = False

        cert_verified: str | bool = False
        for cert in certs:
            try:
                if xml_verify_with_certpem_file(result_xml, cert["data"]):
                    cert_verified = cert["filename"]
                    break
            except Exception:
                # Try the next certificate.
                pass

        print(
            "resultId",
            result_id,
            "    valid:",
            "OK" if self_verified else "FAIL",
            "    Certificate:",
            cert_verified if cert_verified else "None",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
