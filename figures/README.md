把论文使用的 PDF、PNG 或 JPG 图放在此目录，在正文中使用：

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=.8\textwidth]{your-figure.pdf}
  \caption{填写实际图注}
  \label{fig:your-result}
\end{figure}
```

文件名建议使用英文字母、数字和连字符。图中字体、坐标轴、单位和图例由图文件本身决定，应在绘图时一并设置。
