"""Render source-grounded SOG excerpts as an editable SVG (standard library only)."""
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def render():
    folder = ROOT / 'wild/sog'
    left = json.loads((folder/'local-self-healing.json').read_text())
    right = json.loads((folder/'capability-evolver.json').read_text())
    case = json.loads((ROOT/'wild/cases.json').read_text())['retained-evolution-workflow']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1140" viewBox="0 0 1400 1140">',
        '<rect width="1400" height="1140" fill="#f5f7fb"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#20324a}.mono{font-family:Menlo,Consolas,monospace}</style>']
    def text(x,y,value,size=20,weight='normal',color='#20324a',cls=''):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" style="fill:{color}" class="{cls}">{escape(value)}</text>')
    def box(x,y,w,h,fill,stroke='#d6dfea'):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}"/>')
    text(40,48,'Different names. Retained operational structure.',32,'bold')
    text(40,82,'Example SOG Excerpts (Not Full Graphs)',22,color='#52657e')
    text(40,116,f"Saved whole-package scores: Expression {case['SkillTrace-Expression']:.3f}   |   Implementation {case['SkillTrace-Implementation']:.3f}   |   Repo-Jaccard {case['RepoClone-Jaccard']:.3f}",20)
    for x, record, lines in [(40,left,['local-self-healing-','machine-learning']),
                              (730,right,['capability-evolver'])]:
        box(x,142,630,896,'#ffffff')
        for i,line in enumerate(lines):text(x+22,177+i*27,line,24,'bold')
        text(x+22,229,'SkillHub snapshot' if x==40 else 'SkillsRest snapshot',17,color='#6a7a90')
        box(x+20,248,590,90,'#f0edfb')
        text(x+36,277,'ACTIVATION',16,'bold','#645092')
        text(x+36,307,'Solidify a change · Git repository required',21)
        box(x+20,354,590,302,'#eaf3fd')
        text(x+36,383,'PROCEDURE · SELECTED FAILURE PATH',16,'bold','#285b8d')
        for y,label in [(414,'Constraint check + validation + canary'),
                        (467,'Outcome gate: checks pass ∧ no protocol violation'),
                        (533,'Capture failed diff before rollback'),
                        (617,'Roll back tracked changes')]:
            text(x+36,y,label,20,'bold' if y in (533,617) else 'normal')
        text(x+48,439,'↓',25,color='#4278a7')
        text(x+48,498,'↓  failure AND not dry run',18,color='#285b8d')
        text(x+48,565,'↓  rollback enabled AND not dry run',18,color='#285b8d')
        text(x+48,591,'Preserve evidence before destructive recovery',17,color='#52718f')
        box(x+20,672,590,169,'#eaf7f2')
        text(x+36,701,'RESOURCE-FLOW + FIVE-FIELD BLOCK',16,'bold','#2b725a')
        text(x+36,730,'Repository → capture → diff snapshot',21,'bold')
        text(x+36,759,'action: capture   object: failed_change',18,cls='mono')
        text(x+36,785,'tool: version_control   in: repository',18,cls='mono')
        text(x+36,811,'out: diff_snapshot',18,cls='mono')
        box(x+20,857,590,157,'#fff3e6')
        text(x+36,886,'DISTINCT LEARNING HOOK (RETAINED)',16,'bold','#995d25')
        if x==40:
            rows=['Record outcome in persistent knowledge store',
                  'Inputs: error signature, gene, outcome, environment',
                  'Condition: store + gene + error hash; not dry run']
        else:
            rows=['Adapt the gene from learning signals',
                  'Inputs: gene, outcome, learning signals, failure mode',
                  'Condition: valid gene; not dry run']
        for y,line in zip([916,951,984],rows):text(x+36,y,line,19,'bold' if y==916 else 'normal')
    text(40,1071,'Source-grounded editorial annotations · 7 shared blocks + 1 distinct hook per selected excerpt',21,'bold')
    text(40,1105,'Source: src/gep/solidify.js on each side. No whole-graph O score or new detection claim is inferred from this figure.',18,color='#52657e')
    parts.append('</svg>')
    path = ROOT/'assets/wild-sog-comparison.svg'
    path.write_text('\n'.join(parts)+'\n')
    print('Rendered assets/wild-sog-comparison.svg')

if __name__ == '__main__':render()
