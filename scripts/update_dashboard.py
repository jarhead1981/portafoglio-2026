import glob
import json
import os
import re
import pandas as pd


def main():
    # Cerca file excel caricati
    files = glob.glob("data/*.xlsx") + glob.glob("*.xlsx")
    if not files:
        print("Nessun file Excel trovato.")
        return

    latest_file = max(files, key=os.path.getctime)
    print(f"Elaborazione: {latest_file}")

    # Legge il file Directa
    df_raw = pd.read_excel(latest_file)

    # Identifica se è un file Movimenti o Posizioni Patrimonio
    raw_str = df_raw.to_string()

    if "movimenti" in raw_str.lower() or "Data operazione" in raw_str:
        print("Rilevato file MOVIMENTI")
        df = pd.read_excel(latest_file, skiprows=9)
        df.columns = [str(c).strip() for c in df.columns]

        coupons = []
        for _, row in df.iterrows():
            tipo = str(row.get("Tipo operazione", "")).strip()
            if "Cedola" in tipo or "Coupon" in tipo or "Provento" in tipo:
                coupons.append(
                    {
                        "data": str(row.get("Data operazione", "")).strip(),
                        "tipo": tipo,
                        "isin": str(row.get("Isin", "")).strip(),
                        "descrizione": str(row.get("Descrizione", "")).strip(),
                        "importo": float(row.get("Importo euro", 0)),
                    }
                )

        update_html_coupons(coupons)

    else:
        print("Rilevato file PATRIMONIO")
        df = pd.read_excel(latest_file)
        df.columns = [str(c).strip() for c in df.columns]

        cash = 0.0
        positions = []

        for _, row in df.iterrows():
            descr = str(row.get("Descrizione", "")).strip()
            isin = str(row.get("ISIN", "")).strip()

            if "LIQUIDITA" in descr.upper() or "DISPONIBILE" in descr.upper():
                try:
                    cash = float(row.get("Controvalore Euro", 0))
                except:
                    pass
                continue

            if isin and isin.upper() != "NAN" and len(isin) == 12:
                try:
                    qty = float(row.get("Quantità", 0))
                    pmc = float(row.get("Prezzo", 0))
                    price = float(row.get("Prezzo Mercato", pmc))
                    val = float(row.get("Controvalore Euro", qty * price))
                    positions.append(
                        {
                            "isin": isin,
                            "description": descr,
                            "quantity": qty,
                            "pmc": pmc,
                            "price": price,
                            "value": val,
                        }
                    )
                except:
                    pass

        update_html_portfolio(cash, positions)


def update_html_coupons(coupons):
    if not os.path.exists("index.html"):
        return
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    data_json = json.dumps(coupons, indent=2, ensure_ascii=False)
    content = re.sub(
        r"const storicaCedoleData = \[.*?\];",
        f"const storicaCedoleData = {data_json};",
        content,
        flags=re.DOTALL,
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("HTML aggiornato con le cedole.")


def update_html_portfolio(cash, positions):
    if not os.path.exists("index.html"):
        return
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    pos_json = json.dumps(positions, indent=2, ensure_ascii=False)
    content = re.sub(
        r"const directaPositions = \[.*?\];",
        f"const directaPositions = {pos_json};",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"const directaCash = [\d\.]+;", f"const directaCash = {cash};", content
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("HTML aggiornato con patrimonio e posizioni.")


if __name__ == "__main__":
    main()
