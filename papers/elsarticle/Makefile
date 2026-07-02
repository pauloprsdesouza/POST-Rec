# POST-Rec methodology article (Elsevier elsarticle)
MAIN = post-rec-ideation

.PHONY: all clean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex post-rec-references.bib elsarticle.cls
	pdflatex -interaction=nonstopmode $(MAIN).tex
	bibtex $(MAIN)
	pdflatex -interaction=nonstopmode $(MAIN).tex
	pdflatex -interaction=nonstopmode $(MAIN).tex

elsarticle.cls:
	latex elsarticle.ins

clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out $(MAIN).pdf $(MAIN).synctex.gz
