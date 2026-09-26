\NeedsTeXFormat{LaTeX2e}[2022/11/01]
\ProvidesClass{gmcmthesis}[2026/09/21 Official Word layout with portable fonts]
\newif\ifgmcm@coverpage
\gmcm@coverpagefalse
\LoadClass[UTF8,fontset=none,zihao=-4,linespread=1]{ctexart}
\RequirePackage{iftex}
\RequireXeTeX
\RequirePackage{geometry}
\geometry{paperwidth=595.5bp,paperheight=842bp,
  left=64.05bp,right=63.65bp,top=85.1bp,textheight=686.4bp,
  headheight=0bp,headsep=0bp,footskip=0bp}
\RequirePackage{graphicx,eso-pic,xcolor}
\RequirePackage{amsmath,amssymb,bm}
\RequirePackage{booktabs,longtable,tabularx,array}
\RequirePackage{caption,subcaption}
\RequirePackage{enumitem,listings}
\RequirePackage[numbers,sort&compress]{natbib}
\RequirePackage[hidelinks,unicode]{hyperref}
\input{fonts.tex}

% Chinese point sizes are Word/PostScript points (bp), not TeX points.
\renewcommand\normalsize{%
  \@setfontsize\normalsize{12bp}{15.6bp}%
  \abovedisplayskip=6bp plus 2bp minus 2bp
  \belowdisplayskip=6bp plus 2bp minus 2bp
  \abovedisplayshortskip=3bp plus 2bp
  \belowdisplayshortskip=3bp plus 2bp}
\AtBeginDocument{\normalsize\songti}
% Word's nominal bottom margin includes its footer region. A measured filled
% page contains 44 single-spaced lines; this text height preserves that limit.
\setlength{\topskip}{11.95bp}
\setlength{\parindent}{24bp}
\setlength{\parskip}{0bp}
\linespread{1}
\pagestyle{empty}
\raggedbottom
\setlength{\emergencystretch}{1em}
\setcounter{secnumdepth}{3}
\ctexset{
  section={name={},number=\arabic{section},format=\centering\heiti\fontsize{14bp}{18.2bp}\selectfont,
    beforeskip=15.6bp,afterskip=7.8bp,aftername=\hspace{1em}},
  subsection={format=\songti\bfseries\normalsize,beforeskip=7.8bp,afterskip=3.9bp,aftername=\hspace{1em}},
  subsubsection={format=\songti\normalsize,beforeskip=3.9bp,afterskip=0bp,aftername=\hspace{1em}}
}
\setlist{topsep=3.9bp,itemsep=0bp,parsep=0bp,partopsep=0bp,leftmargin=2em}
\DeclareCaptionFont{gmcmbody}{\songti\normalsize}
\captionsetup{font=gmcmbody,labelsep=quad,skip=6bp}
\captionsetup[sub]{font=gmcmbody}
\renewcommand\bibfont{\songti\normalsize}
\setlength{\bibsep}{0bp}
\graphicspath{{figures/}{assets/}}
\lstset{basicstyle=\ttfamily\normalsize,columns=fullflexible,
  keepspaces=true,breaklines=true,showstringspaces=false,
  frame=single,framerule=.4bp,framesep=4bp,
  aboveskip=7.8bp,belowskip=7.8bp,tabsize=4}

% Official Word footer: Times New Roman 9 bp, baseline y=51.025 bp.
\AddToShipoutPictureFG{%
  \ifgmcm@coverpage\else
  \AtPageLowerLeft{\put(298bp,51.025bp){%
    \makebox[0pt][c]{\rmfamily\fontsize{9bp}{9bp}\selectfont\thepage}}}%
  \fi}

\newcommand\gmcm@school{}
\newcommand\gmcm@team{}
\newcommand\gmcm@membera{}
\newcommand\gmcm@memberb{}
\newcommand\gmcm@memberc{}
\newcommand\schoolname[1]{\renewcommand\gmcm@school{#1}}
\newcommand\baominghao[1]{\renewcommand\gmcm@team{#1}}
\newcommand\membera[1]{\renewcommand\gmcm@membera{#1}}
\newcommand\memberb[1]{\renewcommand\gmcm@memberb{#1}}
\newcommand\memberc[1]{\renewcommand\gmcm@memberc{#1}}
\newcommand\gmcm@coverfield[3]{%
  \put(#1bp,#2bp){\makebox[0pt][l]{%
    \coverlatin\songti\bfseries\fontsize{18bp}{23.4bp}\selectfont#3}}}

% Use the original official cover as a vector PDF, at its original size.
% Its fixed labels, logos, rules, and printed page 0 are preserved exactly.
\newcommand\makecover{%
  \clearpage\gmcm@coverpagetrue
  \AddToShipoutPictureBG*{\AtPageLowerLeft{%
    \includegraphics[scale=1]{assets/official-cover.pdf}}}%
  \AddToShipoutPictureFG*{\AtPageLowerLeft{%
    \gmcm@coverfield{186.65}{456.78}{\gmcm@school}%
    \gmcm@coverfield{186.65}{398.22}{\gmcm@team}%
    \gmcm@coverfield{210}{366.23}{\gmcm@membera}%
    \gmcm@coverfield{210}{333.70}{\gmcm@memberb}%
    \gmcm@coverfield{210}{301.67}{\gmcm@memberc}%
  }}%
  \null\clearpage\gmcm@coverpagefalse\setcounter{page}{1}}

% Static artwork uses original Word vectors. Longer titles grow downward;
% the abstract label and text move together without changing font sizes.
\newsavebox\gmcm@titlebox
\newsavebox\gmcm@titlelinebox
\newlength\gmcm@titleextra
\newlength\gmcm@abstractlabelY
\newlength\gmcm@abstractspace
% Editable title field; original Word dimensions remain the class defaults.
\newlength\papertitleleft
\newlength\papertitlewidth
\setlength\papertitleleft{148.1bp}
\setlength\papertitlewidth{245.03bp}
\newcommand\gmcm@titleunderline{%
  % Original underline is part of the PDF artwork. Only replace it when
  % the user changes the field dimensions; the white strip covers ink only.
  \ifdim\papertitleleft=148.1bp
    \ifdim\papertitlewidth=245.03bp\else\gmcm@drawtitleunderline\fi
  \else\gmcm@drawtitleunderline\fi}
\newcommand\gmcm@drawtitleunderline{%
  \put(148bp,576.7bp){\color{white}\rule{245.3bp}{0.8bp}}%
  \put(\papertitleleft,576.94bp){\color{black}\rule{\papertitlewidth}{0.32bp}}}
\renewcommand\maketitle{%
  \clearpage\setcounter{page}{1}%
  \hypersetup{pdftitle={\@title},pdfauthor={},pdfsubject={}}%
  \sbox\gmcm@titlelinebox{\parbox[t]{\papertitlewidth}{%
    \centering\heiti\fontsize{16bp}{20.8bp}\selectfont\strut 题目\strut\par}}%
  \sbox\gmcm@titlebox{\parbox[t]{\papertitlewidth}{%
    \centering\heiti\fontsize{16bp}{20.8bp}\selectfont\strut\@title\strut\par}}%
  \setlength\gmcm@titleextra{\dimexpr\dp\gmcm@titlebox-\dp\gmcm@titlelinebox\relax}%
  % \\[-...] in a title is not supported; use ordinary automatic wrapping.
  \ifdim\gmcm@titleextra<0pt\setlength\gmcm@titleextra{0pt}\fi
  \setlength\gmcm@abstractlabelY{\dimexpr511bp-\gmcm@titleextra\relax}%
  \setlength\gmcm@abstractspace{\dimexpr244.08bp+\gmcm@titleextra\relax}%
  \AddToShipoutPictureBG*{\AtPageUpperLeft{\put(0,-280bp){%
    \includegraphics[scale=1]{assets/summary-heading.pdf}}}}%
  \AddToShipoutPictureBG*{\AtPageLowerLeft{\put(0,\gmcm@abstractlabelY){%
    \includegraphics[scale=1]{assets/abstract-label.pdf}}}}%
  \AddToShipoutPictureFG*{\AtPageLowerLeft{%
    \gmcm@titleunderline
    \put(\papertitleleft,578.85bp){\usebox\gmcm@titlebox}}}%
  \vspace*{\gmcm@abstractspace}% first baseline: 356.73 bp + title extension
  \par}
\renewenvironment{abstract}{\par\normalsize\songti}{\par}
\newcommand\keywords[1]{%
  \par\vspace{15.6bp}\noindent
  {\lishu\fontsize{18bp}{23.4bp}\selectfont 关键词：}%
  {\songti\normalsize#1}\par}
\newcommand\startbody{\clearpage\normalsize\songti}
\newcommand\maketoc{\clearpage\tableofcontents\clearpage}
\newcommand\appendicesbegin{\clearpage\appendix\ctexset{section/name={附录\space,}}}
\endinput
