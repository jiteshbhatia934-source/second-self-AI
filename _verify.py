from pathlib import Path
ROOT = Path('c:/Users/jites/OneDrive/Attachments/Secondself AI Brain')

for p in [ROOT/'static'/'theme.css', ROOT/'static'/'graph_component.html']:
    s = p.read_text(encoding='utf-8')
    print(f'=== {p.name} ({len(s)} bytes) ===')
    for c, lbl in [('#ff6b6b','coral'),('#ffd93d','gold'),('#6bcf7f','emerald'),('#c780fa','violet'),('#ff6b9d','pink')]:
        present = c in s
        print(f'  {lbl:8}: {present}')
    blue = '#38bdf8' in s
    indigo = '#818cf8' in s
    print(f'  old blue #38bdf8: {blue}')
    print(f'  old indigo #818cf8: {indigo}')
    print()
