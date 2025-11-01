up:
	chmod +x ./helper.sh
	./helper.sh

update:
	git pull
	chmod +x ./helper.sh
	./helper.sh build

	