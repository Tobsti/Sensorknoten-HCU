import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import StringIO
from scipy import signal
from scipy import stats
from scipy import interpolate

# Der Start- und Entzeitpunkt der Kalibriermessung Auf die zugeschnitten wird. Der Wert ist der UNIX Timestamp, so ist utc verwirrend
first_timestamp_utc = 1668767980
last_timestamp_utc = 1668857980
last_timestamp = last_timestamp_utc - first_timestamp_utc

plt.rc ('font', size = 22)
font = {'weight' : 'bold',
        'size'   : 22}

def timestamp_shift(array, timestamp_start = first_timestamp_utc):
    """Eine Funktion, um den Startzeitpunkt der Kalibrierung festzugelegen und die Auflösung auf eine Sekunde zu beschränken
    Die Funktion nimt als parameter ein array an und gibt ein array in die gleichen Größe, jedoch mit verschobenen Nullpunkt auf die Startsekunde zurück"""
    # Ursprüglicher Startpunkt: 1668763980
    timestamp_shiftet = [int(round((x-timestamp_start),0)) for x in array]
    return timestamp_shiftet


def verbesserung(kalibrierwerte, messwerte, plot = False, sensor="Sensor", messwert_darstellen=True):
    """Diese Funktion nimmt 2 Numpy arrays mit zwei Spalten. Sie gibt die Mittlere Verbesserung und die beiden Elemente einer Linearen Verbesserung zurück.
    Mit dem Wert Plot kann angegeben, ob das Ergebnis mit dem Sensornamen geplottet werden soll und über messwerte_darstellen kann man sich die Zeitreihe zu 
    den Messwerten anzeigen, um Anomalien in der Vermbesserung ausfindig zu machen. Der erste Plot zeigt die Abweichung nach Zeit und der zweite zeigt die Abweichung nach Wert."""
    interpolation = np.interp(kalibrierwerte[:,0], messwerte[:,0], messwerte[:,1])
    verbesserung = kalibrierwerte [:,1] - interpolation
    mittlere_verbesserung = np.mean(verbesserung)
    slope, intercept, r, p, std_err = stats.linregress(interpolation, verbesserung)
    lineare_verbesserung = (slope * kalibrierwerte[:,1])+intercept

    if plot == True:
        fig, verb = plt.subplots()
        verb.plot(kalibrierwerte[:,0],verbesserung,color="red", label="Verbesserung")
        if messwert_darstellen == True:
            verb.plot(kalibrierwerte[:,0],kalibrierwerte[:,1],color="grey", label="Messwert")
        verb.set(xlabel='Sekunden', ylabel='Verbesserung',title=sensor)
        verb.legend(prop={'size': 20})
        plt.show()

        fig, wverb = plt.subplots()
        wverb.plot(kalibrierwerte[:,1],verbesserung,color="grey", label="Verbesserung nach Messwert",marker="x")
        wverb.plot(kalibrierwerte[:,1],lineare_verbesserung,color="red", label = "Lineare Verbesserung")
        wverb.set(xlabel='Messwert', ylabel='Verbesserung',title=sensor)
        wverb.legend(prop={'size': 20})
        plt.show()
    return [mittlere_verbesserung, slope, intercept]




def kreuzkorrelation(zu_synch,sensorkn,startsekunde=28000, endsekunde=36000,plot=False,title="Kreuzkorrelation"):
    """Funktion zur Berechnung der Kreuzkorrelation 
    Diese Funktion schneidet die beiden Arrays zu_synch und sensorkn auf die start und endsekunde zu und interpoliert die dichteren Sensorknoten Daten
    auf die Zeitpunkte der zy_synch Daten.
    Um die Daten vergleichbar werden die interpolierten Daten des Senorknotens und des zu synchronisierenden Datensatzes normiert, in dem der Mittelwert abgezogen und durch 
    die Standardabweichung geteilt wird. 
    Darauf folgt die Berechnung der Kreuzkorrelation und des dazugehörigen lags und die die argmax Fuktion wird der lag herausgefunden, bei dem die Korrelation am höchsten ist.
    Der Graph der Kreuzkorrelation kannn dann geplottet werden und die Funktion gibt den offset zurück."""
    zu_synch =  zu_synch[find_nearest(zu_synch[:,0],startsekunde):find_nearest(zu_synch[:,0],endsekunde),:]
    sensorkn = sensorkn[find_nearest(sensorkn[:,0],startsekunde):find_nearest(sensorkn[:,0],endsekunde),:]

    interp = np.interp(zu_synch[:,0], sensorkn[:,0],sensorkn[:,1])

    zu_synch_mean = (zu_synch[:,1] - np.mean(zu_synch[:,1]))/(np.std(zu_synch[:,1]))
    interp_mean = (interp - np.mean(interp))/np.std(interp)

    corr = signal.correlate(zu_synch_mean, interp_mean, mode="full")/interp_mean.size
    
    lags = signal.correlation_lags(zu_synch_mean.size, interp_mean.size, mode="full")
    offset = lags[np.argmax(corr)]
    if plot == True:
        fig, ax = plt.subplots()
        ax.plot(lags,corr,"-m",label="Korrelation")
        
        ax.set(xlabel='Lag', ylabel='Korrelation',title=title)
        plt.show()

    return offset

def find_nearest(array,value=last_timestamp):
    """Diese Funktion finden den nähesten Sekundendenwert zu einem bestimmten Value. Ist durch find_index_boundaries wohl obsolet."""
    idx = (np.abs(array - value)).argmin()
    return idx

def find_index_boundaries(array,begin_timestamp = first_timestamp_utc,end_timestamp=last_timestamp_utc):
    """Diese Funktion gibt jeweils den Start- und Endindex zu der Start- und Endsekunde, um die Zeitreihen zurechtschneiden zu können"""
    idx_begin = (np.abs(array - begin_timestamp)).argmin()
    idx_end = (np.abs(array - end_timestamp)).argmin()
    return (idx_begin,idx_end)


def plot_data(data_to_plot,xlabel="x",ylabel="y",title="Grafik"):
    """Eine Funktion, die Das Plotten von mehreren Daten vereinfacht."""
    fig, ax = plt.subplots()

    for data,name,color in data_to_plot:
        ax.plot(data[:,0],data[:,1],color,label=name)
    ax.set(xlabel=xlabel, ylabel=ylabel,title=title)
    ax.legend(prop={'size': 20})

    plt.show()


# Import und zurechtschneiden des Sensorknotendatensatzes
data_sensorknoten_roh = np.genfromtxt("zweiter Messtag\protocoll.txt",delimiter=";")
start_idx_sensorknoten, end_idx_sensorknoten = find_index_boundaries(data_sensorknoten_roh[:,0])
data_sensorknoten = np.insert(np.delete(data_sensorknoten_roh,0,1), 0, timestamp_shift(data_sensorknoten_roh[:,0]),axis=1)[start_idx_sensorknoten:end_idx_sensorknoten,:]


# Import des Fluke Datensatzes mit Umrechnung der Zeit in einen UNIX Timestamp und zurechtschneiden
data_fluke_roh=np.genfromtxt("zweiter Messtag\Fluke975_log_2_Zyklus_edit.csv",delimiter=";", skip_header=1)
fluke_offset = 0
fluke_timestamp=[]
with open("zweiter Messtag\Fluke975_log_2_Zyklus_edit.csv") as file:
    for line in file:
        date_raw = line.strip().split(";")[-1]
        if date_raw != 'Zeitstempel':
            date=datetime.strptime(date_raw,"%d.%m.%Y %H:%M:%S")
            fluke_timestamp.append(date.timestamp())
data_fluke_sortet= np.vstack([fluke_timestamp,data_fluke_roh[:,2],data_fluke_roh[:,5],data_fluke_roh[:,7]]).transpose()
start_idx_fluke, end_idx_fluke = find_index_boundaries(data_fluke_sortet[:,0])

data_fluke= np.vstack([timestamp_shift(fluke_timestamp)[start_idx_fluke:end_idx_fluke],data_fluke_roh[start_idx_fluke:end_idx_fluke,2],data_fluke_roh[start_idx_fluke:end_idx_fluke:,5],data_fluke_roh[start_idx_fluke:end_idx_fluke,7]]).transpose()

data_fluke_kalibriert= np.vstack([timestamp_shift(fluke_timestamp)[start_idx_fluke-fluke_offset:end_idx_fluke-fluke_offset],data_fluke_roh[start_idx_fluke:end_idx_fluke,2],data_fluke_roh[start_idx_fluke:end_idx_fluke:,5],data_fluke_roh[start_idx_fluke:end_idx_fluke,7]]).transpose()


# Importieren des Datensatzes der Klimakammer mit Umrechnen in den UNIX Timestamp, sowie dem Zurechtschneiden. Inklusive Offsetverschiebung um 9 
data_ICH110C_roh=np.genfromtxt("zweiter Messtag\ICH110C_Trampler_1und2_zyklus.csv",delimiter=";", skip_header=1)
ich_time_offset = 9
ich_timestamp=[]
with open("zweiter Messtag\ICH110C_Trampler_1und2_zyklus.csv") as file:
    for line in file:
        date_raw = line.strip().split(";")[0]
        if date_raw != 'Time':
            date=datetime.strptime(date_raw,"%d.%m.%Y %H:%M")
            ich_timestamp.append(date.timestamp())
data_ich = np.vstack([ich_timestamp,data_ICH110C_roh[:,2],data_ICH110C_roh[:,6],data_ICH110C_roh[:,9]*10000,data_ICH110C_roh[:,10]*10000]).transpose()
start_idx_ich, end_idx_ich = find_index_boundaries(data_ich[:,0])
#data_ich_s2 wohl obsolet, da das Zuschneiden auf den Kalibriertag nun automatisch geschieht
data_ich_s2 = np.vstack([timestamp_shift(ich_timestamp[start_idx_ich:end_idx_ich]),data_ICH110C_roh[start_idx_ich:end_idx_ich,2],data_ICH110C_roh[start_idx_ich:end_idx_ich,6],data_ICH110C_roh[start_idx_ich:end_idx_ich,9]*10000,data_ICH110C_roh[start_idx_ich:end_idx_ich,10]*10000]).transpose()

data_ich_s2_timecal = np.vstack([timestamp_shift(ich_timestamp[start_idx_ich-ich_time_offset:end_idx_ich-ich_time_offset]),data_ICH110C_roh[start_idx_ich:end_idx_ich,2],data_ICH110C_roh[start_idx_ich:end_idx_ich,6],data_ICH110C_roh[start_idx_ich:end_idx_ich,9]*10000,data_ICH110C_roh[start_idx_ich:end_idx_ich,10]*10000]).transpose()


# Importieren der Kalibrierdaten inklusive umrechnen des Timestamps. Zuschneiden auf den Kalibrierzeitraum und eine verschiebung um den Offset von 17 
data_kal_roh=np.genfromtxt("zweiter Messtag\BaroTemp_Kalibriersensoren copy.csv",delimiter=" ", skip_header=1)
kal_time_offset = 17
kal_timestamp=[]
with open("zweiter Messtag\BaroTemp_Kalibriersensoren copy.csv") as file:
    startzeit = datetime.strptime("18.11.2022 11:15:41","%d.%m.%Y %H:%M:%S")
    for line in file:
        date_raw = line.strip().split(" ")[0]
        if date_raw != 'Startzeit:':
            data_raw = startzeit + timedelta(seconds=int(date_raw))
            
            kal_timestamp.append(data_raw.timestamp())
data_kal_sorted = np.vstack([kal_timestamp,data_kal_roh[:,1],data_kal_roh[:,2]]).transpose()
start_idx_kal, end_idx_kal = find_index_boundaries(data_kal_sorted[:,0])
print(start_idx_kal, end_idx_kal)

data_kal = np.vstack([timestamp_shift(data_kal_sorted[start_idx_kal:end_idx_kal,0]),data_kal_sorted[start_idx_kal:end_idx_kal,1],data_kal_sorted[start_idx_kal:end_idx_kal,2]]).transpose()
# Das kalibriert bezieht sich auf die Zeitsychronisation. Zukünftig sollte der Name angepasst werden.
data_kal_kalibriert = np.vstack([timestamp_shift(data_kal_sorted[start_idx_kal-kal_time_offset:end_idx_kal-kal_time_offset,0]),data_kal_sorted[start_idx_kal:end_idx_kal,1],data_kal_sorted[start_idx_kal:end_idx_kal,2]]).transpose()




# Beginn der einzelnen Abschnitte für die Berechnung
# Möglichkeit der Berechnung der Kreuzkorrelationtsfunktion
plt_kreuzkorr = False
if plt_kreuzkorr == True:
    print(kreuzkorrelation(data_kal_kalibriert[:,[0,1]],data_sensorknoten[:,[0,3]],plot=True,title="Kreuzkorrelation zwischen Fluke und BMP280"))
    print(data_fluke_kalibriert[1,0]-data_fluke_kalibriert[0,0])


# Möglichkeit der Berechnung und das Darstellen des Rauschens.
# Die Berechnung des Rauschens sollte durch eine Funktion ersetzt werden
rauschen = False
if rauschen == True:
    #startsekunde = 28000
    #endsekunde = 36000

    startsekunde = 38000
    endsekunde = 40000

    rauschen_ich =  data_ich_s2[find_nearest( data_ich_s2[:,0],startsekunde):find_nearest( data_ich_s2[:,0],endsekunde),:]
    rauschen_kal = data_kal[find_nearest(data_kal[:,0],startsekunde):find_nearest(data_kal[:,0],endsekunde),:]
    rauschen_sensorknoten = data_sensorknoten[find_nearest(data_sensorknoten[:,0],startsekunde):find_nearest(data_sensorknoten[:,0],endsekunde),:]
    rauschen_fluke = data_fluke[find_nearest(data_fluke[:,0],startsekunde):find_nearest(data_fluke[:,0],endsekunde),:]

    temp_noise = [[rauschen_sensorknoten[:,[0,2]],"BMP280","-b"],
                      [rauschen_sensorknoten[:,[0,3]],"SHT30","-c"],
                      [rauschen_ich[:,[0,1]],"ICH","-k"],
                      [rauschen_kal[:,[0,1]],"Kalibriersensor","-r"],
                      [rauschen_fluke[:,[0,1]],"Fluke","-m"],
                     ]

    hum_noise = [
                      [rauschen_sensorknoten[:,[0,5]],"SHT30","-c"],
                      [rauschen_ich[:,[0,2]],"ICH","-k"],
                      [rauschen_fluke[:,[0,2]],"Fluke","-m"],
                     ]


    press_noise = [[rauschen_sensorknoten[:,[0,7]],"BMP280","-b"],
                      [rauschen_kal[:,[0,2]],"Kalibriersensor","-r"],
                     ]

    plot_data(temp_noise,"Timestamp","Temperatur °C",f'Temperatur zwischen Sekunde {startsekunde} und {endsekunde}')
    plot_data(hum_noise,"Timestamp","% rh",f'Luftfeuchtigkeit zwischen Sekunde {startsekunde} und {endsekunde}')
    plot_data(press_noise,"Timestamp","hPa",f'Luftdruck zwischen Sekunde {startsekunde} und {endsekunde}')




# Vorlage für unterschiedliche Zeitpunkte der kalibrierung mit möglichkeiten diese immer wieder zu plotten.
plot=False
if plot == True:
    temp_raw = [[data_sensorknoten[:,[0,2]],"BMP280","-b"],
                      [data_sensorknoten[:,[0,3]],"SHT30","-c"],
                      [data_sensorknoten[:,[0,4]],"SHT40","-y"],
                      [data_ich_s2[:,[0,1]],"ICH","-k"],
                      [data_kal[:,[0,1]],"Kalibriersensor","-r"],
                      [data_fluke[:,[0,1]],"Fluke","-m"],
                     ]

    temp_synchronisiert = [[data_sensorknoten[:,[0,2]],"BMP280","-b"],
                      [data_sensorknoten[:,[0,3]],"SHT30","-c"],
                      [data_sensorknoten[:,[0,4]],"SHT40","-y"],
                      [data_ich_s2_timecal[:,[0,1]],"ICH","-k"],
                      [data_kal_kalibriert[:,[0,1]],"Kalibriersensor","-r"],
                      [data_fluke_kalibriert[:,[0,1]],"Fluke","-m"],
                     ]

    hum_synchronisiert = [[data_sensorknoten[:,[0,5]],"SHT30","-c"],
                      [data_sensorknoten[:,[0,6]],"SHT40","-y"],
                      [data_ich_s2_timecal[:,[0,2]],"ICH","-k"],
                      [data_fluke_kalibriert[:,[0,2]],"Fluke","-m"],
                     ]

    hum_raw = [[data_sensorknoten[:,[0,5]],"SHT30","-c"],
                      [data_sensorknoten[:,[0,6]],"SHT40","-y"],
                      [data_ich_s2[:,[0,2]],"ICH","-k"],
                      [data_fluke[:,[0,2]],"Fluke","-m"],
                     ]
    press_raw = [[data_sensorknoten[:,[0,7]],"BMP280","-b"],
                      [data_sensorknoten[:,[0,8]],"QMP6988","-c"],
                      [data_kal_kalibriert[:,[0,2]],"Kalibriersensor","-r"],
                     ]



    co2_raw = [       [data_ich_s2_timecal[:,[0,4]],"ICH_Ist","grey"],
                      [data_ich_s2_timecal[:,[0,3]],"ICH_Soll","-k"],
                      [data_fluke_kalibriert[:,[0,3]],"Fluke","-m"],
                      [data_sensorknoten[:,[0,-2]],"SGP30","-g"],
                     ]
    #plot_data(temp_raw,"Timestamp","°C","Temperaturdaten unverändert")
    #plot_data(temp_synchronisiert,"Timestamp","°C","Temperaturdaten")
    #plot_data(hum_raw,"Timestamp","% rh","Relative Luftfeuchtigkeit unverändert")
    #plot_data(press_raw,"Timestamp","hPa","Luftdruck unverändert")
    #plot_data(hum_synchronisiert,"Timestamp","% rh","Relative Luftfeuchtigkeit synchronisiert")
    plot_data(co2_raw,"Timestamp","ppm","CO_2")


# Möglichkeit die Verbesserung darzustellen und berechnen zu lassen.
verb = True
if verb == True:
    print(verbesserung(data_ich_s2_timecal[:,[0,2]], data_sensorknoten[:,[0,6]], True,"Verbesserung des Luftdrucks vom QMP6988 zum Kalibriersensor",False))