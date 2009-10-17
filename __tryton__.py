#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
{
    'name': 'Stock Location Sequence',
    'name_de_DE': 'Lagerverwaltung Lagerortsequenz',
    'name_fr_FR': 'Séquence emplacement',
    'name_es_CO': 'Secuencia de Sitio del Stock',
    'name_es_ES': 'Secuencia de ubicación de existencias',
    'version': '1.3.0',
    'author': 'B2CK',
    'email': 'info@b2ck.com',
    'website': 'http://www.tryton.org/',
    'description': '''Add sequence on location object
''',
    'description_de_DE': '''Fügt dem Objekt Lagerort eine Sequenz hinzu
''',
    'description_fr_FR': '''Ajoute une séquence sur le modèle emplacement
''',
    'description_es_CO': '''Añade una secuencia e sitio a un objeto
''',
    'description_es_ES': 'Añade una secuencia al objeto ubicación',
    'depends': [
        'ir',
        'stock',
    ],
    'xml': [
        'stock.xml',
    ],
    'translation': [
        'de_DE.csv',
        'fr_FR.csv',
        'es_CO.csv',
        'es_ES.csv',
    ],
}
