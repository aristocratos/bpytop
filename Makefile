PREFIX ?= /usr/local
DOCDIR ?= $(PREFIX)/share/bpytop/doc

all:
	@echo Run \'make install\' to install bpytop.

install:
	@mkdir -p $(DESTDIR)$(PREFIX)/bin
	@cp -p bpytop.py $(DESTDIR)$(PREFIX)/bin/bpytop
	@mkdir -p $(DESTDIR)$(DOCDIR)
	@cp -p README.md $(DESTDIR)$(DOCDIR)
	@cp -pr themes $(DESTDIR)$(PREFIX)/share/bpytop
	@chmod 755 $(DESTDIR)$(PREFIX)/bin/bpytop

uninstall:
	@rm -rf $(DESTDIR)$(PREFIX)/bin/bpytop
	@rm -rf $(DESTDIR)$(DOCDIR)
	@rm -rf $(DESTDIR)$(PREFIX)/share/bpytop
