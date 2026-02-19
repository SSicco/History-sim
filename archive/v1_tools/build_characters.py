#!/usr/bin/env python3
"""
Build characters.json from chapter data + AI-verified alias mapping.

Reads all chapter_02_*.json files, extracts characters from encounter
participant lists, canonicalises them via the ALIAS_MAP, and outputs the
full character schema defined in CONVENTIONS.md Section 2.

Many characters appear under different IDs across chapters (e.g. Queen Lucia
is tagged as "lucia", "lucia_deste", "lucia_visconti", "lucia_of_castile"
etc.). This script maps all variant IDs to a canonical character.

Usage:
    python3 tools/build_characters.py                  # preview character list
    python3 tools/build_characters.py --write           # write characters.json
    python3 tools/build_characters.py --query lucia     # find events across all aliases
    python3 tools/build_characters.py --query lucia -v  # verbose (full summaries)
    python3 tools/build_characters.py --aliases         # show alias mapping
    python3 tools/build_characters.py --orphans         # show IDs not in any alias group
"""

import json
import glob
import os
import sys
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "resources", "data")
EVENTS_PATH = os.path.join(DATA_DIR, "starter_events.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "characters.json")

# ---------------------------------------------------------------------------
# ALIAS MAP
#
# Maps canonical_id -> list of ALL event-data IDs that refer to this character.
# Built by cross-referencing CHARACTER_DATABASE.md, chapter recaps, and
# narrative context.  Each grouping has been verified.
#
# Characters with only one ID still get an entry (aliases = [that_id]).
# ---------------------------------------------------------------------------

ALIAS_MAP = {
    # === ROYAL FAMILY ===

    "juan_ii": {
        "name": "King Juan II of Castile",
        "aliases": ["juan_ii"],
        "category": ["royal_family"],
    },
    "lucia_deste": {
        "name": "Queen Lucia d'Este",
        "aliases": [
            "lucia",                # 108 events — default short form
            "lucia_d_este",         # 5 — apostrophe variant
            "lucia_de_este",        # 1 — Spanish-style particle
            "lucia_deste",          # 8 — no apostrophe
            "lucia_este",           # 1 — abbreviated
            "lucia_visconti",       # 9 — Visconti family connection (verified queen)
            "lucia_of_castile",     # 2 — title after marriage
            "lucia_of_ferrara",     # 1 — origin city
            "lucia_de_ferrara",     # 1 — origin city (Spanish particle)
            "lucia_ferrarese",      # 2 — demonym
            "lucia_queen",          # 1 — title suffix
            "queen_lucia",          # 1 — title prefix
            "lucia_caracciolo",     # 2 — tagged from Palazzo Caracciolo in Naples
            "lucia_medici",         # 1 — tagged from Medici intelligence task
        ],
        "category": ["royal_family", "italian"],
    },
    "catalina": {
        "name": "Princess Catalina of Castile",
        "aliases": [
            "catalina",             # 103
            "catalina_de_trastamara",  # 1
            "catalina_of_castile",     # 5
            "catalina_of_trastamara",  # 1
            "catalina_trastamara",     # 3
        ],
        "category": ["royal_family"],
    },
    "fernando": {
        "name": "Prince Fernando of Castile",
        "aliases": ["fernando", "prince_fernando"],
        "category": ["royal_family"],
    },
    "bianca": {
        "name": "Princess Bianca of Castile",
        "aliases": ["bianca"],
        "category": ["royal_family"],
    },
    "isabel_of_portugal": {
        "name": "Queen Isabel of Portugal",
        "aliases": ["isabel", "isabel_of_portugal"],
        "category": ["royal_family"],
    },
    "maria_of_aragon": {
        "name": "Doña María de Trastámara",
        "aliases": [
            "maria_of_aragon",     # 13 — as Queen of Aragon
            "maria_of_castile",    # 7  — born Castilian princess
            "maria_de_castilla",   # 1  — Spanish-language variant
            "maria",               # 7  — short form (primarily this character)
            "queen_maria",         # 1  — title
            "dona_maria",          # 1  — formal address
        ],
        "category": ["royal_family", "iberian_royalty"],
    },

    # === ROYAL COURT & ADVISORS ===

    "alvaro_de_luna": {
        "name": "Álvaro de Luna",
        "aliases": ["alvaro_de_luna"],
        "category": ["court_advisor"],
    },
    "fernan_alonso_de_robles": {
        "name": "Fernán Alonso de Robles",
        "aliases": [
            "fernan_alonso_de_robles",  # 75
            "ferran_alonso_de_robles",  # 1 — Catalan spelling
            "captain_fernan",            # 4 — military context (verified same)
        ],
        "category": ["court_advisor", "military"],
    },
    "fray_hernando": {
        "name": "Fray Hernando de Talavera",
        "aliases": [
            "fray_hernando",              # 63
            "fray_hernando_de_talavera",  # 3
            "hernando_de_talavera",       # 2
            "father_hernando",            # 1
        ],
        "category": ["court_advisor", "religious"],
    },
    "diego_de_daza": {
        "name": "Diego de Daza",
        "aliases": ["diego_de_daza"],
        "category": ["court_advisor"],
    },
    "dona_beatriz": {
        "name": "Doña Beatriz",
        "aliases": [
            "dona_beatriz",       # 19
            "beatriz",            # 9 — short form (governess context)
            "beatriz_portugal",   # 1 — Portuguese noblewoman
        ],
        "category": ["household"],
    },
    "demetrios_komnenos": {
        "name": "Demetrios Komnenos",
        "aliases": ["demetrios_komnenos"],
        "category": ["household", "byzantine"],
    },

    # === IBERIAN ROYALTY ===

    "alfonso_v": {
        "name": "Alfonso V of Aragon",
        "aliases": [
            "alfonso_v",             # 18
            "alfonso_v_aragon",      # 1
            "alfonso_v_of_aragon",   # 1
            "alfonso",               # 2 — short form
        ],
        "category": ["iberian_royalty"],
    },
    "leonor_of_portugal": {
        "name": "Queen Leonor of Portugal",
        "aliases": [
            "leonor_of_portugal",       # 3
            "queen_leonor",             # 3
            "queen_leonor_of_portugal", # 1
            "leonor",                   # 4 — grandmother at Isabel's death
            "dona_leonor",              # 2 — Constantinople journey companion
        ],
        "category": ["iberian_royalty"],
    },
    "leonor_de_almeida": {
        "name": "Leonor de Almeida",
        "aliases": ["leonor_de_almeida", "dona_leonor_de_almeida"],
        "category": ["nobility"],
    },

    # === PAPAL COURT ===

    "pope_eugenius_iv": {
        "name": "Pope Eugenius IV",
        "aliases": ["pope_eugenius_iv", "eugenius_iv"],
        "category": ["papal_court"],
    },
    "tommaso_parentucelli": {
        "name": "Tommaso Parentucelli",
        "aliases": ["tommaso_parentucelli", "parentucelli"],
        "category": ["papal_court"],
    },
    "cardinal_cesarini": {
        "name": "Cardinal Giuliano Cesarini",
        "aliases": ["cardinal_cesarini", "giuliano_cesarini"],
        "category": ["papal_court"],
    },
    "cardinal_orsini": {
        "name": "Cardinal Giordano Orsini",
        "aliases": ["cardinal_orsini", "giordano_orsini"],
        "category": ["papal_court"],
    },
    "cardinal_rochetaillee": {
        "name": "Cardinal Jean de Rochetaillée",
        "aliases": [
            "cardinal_rochetaillee",
            "jean_de_rochetaillee",
            "cardinal_jean_de_rochetaillee",
            "rochetaillee",
        ],
        "category": ["papal_court"],
    },
    "cardinal_capranica": {
        "name": "Cardinal Capranica",
        "aliases": ["cardinal_capranica"],
        "category": ["papal_court"],
    },
    "cardinal_albergati": {
        "name": "Cardinal Albergati",
        "aliases": ["cardinal_albergati"],
        "category": ["papal_court"],
    },
    "cardinal_colonna": {
        "name": "Cardinal Colonna",
        "aliases": ["cardinal_colonna"],
        "category": ["papal_court"],
    },
    "cardinal_condulmer": {
        "name": "Cardinal Condulmer",
        "aliases": ["cardinal_condulmer"],
        "category": ["papal_court"],
    },
    "louis_aleman": {
        "name": "Louis Aléman",
        "aliases": ["louis_aleman"],
        "category": ["papal_court"],
    },
    "canon_della_rovere": {
        "name": "Canon Giuliano della Rovere",
        "aliases": ["canon_della_rovere", "canon_giuliano_della_rovere"],
        "category": ["papal_court"],
    },

    # === BYZANTINE ===

    "john_viii_palaiologos": {
        "name": "Emperor John VIII Palaiologos",
        "aliases": [
            "john_viii",              # 19
            "john_viii_palaiologos",  # 15
            "john_viii_paleologus",   # 1
            "emperor_john_viii",      # 3
        ],
        "category": ["byzantine"],
    },
    "constantine_xi": {
        "name": "Emperor Constantine XI",
        "aliases": ["constantine_xi", "emperor_constantine_xi"],
        "category": ["byzantine"],
    },
    "george_sphrantzes": {
        "name": "George Sphrantzes",
        "aliases": ["sphrantzes", "george_sphrantzes", "georgios_sphrantzes"],
        "category": ["byzantine"],
    },
    "loukas_notaras": {
        "name": "Loukas Notaras",
        "aliases": ["loukas_notaras", "lucas_notaras", "notaras"],
        "category": ["byzantine"],
    },
    "patriarch_joseph_ii": {
        "name": "Patriarch Joseph II",
        "aliases": ["patriarch_joseph_ii", "patriarch_gregory"],
        "category": ["byzantine", "religious"],
    },
    "bessarion": {
        "name": "Bessarion of Nicaea",
        "aliases": [
            "bessarion",
            "bessarion_of_nicaea",
            "cardinal_bessarion",
            "metropolitan_bessarion",
        ],
        "category": ["byzantine", "religious"],
    },
    "gennadios_scholarios": {
        "name": "Gennadios Scholarios",
        "aliases": [
            "gennadios",
            "gennadios_scholarios",
            "father_gennadios",
            "patriarch_gennadios",
        ],
        "category": ["byzantine", "religious"],
    },
    "isidore_of_kiev": {
        "name": "Isidore of Kiev",
        "aliases": ["isidore", "isidore_of_kiev", "metropolitan_isidore"],
        "category": ["byzantine", "religious"],
    },

    # --- Byzantine noble families ---

    "kantakouzenos": {
        "name": "Kantakouzenos (family head)",
        "aliases": ["kantakouzenos"],
        "category": ["byzantine"],
    },
    "theodoros_kantakouzenos": {
        "name": "Theodoros Kantakouzenos",
        "aliases": ["theodoros_kantakouzenos"],
        "category": ["byzantine"],
    },
    "raoul_kantakouzenos": {
        "name": "Raoul Kantakouzenos",
        "aliases": ["raoul_kantakouzenos"],
        "category": ["byzantine"],
    },
    "constantine_kantakouzenos": {
        "name": "Constantine Kantakouzenos",
        "aliases": ["constantine_kantakouzenos", "konstantine_kantakouzenos"],
        "category": ["byzantine"],
    },
    "ioannes_kantakouzenos": {
        "name": "Ioannes Kantakouzenos",
        "aliases": ["ioannes_kantakouzenos"],
        "category": ["byzantine"],
    },
    "george_kantakouzenos": {
        "name": "George Kantakouzenos",
        "aliases": ["george_kantakouzenos"],
        "category": ["byzantine"],
    },
    "doukas_patriarch": {
        "name": "Doukas Patriarch",
        "aliases": ["doukas_patriarch", "house_doukas_patriarch"],
        "category": ["byzantine"],
    },
    "niketas_doukas": {
        "name": "Niketas Doukas",
        "aliases": ["niketas_doukas"],
        "category": ["byzantine"],
    },
    "constantine_doukas": {
        "name": "Constantine Doukas",
        "aliases": ["constantine_doukas"],
        "category": ["byzantine"],
    },
    "asanes_patriarch": {
        "name": "Asanes Patriarch",
        "aliases": ["asanes_patriarch", "asanes"],
        "category": ["byzantine"],
    },
    "philanthropenos": {
        "name": "Philanthropenos (family head)",
        "aliases": ["philanthropenos", "philanthropenos_patriarch"],
        "category": ["byzantine"],
    },
    "alexios_philanthropenos": {
        "name": "Alexios Philanthropenos",
        "aliases": ["alexios_philanthropenos"],
        "category": ["byzantine"],
    },
    "nikephoros_philanthropenos": {
        "name": "Nikephoros Philanthropenos",
        "aliases": ["nikephoros_philanthropenos"],
        "category": ["byzantine"],
    },
    "demetrios_philanthropenos": {
        "name": "Demetrios Philanthropenos",
        "aliases": ["demetrios_philanthropenos"],
        "category": ["byzantine"],
    },
    "katakolon_philanthropenos": {
        "name": "Katakolon Philanthropenos",
        "aliases": ["katakolon_philanthropenos"],
        "category": ["byzantine"],
    },
    "laskaris": {
        "name": "Laskaris (family representative)",
        "aliases": ["laskaris", "laskaris_representative"],
        "category": ["byzantine"],
    },
    "laskaris_uncle": {
        "name": "Laskaris (uncle)",
        "aliases": ["laskaris_uncle"],
        "category": ["byzantine"],
    },
    "young_laskaris": {
        "name": "Young Laskaris",
        "aliases": ["young_laskaris"],
        "category": ["byzantine"],
    },
    "bryennios": {
        "name": "Bryennios",
        "aliases": ["bryennios", "lord_bryennios"],
        "category": ["byzantine"],
    },
    "bryennios_judge": {
        "name": "Bryennios (judge)",
        "aliases": ["bryennios_judge"],
        "category": ["byzantine"],
    },
    "bryennios_observer": {
        "name": "Bryennios (observer)",
        "aliases": ["bryennios_observer"],
        "category": ["byzantine"],
    },
    "bryennios_patriarch": {
        "name": "Bryennios (patriarch)",
        "aliases": ["bryennios_patriarch"],
        "category": ["byzantine"],
    },
    "bryennios_scholar": {
        "name": "Bryennios (scholar)",
        "aliases": ["bryennios_scholar"],
        "category": ["byzantine"],
    },
    "bryennios_uncle": {
        "name": "Bryennios (uncle)",
        "aliases": ["bryennios_uncle"],
        "category": ["byzantine"],
    },
    "melissenos_cousin": {
        "name": "Melissenos (cousin)",
        "aliases": ["melissenos_cousin", "melissenos"],
        "category": ["byzantine"],
    },
    "chrysoloras": {
        "name": "Chrysoloras",
        "aliases": ["chrysoloras"],
        "category": ["byzantine"],
    },
    "demetrios_chrysoloras": {
        "name": "Demetrios Chrysoloras",
        "aliases": ["demetrios_chrysoloras"],
        "category": ["byzantine"],
    },
    "manuel_chrysoloras": {
        "name": "Manuel Chrysoloras",
        "aliases": ["manuel_chrysoloras"],
        "category": ["byzantine"],
    },
    "kourtikios": {
        "name": "Kourtikios",
        "aliases": ["kourtikios"],
        "category": ["byzantine"],
    },
    "eudokia": {
        "name": "Eudokia",
        "aliases": ["eudokia"],
        "category": ["byzantine"],
    },
    "konstantinos": {
        "name": "Konstantinos",
        "aliases": ["konstantinos"],
        "category": ["byzantine"],
    },

    # --- Constantinople common people (Twelve Apostles) ---

    "theodoros": {
        "name": "Theodoros (wall worker)",
        "aliases": ["theodoros"],
        "category": ["byzantine"],
    },
    "anna": {
        "name": "Anna (merchant's wife)",
        "aliases": ["anna"],
        "category": ["byzantine"],
    },
    "anna_kantakouzenos": {
        "name": "Anna Kantakouzenos",
        "aliases": ["anna_kantakouzenos"],
        "category": ["byzantine"],
    },
    "anna_paleologina": {
        "name": "Anna Paleologina",
        "aliases": ["anna_paleologina"],
        "category": ["byzantine"],
    },
    "demetrios": {
        "name": "Demetrios (young worker)",
        "aliases": ["demetrios"],
        "category": ["byzantine"],
    },
    "demetrios_kantakouzenos": {
        "name": "Demetrios Kantakouzenos",
        "aliases": ["demetrios_kantakouzenos"],
        "category": ["byzantine"],
    },
    "nikephoros": {
        "name": "Nikephoros",
        "aliases": ["nikephoros"],
        "category": ["byzantine"],
    },
    "theodoros_metochites": {
        "name": "Theodoros Metochites",
        "aliases": ["theodoros_metochites"],
        "category": ["byzantine"],
    },
    "theodoros_kataphraktis": {
        "name": "Theodoros Kataphraktis",
        "aliases": ["theodoros_kataphraktis"],
        "category": ["byzantine"],
    },
    "stavros": {
        "name": "Stavros",
        "aliases": ["stavros"],
        "category": ["byzantine"],
    },
    "wall_worker": {
        "name": "Wall worker",
        "aliases": ["wall_worker"],
        "category": ["byzantine"],
    },
    "young_worker": {
        "name": "Young worker",
        "aliases": ["young_worker"],
        "category": ["byzantine"],
    },

    # === OTTOMAN ===

    "murad_ii": {
        "name": "Sultan Murad II",
        "aliases": ["murad_ii"],
        "category": ["ottoman"],
    },
    "hamza_bey": {
        "name": "Hamza Bey",
        "aliases": ["hamza_bey"],
        "category": ["ottoman"],
    },

    # === ITALIAN STATES ===

    "marco_contarini": {
        "name": "Marco Contarini",
        "aliases": ["marco_contarini", "contarini"],
        "category": ["italian"],
    },
    "francesco_contarini": {
        "name": "Francesco Contarini",
        "aliases": ["francesco_contarini", "francisco_contarini"],
        "category": ["italian"],
    },
    "antonio_contarini": {
        "name": "Antonio Contarini",
        "aliases": ["antonio_contarini"],
        "category": ["italian"],
    },
    "lomellini": {
        "name": "Lomellini (Genoese representative)",
        "aliases": ["lomellini"],
        "category": ["italian"],
    },
    "raffaele_lomellini": {
        "name": "Raffaele Lomellini",
        "aliases": ["raffaele_lomellini"],
        "category": ["italian"],
    },
    "battista_lomellini": {
        "name": "Battista Lomellini",
        "aliases": ["battista_lomellini"],
        "category": ["italian"],
    },
    "giovanni_lomellini": {
        "name": "Giovanni Lomellini",
        "aliases": ["giovanni_lomellini"],
        "category": ["italian"],
    },
    "paolo_lomellini": {
        "name": "Paolo Lomellini",
        "aliases": ["paolo_lomellini"],
        "category": ["italian"],
    },
    "benedetto_fregoso": {
        "name": "Benedetto Fregoso",
        "aliases": ["benedetto_fregoso", "fregoso"],
        "category": ["italian"],
    },
    "tommaso_di_campofregoso": {
        "name": "Tommaso di Campofregoso",
        "aliases": ["tommaso_di_campofregoso"],
        "category": ["italian"],
    },
    "giovanni_rossi": {
        "name": "Giovanni Rossi",
        "aliases": ["giovanni_rossi"],
        "category": ["italian"],
    },
    "giovanni_adorno": {
        "name": "Giovanni Adorno",
        "aliases": ["giovanni_adorno"],
        "category": ["italian"],
    },
    "jacopo_de_bardi": {
        "name": "Jacopo de' Bardi",
        "aliases": ["jacopo_de_bardi"],
        "category": ["italian"],
    },
    "niccolo_deste": {
        "name": "Marquess Niccolò III d'Este",
        "aliases": ["niccolo_deste"],
        "category": ["italian"],
    },
    "paolo_grimaldi": {
        "name": "Paolo Grimaldi",
        "aliases": ["paolo_grimaldi"],
        "category": ["italian"],
    },
    "lorenzo_della_torre": {
        "name": "Lorenzo della Torre",
        "aliases": ["lorenzo_della_torre"],
        "category": ["italian"],
    },
    "alessandro_duodo": {
        "name": "Alessandro Duodo",
        "aliases": ["alessandro_duodo"],
        "category": ["italian"],
    },
    "alvise_diedo": {
        "name": "Alvise Diedo",
        "aliases": ["alvise_diedo"],
        "category": ["italian"],
    },

    # --- Italian ladies-in-waiting ---

    "donna_francesca": {
        "name": "Donna Francesca",
        "aliases": ["donna_francesca", "francesca"],
        "category": ["household", "italian"],
    },
    "francesca_de_roberti": {
        "name": "Francesca de' Roberti",
        "aliases": ["francesca_de_roberti"],
        "category": ["italian"],
    },
    "francesca_strozzi": {
        "name": "Francesca Strozzi",
        "aliases": ["francesca_strozzi"],
        "category": ["italian"],
    },
    "isabella_strozzi": {
        "name": "Isabella Strozzi",
        "aliases": ["donna_isabella_strozzi", "isabella_strozzi", "donna_isabella"],
        "category": ["italian"],
    },
    "giulia_bentivoglio": {
        "name": "Giulia Bentivoglio",
        "aliases": ["donna_giulia_bentivoglio", "giulia_bentivoglio"],
        "category": ["italian"],
    },
    "beatrice_d_este": {
        "name": "Beatrice d'Este",
        "aliases": ["beatrice_d_este", "donna_beatrice_d_este"],
        "category": ["italian"],
    },
    "alessandra_gonzaga": {
        "name": "Alessandra Gonzaga",
        "aliases": ["alessandra_gonzaga", "donna_alessandra_gonzaga"],
        "category": ["italian"],
    },
    "caterina_de_medici": {
        "name": "Caterina de' Medici",
        "aliases": ["caterina_de_medici", "donna_caterina"],
        "category": ["italian"],
    },

    # === MILITARY ===

    "bernat_de_centelles": {
        "name": "Bernat de Centelles",
        "aliases": ["bernat_de_centelles", "don_bernat"],
        "category": ["military", "nobility"],
    },
    "count_of_pallars": {
        "name": "Count of Pallars (Hug Roger III)",
        "aliases": ["count_of_pallars", "count_pallars", "pallars", "hug_roger_iii"],
        "category": ["military", "nobility"],
    },
    "don_guillem_de_vic": {
        "name": "Don Guillem de Vic",
        "aliases": ["don_guillem", "don_guillem_de_vic", "guillem_de_vic"],
        "category": ["military", "nobility"],
    },
    "ramon_de_perellos": {
        "name": "Don Ramón de Perellós",
        "aliases": [
            "don_ramon",
            "don_ramon_de_perellos",
            "ramon_de_perellos",
            "ramon_de_perrellos",  # typo variant
        ],
        "category": ["military", "nobility"],
    },
    "juan_de_sotomayor": {
        "name": "Don Juan de Sotomayor",
        "aliases": ["juan_de_sotomayor", "don_juan_de_sotomayor", "juan_sotomayor"],
        "category": ["military"],
    },
    "inigo_lopez_de_mendoza": {
        "name": "Íñigo López de Mendoza",
        "aliases": [
            "inigo_lopez_de_mendoza",
            "inigo_de_mendoza",
            "don_inigo",
            "don_inigo_lopez_de_mendoza",
        ],
        "category": ["military", "nobility"],
    },
    "luis_de_guzman": {
        "name": "Don Luis de Guzmán",
        "aliases": ["luis_de_guzman", "don_luis_de_guzman", "luis_gonzalez_de_guzman"],
        "category": ["military", "nobility"],
    },
    "pedro_gonzalez_de_padilla": {
        "name": "Don Pedro González de Padilla",
        "aliases": ["pedro_gonzalez_de_padilla", "don_pedro_gonzalez_de_padilla"],
        "category": ["military", "nobility"],
    },
    "berenguer_de_bardaxi": {
        "name": "Don Berenguer de Bardaxí",
        "aliases": ["berenguer_de_bardaxi", "don_berenguer_de_bardaxi"],
        "category": ["military", "nobility"],
    },
    "viscount_of_rocaberti": {
        "name": "Viscount of Rocabertí",
        "aliases": ["viscount_of_rocaberti", "rocaberti"],
        "category": ["military", "nobility"],
    },
    "marco_tornesi": {
        "name": "Marco Tornesi",
        "aliases": ["marco_tornesi"],
        "category": ["military"],
    },
    "andrea_vescovi": {
        "name": "Andrea Vescovi",
        "aliases": ["andrea_vescovi"],
        "category": ["military"],
    },
    "thomas_beaumont": {
        "name": "Sir Thomas Beaumont",
        "aliases": ["thomas_beaumont", "sir_thomas"],
        "category": ["military"],
    },
    "thomas_woodville": {
        "name": "Thomas Woodville",
        "aliases": ["thomas_woodville"],
        "category": ["military"],
    },
    "morales": {
        "name": "Captain Morales",
        "aliases": ["morales", "captain_morales", "francisco_morales"],
        "category": ["military"],
    },
    "sebastian_de_morales": {
        "name": "Sebastián de Morales",
        "aliases": ["sebastian_de_morales"],
        "category": ["military"],
    },
    "captain_vargas": {
        "name": "Captain Vargas",
        "aliases": ["captain_vargas"],
        "category": ["military"],
    },
    "captain_torrelles": {
        "name": "Captain Torrelles",
        "aliases": ["captain_torrelles"],
        "category": ["military"],
    },
    "commander_cervantes": {
        "name": "Commander Cervantes",
        "aliases": ["commander_cervantes"],
        "category": ["military"],
    },
    "commander_mendoza": {
        "name": "Commander Mendoza",
        "aliases": ["commander_mendoza"],
        "category": ["military"],
    },
    "commander_orozco": {
        "name": "Commander Orozco",
        "aliases": ["commander_orozco"],
        "category": ["military"],
    },
    "vasco_de_orozco": {
        "name": "Vasco de Orozco",
        "aliases": ["vasco_de_orozco"],
        "category": ["military"],
    },
    "rodrigo_de_cervantes": {
        "name": "Rodrigo de Cervantes",
        "aliases": ["rodrigo_de_cervantes"],
        "category": ["military"],
    },
    "rodrigo_ibanez": {
        "name": "Rodrigo Ibáñez",
        "aliases": ["rodrigo_ibanez"],
        "category": ["military"],
    },
    "gaspar_de_vega": {
        "name": "Gaspar de Vega",
        "aliases": ["gaspar_de_vega"],
        "category": ["military"],
    },
    "luis_de_cordoba": {
        "name": "Luis de Córdoba",
        "aliases": ["luis_de_cordoba"],
        "category": ["military"],
    },
    "martin_de_soria": {
        "name": "Martín de Soria",
        "aliases": ["martin_de_soria"],
        "category": ["military"],
    },
    "francisco_ruiz": {
        "name": "Francisco Ruiz",
        "aliases": ["francisco_ruiz"],
        "category": ["military"],
    },
    "cristobal_medina": {
        "name": "Cristóbal Medina",
        "aliases": ["cristobal_medina"],
        "category": ["military"],
    },
    "alonso_pardo": {
        "name": "Alonso Pardo",
        "aliases": ["alonso_pardo"],
        "category": ["military"],
    },
    "admiral_berenguer": {
        "name": "Admiral Berenguer",
        "aliases": ["admiral_berenguer"],
        "category": ["military"],
    },
    "don_fadrique": {
        "name": "Don Fadrique",
        "aliases": ["don_fadrique"],
        "category": ["military", "nobility"],
    },
    "jean_de_lastic": {
        "name": "Jean de Lastic",
        "aliases": ["jean_de_lastic"],
        "category": ["military", "religious"],
    },

    # === NOBILITY ===

    "pedro_manrique": {
        "name": "Pedro Manrique",
        "aliases": ["pedro_manrique"],
        "category": ["nobility"],
    },
    "pedro_giron": {
        "name": "Pedro Girón",
        "aliases": ["pedro_giron", "pedro_girón"],
        "category": ["nobility"],
    },
    "pedro_fernandez_de_velasco": {
        "name": "Pedro Fernández de Velasco",
        "aliases": ["pedro_fernandez_de_velasco"],
        "category": ["nobility"],
    },
    "pedro_carrillo": {
        "name": "Pedro Carrillo",
        "aliases": ["pedro_carrillo"],
        "category": ["nobility"],
    },
    "garcia_lopez_de_padilla": {
        "name": "García López de Padilla",
        "aliases": ["garcia_lopez_de_padilla"],
        "category": ["nobility"],
    },
    "diego_hurtado_de_mendoza": {
        "name": "Diego Hurtado de Mendoza",
        "aliases": ["diego_hurtado_de_mendoza"],
        "category": ["nobility"],
    },
    "diego_de_anaya": {
        "name": "Diego de Anaya",
        "aliases": ["diego_de_anaya"],
        "category": ["nobility"],
    },
    "diego_de_avalos": {
        "name": "Diego de Ávalos",
        "aliases": ["diego_de_avalos"],
        "category": ["nobility"],
    },
    "diego_de_sotomayor": {
        "name": "Diego de Sotomayor",
        "aliases": ["diego_de_sotomayor"],
        "category": ["nobility"],
    },
    "diego_de_vargas": {
        "name": "Diego de Vargas",
        "aliases": ["diego_de_vargas"],
        "category": ["nobility"],
    },
    "diego_de_vergara": {
        "name": "Diego de Vergara",
        "aliases": ["diego_de_vergara"],
        "category": ["nobility"],
    },
    "diego_fernandez": {
        "name": "Diego Fernández",
        "aliases": ["diego_fernandez"],
        "category": ["nobility"],
    },
    "alonso_de_sotomayor": {
        "name": "Alonso de Sotomayor",
        "aliases": ["alonso_de_sotomayor"],
        "category": ["nobility"],
    },
    "alonso_fernandez": {
        "name": "Alonso Fernández",
        "aliases": ["alonso_fernandez"],
        "category": ["nobility"],
    },
    "filipa_de_vilhena": {
        "name": "Filipa de Vilhena",
        "aliases": ["filipa_de_vilhena"],
        "category": ["nobility"],
    },
    "arnau_despujol": {
        "name": "Arnau Despujol",
        "aliases": ["arnau_despujol"],
        "category": ["nobility"],
    },
    "count_of_cardona": {
        "name": "Count of Cardona",
        "aliases": ["count_of_cardona"],
        "category": ["nobility"],
    },
    "count_of_urgell": {
        "name": "Count of Urgell",
        "aliases": ["count_of_urgell"],
        "category": ["nobility"],
    },
    "rene_of_anjou": {
        "name": "René of Anjou",
        "aliases": ["rene_of_anjou", "rene_d_anjou", "rene"],
        "category": ["nobility"],
    },
    "olivier_de_coetivy": {
        "name": "Olivier de Coëtivy",
        "aliases": ["olivier_de_coetivy"],
        "category": ["nobility"],
    },

    # === RELIGIOUS ===

    "abbott_rodrigo": {
        "name": "Abbot Rodrigo González",
        "aliases": [
            "abbot_rodrigo",
            "abbott_rodrigo",      # common typo
            "abbott_rodrigo_gonzalez",
            "rodrigo_gonzalez",
        ],
        "category": ["religious"],
    },
    "brother_guillem": {
        "name": "Brother Guillem",
        "aliases": ["brother_guillem"],
        "category": ["religious"],
    },
    "brother_martin": {
        "name": "Brother Martín",
        "aliases": ["brother_martin"],
        "category": ["religious"],
    },
    "father_miguel": {
        "name": "Father Miguel",
        "aliases": ["father_miguel"],
        "category": ["religious"],
    },
    "father_bernat_metge": {
        "name": "Father Bernat Metge",
        "aliases": ["father_bernat_metge"],
        "category": ["religious"],
    },
    "alfonso_de_cartagena": {
        "name": "Bishop Alfonso de Cartagena",
        "aliases": [
            "alfonso_de_cartagena",
            "bishop_alfonso_de_cartagena",
            "bishop_alfonso",
        ],
        "category": ["religious"],
    },
    "bishop_of_barcelona": {
        "name": "Bishop of Barcelona (Francesc Climent Sapera)",
        "aliases": [
            "bishop_of_barcelona",
            "bishop_barcelona",
            "bishop_francesc_climent_sapera",
            "francesc_climent_sapera",
        ],
        "category": ["religious"],
    },
    "bishop_of_girona": {
        "name": "Bishop of Girona",
        "aliases": ["bishop_of_girona"],
        "category": ["religious"],
    },
    "bishop_carrera": {
        "name": "Bishop Carrera",
        "aliases": ["bishop_carrera"],
        "category": ["religious"],
    },
    "bishop_jean": {
        "name": "Bishop Jean",
        "aliases": ["bishop_jean"],
        "category": ["religious"],
    },
    "archbishop_cerezuela": {
        "name": "Archbishop Cerezuela of Toledo",
        "aliases": [
            "archbishop_cerezuela",
            "archbishop_alonso_de_toledo",
            "archbishop_of_toledo",
            "cerezuela",
            "juan_de_cerezuela",
        ],
        "category": ["religious"],
    },
    "tomas_de_torquemada": {
        "name": "Tomás de Torquemada",
        "aliases": ["tomas_de_torquemada"],
        "category": ["religious"],
    },
    "lope_de_barrientos": {
        "name": "Lope de Barrientos",
        "aliases": ["lope_de_barrientos"],
        "category": ["religious"],
    },
    "pablo_de_santa_maria": {
        "name": "Pablo de Santa María",
        "aliases": ["pablo_de_santa_maria"],
        "category": ["religious"],
    },

    # === CATALAN / BARCELONA ===

    "bernat_fiveller": {
        "name": "Bernat Fiveller",
        "aliases": ["bernat_fiveller", "fiveller"],
        "category": ["nobility"],
    },
    "gabriel_fiveller": {
        "name": "Gabriel Fiveller",
        "aliases": ["gabriel_fiveller"],
        "category": ["nobility"],
    },
    "pere_joan_de_sant_climent": {
        "name": "Pere Joan de Sant Climent",
        "aliases": ["pere_joan_de_sant_climent", "pere_sant_climent", "sant_climent"],
        "category": ["nobility"],
    },
    "ramon_de_mur": {
        "name": "Ramón de Mur",
        "aliases": ["ramon_de_mur"],
        "category": ["nobility"],
    },

    # === SIGISMUND ===

    "sigismund": {
        "name": "Emperor Sigismund",
        "aliases": ["sigismund", "sigismund_hre"],
        "category": ["nobility"],
    },

    # === POLISH-HUNGARIAN ===

    # (These characters appear in later chapters not yet in event data,
    #  but included for completeness from CHARACTER_DATABASE.md)

    # === RAOUL FAMILY ===

    "raoul": {
        "name": "Raoul",
        "aliases": ["raoul"],
        "category": ["byzantine"],
    },
    "raoul_eldest": {
        "name": "Raoul (eldest brother)",
        "aliases": ["raoul_eldest", "eldest_raoul", "raoul_the_elder"],
        "category": ["byzantine"],
    },
    "raoul_brothers": {
        "name": "Raoul brothers (collective)",
        "aliases": ["raoul_brothers"],
        "category": ["byzantine"],
    },
    "raoul_middle": {
        "name": "Raoul (middle brother)",
        "aliases": ["raoul_middle"],
        "category": ["byzantine"],
    },
    "raoul_soldier": {
        "name": "Raoul (soldier)",
        "aliases": ["raoul_soldier"],
        "category": ["byzantine"],
    },
    "philippe_raoul": {
        "name": "Philippe Raoul",
        "aliases": ["philippe_raoul"],
        "category": ["byzantine"],
    },

    # === HOUSEHOLD / MINOR ===

    "bernat": {
        "name": "Young Lord Bernat",
        "aliases": ["bernat"],
        "category": ["household"],
    },
    "ines": {
        "name": "Inés",
        "aliases": ["ines", "dona_ines"],
        "category": ["household"],
    },
    "ines_de_castro": {
        "name": "Inés de Castro",
        "aliases": ["ines_de_castro"],
        "category": ["household"],
    },
    "pascual": {
        "name": "Pascual",
        "aliases": ["pascual"],
        "category": ["household"],
    },

    # === SEPARATE LUCIA CHARACTERS ===

    "lucia_alvarez": {
        "name": "Lucía Álvarez",
        "aliases": ["lucia_alvarez"],
        "category": ["household"],
    },
    "lucia_de_ahumada": {
        "name": "Lucía de Ahumada",
        "aliases": ["lucia_de_ahumada"],
        "category": ["household"],
    },
    "lucia_de_aragon": {
        "name": "Lucía de Aragón",
        "aliases": ["lucia_de_aragon"],
        "category": ["nobility"],
    },
    "lucia_de_arenoso": {
        "name": "Lucía de Arenoso",
        "aliases": ["lucia_de_arenoso"],
        "category": ["household"],
    },
    "lucia_gonzaga": {
        "name": "Lucía Gonzaga (lady-in-waiting)",
        "aliases": ["lucia_gonzaga"],
        "category": ["household", "italian"],
    },
    "lucia_paleologus": {
        "name": "Lucía Paleologus",
        "aliases": ["lucia_paleologus"],
        "category": ["byzantine"],
    },
    "lucia_zuniga": {
        "name": "Lucía Zúñiga",
        "aliases": ["lucia_zuniga"],
        "category": ["household"],
    },

    # === SEPARATE BEATRIZ CHARACTERS ===

    "beatriz_de_meneses": {
        "name": "Beatriz de Meneses",
        "aliases": ["beatriz_de_meneses"],
        "category": ["nobility"],
    },
    "beatriz_de_manrique": {
        "name": "Beatriz de Manrique",
        "aliases": ["beatriz_de_manrique"],
        "category": ["nobility"],
    },
    "beatriz_de_silva": {
        "name": "Beatriz de Silva",
        "aliases": ["beatriz_de_silva"],
        "category": ["nobility"],
    },

    # === SEPARATE LEONOR CHARACTER ===

    "leonor_de_castilla": {
        "name": "Leonor de Castilla",
        "aliases": ["leonor_de_castilla"],
        "category": ["iberian_royalty"],
    },

    # === OTHER INDIVIDUAL CHARACTERS ===

    "giacomo_fieschi": {
        "name": "Giacomo Fieschi",
        "aliases": ["giacomo_fieschi"],
        "category": ["italian"],
    },
    "giacomo_pallavicini": {
        "name": "Giacomo Pallavicini",
        "aliases": ["giacomo_pallavicini", "pallavicini"],
        "category": ["italian"],
    },
    "giacomo": {
        "name": "Giacomo",
        "aliases": ["giacomo"],
        "category": ["italian"],
    },
    "tomas": {
        "name": "Tomás",
        "aliases": ["tomas"],
        "category": ["household"],
    },
    "tomas_de_lepe": {
        "name": "Tomás de Lepe",
        "aliases": ["tomas_de_lepe"],
        "category": ["military"],
    },
    "tomas_de_palencia": {
        "name": "Tomás de Palencia",
        "aliases": ["tomas_de_palencia"],
        "category": ["military"],
    },
    "garcia": {
        "name": "García",
        "aliases": ["garcia"],
        "category": ["military"],
    },
    "sergeant_garcia": {
        "name": "Sergeant García",
        "aliases": ["sergeant_garcia"],
        "category": ["military"],
    },
    "sergeant_ibanez": {
        "name": "Sergeant Ibáñez",
        "aliases": ["sergeant_ibanez", "ibañez"],
        "category": ["military"],
    },
    "bernardo": {
        "name": "Bernardo",
        "aliases": ["bernardo"],
        "category": ["household"],
    },
    "rodrigo": {
        "name": "Rodrigo",
        "aliases": ["rodrigo"],
        "category": ["household"],
    },
    "diego": {
        "name": "Diego",
        "aliases": ["diego"],
        "category": ["household"],
    },
    "dr_alvares": {
        "name": "Dr. Álvares",
        "aliases": ["dr_alvares"],
        "category": ["household"],
    },
    "dr_goncalo": {
        "name": "Dr. Gonçalo",
        "aliases": ["dr_goncalo"],
        "category": ["household"],
    },
    "master_gonzalo": {
        "name": "Master Gonzalo",
        "aliases": ["master_gonzalo", "master_gonzalo_de_avila"],
        "category": ["household"],
    },
    "hans_the_elder": {
        "name": "Hans the Elder",
        "aliases": ["hans_the_elder"],
        "category": ["economic"],
    },
    "heinrich_moller": {
        "name": "Heinrich Möller",
        "aliases": ["heinrich_moller"],
        "category": ["economic"],
    },
    "harbor_master_ostia": {
        "name": "Harbor Master of Ostia",
        "aliases": ["harbor_master_ostia"],
        "category": ["household"],
    },
    "genoese_officer": {
        "name": "Genoese officer",
        "aliases": ["genoese_officer"],
        "category": ["military"],
    },
    "old_priest": {
        "name": "Old priest",
        "aliases": ["old_priest"],
        "category": ["religious"],
    },
    "grey_haired_nobleman": {
        "name": "Grey-haired nobleman",
        "aliases": ["grey_haired_nobleman"],
        "category": ["nobility"],
    },
    "stocky_knight": {
        "name": "Stocky knight",
        "aliases": ["stocky_knight"],
        "category": ["military"],
    },
    "blacksmith_leader": {
        "name": "Blacksmith leader",
        "aliases": ["blacksmith_leader"],
        "category": ["household"],
    },
    "artisan_representative": {
        "name": "Artisan representative",
        "aliases": ["artisan_representative"],
        "category": ["household"],
    },
    "citizens_representative": {
        "name": "Citizens' representative",
        "aliases": ["citizens_representative"],
        "category": ["household"],
    },
    "merchant_wife": {
        "name": "Merchant's wife",
        "aliases": ["merchant_wife", "merchants_wife"],
        "category": ["household"],
    },
    "venetian_merchants_son": {
        "name": "Venetian merchant's son",
        "aliases": ["venetian_merchants_son"],
        "category": ["household"],
    },
    "queen_joanna_ii": {
        "name": "Queen Joanna II of Naples",
        "aliases": ["queen_joanna_ii"],
        "category": ["italian"],
    },
    "maria_de_sousa": {
        "name": "María de Sousa",
        "aliases": ["maria_de_sousa"],
        "category": ["nobility"],
    },
    "maria_of_chios": {
        "name": "María of Chios",
        "aliases": ["maria_of_chios"],
        "category": ["byzantine"],
    },
    "maria_velasco": {
        "name": "María Velasco",
        "aliases": ["maria_velasco"],
        "category": ["nobility"],
    },
    "mencia_de_figueroa": {
        "name": "Mencía de Figueroa",
        "aliases": ["mencia_de_figueroa"],
        "category": ["nobility"],
    },
    "martin_de_cordoba": {
        "name": "Martín de Córdoba",
        "aliases": ["martin_de_cordoba"],
        "category": ["military"],
    },
    "don_juan_de_zuniga": {
        "name": "Don Juan de Zúñiga",
        "aliases": ["don_juan_de_zuniga", "juan_de_zuniga"],
        "category": ["nobility"],
    },

    # === CHARACTERS FROM CHARACTER_DATABASE.md (not yet in event data) ===

    "isaac_de_baeza": {
        "name": "Isaac de Baeza",
        "aliases": ["isaac_de_baeza", "isaac"],
        "category": ["court_advisor"],
    },
    "mordecai_ben_shlomo": {
        "name": "Mordecai ben Shlomo",
        "aliases": ["mordecai_ben_shlomo", "mordecai"],
        "category": ["court_advisor"],
    },
    "tomas_de_cordoba": {
        "name": "Tomás de Córdoba",
        "aliases": ["tomas_de_cordoba"],
        "category": ["household"],
    },
    "duarte_i": {
        "name": "King Duarte I of Portugal",
        "aliases": ["duarte_i", "duarte", "king_duarte"],
        "category": ["iberian_royalty"],
    },
    "henry_the_navigator": {
        "name": "Prince Henry the Navigator",
        "aliases": ["henry_the_navigator", "prince_henry"],
        "category": ["iberian_royalty"],
    },
    "teresa": {
        "name": "Princess Teresa María of Castile",
        "aliases": ["teresa", "princess_teresa"],
        "category": ["royal_family"],
    },
    "juana": {
        "name": "Princess Juana of Castile",
        "aliases": ["juana", "princess_juana"],
        "category": ["royal_family"],
    },
    "nicolas": {
        "name": "Prince Nicolás de Trastámara",
        "aliases": ["nicolas", "prince_nicolas"],
        "category": ["royal_family"],
    },
    "fray_alonso_de_burgos": {
        "name": "Fray Alonso de Burgos",
        "aliases": ["fray_alonso_de_burgos", "fray_alonso"],
        "category": ["religious"],
    },
    "fra_bartholomew_texier": {
        "name": "Fra Bartholomew Texier",
        "aliases": ["fra_bartholomew_texier", "bartholomew_texier"],
        "category": ["religious"],
    },
    "musa_keita": {
        "name": "Musa Keita",
        "aliases": ["musa_keita", "musa"],
        "category": ["economic"],
    },
    "giacomo_ferrante": {
        "name": "Giacomo Ferrante",
        "aliases": ["giacomo_ferrante"],
        "category": ["economic"],
    },
    "rodrigo_de_ponce": {
        "name": "Don Rodrigo de Ponce",
        "aliases": ["rodrigo_de_ponce"],
        "category": ["economic"],
    },
    "hans_von_steinberg": {
        "name": "Hans von Steinberg",
        "aliases": ["hans_von_steinberg"],
        "category": ["economic"],
    },
    "hans_wenzel": {
        "name": "Hans Wenzel",
        "aliases": ["hans_wenzel"],
        "category": ["economic"],
    },
    "marta": {
        "name": "Marta",
        "aliases": ["marta"],
        "category": ["household"],
    },
    "ser_benedetto": {
        "name": "Ser Benedetto",
        "aliases": ["ser_benedetto"],
        "category": ["household", "italian"],
    },
    "wladyslaw_iii": {
        "name": "Władysław III Jagiellon",
        "aliases": ["wladyslaw_iii", "wladyslaw"],
        "category": ["polish_hungarian"],
    },
    "bishop_olesnicki": {
        "name": "Bishop Zbigniew Oleśnicki",
        "aliases": ["bishop_olesnicki", "olesnicki", "zbigniew_olesnicki"],
        "category": ["polish_hungarian", "religious"],
    },
    "hetman_koniecpol": {
        "name": "Hetman Jan of Koniecpol",
        "aliases": ["hetman_koniecpol", "koniecpol", "jan_koniecpol"],
        "category": ["polish_hungarian", "military"],
    },
    "ban_ujlaki": {
        "name": "Ban Miklós Újlaki",
        "aliases": ["ban_ujlaki", "ujlaki", "miklos_ujlaki"],
        "category": ["polish_hungarian", "military"],
    },
    "jan_tarnowski": {
        "name": "Jan Tarnowski",
        "aliases": ["jan_tarnowski", "tarnowski"],
        "category": ["polish_hungarian", "nobility"],
    },
    "cosimo_de_medici": {
        "name": "Cosimo de' Medici",
        "aliases": ["cosimo_de_medici", "cosimo"],
        "category": ["italian", "economic"],
    },
    "admiral_ataide": {
        "name": "Admiral Ataíde",
        "aliases": ["admiral_ataide", "ataide"],
        "category": ["military"],
    },
    "admiral_vilaragut": {
        "name": "Admiral Vilaragut",
        "aliases": ["admiral_vilaragut", "vilaragut"],
        "category": ["military"],
    },
    "gonzalo_de_cordoba": {
        "name": "Captain Gonzalo de Córdoba",
        "aliases": ["gonzalo_de_cordoba", "captain_gonzalo"],
        "category": ["military"],
    },
    "joao_i": {
        "name": "King João I of Portugal",
        "aliases": ["joao_i", "joao"],
        "category": ["iberian_royalty"],
    },
}


# ---------------------------------------------------------------------------
# Helper: build a reverse lookup  alias_id -> canonical_id
# ---------------------------------------------------------------------------

def _build_reverse_map():
    """Return dict mapping every alias -> canonical_id."""
    rev = {}
    for canonical_id, info in ALIAS_MAP.items():
        for alias in info["aliases"]:
            if alias in rev:
                print(f"WARNING: '{alias}' mapped to both "
                      f"'{rev[alias]}' and '{canonical_id}'", file=sys.stderr)
            rev[alias] = canonical_id
    return rev


REVERSE_MAP = _build_reverse_map()

ENRICHMENT_PATH = os.path.join(DATA_DIR, "character_enrichment.json")

# Category-based fallback personality for characters without enrichment data
CATEGORY_PERSONALITY = {
    "royal_family":     ["noble bearing", "dynastic pride", "courtly"],
    "court_advisor":    ["shrewd", "politically aware", "loyal to the crown"],
    "iberian_royalty":  ["regal", "politically minded", "dynastic"],
    "papal_court":      ["learned", "politically astute", "devout"],
    "byzantine":        ["proud", "pragmatic", "rooted in tradition"],
    "ottoman":          ["disciplined", "strategic", "cultured"],
    "italian":          ["shrewd", "cultured", "pragmatic"],
    "military":         ["disciplined", "brave", "dutiful"],
    "religious":        ["devout", "learned", "principled"],
    "economic":         ["practical", "resourceful", "industrious"],
    "household":        ["devoted", "reliable", "diligent"],
    "nobility":         ["proud", "ambitious", "status-conscious"],
    "polish_hungarian": ["martial", "proud", "frontier-hardened"],
}


def _load_enrichment():
    """Load character_enrichment.json if it exists."""
    if not os.path.exists(ENRICHMENT_PATH):
        return {}
    with open(ENRICHMENT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Remove metadata keys
    return {k: v for k, v in data.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# Load events
# ---------------------------------------------------------------------------

def load_events():
    """Load starter_events.json (run build_events.py --write first)."""
    if not os.path.exists(EVENTS_PATH):
        # Try building from chapter files
        print("starter_events.json not found, building from chapters...",
              file=sys.stderr)
        from build_events import build_events
        return build_events()

    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Build character entries
# ---------------------------------------------------------------------------

def _load_chapters():
    """Load all chapter_02_*.json files and return list of encounters."""
    pattern = os.path.join(DATA_DIR, "chapter_02_*.json")
    encounters = []
    for path in sorted(glob.glob(pattern)):
        with open(path, "r", encoding="utf-8") as f:
            chapter = json.load(f)
        for enc in chapter.get("encounters", []):
            enc["_chapter"] = chapter.get("chapter", "")
            encounters.append(enc)
    return encounters


def _detect_status(canonical_id, info, encounters):
    """Determine character status from chapter data.

    Death events list both the deceased AND witnesses as participants,
    so we can't reliably infer who died. Default to active; status
    should be curated manually or from CHARACTER_DATABASE.md.
    """
    return ["active"]


def _latest_location(canonical_id, info, encounters):
    """Find the most recent location a character appeared at."""
    aliases = set(info["aliases"])
    latest = None
    for enc in encounters:
        if aliases & set(enc.get("participants", [])):
            loc = enc.get("location", "")
            if loc:
                latest = loc
    return latest or ""


def _collect_event_refs(info, encounters):
    """Collect event IDs where this character appears."""
    aliases = set(info["aliases"])
    refs = []
    for enc in encounters:
        if aliases & set(enc.get("participants", [])):
            eid = enc.get("id", "")
            if eid:
                refs.append(eid)
    return refs


def build_characters(events_data):
    """Build the full-schema characters list from ALIAS_MAP + chapter data.

    Merges enrichment data from character_enrichment.json when available.
    Falls back to category-based default personality for unenriched characters.
    """
    encounters = _load_chapters()
    enrichment = _load_enrichment()

    characters = []
    enriched_count = 0

    for canonical_id, info in ALIAS_MAP.items():
        aliases = set(info["aliases"])

        # Count events across all aliases (from starter_events.json)
        event_refs = []
        for evt in events_data["events"]:
            for char_id in evt["characters"]:
                if char_id in aliases:
                    event_refs.append(evt["event_id"])
                    break

        # Derive what we can from chapter encounters
        status = _detect_status(canonical_id, info, encounters)
        location = _latest_location(canonical_id, info, encounters)
        chapter_event_refs = _collect_event_refs(info, encounters)

        # Use chapter-derived refs if available, fall back to events-derived
        final_refs = chapter_event_refs if chapter_event_refs else event_refs

        # Category-based fallback personality
        primary_cat = info.get("category", [""])[0]
        fallback_personality = CATEGORY_PERSONALITY.get(primary_cat, [])

        char_entry = {
            "id": canonical_id,
            "name": info["name"],
            "aliases": info["aliases"],
            "title": "",
            "born": "0000-00-00",
            "status": status,
            "category": info.get("category", []),
            "location": location,
            "current_task": "",
            "personality": fallback_personality,
            "interests": [],
            "speech_style": "",
            "event_refs": final_refs,
        }

        # Merge enrichment data (overrides auto-generated defaults)
        enrich = enrichment.get(canonical_id, {})
        if enrich:
            enriched_count += 1
            for field in ("title", "born", "status", "personality",
                          "interests", "speech_style", "current_task",
                          "location", "appearance"):
                if field in enrich:
                    char_entry[field] = enrich[field]

        characters.append(char_entry)

    # Sort by event count descending, then by name
    characters.sort(key=lambda c: (-len(c["event_refs"]), c["name"]))

    print(f"Enrichment applied: {enriched_count}/{len(characters)} characters",
          file=sys.stderr)

    return {"characters": characters}


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def query_character(events_data, search_term):
    """Find all events for a character, searching across aliases."""
    search = search_term.lower()

    # First: find which canonical character(s) match the search
    matching_aliases = set()
    matching_canonicals = set()

    for canonical_id, info in ALIAS_MAP.items():
        # Check canonical ID
        if search in canonical_id:
            matching_aliases.update(info["aliases"])
            matching_canonicals.add(canonical_id)
            continue
        # Check display name
        if search in info["name"].lower():
            matching_aliases.update(info["aliases"])
            matching_canonicals.add(canonical_id)
            continue
        # Check each alias
        for alias in info["aliases"]:
            if search in alias:
                matching_aliases.update(info["aliases"])
                matching_canonicals.add(canonical_id)
                break

    if not matching_aliases:
        # Fallback: raw substring search in event character lists
        matches = []
        for evt in events_data["events"]:
            for char_id in evt["characters"]:
                if search in char_id:
                    matches.append(evt)
                    break
        return matches, set()

    # Find all events where any alias appears
    matches = []
    for evt in events_data["events"]:
        for char_id in evt["characters"]:
            if char_id in matching_aliases:
                matches.append(evt)
                break

    return matches, matching_canonicals


def find_orphans(events_data):
    """Find character IDs in events that aren't in any alias group."""
    all_event_chars = set()
    for evt in events_data["events"]:
        all_event_chars.update(evt["characters"])

    orphans = {}
    for char_id in sorted(all_event_chars):
        if char_id not in REVERSE_MAP:
            count = sum(1 for e in events_data["events"]
                        if char_id in e["characters"])
            orphans[char_id] = count

    return orphans


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_event(evt, verbose=False):
    """Print a single event in readable format."""
    chars = ", ".join(evt["characters"])
    print(f"  {evt['event_id']}  [{evt['date']}]  {evt['type']}")
    print(f"    Location:   {evt['location']}")
    print(f"    Characters: {chars}")
    if evt.get("summary"):
        summary = evt["summary"]
        if not verbose and len(summary) > 120:
            summary = summary[:117] + "..."
        print(f"    Summary:    {summary}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    verbose = "-v" in args or "--verbose" in args

    events_data = load_events()
    total_events = len(events_data["events"])

    # --aliases: show the alias mapping
    if "--aliases" in args:
        print(f"Character alias mapping ({len(ALIAS_MAP)} characters):\n")
        for canonical_id, info in sorted(ALIAS_MAP.items()):
            aliases = info["aliases"]
            if len(aliases) > 1:
                print(f"  {info['name']}")
                print(f"    canonical: {canonical_id}")
                print(f"    aliases:   {', '.join(aliases)}")
                print()
        return

    # --orphans: show unmapped IDs
    if "--orphans" in args:
        orphans = find_orphans(events_data)
        if orphans:
            print(f"Unmapped character IDs ({len(orphans)}):\n")
            for char_id, count in sorted(orphans.items(),
                                         key=lambda x: -x[1]):
                print(f"  {char_id:45s} ({count} events)")
        else:
            print("No orphan character IDs - all mapped!")
        return

    # --query: find events for a character (across aliases)
    if "--query" in args:
        idx = args.index("--query")
        if idx + 1 >= len(args):
            print("ERROR: --query requires a character name/id", file=sys.stderr)
            sys.exit(1)
        search = args[idx + 1]
        matches, canonicals = query_character(events_data, search)

        if canonicals:
            for cid in sorted(canonicals):
                info = ALIAS_MAP[cid]
                print(f"Character: {info['name']}  (id: {cid})")
                if len(info["aliases"]) > 1:
                    print(f"  Aliases: {', '.join(info['aliases'])}")
            print()

        print(f"Events found: {len(matches)}\n")
        for evt in matches:
            print_event(evt, verbose=verbose)
        return

    # --write: generate characters.json
    if "--write" in args:
        char_data = build_characters(events_data)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(char_data, f, indent=2, ensure_ascii=False)
        print(f"Written {len(char_data['characters'])} characters to "
              f"{OUTPUT_PATH}", file=sys.stderr)
        return

    # Default: preview
    char_data = build_characters(events_data)
    orphans = find_orphans(events_data)

    print(f"Characters: {len(char_data['characters'])} "
          f"(from {total_events} events)")
    print(f"Orphan IDs: {len(orphans)} (not yet mapped)\n")

    # Show top characters by event count
    print("Top 30 characters by event count:\n")
    for char in char_data["characters"][:30]:
        alias_note = ""
        if len(char["aliases"]) > 1:
            alias_note = f"  [{len(char['aliases'])} aliases]"
        evt_count = len(char["event_refs"])
        print(f"  {evt_count:4d}  {char['name']:45s}{alias_note}")

    if orphans:
        print(f"\nUnmapped IDs (run --orphans for full list):")
        for char_id, count in sorted(orphans.items(),
                                     key=lambda x: -x[1])[:10]:
            print(f"  {char_id:45s} ({count} events)")

    print(f"\nRun with --write to save to {OUTPUT_PATH}")
    print(f"Run with --query <name> to search events")
    print(f"Run with --aliases to view alias mapping")
    print(f"Run with --orphans to find unmapped IDs")


if __name__ == "__main__":
    main()
