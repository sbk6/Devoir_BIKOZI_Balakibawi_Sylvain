.PHONY: create-role deploy upload-doc test validate delete

STUDENT     = sbikozi
ACCOUNT_ID  = 629193321657
REGION      = eu-west-3
STACK_NAME  = devoir-$(STUDENT)
TEMPLATE    = infrastructure/template.yaml
DOC_BUCKET  = $(STUDENT)-tech-doc-$(ACCOUNT_ID)
ROLE_NAME   = $(STUDENT)-lambda-iot-role

create-role:
	@echo "Creation du role IAM Lambda..."
	@echo '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' > /tmp/trust.json
	aws iam create-role \
		--role-name $(ROLE_NAME) \
		--assume-role-policy-document file:///tmp/trust.json
	aws iam attach-role-policy \
		--role-name $(ROLE_NAME) \
		--policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
	aws iam put-role-policy \
		--role-name $(ROLE_NAME) \
		--policy-name IoTDataAccess \
		--policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:PutObject"],"Resource":"arn:aws:s3:::$(STUDENT)-iot-datalake-$(ACCOUNT_ID)/*"},{"Effect":"Allow","Action":["dynamodb:PutItem"],"Resource":"arn:aws:dynamodb:$(REGION):$(ACCOUNT_ID):table/$(STUDENT)-iot-metrics"}]}'
	@echo "Role cree : arn:aws:iam::$(ACCOUNT_ID):role/$(ROLE_NAME)"

validate:
	aws cloudformation validate-template \
		--template-body file://$(TEMPLATE) \
		--region $(REGION)

deploy:
	aws cloudformation create-stack \
		--stack-name $(STACK_NAME) \
		--template-body file://$(TEMPLATE) \
		--capabilities CAPABILITY_NAMED_IAM \
		--parameters ParameterKey=StudentName,ParameterValue=$(STUDENT) \
		             ParameterKey=ExistingLambdaRoleArn,ParameterValue=arn:aws:iam::$(ACCOUNT_ID):role/$(ROLE_NAME) \
		             ParameterKey=ExistingOACId,ParameterValue=E3A1AYI8AX4F18 \
		--region $(REGION)
	@echo "Attente de la creation du stack..."
	aws cloudformation wait stack-create-complete \
		--stack-name $(STACK_NAME) --region $(REGION)
	aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) --region $(REGION) \
		--query "Stacks[0].Outputs"


upload-doc:
	aws s3 cp index.html s3://$(DOC_BUCKET)/ --region $(REGION)
	@echo "index.html uploade sur s3://$(DOC_BUCKET)/"

test:
	pip install requests -q
	python test_client.py


delete:
	aws cloudformation delete-stack \
		--stack-name $(STACK_NAME) --region $(REGION)
	aws cloudformation wait stack-delete-complete \
		--stack-name $(STACK_NAME) --region $(REGION)
	@echo "Stack supprime."
