import re
import pandas as pd
from collections import defaultdict
from weasyprint import HTML

# Dati del torneo
text = """
Turno 1
FACILINI LUCA B VS BATTANI IONE -> 6-7
ALEXANDRA SOCIO VS ANTONIO FRANCHINO -> 7-5
SERGIO BENEDETTA VS DONATELLO LUIGI -> 7-5
MILANESI IVAN VS SALVATORE MARCELLO -> 7-2
VITTORIO ALEXANDER VS GIOVI MASSI -> 7-4
Turno 2
FACILINI LUCA B VS ANTONIO FRANCHINO ->7-2
BATTANI IONE VS DONATELLO LUIGI -> 7-2
ALEXANDRA SOCIO VS SALVATORE MARCELLO -> 7-5
SERGIO BENEDETTA VS GIOVI MASSI -> 7-6
MILANESI IVAN VS VITTORIO ALEXANDER -> 7-3
Turno 3
FACILINI LUCA B VS DONATELLO LUIGI -> 1-7
ANTONIO FRANCHINO VS SALVATORE MARCELLO -> 7-3
BATTANI IONE VS GIOVI MASSI -> 7-5
ALEXANDRA SOCIO VS VITTORIO ALEXANDER -> 4-7
SERGIO BENEDETTA VS MILANESI IVAN -> 7-6
Turno 4
FACILINI LUCA B VS SALVATORE MARCELLO -> 4-7
DONATELLO LUIGI VS GIOVI MASSI -> 7-4
ANTONIO FRANCHINO VS VITTORIO ALEXANDER -> 3 - 7
BATTANI IONE VS MILANESI IVAN -> 5-7
ALEXANDRA SOCIO VS SERGIO BENEDETTA -> 3-7
Turno 5
FACILINI LUCA B VS GIOVI MASSI -> 7-5
SALVATORE MARCELLO VS VITTORIO ALEXANDER -> 3-7
DONATELLO LUIGI VS MILANESI IVAN -> 7-6
ANTONIO FRANCHINO VS SERGIO BENEDETTA -> 6-7
BATTANI IONE VS ALEXANDRA SOCIO -> 7-0
Turno 6
FACILINI LUCA B VS VITTORIO ALEXANDER -> 3-7
GIOVI MASSI VS MILANESI IVAN -> 3-7
SALVATORE MARCELLO VS SERGIO BENEDETTA -> 3-7
DONATELLO LUIGI VS ALEXANDRA SOCIO -> 5-7
ANTONIO FRANCHINO VS BATTANI IONE -> 3-7
Turno 7
FACILINI LUCA B VS MILANESI IVAN -> 7-5
VITTORIO ALEXANDER VS SERGIO BENEDETTA -> 3-7
GIOVI MASSI VS ALEXANDRA SOCIO -> 7-6
SALVATORE MARCELLO VS BATTANI IONE ->7-6
DONATELLO LUIGI VS ANTONIO FRANCHINO -> 3-7
Turno 8
FACILINI LUCA B VS SERGIO BENEDETTA -> 6-7
MILANESI IVAN VS ALEXANDRA SOCIO -> 7-6
VITTORIO ALEXANDER VS BATTANI IONE -> 2-7
GIOVI MASSI VS ANTONIO FRANCHINO -> 4-7
SALVATORE MARCELLO VS DONATELLO LUIGI -> 7-4
Turno 9
FACILINI LUCA B VS ALEXANDRA SOCIO -> 7-6
SERGIO BENEDETTA VS BATTANI IONE -> 7-6
MILANESI IVAN VS ANTONIO FRANCHINO -> 5-7
VITTORIO ALEXANDER VS DONATELLO LUIGI -> 7-3
GIOVI MASSI VS SALVATORE MARCELLO -> 5-7
"""

stats = defaultdict(lambda: {'partite': 0, 'vinte': 0, 'perse': 0, 'punti_fatti': 0, 'punti_subiti': 0, 'punti_classifica': 0})

for line in text.strip().split('\n'):
    if "VS" in line and "->" in line:
        match = re.match(r'^\s*(.*?)\s+VS\s+(.*?)\s*->\s*(\d+)\s*-\s*(\d+)\s*$', line)
        if match:
            p1, p2, s1, s2 = match.groups()
            s1, s2 = int(s1), int(s2)
            
            stats[p1]['partite'] += 1
            stats[p2]['partite'] += 1
            stats[p1]['punti_fatti'] += s1
            stats[p1]['punti_subiti'] += s2
            stats[p2]['punti_fatti'] += s2
            stats[p2]['punti_subiti'] += s1
            
            if s1 > s2:
                stats[p1]['vinte'] += 1
                stats[p1]['punti_classifica'] += 3
                stats[p2]['perse'] += 1
            else:
                stats[p2]['vinte'] += 1
                stats[p2]['punti_classifica'] += 3
                stats[p1]['perse'] += 1

df = pd.DataFrame([
    {
        'Giocatore': k,
        'Partite': v['partite'],
        'Vinte': v['vinte'],
        'Perse': v['perse'],
        'Punti Fatti': v['punti_fatti'],
        'Punti Subiti': v['punti_subiti'],
        'Diff. Punti': v['punti_fatti'] - v['punti_subiti'],
        'Punti Classifica': v['punti_classifica']
    }
    for k, v in stats.items()
])

df = df.sort_values(by=['Punti Classifica', 'Vinte', 'Diff. Punti'], ascending=False).reset_index(drop=True)
df.index = df.index + 1

html_content = """
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<style>
    @page { size: A4 portrait; margin: 12mm; background-color: #f4f6f8; }
    body { font-family: Helvetica, Arial, sans-serif; color: #2c3e50; font-size: 11pt; line-height: 1.4; margin: 0; }
    .header-banner { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
    .header-banner h1 { margin: 0 0 5px 0; font-size: 22pt; text-transform: uppercase; }
    .card { background: white; border-radius: 8px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h2 { color: #1e3c72; font-size: 13pt; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-top: 0; text-transform: uppercase; }
    table { width: 100%; border-collapse: collapse; margin-top: 5px; }
    th, td { padding: 8px; text-align: center; font-size: 10pt; }
    th { background-color: #1e3c72; color: white; text-transform: uppercase; }
    th:first-child, td:first-child { text-align: left; }
    tr:nth-child(even) { background-color: #f8fafc; }
    .podium-1 { background-color: #fffbeb !important; font-weight: bold; color: #b45309; }
    .podium-2 { background-color: #f1f5f9 !important; font-weight: bold; }
    .podium-3 { background-color: #fff7ed !important; font-weight: bold; }
    .badge-win { background-color: #def7ec; color: #03543f; padding: 2px 6px; border-radius: 10px; font-weight: bold; }
    .badge-loss { background-color: #fde8e8; color: #9b1c1c; padding: 2px 6px; border-radius: 10px; font-weight: bold; }
    .footer { text-align: center; font-size: 9pt; color: #718096; margin-top: 15px; border-top: 1px solid #cbd5e0; padding-top: 10px; }
</style>
</head>
<body>

<div class="header-banner">
    <h1>Torneo a Coppie Fisse</h1>
    <p>Girone A — Classifica Finale & Statistiche</p>
</div>

<div class="card">
    <h2>Classifica Generale</h2>
    <table>
        <thead>
            <tr>
                <th>Pos</th>
                <th>Coppia / Giocatore</th>
                <th>Pt</th>
                <th>G</th>
                <th>V</th>
                <th>P</th>
                <th>PF</th>
                <th>PS</th>
            </tr>
        </thead>
        <tbody>
"""

for idx, row in df.iterrows():
    r_class = "podium-1" if idx == 1 else ("podium-2" if idx == 2 else ("podium-3" if idx == 3 else ""))
    html_content += f"""
            <tr class="{r_class}">
                <td>{idx}º</td>
                <td style="text-align: left;">{row['Giocatore']}</td>
                <td><strong>{row['Punti Classifica']}</strong></td>
                <td>{row['Partite']}</td>
                <td><span class="badge-win">{row['Vinte']}</span></td>
                <td><span class="badge-loss">{row['Perse']}</span></td>
                <td>{row['Punti Fatti']}</td>
                <td>{row['Punti Subiti']}</td>
            </tr>
    """

html_content += """
        </tbody>
    </table>
</div>

<div class="footer">Torneo a Coppie Fisse — Report Ufficiale</div>
</body>
</html>
"""

# Generazione PDF
HTML(string=html_content).write_pdf("volantino_partite_torneo.pdf")
print("PDF aggiornato con successo!")
