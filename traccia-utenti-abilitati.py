####
#### Script per l'inserimento degli utenti che possono inserire gli ordini
#### Tutti quelli che scriveranno all'admin saranno inseriti dentro la tabella utenti_abilitati e potranno inserire un nuovo ordine
#### Script legato al file Ordini-Bot.py

import sqlite3
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.functions.messages import UpdateDialogFilterRequest
import configparser
import random
from telethon.tl.types import InputPeerUser

print("Initializing...")
config = configparser.ConfigParser()
config.read('config.ini')
API_ID = config.get('default','api_id')
API_HASH = config.get('default','api_hash')
ID_TELEGRAM_ADMIN = config.get('default','id_telegram_admin')

nome_sessione = "sessions/sessione_traccia_utenti"
client = TelegramClient(nome_sessione, API_ID, API_HASH).start()



# Funzione che permette di ottenere la lista di cartelle dentro telegram
async def ottieni_cartelle():
    try:
        request = await client(GetDialogFiltersRequest())
        return request
    except Exception as error:
        print('Cause: {}'.format(error))
        return error


# Funzione che permette di aggiungere un utente ad una cartella
async def aggiungi_utente_a_cartella(folder_id, new):
    try:
       await client(UpdateDialogFilterRequest(folder_id, new))
    except Exception as error:
        print('Cause: {}'.format(error))
        return error


def aggiunti_utente_in_utenti_abilitati(SENDER, numero_cartella):
    try:
        # Inserisco l'id dell'utente dentro alla tabella utenti_abilitati
        sql_command = "INSERT INTO utenti_abilitati VALUES (?, ?);"
        crsr.execute(sql_command, (str(SENDER), numero_cartella,))
        conn.commit()
    except:
        pass


## Ad ogni messaggio ricevuto
@client.on(events.NewMessage())
async def start(event):
    
    # Ottengo il SENDER del messaggio
    sender = await event.get_sender()
    SENDER = sender.id

    # Eseguo codice solamente se il messaggio NON lo invio io
    if(SENDER != int(ID_TELEGRAM_ADMIN)):
        stringa_evento = str(event)

        # Controllo che sia un messaggio personale
        if("original_update=UpdateShortMessage" in stringa_evento):
            # Appena mi arriva un messaggio controllo che questo utente non l'ho già posizionato dentro una delle cartelle
            try:
                # 1. Controllo che il sender non sia già in una delle cartelle (qui devo controllare entrambe)
                lista_cartelle = await ottieni_cartelle()

                cartella_UNO = lista_cartelle[0]; id_cartella_UNO = cartella_UNO.id
                cartella_DUE = lista_cartelle[1]; id_cartella_DUE = cartella_DUE.id

                # Controllo che l'utente non sia nella cartella UNO
                num_utenti_cartella_1 = 0
                for utente in cartella_UNO.include_peers:
                    # Se trovo il sender dentro la cartella UNO non faccio nulla
                    try:
                        if(SENDER == utente.user_id): return # Utente già presente nella cartella UNO
                        else: num_utenti_cartella_1 += 1 # Altrimenti aumento di uno il numero di chat trovate
                    # Eccezione di controllo, se l'utente non ha un USERID significa che è stata inserita una chat tipo un gruppo dentro la cartella 
                    # In questo caso si aumenta solamente il numero di chat presenti ed il programma non crasha
                    except:
                        num_utenti_cartella_1 += 1

                # Controllo che l'utente non sia nella cartella DUE
                num_utenti_cartella_2 = 0
                for utente in cartella_DUE.include_peers:
                    # Se trovo il sender dentro la cartella DUE non faccio nulla
                    try:
                        if(SENDER == utente.user_id): return # Utente già presente nella cartella DUE
                        else: num_utenti_cartella_2 += 1
                    except:
                        num_utenti_cartella_2 += 1

                # 2. Se l'esecuzione arriva a questo punto significa che è un nuovo utente e devo smistarlo dentro una cartella
                
                # Ottengo l'entità dell'utente
                entity = await client.get_entity(SENDER)
                utente_da_aggiungere = InputPeerUser(entity.id, entity.access_hash) 

                # Se il numero di utenti nella cartella uno è maggiore di quelli nella cartella DUE allora inserisco l'utente nella DUE
                if(num_utenti_cartella_1 > num_utenti_cartella_2):
                    # Aggiungo l'utente sulla cartella DUE
                    cartella_DUE.include_peers.append(utente_da_aggiungere) 
                    await aggiungi_utente_a_cartella(id_cartella_DUE, cartella_DUE) # SENDER posizionato nella cartella DUE
                    aggiunti_utente_in_utenti_abilitati(SENDER, 2) # Aggiungo l'utente dentro al db con CARTELLA 2
                    

                # Altrimenti la cartella DUE ha più utenti della UNO, inserisco l'utente sulla UNO
                elif(num_utenti_cartella_1 < num_utenti_cartella_2):
                    # Aggiungo l'utente sulla cartella UNO
                    cartella_UNO.include_peers.append(utente_da_aggiungere) 
                    await aggiungi_utente_a_cartella(id_cartella_UNO, cartella_UNO)  # SENDER posizionato nella cartella UNO
                    aggiunti_utente_in_utenti_abilitati(SENDER, 1) # Aggiungo l'utente dentro al db con CARTELLA 1

                # Se hanno lo stesso numero di utenti lo inserisco in modo casuale
                elif(num_utenti_cartella_1 == num_utenti_cartella_2):
                    scelta_random = bool(random.getrandbits(1))
                    if(scelta_random):
                        cartella_UNO.include_peers.append(utente_da_aggiungere) 
                        await aggiungi_utente_a_cartella(id_cartella_UNO, cartella_UNO)  # SENDER posizionato nella cartella UNO
                        aggiunti_utente_in_utenti_abilitati(SENDER, 1) # Aggiungo l'utente dentro al db con CARTELLA 2
                    else:
                        cartella_DUE.include_peers.append(utente_da_aggiungere) 
                        await aggiungi_utente_a_cartella(id_cartella_DUE, cartella_DUE) # SENDER posizionato nella cartella DUE
                        aggiunti_utente_in_utenti_abilitati(SENDER, 2) # Aggiungo l'utente dentro al db con CARTELLA 2

                
            except Exception as error:
                print('Cause: {}'.format(error))
        
           



##### MAIN
if __name__ == '__main__':
    try:
        print("Bot Started")
        conn = sqlite3.connect('Databases/Database_utenti_abilitati.db', check_same_thread=False)
        crsr = conn.cursor()
        sql_command = """CREATE TABLE IF NOT EXISTS utenti_abilitati (id_utente VARCHAR(50) PRIMARY KEY, numero_cartella INT(3));"""
        crsr.execute(sql_command)
        print("Tabella utenti_abilitati presente")

        try:
            # Inserisco l'id dell'utente dentro alla tabella utenti_abilitati
            sql_command = "INSERT INTO utenti_abilitati VALUES (?, ?);"
            crsr.execute(sql_command, (str(ID_TELEGRAM_ADMIN), 0,))
            conn.commit()
        except:
            pass
        



        client.run_until_disconnected()
    except Exception as error:
        print('Cause: {}'.format(error))



