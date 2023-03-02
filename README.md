# Sensorknoten-HCU

Dieses Github Repository wurde aufgrund der Bachelorarbeit "Entwicklung, Kalibrierung und Implementierung eines Multisensorsystems für Bauwerksdaten in ein bestehendes Überwachungssystem" erstellt. 
Es dient zum einen der Dokumentation und der Weiternutzung des Codes und zum anderen dient es als Code-Hoster um einen neuen Sensorknoten zu erstellen. 

# Stand des Systems

Um das System final zu nutzen fehlen noch 2 Hardwareanpassungen an dem Sensorknoten, die im Laufe der 7. KW getroffen werden. 
Eine finale Installation soll dann in der 8. KW erfolgen.

# Inhalt

**.env**  -  Eine Environment-Datei als Platzhalter für die Zugangsdaten zur Datenbank fungiert. </br>
**.gitignore**  -  gitignore File, um die Zugangsdaten nicht zu leaken.</br>
**Anleitung_Sensorknoten.pdf**  -  Eine Ausführliche PDF-Anleitung zum Erstellen und Nutzen eines Sensorknotens.</br>
**LICENSE.md**  -  Lizens-File, der den Rechtlichen Rahmen dieses Repo regelt.</br>
**README.md**  -  Beschreibungsdatei</br>
**analyzer.py**  -  benutztes Script, um die Kalibrierparameter zu berechnen. Kann primär nur mit den Datensätzen aus den genutzten Kalibriersensoren umgehen</br>
**installation_sensorknoten.sh**  -  Ein in Bash geschriebenes Installationsscript, welches den Raspberry Pi auf Sensoren vorbereitet, alle Einstellungen trifft und das  sensorknoten.py-Script herunterläd.</br>
**sensorknoten.py**  -  Das wiederholende Python-Script für den Sensorknoten, welches die Sensoren steuert, die Kalibrierfunktionen an die Messdaten anbringt und die Daten auf einen USB-Stick, oder der Datenbank schreibt.</br>
**analyzer.py**  -  benutztes Script, um die Kalibrierparameter zu berechnen. Kann primär nur mit den Datensätzen aus den genutzten Kalibriersensoren umgehen

