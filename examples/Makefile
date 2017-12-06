AS = ca65
ASFLAGS = -g -t c64

LD = ld65
LDFLAGS = -u __EXEHDR__ -m labels.txt -Ln symbols -C c64-asm.cfg c64.lib

.PHONY: all run clean

all: test.d64.gz


test.prg: test.o
	$(LD) $(LDFLAGS) -o $@ $<

test.d64.gz: test.d64
	gzip -c $< > $@

test.d64: test.prg
	c1541 -format TEST,17 d64 $@
	c1541 -attach $@ -write $<
	c1541 -attach $@ -list

clean:
	-rm *.o *.prg labels.txt symbols *.d64 *.d64.gz

run: test.d64.gz
	x64 test.d64.gz
