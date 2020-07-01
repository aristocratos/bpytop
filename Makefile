PREFIX ?= /usr/local
DOCDIR ?= $(PREFIX)/share/doc/bpytop

all:
	@echo Run \'make install\' to install bpytop.

install:
	@mkdir -p $(DESTDIR)$(PREFIX)/bin
	@cp -p bpytop $(DESTDIR)$(PREFIX)/bin/bpytop
	@mkdir -p $(DESTDIR)$(DOCDIR)
	@cp -p README.md $(DESTDIR)$(DOCDIR)
	@chmod 755 $(DESTDIR)$(PREFIX)/bin/bpytop

uninstall:
	@rm -rf $(DESTDIR)$(PREFIX)/bin/bpytop
	@rm -rf $(DESTDIR)$(DOCDIR)
