PREFIX ?= /usr/local
DOCDIR ?= $(PREFIX)/share/bpytop/doc
PYTHON_INTERPRETER ?= $$(which python3)

all:
	@echo Run \'make install\' to install bpytop.

install:
	@$(PYTHON_INTERPRETER) -c "import psutil" || (echo "psutil not installed in $(PYTHON_INTERPRETER)"; exit 1)
	@echo "#!$(PYTHON_INTERPRETER)" | cat - bpytop.py > temp
	@mkdir -p $(DESTDIR)$(PREFIX)/bin
	@cp -p temp $(DESTDIR)$(PREFIX)/bin/bpytop
	@mkdir -p $(DESTDIR)$(DOCDIR)
	@cp -p README.md $(DESTDIR)$(DOCDIR)
	@cp -pr themes $(DESTDIR)$(PREFIX)/share/bpytop
	@chmod 755 $(DESTDIR)$(PREFIX)/bin/bpytop
	@rm temp

uninstall:
	@rm -rf $(DESTDIR)$(PREFIX)/bin/bpytop
	@rm -rf $(DESTDIR)$(DOCDIR)
	@rm -rf $(DESTDIR)$(PREFIX)/share/bpytop
