.PHONY: test dist clean

.DEFAULT_TARGET = test

test:
	python3 -B -m unittest test.basic

dist:
	python3 -m build

clean:
	rm -rf revo.egg-info dist
