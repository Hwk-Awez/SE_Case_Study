import os
import re
import subprocess
import markdown

def convert_md_to_pdf():
    base_dir = r"D:\Later Projects\SE_Case_Study"
    md_path = os.path.join(base_dir, "TEAM_PPT_AND_REPORT_MASTER_GUIDE.md")
    html_path = os.path.join(base_dir, "TEAM_PPT_AND_REPORT_MASTER_GUIDE.html")
    pdf_path = os.path.join(base_dir, "TEAM_PPT_AND_REPORT_MASTER_GUIDE.pdf")

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert Markdown to HTML
    html_body = markdown.markdown(
        md_content,
        extensions=['extra', 'tables', 'fenced_code', 'toc', 'nl2br', 'sane_lists']
    )

    # Wrap in executive HTML template with printing CSS
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Software Component Cataloguing & Reuse Tracking System - Master Guide</title>
<style>
  @page {{
    size: A4;
    margin: 18mm 15mm 18mm 15mm;
    @bottom-right {{
      content: counter(page);
    }}
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1f2937;
    background: #ffffff;
    margin: 0;
    padding: 0;
  }}

  h1, h2, h3, h4, h5, h6 {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #111827;
    font-weight: 700;
    margin-top: 1.4em;
    margin-bottom: 0.5em;
  }}

  h1 {{
    font-size: 20pt;
    border-bottom: 2px solid #2563eb;
    padding-bottom: 6px;
    margin-top: 1.8em;
    page-break-before: always;
  }}

  h1:first-of-type {{
    page-break-before: avoid;
    margin-top: 0;
  }}

  h2 {{
    font-size: 14pt;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 4px;
    color: #1e40af;
  }}

  h3 {{
    font-size: 12pt;
    color: #374151;
  }}

  p, li {{
    margin-bottom: 0.5em;
  }}

  blockquote {{
    margin: 1em 0;
    padding: 10px 16px;
    background-color: #f0fdf4;
    border-left: 4px solid #16a34a;
    color: #166534;
    font-size: 10pt;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.2em 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }}

  th, td {{
    border: 1px solid #d1d5db;
    padding: 7px 10px;
    text-align: left;
    vertical-align: top;
  }}

  th {{
    background-color: #f3f4f6;
    font-weight: 600;
    color: #111827;
  }}

  tr:nth-child(even) {{
    background-color: #f9fafb;
  }}

  code {{
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9.5pt;
    background-color: #f3f4f6;
    padding: 2px 5px;
    border-radius: 4px;
    border: 1px solid #e5e7eb;
    color: #b91c1c;
  }}

  pre {{
    background-color: #1e293b;
    color: #f8fafc;
    padding: 12px 14px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 8.5pt;
    line-height: 1.45;
    page-break-inside: avoid;
    margin: 1em 0;
  }}

  pre code {{
    background-color: transparent;
    color: inherit;
    border: none;
    padding: 0;
    font-size: inherit;
  }}

  hr {{
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 1.8em 0;
  }}

  ul, ol {{
    padding-left: 24px;
    margin-bottom: 1em;
  }}

  li {{
    margin-bottom: 4px;
  }}

  .header-box {{
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    color: white;
    padding: 24px;
    border-radius: 8px;
    margin-bottom: 24px;
  }}

  .header-box h1 {{
    color: white;
    border: none;
    margin: 0 0 8px 0;
    padding: 0;
    font-size: 22pt;
  }}

  .header-box p {{
    margin: 0;
    font-size: 11pt;
    opacity: 0.95;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"Generated HTML: {html_path}")

    # Use Google Chrome or MS Edge for PDF rendering
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    executable = None
    for cp in chrome_paths:
        if os.path.exists(cp):
            executable = cp
            break

    if not executable:
        print("No browser found for PDF printing.")
        return

    cmd = [
        executable,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        f"--print-to-pdf={pdf_path}",
        "--no-pdf-header-footer",
        html_path
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(pdf_path):
        print(f"Successfully created PDF: {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")
    else:
        print(f"PDF creation failed: {result.stderr}")

if __name__ == "__main__":
    convert_md_to_pdf()
