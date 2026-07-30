# Tilasto-analyysit

Shiny for Python -sovellus korkeakoulujen hakijoiden tilastojen analysointiin ja visualisointiin.

## Rakenne

```
data/{year}/          # Raakadata (Excel-tiedostot → CSV)
analysis/{year}/      # Esikäsitellyt JSON-tulokset
xlsx_to_csv.py        # Muuntaa Excel-hakijatiedostot CSV:ksi
preanalysis.py        # Parsii CSV:t ja laskee tilastot → JSON
analysis.py           # Laskee lisätilastot JSON-tiedostoihin
app.py                # Shiny-sovellus
```

## Käyttö

### 1. Asenna riippuvuudet

```bash
pip install -r requirements.txt
```

### 2. Valmistele data

```bash
# Muunna Excel-tiedostot CSV:ksi
python xlsx_to_csv.py

# Esikäsittele data (luo analysis/-kansion JSON-tiedostot)
python preanalysis.py

# Laske lisätilastot
python analysis.py
```

### 3. Käynnistä sovellus

```bash
python -m shiny run app.py --reload
```

`--reload` käynnistää palvelimen uudelleen automaattisesti koodimuutosten yhteydessä.
