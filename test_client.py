"""
Devoir Final - Script de test client IoT
Envoie un payload de donnees IoT via HTTP POST vers le pipeline serverless.

Usage:
    1. Remplacer CLOUDFRONT_INGESTION_URL par la valeur de l'Output 'CloudFrontIngestionURL'
    2. pip install requests
    3. python test_client.py
"""

import requests
import json
import sys

# ============================================================
# CONFIGURATION - Remplacer par votre URL CloudFront (Outputs)
# ============================================================
CLOUDFRONT_INGESTION_URL = "https://d2xpud3y6q0d90.cloudfront.net"


# ============================================================
# PAYLOAD VALIDE - 4 mesures IoT structurees
# ============================================================
VALID_PAYLOAD = {
    "records": [
        {"sensor_id": "sensor-001", "temperature": 23.5,  "status": "OK"},
        {"sensor_id": "sensor-002", "temperature": 41.2,  "status": "ERROR"},
        {"sensor_id": "sensor-003", "temperature": 19.8,  "status": "OK"},
        {"sensor_id": "sensor-004", "temperature": 55.0,  "status": "ERROR"}
    ]
}

# ============================================================
# PAYLOAD CORROMPU - pour tester la gestion des erreurs Lambda
# ============================================================
CORRUPT_PAYLOAD = "{ ceci est un json invalide !!!"


def test_valid_ingestion():
    """Test 1 : envoi d'un payload valide - attend HTTP 201."""
    print("=" * 60)
    print("TEST 1 : Ingestion payload valide")
    print("=" * 60)
    print(f"URL cible : {CLOUDFRONT_INGESTION_URL}/ingest")
    print(f"Payload :\n{json.dumps(VALID_PAYLOAD, indent=2)}\n")

    response = requests.post(
        f"{CLOUDFRONT_INGESTION_URL}/ingest",
        json=VALID_PAYLOAD,
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    print(f"Statut HTTP : {response.status_code}")
    try:
        print(f"Reponse :\n{json.dumps(response.json(), indent=2)}")
    except Exception:
        print(f"Reponse brute : {response.text}")

    if response.status_code == 201:
        print("\n[SUCCES] Donnees ingestion reussie - statut 201 recu.")
    else:
        print(f"\n[ECHEC] Statut inattendu : {response.status_code}")

    return response


def test_corrupt_payload():
    """Test 2 : envoi d'un payload corrompu - doit lever une exception Lambda."""
    print("\n" + "=" * 60)
    print("TEST 2 : Ingestion payload corrompu (test gestion d'erreur)")
    print("=" * 60)
    print(f"Payload corrompu : {CORRUPT_PAYLOAD}\n")

    response = requests.post(
        f"{CLOUDFRONT_INGESTION_URL}/ingest",
        data=CORRUPT_PAYLOAD,
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    print(f"Statut HTTP : {response.status_code}")
    print(f"Reponse brute : {response.text}")
    print("\n[INFO] Verifier les logs CloudWatch pour la Stack Trace Python.")

    return response


if __name__ == "__main__":
    if "REMPLACER" in CLOUDFRONT_INGESTION_URL:
        print("[ERREUR] Veuillez remplacer CLOUDFRONT_INGESTION_URL dans le script.")
        sys.exit(1)

    test_valid_ingestion()
    test_corrupt_payload()
