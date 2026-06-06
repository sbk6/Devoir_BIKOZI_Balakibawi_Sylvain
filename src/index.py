"""
Devoir Final - Pipeline IoT Serverless
Fonction Lambda d'ingestion de donnees IoT en temps reel

Auteur  : BIKOZI Balakibawi Sylvain
Cours   : Introduction a AWS - Master 1 IABD
Prof    : Mofiala Herve LOKOSSOU
"""

import json
import boto3
import os
import uuid
from datetime import datetime
from decimal import Decimal

# Clients boto3 initialises hors du handler (reutilises entre invocations)
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    """
    Point d'entree Lambda.

    Recoit un payload HTTP POST contenant une liste de mesures IoT,
    sauvegarde le payload brut dans S3 (Data Lake) et ecrit un rapport
    d'execution agrege dans DynamoDB (Feature Store).

    Args:
        event: Evenement API Gateway v2 (format payload 2.0)
        context: Contexte d'execution Lambda

    Returns:
        dict: Reponse HTTP 201 avec rapport d'ingestion, ou 400/500 si erreur
    """
    # --- 1. Extraction et validation du corps JSON ---
    raw_body = event.get('body', '{}')
    body = json.loads(raw_body)
    records = body.get('records', [])

    if not records:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Aucun enregistrement trouve dans le payload'})
        }

    # --- 2. Calcul des metriques a la volee ---
    temperatures = [float(r['temperature']) for r in records if 'temperature' in r]
    avg_temperature = round(sum(temperatures) / len(temperatures), 2) if temperatures else 0.0
    error_count = sum(1 for r in records if r.get('status') == 'ERROR')
    record_count = len(records)

    # --- 3. Generation des identifiants et partitionnement temporel ---
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Cle S3 avec partitionnement temporel : raw-zone/year=YYYY/month=MM/
    s3_key = f"raw-zone/year={now.year}/month={now.month:02d}/{request_id}.json"

    # --- 4. Sauvegarde du payload brut dans S3 (Data Lake) ---
    s3_client.put_object(
        Bucket=os.environ['S3_BUCKET'],
        Key=s3_key,
        Body=json.dumps(body, ensure_ascii=False),
        ContentType='application/json'
    )

    # --- 5. Ecriture du rapport d'execution dans DynamoDB (Feature Store) ---
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    table.put_item(Item={
        'request_id': request_id,
        'timestamp': now.isoformat(),
        's3_path': s3_key,
        'avg_temperature': Decimal(str(avg_temperature)),
        'error_count': error_count,
        'record_count': record_count
    })

    # --- 6. Reponse HTTP 201 ---
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': 'Donnees ingestion reussie',
            'request_id': request_id,
            's3_path': s3_key,
            'avg_temperature': avg_temperature,
            'error_count': error_count,
            'record_count': record_count
        })
    }
