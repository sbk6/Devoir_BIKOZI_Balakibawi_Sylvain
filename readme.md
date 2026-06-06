# Devoir Final - Pipeline d'Ingestion de Donnees IoT en Temps Reel (Serverless)

**Cours :** Introduction a AWS - Master 1 IABD  
**Auteur :** BIKOZI Balakibawi Sylvain  
**Responsable :** Mofiala Herve LOKOSSOU  
**Region AWS :** `eu-west-3` (Paris)

---

## Architecture

```
Capteur IoT  --POST-->  CloudFront #1  -->  API Gateway HTTP  -->  Lambda Python 3.11
                                                                        |           |
                                                                   S3 Data Lake  DynamoDB
                                                             (raw-zone/year/month)

Navigateur  ---------->  CloudFront #2  --OAC-->  S3 Documentation (prive)
```

**Ressources deploiees par CloudFormation :**
- 2 buckets S3 (Data Lake + Documentation)
- 1 table DynamoDB (Feature Store)
- 1 role IAM Lambda
- 1 fonction Lambda Python 3.11
- 1 API Gateway HTTP v2 (route `POST /ingest`)
- 2 distributions CloudFront (ingestion + documentation OAC)

---

## Structure du projet

```
Devoir_BIKOZI_Balakibawi_Sylvain/
├── infrastructure/
│   └── template.yaml     <- Template CloudFormation (infrastructure complete)
├── src/
│   └── index.py          <- Code source Lambda (documentation/reference)
├── test_client.py         <- Script de test IoT (payload valide + corrompu)
├── index.html             <- Site de documentation technique
└── README.md              <- Ce fichier
```

---

## Prerequis

| Outil | Version | Verification |
|-------|---------|--------------|
| AWS CLI v2 | 2.x | `aws --version` |
| Python | 3.8+ | `python --version` |
| pip | - | `pip --version` |
| Compte AWS | Droits Admin IAM | `aws sts get-caller-identity` |

### Configurer les credentials AWS

```bash
aws configure
# AWS Access Key ID     : <votre_access_key>
# AWS Secret Access Key : <votre_secret_key>
# Default region name   : eu-west-3
# Default output format : json
```

---

## Deploiement - Etape par etape

> Les commandes AWS CLI sont **identiques sur Windows (PowerShell/CMD) et Mac/Linux**.

### Etape 1 - Cloner le depot

```bash
git clone <URL_DU_REPO>
cd Devoir_BIKOZI_Balakibawi_Sylvain
```

### Etape 2 - Deployer l'infrastructure CloudFormation

```bash
aws cloudformation create-stack \
  --stack-name devoir-sbikozi \
  --template-body file://infrastructure/template.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=StudentName,ParameterValue=sbikozi \
  --region eu-west-3
```

> **Duree estimee : 15 a 20 minutes** (les distributions CloudFront prennent du temps).

Attendre la fin du deploiement :

```bash
aws cloudformation wait stack-create-complete \
  --stack-name devoir-sbikozi \
  --region eu-west-3

echo "Stack deploye avec succes !"
```

### Etape 3 - Recuperer les URLs CloudFront (Outputs)

```bash
aws cloudformation describe-stacks \
  --stack-name devoir-sbikozi \
  --region eu-west-3 \
  --query "Stacks[0].Outputs" \
  --output table
```

Vous obtiendrez :

| OutputKey | Description |
|-----------|-------------|
| `CloudFrontIngestionURL` | URL pour envoyer les donnees IoT (a utiliser dans test_client.py) |
| `CloudFrontDocURL` | URL du site de documentation |
| `DataLakeBucketName` | Nom du bucket S3 Data Lake |
| `TechDocBucketName` | Nom du bucket S3 Documentation |

### Etape 4 - Uploader la documentation dans S3

Remplacer `<TechDocBucketName>` par la valeur de l'Output :

```bash
aws s3 cp index.html s3://<TechDocBucketName>/ --region eu-west-3
```

Exemple :
```bash
aws s3 cp index.html s3://sbikozi-tech-doc-629193321657/ --region eu-west-3
```

**Verification blocage acces direct S3 :** Ouvrir l'URL S3 directe dans un navigateur
→ le resultat doit etre `AccessDenied` (bucket prive).

**Verification via CloudFront :** Ouvrir `CloudFrontDocURL` dans un navigateur
→ le site de documentation s'affiche correctement via CDN securise.

### Etape 5 - Tester le pipeline IoT

Modifier `test_client.py` ligne 17, remplacer par votre `CloudFrontIngestionURL` :

```python
CLOUDFRONT_INGESTION_URL = "https://XXXXXXX.cloudfront.net"
```

Installer les dependances et lancer les tests :

```bash
pip install requests
python test_client.py
```

**Resultat attendu Test 1 (payload valide) :**
```
Statut HTTP : 201
{"message": "Donnees ingestion reussie", "request_id": "...",
 "avg_temperature": 34.88, "error_count": 2}
[SUCCES] Donnees ingestion reussie - statut 201 recu.
```

**Resultat attendu Test 2 (payload corrompu) :**
```
Statut HTTP : 500
[INFO] Verifier les logs CloudWatch pour la Stack Trace Python.
```

---

## Verification dans la Console AWS

### S3 - Data Lake
Console AWS → S3 → `sbikozi-iot-datalake-<account_id>`  
Arborescence attendue :
```
raw-zone/
└── year=2026/
    └── month=06/
        └── <uuid>.json
```

### DynamoDB - Feature Store
Console AWS → DynamoDB → Tables → `sbikozi-iot-metrics` → Explore items

Colonnes : `request_id` | `timestamp` | `avg_temperature` | `error_count` | `record_count` | `s3_path`

### CloudWatch Logs - Lambda
Console AWS → CloudWatch → Log groups → `/aws/lambda/sbikozi-iot-ingestion`

- **Execution reussie** : log contenant `Data ingested successfully`
- **Execution en echec** : log contenant `JSONDecodeError` (payload corrompu Test 2)

---

## Nettoyage - Supprimer le stack

**Vider les buckets S3 d'abord** (obligatoire avant suppression) :

```bash
# Recuperer les noms des buckets depuis les outputs
DATA_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name devoir-sbikozi --region eu-west-3 \
  --query "Stacks[0].Outputs[?OutputKey=='DataLakeBucketName'].OutputValue" \
  --output text)

DOC_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name devoir-sbikozi --region eu-west-3 \
  --query "Stacks[0].Outputs[?OutputKey=='TechDocBucketName'].OutputValue" \
  --output text)

aws s3 rm s3://$DATA_BUCKET/ --recursive --region eu-west-3
aws s3 rm s3://$DOC_BUCKET/ --recursive --region eu-west-3
```

**Sur Windows PowerShell :**
```powershell
$DATA_BUCKET = aws cloudformation describe-stacks `
  --stack-name devoir-sbikozi --region eu-west-3 `
  --query "Stacks[0].Outputs[?OutputKey=='DataLakeBucketName'].OutputValue" `
  --output text

$DOC_BUCKET = aws cloudformation describe-stacks `
  --stack-name devoir-sbikozi --region eu-west-3 `
  --query "Stacks[0].Outputs[?OutputKey=='TechDocBucketName'].OutputValue" `
  --output text

aws s3 rm "s3://$DATA_BUCKET/" --recursive --region eu-west-3
aws s3 rm "s3://$DOC_BUCKET/" --recursive --region eu-west-3
```

**Supprimer le stack :**
```bash
aws cloudformation delete-stack \
  --stack-name devoir-sbikozi \
  --region eu-west-3

aws cloudformation wait stack-delete-complete \
  --stack-name devoir-sbikozi \
  --region eu-west-3

echo "Stack supprime."
```

---

## Note technique - Comptes AWS avec restrictions IAM

Sur certains comptes Lab, la permission `iam:TagRole` est absente, ce qui empeche
CloudFormation de creer le role IAM automatiquement.

**Solution : passer un role pre-cree en parametre**

Etape 1 - Creer le fichier `trust-policy.json` :
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "lambda.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
```

Etape 2 - Creer le role :
```bash
aws iam create-role \
  --role-name sbikozi-lambda-iot-role \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
  --role-name sbikozi-lambda-iot-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Etape 3 - Deployer en passant le role :
```bash
aws cloudformation create-stack \
  --stack-name devoir-sbikozi \
  --template-body file://infrastructure/template.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=StudentName,ParameterValue=sbikozi \
    ParameterKey=ExistingLambdaRoleArn,ParameterValue=arn:aws:iam::<ACCOUNT_ID>:role/sbikozi-lambda-iot-role \
  --region eu-west-3
```

---

*Devoir Final - Introduction a AWS - Master 1 IABD - BIKOZI Balakibawi Sylvain - 2026*
