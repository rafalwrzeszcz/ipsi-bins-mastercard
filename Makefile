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
	# TODO

destroy:
	# TODO

# particular files

target/build:
	mkdir -p $@
