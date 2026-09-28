"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer NORDRHEIN-WESTFALEN. Nach
§ 57 Abs. 1 BauO NRW 2018 sind untere Bauaufsichtsbehoerden "die
kreisfreien Staedte, die Grossen kreisangehoerigen Staedte und die
Mittleren kreisangehoerigen Staedte" sowie "die Kreise fuer die
uebrigen kreisangehoerigen Gemeinden". § 85 Abs. 4 BauO NRW: "Das
Baulastenverzeichnis wird von der Bauaufsichtsbehoerde gefuehrt" -
dieselbe untere Bauaufsichtsbehoerde fuehrt damit auch das
Baulastenverzeichnis. Die Liste der Grossen (35) und Mittleren (132)
kreisangehoerigen Staedte stammt aus der amtlichen "Verordnung zur
Bestimmung der Grossen kreisangehoerigen Staedte und der Mittleren
kreisangehoerigen Staedte nach § 4 der Gemeindeordnung fuer das Land
Nordrhein-Westfalen" (Stand 01.01.2025) - direkt per Live-Browser-Abruf
von recht.nrw.de gelesen (Volltext, nicht JS-verkuerzt).

31 Landkreise + 22 kreisfreie Staedte = 53 "Kreise" in
AdministrativeUnit erhalten je eine COUNTY-Regel. Zusaetzlich 167
Grosse/Mittlere kreisangehoerige Staedte (aus der genannten
Verordnung) erhalten eine eigene MUNICIPALITY-Regel, da sie trotz
Kreisangehoerigkeit selbst untere Bauaufsichtsbehoerde sind (nimmt
automatisch Vorrang vor der COUNTY-Regel ihres Landkreises).

53 neue COUNTY-Regeln je Auskunftsart + 167 neue MUNICIPALITY-Regeln je
Auskunftsart = 440 Regeln insgesamt (abzueglich etwaiger bereits
bestehender Alt-Abdeckung, die der Konfliktpruefung korrekt als
Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Nordrhein-Westfalen)"
BAUO_NRW_URL = "https://recht.nrw.de/lrgv/gesetz/01012024-bauordnung-fuer-das-land-nordrhein-westfalen-landesbauordnung-2018-bauo-nrw/"
VERORDNUNG_URL = "https://recht.nrw.de/lrgv/rechtsverordnung/01012025-verordnung-zur-bestimmung-der-grossen-kreisangehoerigen-staedte-und/"
QUOTE_KREIS = ("§ 57 Abs. 1 BauO NRW: 'Untere Bauaufsichtsbehörden: a) die kreisfreien Städte, die "
               "Großen kreisangehörigen Städte und die Mittleren kreisangehörigen Städte als untere "
               "Bauaufsichtsbehörden sowie b) die Kreise für die übrigen kreisangehörigen "
               "Gemeinden.' § 85 Abs. 4 BauO NRW: 'Das Baulastenverzeichnis wird von der "
               "Bauaufsichtsbehörde geführt.'")
QUOTE_AUSNAHME = ("§ 1/§ 2 der Verordnung zur Bestimmung der Großen kreisangehörigen Städte und der "
                   "Mittleren kreisangehörigen Städte nach § 4 GO NRW (Stand 01.01.2025): 'Die "
                   "nachfolgend aufgezählten Gemeinden nehmen als Große/Mittlere kreisangehörige "
                   "Städte zusätzliche Aufgaben nach § 4 Abs. 1 der Gemeindeordnung ... wahr.'")

# Stadtname -> dict(typ, ags, street, plz, city, email)
KREISANGEHOERIGE_STAEDTE_AGS = {
    'Ahaus': dict(typ='Mittel', ags='05554004', street='Rathausplatz 1', plz='48683', city='Ahaus', email='info@ahaus.de'),
    'Ahlen': dict(typ='Mittel', ags='05570004', street='Westenmauer 10', plz='59227', city='Ahlen', email='rathaus@stadt.ahlen.de'),
    'Alsdorf': dict(typ='Mittel', ags='05334004', street='Hubertusstr.17', plz='52477', city='Alsdorf', email='info@alsdorf.de'),
    'Altena': dict(typ='Mittel', ags='05962004', street='Lüdenscheider Str. 22', plz='58762', city='Altena', email='post@altena.de'),
    'Arnsberg': dict(typ='Groß', ags='05958004', street='Rathausplatz 2', plz='59759', city='Arnsberg', email='stadt@arnsberg.de'),
    'Attendorn': dict(typ='Mittel', ags='05966004', street='Kölner Str. 12', plz='57439', city='Attendorn', email='stadt@attendorn.de'),
    'Bad Honnef': dict(typ='Mittel', ags='05382008', street='Rathausplatz 1', plz='53604', city='Bad Honnef', email='info@bad-honnef.de'),
    'Bad Oeynhausen': dict(typ='Mittel', ags='05770004', street='Ostkorso 8', plz='32545', city='Bad Oeynhausen', email='info@badoeynhausen.de'),
    'Bad Salzuflen': dict(typ='Mittel', ags='05766008', street='Rudolph-Brandes-Allee 19', plz='32105', city='Bad Salzuflen', email='stadt@bad-salzuflen.de'),
    'Baesweiler': dict(typ='Mittel', ags='05334008', street='Mariastr. 2', plz='52499', city='Baesweiler', email='info@stadt.baesweiler.de'),
    'Beckum': dict(typ='Mittel', ags='05570008', street='Weststr. 46', plz='59269', city='Beckum', email='stadt@beckum.de'),
    'Bedburg': dict(typ='Mittel', ags='05362004', street='Am Rathaus 1', plz='50181', city='Bedburg', email='stadtverwaltung@bedburg.de'),
    'Bergheim': dict(typ='Groß', ags='05362008', street='Bethlehemer Str. 9-11', plz='50126', city='Bergheim', email='rathaus@bergheim.de'),
    'Bergisch Gladbach': dict(typ='Groß', ags='05378004', street='Konrad-Adenauer-Platz 1', plz='51465', city='Bergisch Gladbach', email='info@bergischgladbach.de'),
    'Bergkamen': dict(typ='Mittel', ags='05978004', street='Rathausplatz 1', plz='59192', city='Bergkamen', email='info@bergkamen.de'),
    'Bocholt': dict(typ='Groß', ags='05554008', street='Kaiser- Wilhelm-Str. 52-58', plz='46395', city='Bocholt', email='stadtverwaltung@mail.bocholt.de'),
    'Borken': dict(typ='Mittel', ags='05554012', street='Im Piepershagen 17', plz='46325', city='Borken', email='stadtpost@borken.de'),
    'Bornheim': dict(typ='Mittel', ags='05382012', street='Rathausstr. 2', plz='53332', city='Bornheim', email='info@stadt-bornheim.de'),
    'Brilon': dict(typ='Mittel', ags='05958012', street='Am Markt 1', plz='59929', city='Brilon', email='info@brilon.de'),
    'Brühl': dict(typ='Mittel', ags='05362012', street='Uhlstr. 3', plz='50321', city='Brühl', email='stadtverwaltung@bruehl.de'),
    'Bünde': dict(typ='Mittel', ags='05758004', street='Bahnhofstraße 15', plz='32257', city='Bünde', email='info@buende.de'),
    'Castrop-Rauxel': dict(typ='Groß', ags='05562004', street='Europaplatz 1', plz='44575', city='Castrop-Rauxel', email='stadtverwaltung@castrop-rauxel.de'),
    'Coesfeld': dict(typ='Mittel', ags='05558012', street='Markt 8', plz='48653', city='Coesfeld', email='stadt@coesfeld.de'),
    'Datteln': dict(typ='Mittel', ags='05562008', street='Genthiner Str. 8', plz='45711', city='Datteln', email='verwaltung@stadt-datteln.de'),
    'Delbrück': dict(typ='Mittel', ags='05774020', street='Himmelreichallee 20', plz='33129', city='Delbrück', email='info@delbrueck.de'),
    'Detmold': dict(typ='Groß', ags='05766020', street='Marktplatz 5', plz='32756', city='Detmold', email='info@detmold.de'),
    'Dinslaken': dict(typ='Groß', ags='05170008', street='Platz d\' Agen 1', plz='46535', city='Dinslaken', email='info@dinslaken.de'),
    'Dormagen': dict(typ='Groß', ags='05162004', street='Paul-Wierich-Platz 2', plz='41539', city='Dormagen', email='stadtverwaltung@stadt-dormagen.de'),
    'Dorsten': dict(typ='Groß', ags='05562012', street='Halterner Str. 5', plz='46284', city='Dorsten', email='poststelle@dorsten.de'),
    'Dülmen': dict(typ='Mittel', ags='05558016', street='Markt 1', plz='48249', city='Dülmen', email='stadt@duelmen.de'),
    'Düren': dict(typ='Groß', ags='05358008', street='Kaiserplatz 2-4', plz='52349', city='Düren', email='stadt@dueren.de'),
    'Elsdorf': dict(typ='Mittel', ags='05362016', street='Gladbacher Str. 111', plz='50189', city='Elsdorf', email='buergermeister@elsdorf.de'),
    'Emmerich': dict(typ='Mittel', ags='05154008', street='Geistmarkt 1', plz='46446', city='Emmerich am Rhein', email='stadtverwaltung@stadt-emmerich.de'),
    'Emsdetten': dict(typ='Mittel', ags='05566008', street='Am Markt 1', plz='48282', city='Emsdetten', email='info@emsdetten.de'),
    'Ennepetal': dict(typ='Mittel', ags='05954008', street='Bismarckstr. 21', plz='58256', city='Ennepetal', email='stadt@ennepetal.de'),
    'Erftstadt': dict(typ='Mittel', ags='05362020', street='Holzdamm 10', plz='50374', city='Erftstadt', email='buergermeisterin@erftstadt.de'),
    'Erkelenz': dict(typ='Mittel', ags='05370004', street='Johannismarkt 17', plz='41812', city='Erkelenz', email='info@erkelenz.de'),
    'Erkrath': dict(typ='Mittel', ags='05158004', street='Bahnstr. 16', plz='40699', city='Erkrath', email='info@erkrath.de'),
    'Eschweiler': dict(typ='Mittel', ags='05334012', street='Johannes-Rau-Platz 1', plz='52249', city='Eschweiler', email='Stadtverwaltung@eschweiler.de'),
    'Espelkamp': dict(typ='Mittel', ags='05770008', street='Wilhelm-Kern-Platz 1', plz='32339', city='Espelkamp', email='info@espelkamp.de'),
    'Euskirchen': dict(typ='Mittel', ags='05366016', street='Kölner Str. 75', plz='53879', city='Euskirchen', email='info@euskirchen.de'),
    'Frechen': dict(typ='Mittel', ags='05362024', street='Johann-Schmitz-Platz 1-3', plz='50226', city='Frechen', email='rathaus@stadt-frechen.de'),
    'Geilenkirchen': dict(typ='Mittel', ags='05370012', street='Markt 9', plz='52511', city='Geilenkirchen', email='stadt@geilenkirchen.de'),
    'Geldern': dict(typ='Mittel', ags='05154012', street='Issumer Tor 36', plz='47608', city='Geldern', email='info@geldern.de'),
    'Gevelsberg': dict(typ='Mittel', ags='05954012', street='Rathausplatz 1', plz='58285', city='Gevelsberg', email='Rathaus@stadtgevelsberg.de'),
    'Gladbeck': dict(typ='Groß', ags='05562014', street='Willy-Brandt-Platz 2', plz='45964', city='Gladbeck', email='rathaus@stadt-gladbeck.de'),
    'Goch': dict(typ='Mittel', ags='05154016', street='Markt 2', plz='47574', city='Goch', email='info@goch.de'),
    'Greven': dict(typ='Mittel', ags='05566012', street='Rathausstr. 6', plz='48268', city='Greven', email='info@stadt-greven.de'),
    'Grevenbroich': dict(typ='Groß', ags='05162008', street='Am Markt 1', plz='41515', city='Grevenbroich', email='info@grevenbroich.de'),
    'Gronau (Westf.)': dict(typ='Mittel', ags='05554020', street='Neustr. 31', plz='48599', city='Gronau (Westf.)', email='info@gronau.de'),
    'Gummersbach': dict(typ='Mittel', ags='05374012', street='Rathausplatz 1', plz='51643', city='Gummersbach', email='rathaus@stadt-gummersbach.de'),
    'Gütersloh': dict(typ='Groß', ags='05754008', street='Berliner Str. 70', plz='33330', city='Gütersloh', email='kontakt@guetersloh.de'),
    'Haan': dict(typ='Mittel', ags='05158008', street='Kaiserstr. 85', plz='42781', city='Haan', email='post@stadt-haan.de'),
    'Haltern': dict(typ='Mittel', ags='05562016', street='Dr.-Conrads-Str. 1', plz='45721', city='Haltern am See', email='stadtverwaltung@haltern.de'),
    'Hamminkeln': dict(typ='Mittel', ags='05170012', street='Brüner Straße 9', plz='46499', city='Hamminkeln', email='info@hamminkeln.de'),
    'Harsewinkel': dict(typ='Mittel', ags='05754016', street='Münsterstr. 14', plz='33428', city='Harsewinkel', email='kontakt@harsewinkel.de'),
    'Hattingen': dict(typ='Mittel', ags='05954016', street='Rathausplatz 1', plz='45525', city='Hattingen', email='info@hattingen.de'),
    'Heiligenhaus': dict(typ='Mittel', ags='05158012', street='Hauptstr. 157', plz='42579', city='Heiligenhaus', email='info@heiligenhaus.de'),
    'Heinsberg': dict(typ='Mittel', ags='05370016', street='Apfelstr. 60', plz='52525', city='Heinsberg', email='stadt@heinsberg.de'),
    'Hemer': dict(typ='Mittel', ags='05962016', street='Hademareplatz 44', plz='58675', city='Hemer', email='post@hemer.de'),
    'Hennef (Sieg)': dict(typ='Mittel', ags='05382020', street='Frankfurter Str. 97', plz='53773', city='Hennef (Sieg)', email='info@hennef.de'),
    'Herdecke': dict(typ='Mittel', ags='05954020', street='Kirchplatz 3', plz='58313', city='Herdecke', email='stadtverwaltung@herdecke.de'),
    'Herford': dict(typ='Groß', ags='05758012', street='Rathausplatz 1', plz='32052', city='Herford', email='info@herford.de'),
    'Herten': dict(typ='Groß', ags='05562020', street='Kurt-Schumacher-Str. 2', plz='45699', city='Herten', email='stadtverwaltung@herten.de'),
    'Herzogenrath': dict(typ='Mittel', ags='05334016', street='Rathausplatz 1', plz='52134', city='Herzogenrath', email='poststelle@herzogenrath.de-mail.de'),
    'Hilden': dict(typ='Mittel', ags='05158016', street='Am Rathaus 1', plz='40721', city='Hilden', email='info@hilden.de'),
    'Höxter': dict(typ='Mittel', ags='05762020', street='Westerbachstr. 45', plz='37671', city='Höxter', email='rathaus@hoexter.de'),
    'Hückelhoven': dict(typ='Mittel', ags='05370020', street='Rathausplatz 1', plz='41836', city='Hückelhoven', email='info@hueckelhoven.de'),
    'Hürth': dict(typ='Mittel', ags='05362028', street='Friedrich-Ebert-Str. 40', plz='50354', city='Hürth', email='rathaus@huerth.de'),
    'Ibbenbüren': dict(typ='Mittel', ags='05566028', street='Alte Münsterstr. 16', plz='49477', city='Ibbenbüren', email='info@ibbenbueren.de'),
    'Iserlohn': dict(typ='Groß', ags='05962024', street='Schillerplatz 7', plz='58636', city='Iserlohn', email='info@iserlohn.de'),
    'Jüchen': dict(typ='Mittel', ags='05162012', street='Am Rathaus 5', plz='41363', city='Jüchen', email='stadt@juechen.de'),
    'Jülich': dict(typ='Mittel', ags='05358024', street='Große Rurstr. 17', plz='52428', city='Jülich', email='info@juelich.de'),
    'Kaarst': dict(typ='Mittel', ags='05162016', street='Am Neumarkt 2', plz='41564', city='Kaarst', email='info@kaarst.de'),
    'Kamen': dict(typ='Mittel', ags='05978020', street='Rathausplatz 1', plz='59174', city='Kamen', email='rathaus@stadt-kamen.de'),
    'Kamp-Lintfort': dict(typ='Mittel', ags='05170020', street='Am Rathaus 2', plz='47475', city='Kamp-Lintfort', email='info@kamp-lintfort.de'),
    'Kempen': dict(typ='Mittel', ags='05166012', street='Buttermarkt 1', plz='47906', city='Kempen', email='rathaus@kempen.de'),
    'Kerpen': dict(typ='Groß', ags='05362032', street='Jahnplatz 1', plz='50171', city='Kerpen', email='buergermeister@stadt-kerpen.de'),
    'Kevelaer': dict(typ='Mittel', ags='05154032', street='Peter-Plümpe-Platz 12', plz='47623', city='Kevelaer', email='info@kevelaer.de'),
    'Kleve': dict(typ='Mittel', ags='05154036', street='Minoritenplatz 1', plz='47533', city='Kleve', email='stadt-kleve@kleve.de'),
    'Korschenbroich': dict(typ='Mittel', ags='05162020', street='Sebastianusstr. 1', plz='41352', city='Korschenbroich', email='stadt@korschenbroich.de'),
    'Kreuztal': dict(typ='Mittel', ags='05970024', street='Siegener Str. 5', plz='57223', city='Kreuztal', email='stadt.kreuztal@kreuztal.de'),
    'Königswinter': dict(typ='Mittel', ags='05382024', street='Drachenfelsstraße 9-11', plz='53639', city='Königswinter', email='stadtverwaltung@koenigswinter.de'),
    'Lage': dict(typ='Mittel', ags='05766040', street='Am Drawen Hof 1', plz='32791', city='Lage', email='epost@lage.de'),
    'Langenfeld (Rhld.)': dict(typ='Mittel', ags='05158020', street='Konrad-Adenauer-Platz 1', plz='40764', city='Langenfeld (Rhld.)', email='info@langenfeld.de'),
    'Leichlingen (Rhld.)': dict(typ='Mittel', ags='05378016', street='Am Büscherhof 1', plz='42799', city='Leichlingen (Rhld.)', email='info@leichlingen.de'),
    'Lemgo': dict(typ='Mittel', ags='05766044', street='Marktplatz 1', plz='32657', city='Lemgo', email='info@lemgo.de'),
    'Lennestadt': dict(typ='Mittel', ags='05966020', street='Thomas-Morus-Platz 1', plz='57368', city='Lennestadt', email='Rathaus@lennestadt.de'),
    'Lippstadt': dict(typ='Groß', ags='05974028', street='Ostwall 1', plz='59555', city='Lippstadt', email='post@stadt-lippstadt.de'),
    'Lohmar': dict(typ='Mittel', ags='05382028', street='Rathausstr. 4', plz='53797', city='Lohmar', email='Rathaus@Lohmar.de'),
    'Löhne': dict(typ='Mittel', ags='05758024', street='Oeynhausener Str. 41', plz='32584', city='Löhne', email='info@loehne.de'),
    'Lübbecke': dict(typ='Mittel', ags='05770020', street='Kreishausstr. 2-4', plz='32312', city='Lübbecke', email='info@luebbecke.de'),
    'Lüdenscheid': dict(typ='Groß', ags='05962032', street='Rathausplatz 2', plz='58507', city='Lüdenscheid', email='post@luedenscheid.de'),
    'Lünen': dict(typ='Groß', ags='05978024', street='Willy-Brandt-Platz 1', plz='44532', city='Lünen', email='stadtverwaltung@luenen.de'),
    'Marl': dict(typ='Groß', ags='05562024', street='Carl-Duisberg-Straße 165', plz='45772', city='Marl', email='info@marl.de'),
    'Mechernich': dict(typ='Mittel', ags='05366028', street='Bergstr. 1', plz='53894', city='Mechernich', email='info@mechernich.de'),
    'Meckenheim': dict(typ='Mittel', ags='05382032', street='Siebengebirgsring 4', plz='53340', city='Meckenheim', email='stadt.meckenheim@meckenheim.de'),
    'Meerbusch': dict(typ='Mittel', ags='05162022', street='Neusser Feldweg 4', plz='40670', city='Meerbusch', email='stadt@meerbusch.de'),
    'Menden (Sauerland)': dict(typ='Mittel', ags='05962040', street='Neumarkt 5', plz='58706', city='Menden (Sauerland)', email='stadt@menden.de'),
    'Meschede': dict(typ='Mittel', ags='05958032', street='Franz-Stahlmecke-Platz 2', plz='59872', city='Meschede', email='post@meschede.de'),
    'Mettmann': dict(typ='Mittel', ags='05158024', street='Neanderstr. 85', plz='40822', city='Mettmann', email='info@mettmann.de'),
    'Minden': dict(typ='Groß', ags='05770024', street='Kleiner Domhof 17', plz='32423', city='Minden', email='info@minden.de'),
    'Moers': dict(typ='Groß', ags='05170024', street='Rathausplatz 1', plz='47441', city='Moers', email='info@moers.de'),
    'Monheim': dict(typ='Mittel', ags='05158026', street='Rathausplatz 2', plz='40789', city='Monheim am Rhein', email='info@monheim.de'),
    'Netphen': dict(typ='Mittel', ags='05970032', street='Amtsstr. 2 + 6', plz='57250', city='Netphen', email='stadt@netphen.de'),
    'Nettetal': dict(typ='Mittel', ags='05166016', street='Doerkesplatz 11', plz='41334', city='Nettetal', email='stadtnettetal@nettetal.de'),
    'Neukirchen-Vluyn': dict(typ='Mittel', ags='05170028', street='Hans-Böckler-Str. 26', plz='47506', city='Neukirchen-Vluyn', email='info@neukirchen-vluyn.de'),
    'Neuss': dict(typ='Groß', ags='05162024', street='Markt 2', plz='41460', city='Neuss', email='stadtverwaltung@stadt.neuss.de'),
    'Niederkassel': dict(typ='Mittel', ags='05382044', street='Rathausstr. 19', plz='53859', city='Niederkassel', email='info@niederkassel.de'),
    'Oelde': dict(typ='Mittel', ags='05570028', street='Ratsstiege 1', plz='59302', city='Oelde', email='online@oelde.de'),
    'Oer-Erkenschwick': dict(typ='Mittel', ags='05562028', street='Rathausplatz 1', plz='45739', city='Oer-Erkenschwick', email='rathaus@Oer-Erkenschwick.de'),
    'Olpe': dict(typ='Mittel', ags='05966024', street='Franziskanerstr. 6', plz='57462', city='Olpe', email='rathaus@olpe.de'),
    'Overath': dict(typ='Mittel', ags='05378024', street='Hauptstr. 25', plz='51491', city='Overath', email='post@overath.de'),
    'Paderborn': dict(typ='Groß', ags='05774032', street='Am Hoppenhof 33', plz='33104', city='Paderborn', email='info@paderborn.de'),
    'Petershagen': dict(typ='Mittel', ags='05770028', street='Bahnhofstr. 63', plz='32469', city='Petershagen', email='info@petershagen.de'),
    'Plettenberg': dict(typ='Mittel', ags='05962052', street='Grünestr. 12', plz='58840', city='Plettenberg', email='post@plettenberg.de'),
    'Porta Westfalica': dict(typ='Mittel', ags='05770032', street='Kempstr. 1', plz='32457', city='Porta Westfalica', email='info@portawestfalica.de'),
    'Pulheim': dict(typ='Mittel', ags='05362036', street='Alte Kölner Str. 26', plz='50259', city='Pulheim', email='stadtpulheim@pulheim.de'),
    'Radevormwald': dict(typ='Mittel', ags='05374036', street='Hohenfuhrstr. 13', plz='42477', city='Radevormwald', email='stadt@radevormwald.de'),
    'Ratingen': dict(typ='Groß', ags='05158028', street='Minoritenstr. 2-6', plz='40878', city='Ratingen', email='stadt@ratingen.de'),
    'Recklinghausen': dict(typ='Groß', ags='05562032', street='Rathausplatz 3-4', plz='45657', city='Recklinghausen', email='stadtverwaltung@recklinghausen.de'),
    'Rheda-Wiedenbrück': dict(typ='Mittel', ags='05754028', street='Rathausplatz 13', plz='33378', city='Rheda-Wiedenbrück', email='info@rh-wd.de'),
    'Rheinbach': dict(typ='Mittel', ags='05382048', street='Schweigelstr. 23', plz='53359', city='Rheinbach', email='infothek@stadt-rheinbach.de'),
    'Rheinberg': dict(typ='Mittel', ags='05170032', street='Kirchplatz 10', plz='47495', city='Rheinberg', email='stadtverwaltung@rheinberg.de'),
    'Rheine': dict(typ='Groß', ags='05566076', street='Klosterstr. 14', plz='48431', city='Rheine', email='stadt@rheine.de'),
    'Rietberg': dict(typ='Mittel', ags='05754032', street='Rathausstr. 31', plz='33397', city='Rietberg', email='info@stadt-rietberg.de'),
    'Rösrath': dict(typ='Mittel', ags='05378028', street='Hauptstr. 229', plz='51503', city='Rösrath', email='infoStadt@roesrath.de'),
    'Salzkotten': dict(typ='Mittel', ags='05774036', street='Marktstr. 8', plz='33154', city='Salzkotten', email='stadtverwaltung@salzkotten.de'),
    'Sankt Augustin': dict(typ='Mittel', ags='05382056', street='Markt 1', plz='53757', city='Sankt Augustin', email='bmbuero@sankt-augustin.de'),
    'Schloß Holte-Stukenbrock': dict(typ='Mittel', ags='05754036', street='Rathausstr. 2', plz='33758', city='Schloß Holte-Stukenbrock', email='info@stadt-shs.de'),
    'Schmallenberg': dict(typ='Mittel', ags='05958040', street='Unterm Werth 1', plz='57392', city='Schmallenberg', email='post@schmallenberg.de'),
    'Schwelm': dict(typ='Mittel', ags='05954024', street='Hauptstr. 14', plz='58332', city='Schwelm', email='info@schwelm.de'),
    'Schwerte': dict(typ='Mittel', ags='05978028', street='Rathausstr. 31', plz='58239', city='Schwerte', email='info@stadt-schwerte.de'),
    'Selm': dict(typ='Mittel', ags='05978032', street='Adenauerplatz 2', plz='59379', city='Selm', email='info@stadtselm.de'),
    'Siegburg': dict(typ='Mittel', ags='05382060', street='Nogenter Platz 10', plz='53721', city='Siegburg', email='rathaus@siegburg.de'),
    'Siegen': dict(typ='Groß', ags='05970040', street='Markt 2', plz='57072', city='Siegen', email='info@siegen.de'),
    'Soest': dict(typ='Mittel', ags='05974040', street='Am Vreithof 8', plz='59494', city='Soest', email='post@soest.de'),
    'Sprockhövel': dict(typ='Mittel', ags='05954028', street='Rathausplatz 4', plz='45549', city='Sprockhövel', email='info@sprockhoevel.de'),
    'Steinfurt': dict(typ='Mittel', ags='05566084', street='Emsdettener Str. 40', plz='48565', city='Steinfurt', email='info@stadt-steinfurt.de'),
    'Stolberg (Rhld.)': dict(typ='Mittel', ags='05334032', street='Rathausstr. 11-13', plz='52222', city='Stolberg', email='info@stolberg.de'),
    'Sundern (Sauerland)': dict(typ='Mittel', ags='05958044', street='Rathausplatz 1', plz='59846', city='Sundern (Sauerland)', email='rathaus@stadt-sundern.de'),
    'Troisdorf': dict(typ='Groß', ags='05382068', street='Kölner Str. 176', plz='53840', city='Troisdorf', email='rathaus@troisdorf.de'),
    'Tönisvorst': dict(typ='Mittel', ags='05166028', street='Bahnstr. 15', plz='47918', city='Tönisvorst', email='buergermeister@toenisvorst.de'),
    'Unna': dict(typ='Groß', ags='05978036', street='Rathausplatz 1', plz='59423', city='Unna', email='post@stadt-unna.de'),
    'Velbert': dict(typ='Groß', ags='05158032', street='Thomasstr. 1', plz='42551', city='Velbert', email='stadt@velbert.de'),
    'Verl': dict(typ='Mittel', ags='05754044', street='Paderborner Str. 5', plz='33415', city='Verl', email='kontakt@verl.de'),
    'Viersen': dict(typ='Groß', ags='05166032', street='Rathausmarkt 1', plz='41747', city='Viersen', email='stadt@viersen.de'),
    'Voerde (Niederrhein)': dict(typ='Mittel', ags='05170044', street='Rathausplatz 20', plz='46562', city='Voerde', email='info@voerde.de'),
    'Waltrop': dict(typ='Mittel', ags='05562036', street='Münsterstr. 1', plz='45731', city='Waltrop', email='stadtverwaltung@waltrop.de'),
    'Warendorf': dict(typ='Mittel', ags='05570052', street='Lange Kesselstr. 4-6', plz='48231', city='Warendorf', email='stadt@warendorf.de'),
    'Warstein': dict(typ='Mittel', ags='05974044', street='Dieplohstr.1', plz='59581', city='Warstein', email='post@warstein.de'),
    'Wegberg': dict(typ='Mittel', ags='05370040', street='Rathausplatz 25', plz='41844', city='Wegberg', email='posteingang@stadt.wegberg.de'),
    'Werdohl': dict(typ='Mittel', ags='05962060', street='Goethestr. 51', plz='58791', city='Werdohl', email='post@werdohl.de'),
    'Werl': dict(typ='Mittel', ags='05974052', street='Hedwig-Dransfeld-Str. 23-23a', plz='59457', city='Werl', email='post@werl.de'),
    'Wermelskirchen': dict(typ='Mittel', ags='05378032', street='Telegrafenstr. 29-33', plz='42929', city='Wermelskirchen', email='post@wermelskirchen.de'),
    'Werne': dict(typ='Mittel', ags='05978040', street='Konrad-Adenauer-Platz 1', plz='59368', city='Werne', email='verwaltung@werne.de'),
    'Wesel': dict(typ='Groß', ags='05170048', street='Klever-Tor-Platz 1', plz='46483', city='Wesel', email='poststelle@wesel.de'),
    'Wesseling': dict(typ='Mittel', ags='05362040', street='Alfons-Müller-Platz', plz='50389', city='Wesseling', email='rathaus@wesseling.de'),
    'Wetter (Ruhr)': dict(typ='Mittel', ags='05954032', street='Kaiserstr. 170', plz='58300', city='Wetter (Ruhr)', email='stadtverwaltung@stadt-wetter.de'),
    'Wiehl': dict(typ='Mittel', ags='05374048', street='Bahnhofstr. 1', plz='51674', city='Wiehl', email='rathaus@wiehl.de'),
    'Willich': dict(typ='Mittel', ags='05166036', street='Hauptstr. 6', plz='47877', city='Willich', email='info@stadt-willich.de'),
    'Wipperfürth': dict(typ='Mittel', ags='05374052', street='Marktplatz 1', plz='51688', city='Wipperfürth', email='info@wipperfuerth.de'),
    'Witten': dict(typ='Groß', ags='05954036', street='Marktstr. 16', plz='58452', city='Witten', email='poststelle@stadt-witten.de'),
    'Wülfrath': dict(typ='Mittel', ags='05158036', street='Am Rathaus 1', plz='42489', city='Wülfrath', email='verwaltung@stadt.wuelfrath.de'),
    'Würselen': dict(typ='Mittel', ags='05334036', street='Morlaixplatz 1', plz='52146', city='Würselen', email='info@wuerselen.de'),
    'Xanten': dict(typ='Mittel', ags='05170052', street='Karthaus 2', plz='46509', city='Xanten', email='post@xanten.de'),
    'Übach-Palenberg': dict(typ='Mittel', ags='05370028', street='Rathausplatz 4', plz='52531', city='Übach-Palenberg', email='info@uebach-palenberg.de'),
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.administrative_unit import AdministrativeUnit
    from app.models.authority import Authority
    from app.services.address_directory import SATZART_KREIS, build_ars_index, load_address_directory
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"
    df = load_address_directory(DESTATIS_PATH)
    nrw = df[df["Land_name"] == "Nordrhein-Westfalen"]
    kreis_ars_index = build_ars_index(nrw[nrw["Satzart"] == SATZART_KREIS])

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Nordrhein-Westfalen").all()
        gpk = {}
        for u in kreis_units:
            gpk.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}
        kreisfreie = {k for k, gset in gpk.items() if len(gset) == 1}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-nrw-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id in ["BAUAKTEN", "BAULASTEN"]:
            for ags_kreis, kreis_name in kreis_names.items():
                addr = kreis_ars_index.get(str(int(ags_kreis)))
                authority_name = f"{kreis_name} - Bauaufsichtsbehörde" if ags_kreis in kreisfreie \
                    else f"Kreis {kreis_name} - Bauaufsichtsbehörde"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Kreis/kreisfreie Stadt)",
                        street=addr.strasse if addr else None, house_number=None,
                        postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                        state="Nordrhein-Westfalen", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} NRW - Kreise",
                    request_type_id=request_type_id, state="Nordrhein-Westfalen", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=BAUO_NRW_URL,
                    source_license="Amtliche Rechtsgrundlage (BauO NRW) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, info in KREISANGEHOERIGE_STAEDTE_AGS.items():
                authority_name = f"Stadt {name} - Bauaufsichtsbehörde ({info['typ']}e kreisangehörige Stadt)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type=f"Untere Bauaufsichtsbehörde ({info['typ']}e kreisangehörige Stadt, § 4 GO NRW)",
                        street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                        state="Nordrhein-Westfalen", phone=None, email=info["email"],
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} NRW - kreisangehörige Städte",
                    request_type_id=request_type_id, state="Nordrhein-Westfalen", ags=info["ags"],
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=VERORDNUNG_URL,
                    source_license="Amtliche Rechtsgrundlage (Verordnung nach § 4 GO NRW) + amtliches "
                                   "Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes="Siehe source-Feld",
                resulting_verification_status="VERIFIED",
            )
            approved += 1
        db.commit()
        print(f"\n{approved} Regeln freigegeben.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
