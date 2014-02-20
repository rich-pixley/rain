# Time-stamp: <20-Feb-2014 11:49:23 PST by rich@noir.com>

# Copyright © 2013 K Richard Pixley
#

all: build
unames := $(shell uname -s)

packagename := rain

venvsuffix := 

pyver := 3.3
vpython := python${pyver}

ifeq (${unames},Darwin)
virtualenv := /Library/Frameworks/Python.framework/Versions/${pyver}/bin/virtualenv
else
ifeq (${unames},Linux)
virtualenv := virtualenv -p ${vpython}
else
$(error Unrecognized system)
endif
endif

venvbase := ${packagename}-dev
venv := ${venvbase}-${pyver}
pythonbin := ${venv}/bin
python := ${pythonbin}/python

activate := . ${pythonbin}/activate
setuppy := ${activate} && python setup.py
#pypi := 
pypi := -r https://testpypi.python.org/pypi

pydoctor := ${venv}/bin/pydoctor

.PHONY: ve
ve: ${python}
${python}:
	${virtualenv} --no-site-packages ${venv}
	find ${venv} -name distribute\* -o -name setuptools\* \
		| xargs rm -rf

.PHONY: clean
clean:
	rm -rf ${venvbase}* .stamp-virtualenv .stamp-apt build \
		dist ${packagename}.egg-info *.pyc apidocs *.egg *~ \
		__pycache__

# doc: ${pydoctor}
# 	${activate} && pydoctor --add-module=${packagename}.py \
# 		--add-module=test_${packagename}.py \
# 		--add-module=test_spread.py \
# 		&& firefox apidocs/index.html

setuppy.%: ${python}
	${activate} && python setup.py $*

.PHONY: build
build: ${packagename}.egg-info/SOURCES.txt

${packagename}.egg-info/SOURCES.txt: ${packagename}/__init__.py setup.py ${python}
	${setuppy} build

.PHONY: check
check: ${python} develop
	${setuppy} nosetests

sdist_format := bztar

.PHONY: sdist
sdist: ${python}
	${setuppy} sdist --formats=${sdist_format}

.PHONY: bdist
bdist: ${python}
	${setuppy} bdist

.PHONY: bdist_wheel
bdist_wheel: ${python}
	${setuppy} bdist_wheel

.PHONY: develop
develop: ${venv}/lib/${vpython}/site-packages/${packagename}.egg-link

${venv}/lib/${vpython}/site-packages/${packagename}.egg-link: setup.py ${python} ${packagename}/__init__.py
	${setuppy} --version 
	#${setuppy} lint
	${setuppy} develop

.PHONY: bdist_upload
bdist_upload: ${python} 
	${setuppy} bdist_egg upload ${pypi}

.PHONY: sdist_upload
sdist_upload: ${python}
	${setuppy} sdist --formats=${sdist_format} upload ${pypi}

.PHONY: register
register: ${python}
	${setuppy} $@ ${pypi}

long.html: long.rst
	${setuppy} build
	docutils-*-py${pyver}.egg/EGG-INFO/scripts/rst2html.py $< > $@-new && mv $@-new $@

long.rst: ; ${setuppy} --long-description > $@-new && mv $@-new $@


.PHONY: bdist_egg
bdist_egg: ${python}
	${setuppy} $@

doctrigger = docs/build/html/index.html

.PHONY: docs
docs: ${doctrigger}
${doctrigger}: ${python} docs/source/index.rst ${packagename}/__init__.py
	${setuppy} build_sphinx

.PHONY: lint
lint: ${python}
	${setuppy} $@

.PHONY: install
install: ${python}
	${setuppy} $@ --user

.PHONY: build_sphinx
build_sphinx: ${python}
	${setuppy} $@

.PHONY: nosetests
nosetests: ${python}
	${setuppy} $@

.PHONY: test
test: ${python}
	${setuppy} $@

.PHONY: docs_upload upload_docs
upload_docs docs_upload: ${doctrigger}
	${setuppy} upload_docs ${pypi}

supported_versions := \
	2.7 \

bigcheck: ${supported_versions:%=bigcheck-%}
bigcheck-%:; $(MAKE) pyver=$* check

bigupload: register sdist_upload ${supported_versions:%=bigupload-%} docs_upload
bigupload-%:; $(MAKE) pyver=$* bdist_upload
