# TFG_Informatica
TODO:
Guardar en BDD els counters+percent de l'article de la HomePage de cada dia per a cada versió linguistica amb un timestamp.
Córrer l'script cada 6 hores i que ho guardi en una BD.
Crear APP de dash que utilitzi aquesta BD per visualitzar un stacked barchart per veure totes
Extra: Triar una llengua i veure evolucio en el temps
Extra Extra: Fer-ho per als projectes germans


Queries:
- Trobar els titols i els page_id de cada outlink d'una pàgina (Per fer més d'una pàgina, usar la clausula "IN" en comptes de "=")
"SELECT pagelinks.pl_title, page.page_id 
FROM pagelinks 
INNER JOIN page ON pagelinks.pl_title = page.page_title
WHERE pagelinks.pl_from = 1378 AND pagelinks.pl_from_namespace = 0 AND pagelinks.pl_namespace = 0"

- Count gender outlinks of a given article
 """SELECT ?gender ?genderLabel (count(distinct ?person) as ?number) 
   WHERE
   {
     ?person ?transcluded wd:qualifier.
     ?person wdt:P31 wd:Q5.
     ?person wdt:P21 ?gender.
     SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
   ?gender rdfs:label ?genderLabel.}
   }
   GROUP BY  ?gender ?genderLabel """
   

- Show gender outlinks and Q of a given article
"""SELECT DISTINCT ?person ?personLabel  ?genderLabel 
   WHERE
   {
     ?person ?transcluded wd:qualifier.
     ?person wdt:P31 wd:Q5.
     ?person wdt:P21 ?gender.
     SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
   }"""
   
- Count the genders of the given articles:
SELECT ?gender ?genderLabel (count(distinct ?person) as ?number)
WHERE { 
  VALUES ?person{
  wd:Q5593
  wd:Q23548
  wd:Q5577
} 
     ?person wdt:P31 wd:Q5.
     ?person wdt:P21 ?gender.
     SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
   ?gender rdfs:label ?genderLabel.}
   }
   GROUP BY  ?gender ?genderLabel