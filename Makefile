default: package

# stage commands

clean:
	rm -rf target

build: target/build
	cp -r src/* target/build
	pip3 install -r target/build/requirements.txt --target target/build

package: build
	(cd target/build ; zip ../lambda.zip . -r)

deploy: package
	sam deploy \
		--stack-name ${_APP_STACK_NAME} \
		--s3-bucket ${_APP_DEPLOY_BUCKET} \
		--capabilities CAPABILITY_IAM \
		--template cloudformation/lambda.yaml \
		--parameter-overrides BinsTableName=${BINS_TABLE_NAME} MastercardSecretName=${SECRET_NAME}

destroy:
	sam delete --stack-name ${_APP_STACK_NAME}

# helpers

run:
	(cd target/build && python -c 'from index import handler; handler(None, None)')

# particular files

target/build:
	mkdir -p $@
