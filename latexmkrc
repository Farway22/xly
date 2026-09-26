# Overleaf's default pdfLaTeX selection uses latexmk -pdf. Route that rule
# to XeLaTeX so the user does not have to change the project compiler setting.
$pdflatex = 'xelatex %O %S';
$pdf_mode = 1;
