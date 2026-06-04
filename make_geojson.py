import osmnx as ox
import geopandas as gpd
import json, os

os.makedirs("data", exist_ok=True)

# Tolerance in degrees for simplification (~0.0005 deg ~= 50m).
SIMPLIFY = 0.0005

# key = id, value = (Display Name, Country, [OSM queries to merge])
islands = {

    # --- Malta ---
    "malta":         ("Malta",            "Malta", ["Malta Island, Malta"]),
    "gozo":          ("Gozo",             "Malta", ["Gozo, Malta"]),
    "comino":        ("Comino",           "Malta", ["Comino, Malta", "Cominotto, Malta"]),

    # --- Channel Islands ---
    "jersey":        ("Jersey",           "Channel Islands", ["Jersey"]),
    "guernsey":      ("Guernsey",         "Channel Islands", ["Guernsey"]),
    "alderney":      ("Alderney",         "Channel Islands", ["Alderney"]),
    "sark":          ("Sark",             "Channel Islands", ["Sark"]),
    "herm":          ("Herm",             "Channel Islands", ["Herm"]),

    # --- United Kingdom ---
    "great_britain": ("Great Britain",    "United Kingdom", ["Great Britain"]),
    "isle_of_man":   ("Isle of Man",      "United Kingdom", ["Isle of Man"]),
    "isle_of_wight": ("Isle of Wight",    "United Kingdom", ["Isle of Wight, England"]),
    "anglesey":      ("Anglesey",         "United Kingdom", ["Anglesey, Wales"]),
    "skye":          ("Isle of Skye",     "United Kingdom", ["Isle of Skye, Scotland"]),
    "lewis_harris":  ("Lewis & Harris",   "United Kingdom", ["Isle of Lewis, Scotland", "Isle of Harris, Scotland"]),
    "orkney":        ("Orkney Mainland",  "United Kingdom", ["Mainland, Orkney, Scotland"]),
    "shetland":      ("Shetland Mainland","United Kingdom", ["Mainland, Shetland, Scotland"]),

    # --- Ireland ---
    "ireland":       ("Ireland",          "Ireland", ["Ireland"]),

    # --- Italy ---
    "sicily":        ("Sicily",           "Italy", ["Sicily, Italy"]),
    "sardinia":      ("Sardinia",         "Italy", ["Sardinia, Italy"]),
    "elba":          ("Elba",             "Italy", ["Elba, Italy"]),
    "capri":         ("Capri",            "Italy", ["Capri, Italy"]),
    "ischia":        ("Ischia",           "Italy", ["Ischia, Italy"]),

    # --- France ---
    "corsica":       ("Corsica",          "France", ["Corsica, France"]),

    # --- Spain ---
    "mallorca":      ("Mallorca",         "Spain", ["Mallorca, Spain"]),
    "menorca":       ("Menorca",          "Spain", ["Menorca, Spain"]),
    "ibiza":         ("Ibiza",            "Spain", ["Ibiza, Spain"]),
    "formentera":    ("Formentera",       "Spain", ["Formentera, Spain"]),
    "tenerife":      ("Tenerife",         "Spain", ["Tenerife, Spain"]),
    "gran_canaria":  ("Gran Canaria",     "Spain", ["Gran Canaria, Spain"]),
    "lanzarote":     ("Lanzarote",        "Spain", ["Lanzarote, Spain"]),
    "fuerteventura": ("Fuerteventura",    "Spain", ["Fuerteventura, Spain"]),

    # --- Greece ---
    "crete":         ("Crete",            "Greece", ["Crete, Greece"]),
    "rhodes":        ("Rhodes",           "Greece", ["Rhodes, Greece"]),
    "corfu":         ("Corfu",            "Greece", ["Corfu, Greece"]),
    "mykonos":       ("Mykonos",          "Greece", ["Mykonos, Greece"]),
    "santorini":     ("Santorini",        "Greece", ["Santorini, Greece"]),
    "naxos":         ("Naxos",            "Greece", ["Naxos, Greece"]),
    "kos":           ("Kos",              "Greece", ["Kos, Greece"]),
    "zakynthos":     ("Zakynthos",        "Greece", ["Zakynthos, Greece"]),

    # --- Cyprus ---
    "cyprus":        ("Cyprus",           "Cyprus", ["Cyprus"]),

    # --- Portugal ---
    "madeira":       ("Madeira",          "Portugal", ["Madeira, Portugal"]),
    "sao_miguel":    ("Sao Miguel (Azores)", "Portugal", ["Sao Miguel, Azores, Portugal"]),

    # --- Denmark ---
    "bornholm":      ("Bornholm",         "Denmark", ["Bornholm, Denmark"]),

    # --- Sweden ---
    "gotland":       ("Gotland",          "Sweden", ["Gotland, Sweden"]),
    "oland":         ("Oland",            "Sweden", ["Oland, Sweden"]),

    # --- Germany ---
    "rugen":         ("Rugen",            "Germany", ["Rugen, Germany"]),

    # --- Netherlands ---
    "texel":         ("Texel",            "Netherlands", ["Texel, Netherlands"]),

    # --- Finland ---
    "aland":         ("Aland (main)",     "Finland", ["Fasta Aland, Aland"]),
}

catalog = []

for key, (display, country, queries) in islands.items():
    print("Building " + display + "...")
    try:
        geoms = []
        for q in queries:
            g = ox.geocode_to_gdf(q)
            geoms.append(g.geometry.iloc[0])

        merged = gpd.GeoDataFrame(geometry=geoms, crs=4326).dissolve()

        geom0 = merged.geometry.iloc[0]
        if geom0.geom_type == "Polygon":
            npts = len(geom0.exterior.coords)
        else:
            npts = max(len(p.exterior.coords) for p in geom0.geoms)

        if npts < 20:
            print("   ! WARNING: " + display + " returned only " + str(npts) +
                  " points (likely a bounding box). Saved anyway - check it.")

        merged["geometry"] = merged.simplify(SIMPLIFY)
        out_path = "data/" + key + ".geojson"
        merged.to_file(out_path, driver="GeoJSON")

        catalog.append({"id": key, "name": display, "country": country})
        size_kb = os.path.getsize(out_path) / 1024
        print("   saved " + out_path + "  (" + str(round(size_kb)) + " KB, " +
              str(npts) + " points)")
    except Exception as e:
        print("   ! SKIPPED " + display + ": " + str(e))

catalog.sort(key=lambda c: (c["country"], c["name"]))
with open("countries.json", "w") as f:
    json.dump(catalog, f, indent=2)

print("")
print("Done! " + str(len(catalog)) + " islands saved.")
print("Upload countries.json (and any new data files) to GitHub.")
