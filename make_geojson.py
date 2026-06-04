import osmnx as ox
import geopandas as gpd
import json, os

os.makedirs("data", exist_ok=True)

# Tolerance in degrees for simplification (~0.0005 deg ~= 50m).
# Bigger number = lighter file but less coastline detail.
SIMPLIFY = 0.0005

# key = filename/id, value = (Display Name, [OSM queries to merge])
islands = {

    # --- Malta ---
    "malta":         ("Malta",          ["Malta Island, Malta"]),
    "gozo":          ("Gozo",           ["Gozo, Malta"]),
    "comino":        ("Comino",         ["Comino, Malta", "Cominotto, Malta"]),

    # --- Channel Islands ---
    "jersey":        ("Jersey",         ["Jersey"]),
    "guernsey":      ("Guernsey",       ["Guernsey"]),
    "alderney":      ("Alderney",       ["Alderney"]),
    "sark":          ("Sark",           ["Sark"]),
    "herm":          ("Herm",           ["Herm"]),

    # --- British Isles ---
    "great_britain": ("Great Britain",  ["Great Britain"]),
    "ireland":       ("Ireland",        ["Ireland"]),
    "isle_of_man":   ("Isle of Man",    ["Isle of Man"]),
    "isle_of_wight": ("Isle of Wight",  ["Isle of Wight, England"]),
    "anglesey":      ("Anglesey",       ["Anglesey, Wales"]),
    "skye":          ("Isle of Skye",   ["Isle of Skye, Scotland"]),
    "lewis_harris":  ("Lewis & Harris", ["Isle of Lewis, Scotland", "Isle of Harris, Scotland"]),
    "orkney":        ("Orkney Mainland",   ["Mainland, Orkney, Scotland"]),
    "shetland":      ("Shetland Mainland", ["Mainland, Shetland, Scotland"]),

    # --- Western Mediterranean (Italy / France / Spain) ---
    "sicily":        ("Sicily",         ["Sicily, Italy"]),
    "sardinia":      ("Sardinia",       ["Sardinia, Italy"]),
    "corsica":       ("Corsica",        ["Corsica, France"]),
    "elba":          ("Elba",           ["Elba, Italy"]),
    "capri":         ("Capri",          ["Capri, Italy"]),
    "ischia":        ("Ischia",         ["Ischia, Italy"]),
    "mallorca":      ("Mallorca",       ["Mallorca, Spain"]),
    "menorca":       ("Menorca",        ["Menorca, Spain"]),
    "ibiza":         ("Ibiza",          ["Ibiza, Spain"]),
    "formentera":    ("Formentera",     ["Formentera, Spain"]),

    # --- Greece / Aegean / Ionian ---
    "crete":         ("Crete",          ["Crete, Greece"]),
    "rhodes":        ("Rhodes",         ["Rhodes, Greece"]),
    "corfu":         ("Corfu",          ["Corfu, Greece"]),
    "mykonos":       ("Mykonos",        ["Mykonos, Greece"]),
    "santorini":     ("Santorini",      ["Santorini, Greece"]),
    "naxos":         ("Naxos",          ["Naxos, Greece"]),
    "kos":           ("Kos",            ["Kos, Greece"]),
    "zakynthos":     ("Zakynthos",      ["Zakynthos, Greece"]),

    # --- Cyprus ---
    "cyprus":        ("Cyprus",         ["Cyprus"]),

    # --- Atlantic (Portugal / Spain) ---
    "madeira":       ("Madeira",        ["Madeira, Portugal"]),
    "sao_miguel":    ("Sao Miguel (Azores)", ["Sao Miguel, Azores, Portugal"]),
    "tenerife":      ("Tenerife",       ["Tenerife, Spain"]),
    "gran_canaria":  ("Gran Canaria",   ["Gran Canaria, Spain"]),
    "lanzarote":     ("Lanzarote",      ["Lanzarote, Spain"]),
    "fuerteventura": ("Fuerteventura",  ["Fuerteventura, Spain"]),

    # --- Northern Europe ---
    "bornholm":      ("Bornholm",       ["Bornholm, Denmark"]),
    "gotland":       ("Gotland",        ["Gotland, Sweden"]),
    "oland":         ("Oland",          ["Oland, Sweden"]),
    "rugen":         ("Rugen",          ["Rugen, Germany"]),
    "texel":         ("Texel",          ["Texel, Netherlands"]),
    "aland":         ("Aland (main)",   ["Fasta Aland, Aland"]),
}

catalog = []

for key, (display, queries) in islands.items():
    print("Building " + display + "...")
    try:
        # fetch each query and combine into one shape
        geoms = []
        for q in queries:
            g = ox.geocode_to_gdf(q)
            geoms.append(g.geometry.iloc[0])

        merged = gpd.GeoDataFrame(geometry=geoms, crs=4326).dissolve()

        # sanity check: a real coastline has many points; a box has ~5
        geom0 = merged.geometry.iloc[0]
        if geom0.geom_type == "Polygon":
            npts = len(geom0.exterior.coords)
        else:
            npts = max(len(p.exterior.coords) for p in geom0.geoms)

        if npts < 20:
            print("   ! WARNING: " + display + " returned only " + str(npts) +
                  " points (likely a bounding box, not real coastline). Saved anyway - check it.")

        # simplify to keep the file size sane
        merged["geometry"] = merged.simplify(SIMPLIFY)

        out_path = "data/" + key + ".geojson"
        merged.to_file(out_path, driver="GeoJSON")

        catalog.append({"id": key, "name": display})
        size_kb = os.path.getsize(out_path) / 1024
        print("   saved " + out_path + "  (" + str(round(size_kb)) + " KB, " +
              str(npts) + " points)")

    except Exception as e:
        print("   ! SKIPPED " + display + ": " + str(e))

# write the dropdown list, sorted alphabetically by display name
catalog.sort(key=lambda c: c["name"])
with open("countries.json", "w") as f:
    json.dump(catalog, f, indent=2)

print("")
print("Done! " + str(len(catalog)) + " islands saved.")
print("Upload the 'data' folder and countries.json to GitHub.")
