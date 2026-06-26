#!/usr/bin/env python3
import sys, html, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/"src"))
from open_notator.core import SonFile, write_midi

IN=ROOT/"SON_FILES_HERE"
OUT=ROOT/"Converted_MIDI_Output"
REP=ROOT/"Reports"
OUT.mkdir(exist_ok=True); REP.mkdir(exist_ok=True)

def row(*cells):
    return "<tr>"+"".join("<td>%s</td>"%html.escape(str(c)) for c in cells)+"</tr>"

print("OpenNotator v0.1.1 no-Tk")
print("Input:", IN)
print("Output:", OUT)
print()

summaries=[]
for p in sorted(list(IN.glob("*.SON"))+list(IN.glob("*.son"))):
    try:
        song=SonFile(p)
        out=OUT/(p.stem+".mid")
        write_midi(song,out)
        summaries.append((p.name,"OK",song.tempo,len(song.segments),len(song.arrangement),sum(1 for s in song.segments if s.notes),out.name,""))
        print("OK", p.name, "->", out)
    except Exception as e:
        summaries.append((p.name,"FAILED","","","","","",str(e)))
        print("FAILED", p.name, e)

report=REP/"OPEN_ME_OpenNotator_Report.html"
with report.open("w",encoding="utf-8") as f:
    f.write("""<!doctype html><meta charset='utf-8'><title>OpenNotator Report</title>
<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;margin:28px}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:5px 8px}th{background:#eee}</style>
<h1>OpenNotator v0.1.1 Report</h1>
<p>MIDI output folder: <code>Converted_MIDI_Output</code></p>
<table><tr><th>File</th><th>Status</th><th>Tempo</th><th>Segments</th><th>Arrangement</th><th>Note segments</th><th>MIDI</th><th>Error</th></tr>""")
    for s in summaries:
        f.write(row(*s))
    f.write("</table>")

print()
print("Finished:", sum(1 for s in summaries if s[1]=="OK"), "converted,", sum(1 for s in summaries if s[1]!="OK"), "failed")
print("Report:", report)
subprocess.call(["open", str(report)])
