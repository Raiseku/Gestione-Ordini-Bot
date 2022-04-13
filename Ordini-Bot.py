
from operator import truediv
import configparser
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import asyncio
import sqlite3
import pandas as pd
from datetime import datetime


print("Initializing...")
config = configparser.ConfigParser()
config.read('config.ini')
API_ID = config.get('default','api_id')
API_HASH = config.get('default','api_hash')
BOT_TOKEN = config.get('default','bot_token')
ID_TELEGRAM_ADMIN = config.get('default','id_telegram_admin')
nome_sessione = "sessions/sessione_bot"


client = TelegramClient(nome_sessione, API_ID, API_HASH).start(bot_token = BOT_TOKEN)


## INFO generiche di utilizzo
testo_annullamento = "<b>Ricevuto 📖 </b>\nGrazie di avermi contattato. Scrivi nuovamente /start se vuoi ordinare un prodotto."


ID_AMAZON = 1
ID_ZALANDO = 2 


###### FUNZIONI SINCRONE
def press_event(user_id):
    return events.CallbackQuery(func=lambda e: e.sender_id == user_id)

### COMANDO DI CREAZIONE DEL FILE CSV
def crea_csv(cartella):
    if(cartella == "ordiniCompleti"):
        df = pd.read_sql('SELECT * from ordini', conn)
        df.to_csv('File CSV/ordini_totali_confermati.csv')
    elif(cartella == "cartella1"):
        df = pd.read_sql('SELECT * from ordini_cartella_1', conn)
        df.to_csv('File CSV/ordini_cartella1_confermati.csv')
    elif(cartella == "cartella2"):
        df = pd.read_sql('SELECT * from ordini_cartella_2', conn)
        df.to_csv('File CSV/ordini_cartella2_confermati.csv')

    


### GESTIONE LISTA ORDINI
def gestione_for_compatto(ans):
    testo_messaggio = ""
    for i in ans:
        id = i[0]
        first_name = i[3]
        risp1 = i[5]
        data = i[10]
        testo_messaggio += "<b>"+ str(id) +"</b> | " + "<b>"+ str(first_name) +"</b> | " + "<b>"+ str(risp1)+"</b> | " + "<b>"+ str(data)+"</b>\n"
    tot = "<b>Ricevuto 📖 </b> Informazioni sugli ordini:\n\n"+testo_messaggio
    return tot


def get_full_info_su_utente(ans):
    for i in ans:
        id = i[0]
        id_utente = i[1]
        username = i[2]
        first_name = i[3]
        last_name = i[4]
        risp1 = i[5]
        risp2 = i[6]
        risp3 = i[7]
        risp4 = i[8]
        risp5 = i[9]
        data = i[10]
        cartella = i[11]
        testo_messaggio = "<b>CLIENTE</b>\n"\
            "<b>ID ordine: </b>"+ str(id) +"\n"\
            "<b>ID utente telegram: </b>"+ str(id_utente) +"\n"\
            "<b>Username: </b>"+ str(username) +"\n"\
            "<b>Nome: </b>"+ str(first_name) +"\n"\
            "<b>Cognome: </b>"+ str(last_name) +"\n\n"\
            "<b>ORDINE</b>\n"\
            "<b>Risposta 1: </b>"+ str(risp1) +"\n"\
            "<b>Risposta 2: </b>"+ str(risp2) +"\n"\
            "<b>Risposta 3: </b>"+ str(risp3) +"\n"\
            "<b>Risposta 4: </b>"+ str(risp4) +"\n"\
            "<b>Risposta 5: </b>"+ str(risp5) +"\n"\
            "<b>Data ordine: </b>"+ str(data) +"\n"\
            "<b>Cartella: </b>"+ str(cartella) +"\n"
    return "<b>Ricevuto 📖</b>\nDettaglio del cliente da te selezionato:\n\n" + testo_messaggio


def ottieni_disponibilita(ID_SITO):
    sql_command = "SELECT * FROM abilitazione_siti WHERE Id=?;"
    ans = crsr.execute(sql_command, [ID_SITO])
    ans = crsr.fetchall() 
    lista_id = []
    nome_siti = []
    lista_disponibilita = ""
    if(ans):
        for i in ans:
            lista_id.append(i[0])
            nome_siti.append(i[1])
            lista_disponibilita = i[2]
    return lista_disponibilita



def controlla_utente_abilitato(SENDER):
    crsr_utenti_abilitati.execute("SELECT * FROM utenti_abilitati")
    ans = crsr_utenti_abilitati.fetchall() 
    if(ans):
        for i in ans:
            id_utente = i[0]
            if(str(id_utente) == str(SENDER)):
                return True
    return False   
    


##### FUNZIONI ASINCRONE

@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    sender = await event.get_sender()
    SENDER = sender.id

    ## Controllo che chi ha avviato il bot abbia precedentemente scritto all'admin
    if(controlla_utente_abilitato(SENDER)):
        
        try:
            async with client.conversation(await event.get_chat(), exclusive=True) as conv:
                while True:
                    keyboard_1 = [
                        [
                        Button.inline("Nuovo ordine", b"aggiungi_ordine")
                        ],
                        [
                        Button.inline("Termina conversazione", b"termina_conversazione")
                        ]
                    ]

                    msg_iniziale = await conv.send_message("Ciao, io sono <b>Ordini-Bot</b> 🤖\nClicca \"Nuovo ordine\" per inserire un nuovo ordine, oppure termina la conversazione.", buttons=keyboard_1, parse_mode='html')

                    press = await conv.wait_event(press_event(SENDER))
                    scelta_1 = str(press.data.decode("utf-8"))

                    if(scelta_1 == "aggiungi_ordine"):
                        msg_ricezione = await conv.send_message('<b>Ricevuto 🤖</b>\nRispondi alle seguenti domande:', parse_mode='html')
                        await msg_iniziale.delete()
                        
                        

                        ### DOMANDA 1
                        keyboard_1 = [
                            [  
                                Button.inline("Amazon", b"amazon"), 
                                Button.inline("Zalando", b"zalando")
                            ],
                            [
                                Button.inline("Annulla ordine", b"ANNULLATO")
                            ]
                        ]

                        sito_disponibile = False
                        while sito_disponibile is False:
                            inserimento_beyboard = await conv.send_message("<b>DOMANDA 1:</b> Su che sito vuoi fare l'ordine?", buttons=keyboard_1, parse_mode='html')
                            press = await conv.wait_event(press_event(SENDER))
                            scelta_1 = str(press.data.decode("utf-8"))
                            if(scelta_1 == "amazon"):
                                disponibilita_amazon = ottieni_disponibilita(ID_AMAZON) # 1 è l'id di amazon
                                if(disponibilita_amazon != "Disponibile"):
                                    #scelta_1 = "amazon" # Lui ha scelto amazon, quindi finchè non mi cambia scelta non lo lascio andare
                                    await inserimento_beyboard.delete()
                                    await conv.send_message("⚠️ Attenzione ⚠️\nAttualmente non prendiamo ordini per <b>Amazon</b>, prova a scegliere un altro sito.", parse_mode='html')
                                else:
                                    sito_disponibile = True # ed esco dal ciclo

                            elif(scelta_1 == "zalando"): 
                                disponibilita_zalando = ottieni_disponibilita(ID_ZALANDO) # 2 è l'id di zalando
                                if(disponibilita_zalando != "Disponibile"):
                                    await inserimento_beyboard.delete()
                                    await conv.send_message("⚠️ Attenzione ⚠️\nAttualmente non prendiamo ordini per <b>Zalando</b>, prova a scegliere un altro sito.", parse_mode='html')
                                else:
                                    sito_disponibile = True # ed esco dal ciclo

                            #await conv.send_message('Hai scelto :' + str(scelta_1)) # Scommentare questa riga per restituire come messaggio la scelta cliccata dall'utente
                            elif(scelta_1 == "ANNULLATO"): await inserimento_beyboard.delete(); await msg_ricezione.delete(); await event.respond(testo_annullamento, parse_mode='html'); return

                        # Elimino la Keyboard
                        await inserimento_beyboard.delete()
                    
                        ### DOMANDA 2
                        keyboard_2 = [
                            [
                                Button.inline("Annulla ordine", b"ANNULLATO")
                            ]
                        ]

                        while True:
                            inserimento_beyboard = await conv.send_message("<b>DOMANDA 2:</b> seconda domanda da modificare", buttons=keyboard_2, parse_mode='html')
                            tasks = [conv.wait_event(press_event(SENDER)), conv.get_response()]
                            done, pendind = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                            CLICK_O_TESTO = done.pop().result()
                            if type(CLICK_O_TESTO) is events.callbackquery.CallbackQuery.Event:
                                scelta_2 = str(CLICK_O_TESTO.data.decode('utf-8'))
                            else:
                                scelta_2 = CLICK_O_TESTO.text
                                if(len(scelta_2) > 30):
                                    await conv.send_message("⚠️ Attenzione ⚠️\nLa lunghezza della risposta deve essere minore di trenta caratteri, riprovare.", parse_mode='html')
                                    continue
                                else:
                                    # Altrimenti la risposta è accettabile, quindi esco dal ciclo
                                    break

                            if(scelta_2 == "ANNULLATO"): await inserimento_beyboard.delete(); await msg_ricezione.delete(); await event.respond(testo_annullamento, parse_mode='html'); return


                        await inserimento_beyboard.delete()

                        ### DOMANDA 3
                        keyboard_3 = [
                            [
                                Button.inline("Annulla ordine", b"ANNULLATO")
                            ]
                        ]

                        while True:
                            inserimento_beyboard = await conv.send_message("<b>DOMANDA 3:</b> terza domanda da modificare", buttons=keyboard_3, parse_mode='html')
                            tasks = [conv.wait_event(press_event(SENDER)), conv.get_response()]
                            done, pendind = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                            CLICK_O_TESTO = done.pop().result()
                            if type(CLICK_O_TESTO) is events.callbackquery.CallbackQuery.Event:
                                scelta_3 = str(CLICK_O_TESTO.data.decode('utf-8'))
                            else:
                                scelta_3 = CLICK_O_TESTO.text
                                if(len(scelta_3) > 30):
                                    await conv.send_message("⚠️ Attenzione ⚠️\nLa lunghezza della risposta deve essere minore di trenta caratteri, riprovare.", parse_mode='html')
                                    continue
                                else:
                                    # Altrimenti la risposta è accettabile, quindi esco dal ciclo
                                    break
                            if(scelta_3 == "ANNULLATO"): await inserimento_beyboard.delete(); await msg_ricezione.delete(); await event.respond(testo_annullamento, parse_mode='html'); return


                        await inserimento_beyboard.delete()

                        ### DOMANDA 4
                        keyboard_4 = [
                            [
                                Button.inline("Annulla ordine", b"ANNULLATO")
                            ]
                        ]


                        while True:
                            inserimento_beyboard = await conv.send_message("<b>DOMANDA 4:</b> quarta domanda da modificare", buttons=keyboard_4, parse_mode='html')
                            tasks = [conv.wait_event(press_event(SENDER)), conv.get_response()]
                            done, pendind = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                            CLICK_O_TESTO = done.pop().result()
                            if type(CLICK_O_TESTO) is events.callbackquery.CallbackQuery.Event:
                                scelta_4 = str(CLICK_O_TESTO.data.decode('utf-8'))
                            else:
                                scelta_4 = CLICK_O_TESTO.text
                                if(len(scelta_4) > 30):
                                    await conv.send_message("⚠️ Attenzione ⚠️\nLa lunghezza della risposta deve essere minore di trenta caratteri, riprovare.", parse_mode='html')
                                    continue
                                else:
                                    # Altrimenti la risposta è accettabile, quindi esco dal ciclo
                                    break

                            if(scelta_4 == "ANNULLATO"): await inserimento_beyboard.delete(); await msg_ricezione.delete(); await event.respond(testo_annullamento, parse_mode='html'); return


                        await inserimento_beyboard.delete()


                        ### DOMANDA 5
                        keyboard_5 = [
                            [
                                Button.inline("Annulla ordine", b"ANNULLATO")
                            ]
                        ]

                        while True:
                            inserimento_beyboard = await conv.send_message("<b>DOMANDA 5:</b> quinta domanda da modificare", buttons=keyboard_5, parse_mode='html')
                            tasks = [conv.wait_event(press_event(SENDER)), conv.get_response()]
                            done, pendind = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                            CLICK_O_TESTO = done.pop().result()
                            if type(CLICK_O_TESTO) is events.callbackquery.CallbackQuery.Event:
                                scelta_5 = str(CLICK_O_TESTO.data.decode('utf-8'))
                            else:
                                scelta_5 = CLICK_O_TESTO.text
                                if(len(scelta_5) > 30):
                                    await conv.send_message("⚠️ Attenzione ⚠️\nLa lunghezza della risposta deve essere minore di trenta caratteri, riprovare.", parse_mode='html')
                                    continue
                                else:
                                    break

                            if(scelta_5 == "ANNULLATO"): await inserimento_beyboard.delete(); await msg_ricezione.delete(); await event.respond(testo_annullamento, parse_mode='html'); return

                        await inserimento_beyboard.delete()

                        ### DOMANDA FINALE
                        keyboard_LAST = [
                            [
                            Button.inline("Conferma ordine", b"CONFERMATO")
                            ],
                            [
                            Button.inline("Annulla ordine", b"ANNULLATO")
                            ]
                        ]

                        inserimento_beyboard = await conv.send_message("<b>Domande terminate</b>, vuoi confermare l'ordine?", buttons=keyboard_LAST, parse_mode='html')
                        press = await conv.wait_event(press_event(SENDER))
                        scelta_last = str(press.data.decode("utf-8"))

                        ### ANNULLAMENTO DELL'ORDINE
                        if(scelta_last == "ANNULLATO"): 
                            await inserimento_beyboard.delete(); await msg_ricezione.delete(); await event.respond(testo_annullamento, parse_mode='html'); return

                        else:
                            # Ottengo le informazioni dell'utente che ha scritto al bot ed ha risposto a tutte le domande
                            if(sender.username == ""): username = "non presente"
                            else: username = sender.username #USERNAME

                            if(sender.first_name == ""): first_name = "non presente"
                            else: first_name = sender.first_name #NOME

                            if(sender.last_name == ""): last_name = "non presente"
                            else: last_name = sender.last_name #COGNOME

                            # Ottengo la data e l'ora di quando ha confermato l'ordine
                            now = datetime.now()
                            dt_string = now.strftime("%d/%m/%Y")

                            # Ottengo la cartella in cui è posizionato l'utente, la query va fatta al DB [utenti_abilitati]
                            crsr_utenti_abilitati.execute("""SELECT * FROM utenti_abilitati WHERE Id_utente = (?)""", (SENDER,))
                            ans = crsr_utenti_abilitati.fetchall() 
                            if(ans):
                                for i in ans:
                                    cartella_utente = i[1]
                            else:
                                cartella_utente = 0

                            # Inserisco l'utente e le risposte che ha fornito dentro al database SICURAMENTE nella tabella generale
                            params = (sender.id, username, first_name, last_name, scelta_1, scelta_2, scelta_3, scelta_4, scelta_5, dt_string, cartella_utente)
                            sql_command = "INSERT INTO ordini VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
                            crsr.execute(sql_command, params)
                            conn.commit()

                            # poi in base alla cartella inserisco in quelli gerarchici
                            # INSERT DENTRO TABELLA GENERALE E TABELLA CARTELLA 1
                            if(cartella_utente == 1):
                                params = (sender.id, username, first_name, last_name, scelta_1, scelta_2, scelta_3, scelta_4, scelta_5, dt_string, cartella_utente)
                                sql_command = "INSERT INTO ordini_cartella_1 VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
                                crsr.execute(sql_command, params)
                                conn.commit()

                            # INSERT DENTRO TABELLA GENERALE E TABELLA CARTELLA 1
                            elif(cartella_utente == 2):
                                params = (sender.id, username, first_name, last_name, scelta_1, scelta_2, scelta_3, scelta_4, scelta_5, dt_string, cartella_utente)
                                sql_command = "INSERT INTO ordini_cartella_2 VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
                                crsr.execute(sql_command, params)
                                conn.commit()


                            ### Termino la conversazione
                            await conv.send_message('<b>Ordine correttamente inserito ✔️\n</b>Grazie di avermi contattato. Scrivi /start per inserire un nuovo ordine.', parse_mode='html')
                            
                            ## Quando l'utente ha inserito un nuovo ordine lo aggiungo direttamente al csv, così da non dover cliccare sempre il bottone sulla gestione degli ordini
                            try:
                                if(cartella_utente == 0):
                                    crea_csv("ordiniCompleti")
                                elif(cartella_utente == 1):
                                    crea_csv("cartella1")
                                elif(cartella_utente == 2):
                                    crea_csv("cartella2")
                            except:
                                print("Non faccio nulla, c'è stato qualche problema durante la creazione del file. In questo caso sarà l'admin a dover creare manualmente il file")
                            await inserimento_beyboard.delete()
                            await msg_ricezione.delete()
                            return 

                    elif (scelta_1 == "termina_conversazione"):
                        await msg_iniziale.delete()
                        await event.respond(testo_annullamento, parse_mode="html")
                        return


        except Exception as e:
            print(e)
            await client.send_message(SENDER, "<b>Conversazione Terminata ✔️</b>\nÈ trascorso troppo tempo dall'ultima tua risposta. Scrivi /start per inserire un nuovo ordine.", parse_mode='html')


    else:
        # Ottengo l'entità dell'admin che servirà ad inviare un messaggio agli utenti che non hanno l'abilitazione ad inserire un ordine
        entity = await client.get_entity(int(ID_TELEGRAM_ADMIN))
        await client.send_message(SENDER, "<b>Errore ❌</b>\nNon hai il permesso di utilizzare questo comando. Invia un messaggio a "+"t.me/"+entity.username+" per essere abilitato.", parse_mode='html')
    
    


 
@client.on(events.NewMessage(pattern="/gestisciOrdini"))
async def start(event):

    sender = await event.get_sender()
    SENDER = sender.id

    ### Controllo che il SENDER sia uno degli admin definiti dentro il file ad_admin.txt
    lista_id_admin = []
    with open('id_admin.txt','r') as f:
        for i in f.readlines():
            lista_id_admin.append(i.strip())

    ### Se il SENDER è dentro la lista degli admin mostro i bottoni, altrimenti invio un messaggio di errore dato che non ha i permessi
    if(str(SENDER) in lista_id_admin):
        try:
            ## INIZIO DELLA CONVERSAZIONE
            async with client.conversation(await event.get_chat(), exclusive=True) as conv:
                # Quando la conversazione inizia imposto una variabile che mi servirà per ricordare la scelta fatta dall'utente
                cartella_selezionata_in_conversazione = ""
#
#
# _____________________________________________ SCELTA GESTIONE CARTELLE
#
#
                while True:
                    # Se non è ancora stata selezionata una cartella allora la faccio selezionare
                    if(cartella_selezionata_in_conversazione == ""):
                        ### Messaggio iniziale in cui l'utente sceglie quale utenti vuole gestire
                        keyboard_selezionamento_cartella = [
                            [
                                Button.inline("Cartella ordini totali", b"gestione_totale"),
                            ],
                            [
                                Button.inline("Cartella 1", b"gestione_cartella_1"),
                                Button.inline("Cartella 2", b"gestione_cartella_2")
                            ],
                            [
                                Button.inline("Termina conversazione", b"termina_conversazione")
                            ]
                        ]

                        testo_di_gestione = "<b>💼 GESTIONE ORDINI 💼</b>\n\nSeleziona la cartella di cui vuoi gestire gli ordini"
                        gestione_ordini_keyboard = await conv.send_message(testo_di_gestione, buttons=keyboard_selezionamento_cartella, parse_mode='html')
                        press = await conv.wait_event(press_event(SENDER))
                        scelta_gestione_cartelle = str(press.data.decode("utf-8"))
                        #id_modificare = press.original_update.msg_id
                        if(scelta_gestione_cartelle == "gestione_totale"):
                            cartella_selezionata_in_conversazione = "gestione_totale"
                            await gestione_ordini_keyboard.delete()

                        elif(scelta_gestione_cartelle == "gestione_cartella_1"):
                            cartella_selezionata_in_conversazione = "gestione_cartella_1"
                            print("GESTISCO ORDINI DELLA CARTELLA 1")
                            await gestione_ordini_keyboard.delete()

                        elif(scelta_gestione_cartelle == "gestione_cartella_2"):
                            cartella_selezionata_in_conversazione = "gestione_cartella_2"
                            print("GESTISCO ORDINI DELLA CARTELLA 2")
                            await gestione_ordini_keyboard.delete()


                        elif(scelta_gestione_cartelle == "termina_conversazione"):
                            await gestione_ordini_keyboard.delete()
                            await conv.send_message("<b>Conversazione terminata ✔️</b>\n", parse_mode='html')
                            return
                    
                    # Se invece l'utente ha già selezionato la cartella su cui vuole lavorare allora non stampo il messaggio precedente.
                    else:
#
#
# _____________________________________________ CARTELLA GENERALE
#
#
                        if(cartella_selezionata_in_conversazione == "gestione_totale"):

                            keyboard_di_gestione = [
                                [
                                    Button.inline("Lista Ordini", b"lista_ordini"),
                                    Button.inline("Seleziona Ordine", b"dettaglio_ordine")
                                ],
                                [
                                    Button.inline("Crea CSV", b"crea_csv"),
                                    Button.inline("Cancella Ordine", b"elimina_ordine")
                                ],
                                [
                                    Button.inline("Gestisci disponibilità siti", b"gestione_disponibilita")
                                ],
                                [
                                    Button.inline("Termina conversazione", b"termina_conversazione")
                                ]
                            ]

                            ### Messaggio di gestione con i bottoni
                            testo_di_gestione = "<b>💼 GESTIONE ORDINI 💼</b>\n📁 Cartella ordini totali"
                            gestione_ordini_keyboard = await conv.send_message(testo_di_gestione, buttons=keyboard_di_gestione, parse_mode='html')
                            press = await conv.wait_event(press_event(SENDER))
                            scelta_GESTIONE = str(press.data.decode("utf-8"))
                            #id_modificare = press.original_update.msg_id

                            ### BOTTONE GESTIONE DISPONIBILITà
                            if(scelta_GESTIONE == "gestione_disponibilita"):
                                # 1. Invio un messaggio con lo stato attuale della disponibilità
                                disponibilita_amazon = ottieni_disponibilita(ID_AMAZON) # 1 è l'id di amazon
                                disponibilita_zalando = ottieni_disponibilita(ID_ZALANDO) # 2 è l'id di zalando

                                testo_messaggio = "<b>Ricevuto ✔️</b>\nLo stato attuale è il seguente:\n<b>Amazon</b>: "+disponibilita_amazon+"\n<b>Zalando</b>: "+disponibilita_zalando
                                await conv.send_message(testo_messaggio, parse_mode='html')
                                await gestione_ordini_keyboard.delete()

                                keyboard_disponibilita_siti_2 = [
                                    [
                                        Button.inline("Amazon", b"scelta_amazon"),
                                        Button.inline("Zalando", b"scelta_zalando")
                                    ],
                                    [
                                        Button.inline("Torna indietro", b"torna_indietro")
                                    ]   
                                ]

                                gestione_modifica_sito_keyboard = await conv.send_message("Di quale sito vuoi modificare lo stato?", buttons=keyboard_disponibilita_siti_2, parse_mode='html')
                                modifica = await conv.wait_event(press_event(SENDER))
                                scelta_disponibilita = str(modifica.data.decode("utf-8"))

                                if(scelta_disponibilita == "torna_indietro"):
                                    await gestione_modifica_sito_keyboard.delete()
                                    continue
                                    

                                elif(scelta_disponibilita == "scelta_amazon"):
                                    if(disponibilita_amazon == "Disponibile"):
                                        nuova_disp_amazon = "Non disponibile"
                                        update_amazon = (nuova_disp_amazon, ID_AMAZON)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_amazon)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Amazon</b> è: <b>"+nuova_disp_amazon+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                    elif(disponibilita_amazon == "Non disponibile"):
                                        nuova_disp_amazon = "Disponibile"
                                        update_amazon = (nuova_disp_amazon, ID_AMAZON)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_amazon)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Amazon</b> è: <b>"+nuova_disp_amazon+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                

                                elif(scelta_disponibilita == "scelta_zalando"):
                                    if(disponibilita_zalando == "Disponibile"):
                                        nuova_disp_zalando = "Non disponibile"
                                        update_zalando = (nuova_disp_zalando, ID_ZALANDO)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_zalando)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Zalando</b> è: <b>"+nuova_disp_zalando+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                    elif(disponibilita_zalando == "Non disponibile"):
                                        nuova_disp_zalando = "Disponibile"
                                        update_zalando = (nuova_disp_zalando, ID_ZALANDO)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_zalando)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Zalando</b> è: <b>"+nuova_disp_zalando+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                    

                            ### BOTTONE LISTA ORDINI COMPLETI
                            if(scelta_GESTIONE == "lista_ordini"):
                                crsr.execute("SELECT * FROM ordini")
                                ans = crsr.fetchall() 
                                if(ans):
                                    testo_messaggio = gestione_for_compatto(ans) 
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()
                                else:
                                    testo_messaggio = "Non sono presenti ordini all'interno del database."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()



                            ### BOTTONE DETTAGLIO ORDINE
                            elif(scelta_GESTIONE == "dettaglio_ordine"):
                                crsr.execute("SELECT * FROM ordini")
                                ans = crsr.fetchall() 
                                if(ans):
                                    testo_messaggio = gestione_for_compatto(ans)
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await conv.send_message("<b>Ricevuto ✔️</b>Inviami il numero dell'ordine di cui vuoi il dettaglio", parse_mode='html')
                                    resp = (await conv.get_response()).raw_text
                                    numero = resp
                                    if(resp.isnumeric()):
                                        sql_command = "SELECT * FROM ordini WHERE Id = (?);"
                                        ans = crsr.execute(sql_command, [numero])
                                        ans = crsr.fetchall() 
                                        if(ans):
                                            testo_messaggio = get_full_info_su_utente(ans)
                                            await conv.send_message(testo_messaggio, parse_mode='html')
                                            await gestione_ordini_keyboard.delete()
                                        else:
                                            testo_messaggio = "Errore ❌\nIl messaggio con id {} non è presente.".format(numero)
                                            await conv.send_message(testo_messaggio, parse_mode='html')
                                            await gestione_ordini_keyboard.delete()
                                    else:
                                        testo_messaggio = "Errore ❌\nL'<b>ID</b> deve essere numerico."
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                else:
                                    testo_messaggio = "Non sono presenti ordini all'interno del database."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()

                                
                            ### BOTTONE CREA CSV
                            elif(scelta_GESTIONE == "crea_csv"):
                                try:
                                    crea_csv("ordiniCompleti")
                                    testo_messaggio = "<b>File csv creato correttamente ✔️</b>\nLo troverai nella stessa cartella di questo codice."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()
                                except:
                                    testo_messaggio = "Errore ❌\nRiprova più tardi, attualmente non posso creare il file csv."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()



                            ### BOTTONE ELIMINA ORDINE
                            elif(scelta_GESTIONE == "elimina_ordine"):
                                # Select per mostrare tutti gli ordini fino ad ora inseriti
                                crsr.execute("SELECT * FROM ordini")
                                ans = crsr.fetchall() 
                                if(ans):
                                    testo_messaggio = gestione_for_compatto(ans) 
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()

                                    # Inizio dell'operazione di delete
                                    await conv.send_message("<b>Ricevuto ⌨️</b>\nInviami il numero dell'ordine che vuoi eliminare", parse_mode='html')
                                    resp = (await conv.get_response()).raw_text
                                    numero = resp
                                    if(numero.isnumeric()):
                                        ## SELECT PER DOPO
                                        sql_command = "SELECT * FROM ordini WHERE Id = (?);"
                                        ans_SELECT = crsr.execute(sql_command, [numero])
                                        ans_SELECT = crsr.fetchall() 
                                        ## DELETE
                                        sql_command = "DELETE FROM ordini WHERE Id = (?);"
                                        ans = crsr.execute(sql_command, (numero,))
                                        conn.commit()
                                        # Se l'ordine selezionato non è presente allora restituisco un errore
                                        if ans.rowcount < 1:
                                            testo_messaggio = "Errore ❌\nL'ordine con ID {} non è presente.".format(numero)
                                            await conv.send_message(testo_messaggio, parse_mode='html')
                                            await gestione_ordini_keyboard.delete()

                                        # Altrimenti restituisco il messaggio che la righe è stata effettivamente eliminata, inoltre aggiorno il file CSV
                                        else: 
                                            testo_messaggio = ""
                                            for i in ans_SELECT:
                                                numero_id = i[0]
                                                testo_messaggio = "<b>Ricevuto 🗑️</b>\n\nHo eliminato l'ordine con ID <b>{}</b>.".format(numero_id)
                                                await conv.send_message(testo_messaggio, parse_mode='html')
                                                await gestione_ordini_keyboard.delete()
                                            try:
                                                crea_csv("ordiniCompleti")
                                                testo_messaggio = "<b>File csv aggiornato correttamente ✔️</b>\nLo troverai nella stessa cartella di questo codice."
                                                await conv.send_message(testo_messaggio, parse_mode='html')
                                                await gestione_ordini_keyboard.delete()
                                            except:
                                                testo_messaggio = "<b>Errore ❌</b>\nAttualmente non posso aggiornare il file csv, riprova più tardi."
                                                await conv.send_message(testo_messaggio, parse_mode='html')
                                                await gestione_ordini_keyboard.delete()

                                    else:
                                        testo_messaggio = "<b>Errore ❌</b>\nL'<b>ID</b> dell'ordine deve essere numerico."
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()

                                else:
                                    testo_messaggio = "<b>Errore ❌</b>\nNon sono presenti ordini all'interno del database, non è possibile svolgere l'operazione di cancellazione."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()

                            ### BOTTONE TERMINA CONVERSAZIONE
                            elif(scelta_GESTIONE == "termina_conversazione"):
                                await gestione_ordini_keyboard.delete()
                                await conv.send_message("<b>Conversazione terminata ✔️</b>\n", parse_mode='html')
                                return

#
#
# _____________________________________________ GESTIONE CARTELLA 1
#
#
                        elif(scelta_gestione_cartelle == "gestione_cartella_1"):
                            keyboard_di_gestione = [
                                [
                                    Button.inline("Lista Ordini", b"lista_ordini"),
                                    Button.inline("Seleziona Ordine", b"dettaglio_ordine")
                                ],
                                [
                                    Button.inline("Crea CSV", b"crea_csv"),
                                    Button.inline("Cancella Ordine", b"elimina_ordine")
                                ],
                                [
                                    Button.inline("Gestisci disponibilità siti", b"gestione_disponibilita")
                                ],
                                [
                                    Button.inline("Termina conversazione", b"termina_conversazione")
                                ]
                            ]

                            ### Messaggio di gestione con i bottoni
                            testo_di_gestione = "<b>💼 GESTIONE ORDINI</b>\n📁 Cartella uno (1)"
                            gestione_ordini_keyboard = await conv.send_message(testo_di_gestione, buttons=keyboard_di_gestione, parse_mode='html')
                            press = await conv.wait_event(press_event(SENDER))
                            scelta_GESTIONE = str(press.data.decode("utf-8"))

                            if(scelta_GESTIONE == "gestione_disponibilita"):
                                # 1. Invio un messaggio con lo stato attuale della disponibilità
                                disponibilita_amazon = ottieni_disponibilita(ID_AMAZON) # 1 è l'id di amazon
                                disponibilita_zalando = ottieni_disponibilita(ID_ZALANDO) # 2 è l'id di zalando

                                testo_messaggio = "<b>Ricevuto ✔️</b>\nLo stato attuale è il seguente:\n<b>Amazon</b>: "+disponibilita_amazon+"\n<b>Zalando</b>: "+disponibilita_zalando
                                await conv.send_message(testo_messaggio, parse_mode='html')
                                await gestione_ordini_keyboard.delete()

                                keyboard_disponibilita_siti_2 = [
                                    [
                                        Button.inline("Amazon", b"scelta_amazon"),
                                        Button.inline("Zalando", b"scelta_zalando")
                                    ],
                                    [
                                        Button.inline("Torna indietro", b"torna_indietro")
                                    ]   
                                ]

                                gestione_modifica_sito_keyboard = await conv.send_message("Di quale sito vuoi modificare lo stato?", buttons=keyboard_disponibilita_siti_2, parse_mode='html')
                                modifica = await conv.wait_event(press_event(SENDER))
                                scelta_disponibilita = str(modifica.data.decode("utf-8"))

                                if(scelta_disponibilita == "torna_indietro"):
                                    await gestione_modifica_sito_keyboard.delete()
                                    continue
                                    

                                elif(scelta_disponibilita == "scelta_amazon"):
                                    if(disponibilita_amazon == "Disponibile"):
                                        nuova_disp_amazon = "Non disponibile"
                                        update_amazon = (nuova_disp_amazon, ID_AMAZON)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_amazon)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Amazon</b> è: <b>"+nuova_disp_amazon+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                    elif(disponibilita_amazon == "Non disponibile"):
                                        nuova_disp_amazon = "Disponibile"
                                        update_amazon = (nuova_disp_amazon, ID_AMAZON)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_amazon)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Amazon</b> è: <b>"+nuova_disp_amazon+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                

                                elif(scelta_disponibilita == "scelta_zalando"):
                                    if(disponibilita_zalando == "Disponibile"):
                                        nuova_disp_zalando = "Non disponibile"
                                        update_zalando = (nuova_disp_zalando, ID_ZALANDO)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_zalando)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Zalando</b> è: <b>"+nuova_disp_zalando+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                    elif(disponibilita_zalando == "Non disponibile"):
                                        nuova_disp_zalando = "Disponibile"
                                        update_zalando = (nuova_disp_zalando, ID_ZALANDO)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_zalando)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Zalando</b> è: <b>"+nuova_disp_zalando+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                    

                            ### BOTTONE LISTA ORDINI COMPLETI
                            if(scelta_GESTIONE == "lista_ordini"):
                                crsr.execute("SELECT * FROM ordini_cartella_1")
                                ans = crsr.fetchall() 
                                if(ans):
                                    testo_messaggio = gestione_for_compatto(ans) 
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()
                                else:
                                    testo_messaggio = "Non sono presenti ordini all'interno del database."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()



                            ### BOTTONE DETTAGLIO ORDINE
                            elif(scelta_GESTIONE == "dettaglio_ordine"):
                                crsr.execute("SELECT * FROM ordini_cartella_1")
                                ans = crsr.fetchall() 
                                if(ans):
                                    testo_messaggio = gestione_for_compatto(ans)
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await conv.send_message("<b>Ricevuto ✔️</b>Inviami il numero dell'ordine di cui vuoi il dettaglio", parse_mode='html')
                                    resp = (await conv.get_response()).raw_text
                                    numero = resp
                                    if(resp.isnumeric()):
                                        sql_command = "SELECT * FROM ordini_cartella_1 WHERE Id = (?);"
                                        ans = crsr.execute(sql_command, [numero])
                                        ans = crsr.fetchall() 
                                        if(ans):
                                            testo_messaggio = get_full_info_su_utente(ans)
                                            await conv.send_message(testo_messaggio, parse_mode='html')
                                            await gestione_ordini_keyboard.delete()
                                        else:
                                            testo_messaggio = "Errore ❌\nIl messaggio con id {} non è presente.".format(numero)
                                            await conv.send_message(testo_messaggio, parse_mode='html')
                                            await gestione_ordini_keyboard.delete()
                                    else:
                                        testo_messaggio = "Errore ❌\nL'<b>ID</b> deve essere numerico."
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                else:
                                    testo_messaggio = "Non sono presenti ordini all'interno del database."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()

                                
                            ### BOTTONE CREA CSV
                            elif(scelta_GESTIONE == "crea_csv"):
                                try:
                                    crea_csv("cartella1")
                                    testo_messaggio = "<b>File csv creato correttamente ✔️</b>\nLo troverai nella stessa cartella di questo codice."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()
                                except:
                                    testo_messaggio = "Errore ❌\nRiprova più tardi, attualmente non posso creare il file csv."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()



                            ### BOTTONE ELIMINA ORDINE
                            elif(scelta_GESTIONE == "elimina_ordine"):
                                # Select per mostrare tutti gli ordini fino ad ora inseriti
                                crsr.execute("SELECT * FROM ordini_cartella_1")
                                ans = crsr.fetchall() 
                                if(ans):
                                    testo_messaggio = gestione_for_compatto(ans) 
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()

                                    # Inizio dell'operazione di delete
                                    await conv.send_message("<b>Ricevuto ⌨️</b>\nInviami il numero dell'ordine che vuoi eliminare", parse_mode='html')
                                    resp = (await conv.get_response()).raw_text
                                    numero = resp
                                    if(numero.isnumeric()):
                                        ## SELECT PER DOPO
                                        sql_command = "SELECT * FROM ordini_cartella_1 WHERE Id = (?);"
                                        ans_SELECT = crsr.execute(sql_command, [numero])
                                        ans_SELECT = crsr.fetchall() 
                                        ## DELETE
                                        sql_command = "DELETE FROM ordini_cartella_1 WHERE Id = (?);"
                                        ans = crsr.execute(sql_command, (numero,))
                                        conn.commit()
                                        # Se l'ordine selezionato non è presente allora restituisco un errore
                                        if ans.rowcount < 1:
                                            testo_messaggio = "Errore ❌\nL'ordine con ID {} non è presente.".format(numero)
                                            await conv.send_message(testo_messaggio, parse_mode='html')
                                            await gestione_ordini_keyboard.delete()

                                        # Altrimenti restituisco il messaggio che la righe è stata effettivamente eliminata, inoltre aggiorno il file CSV
                                        else: 
                                            testo_messaggio = ""
                                            for i in ans_SELECT:
                                                numero_id = i[0]
                                                testo_messaggio = "<b>Ricevuto 🗑️</b>\n\nHo eliminato l'ordine con ID <b>{}</b>.".format(numero_id)
                                                await conv.send_message(testo_messaggio, parse_mode='html')
                                                await gestione_ordini_keyboard.delete()
                                            try:
                                                crea_csv("cartella1")
                                                testo_messaggio = "<b>File csv aggiornato correttamente ✔️</b>\nLo troverai nella stessa cartella di questo codice."
                                                await conv.send_message(testo_messaggio, parse_mode='html')
                                                await gestione_ordini_keyboard.delete()
                                            except:
                                                testo_messaggio = "<b>Errore ❌</b>\nAttualmente non posso aggiornare il file csv, riprova più tardi."
                                                await conv.send_message(testo_messaggio, parse_mode='html')
                                                await gestione_ordini_keyboard.delete()

                                    else:
                                        testo_messaggio = "<b>Errore ❌</b>\nL'<b>ID</b> dell'ordine deve essere numerico."
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()

                                else:
                                    testo_messaggio = "<b>Errore ❌</b>\nNon sono presenti ordini all'interno del database, non è possibile svolgere l'operazione di cancellazione."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()

                            ### BOTTONE TERMINA CONVERSAZIONE
                            elif(scelta_GESTIONE == "termina_conversazione"):
                                await gestione_ordini_keyboard.delete()
                                await conv.send_message("<b>Conversazione terminata ✔️</b>\n", parse_mode='html')
                                return

#
#
# _____________________________________________ GESTIONE CARTELLA 2
#
#
                        elif(scelta_gestione_cartelle == "gestione_cartella_2"):
                            keyboard_di_gestione = [
                                [
                                    Button.inline("Lista Ordini", b"lista_ordini"),
                                    Button.inline("Seleziona Ordine", b"dettaglio_ordine")
                                ],
                                [
                                    Button.inline("Crea CSV", b"crea_csv"),
                                    Button.inline("Cancella Ordine", b"elimina_ordine")
                                ],
                                [
                                    Button.inline("Gestisci disponibilità siti", b"gestione_disponibilita")
                                ],
                                [
                                    Button.inline("Termina conversazione", b"termina_conversazione")
                                ]
                            ]

                            ### Messaggio di gestione con i bottoni
                            testo_di_gestione = "<b>💼 GESTIONE ORDINI</b>\n📁 Cartella due (2)"
                            gestione_ordini_keyboard = await conv.send_message(testo_di_gestione, buttons=keyboard_di_gestione, parse_mode='html')
                            press = await conv.wait_event(press_event(SENDER))
                            scelta_GESTIONE = str(press.data.decode("utf-8"))

                            if(scelta_GESTIONE == "gestione_disponibilita"):
                                # 1. Invio un messaggio con lo stato attuale della disponibilità
                                disponibilita_amazon = ottieni_disponibilita(ID_AMAZON) # 1 è l'id di amazon
                                disponibilita_zalando = ottieni_disponibilita(ID_ZALANDO) # 2 è l'id di zalando

                                testo_messaggio = "<b>Ricevuto ✔️</b>\nLo stato attuale è il seguente:\n<b>Amazon</b>: "+disponibilita_amazon+"\n<b>Zalando</b>: "+disponibilita_zalando
                                await conv.send_message(testo_messaggio, parse_mode='html')
                                await gestione_ordini_keyboard.delete()

                                keyboard_disponibilita_siti_2 = [
                                    [
                                        Button.inline("Amazon", b"scelta_amazon"),
                                        Button.inline("Zalando", b"scelta_zalando")
                                    ],
                                    [
                                        Button.inline("Torna indietro", b"torna_indietro")
                                    ]   
                                ]

                                gestione_modifica_sito_keyboard = await conv.send_message("Di quale sito vuoi modificare lo stato?", buttons=keyboard_disponibilita_siti_2, parse_mode='html')
                                modifica = await conv.wait_event(press_event(SENDER))
                                scelta_disponibilita = str(modifica.data.decode("utf-8"))

                                if(scelta_disponibilita == "torna_indietro"):
                                    await gestione_modifica_sito_keyboard.delete()
                                    continue
                                    

                                elif(scelta_disponibilita == "scelta_amazon"):
                                    if(disponibilita_amazon == "Disponibile"):
                                        nuova_disp_amazon = "Non disponibile"
                                        update_amazon = (nuova_disp_amazon, ID_AMAZON)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_amazon)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Amazon</b> è: <b>"+nuova_disp_amazon+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                    elif(disponibilita_amazon == "Non disponibile"):
                                        nuova_disp_amazon = "Disponibile"
                                        update_amazon = (nuova_disp_amazon, ID_AMAZON)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_amazon)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Amazon</b> è: <b>"+nuova_disp_amazon+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                
                                elif(scelta_disponibilita == "scelta_zalando"):
                                    if(disponibilita_zalando == "Disponibile"):
                                        nuova_disp_zalando = "Non disponibile"
                                        update_zalando = (nuova_disp_zalando, ID_ZALANDO)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_zalando)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Zalando</b> è: <b>"+nuova_disp_zalando+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                    elif(disponibilita_zalando == "Non disponibile"):
                                        nuova_disp_zalando = "Disponibile"
                                        update_zalando = (nuova_disp_zalando, ID_ZALANDO)
                                        sql_command="""UPDATE abilitazione_siti SET disponibilita=? WHERE Id=?"""
                                        crsr.execute(sql_command, update_zalando)
                                        conn.commit()
                                        testo_messaggio = "<b>Ricevuto ✔️</b>\nIl nuovo stato del sito <b>Zalando</b> è: <b>"+nuova_disp_zalando+"</b>"
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                        await gestione_modifica_sito_keyboard.delete()

                                    

                            ### BOTTONE LISTA ORDINI COMPLETI
                            if(scelta_GESTIONE == "lista_ordini"):
                                crsr.execute("SELECT * FROM ordini_cartella_2")
                                ans = crsr.fetchall() 
                                if(ans):
                                    testo_messaggio = gestione_for_compatto(ans) 
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()
                                else:
                                    testo_messaggio = "Non sono presenti ordini all'interno del database."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()



                            ### BOTTONE DETTAGLIO ORDINE
                            elif(scelta_GESTIONE == "dettaglio_ordine"):
                                crsr.execute("SELECT * FROM ordini_cartella_2")
                                ans = crsr.fetchall() 
                                if(ans):
                                    testo_messaggio = gestione_for_compatto(ans)
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await conv.send_message("<b>Ricevuto ✔️</b>Inviami il numero dell'ordine di cui vuoi il dettaglio", parse_mode='html')
                                    resp = (await conv.get_response()).raw_text
                                    numero = resp
                                    if(resp.isnumeric()):
                                        sql_command = "SELECT * FROM ordini_cartella_2 WHERE Id = (?);"
                                        ans = crsr.execute(sql_command, [numero])
                                        ans = crsr.fetchall() 
                                        if(ans):
                                            testo_messaggio = get_full_info_su_utente(ans)
                                            await conv.send_message(testo_messaggio, parse_mode='html')
                                            await gestione_ordini_keyboard.delete()
                                        else:
                                            testo_messaggio = "Errore ❌\nIl messaggio con id {} non è presente.".format(numero)
                                            await conv.send_message(testo_messaggio, parse_mode='html')
                                            await gestione_ordini_keyboard.delete()
                                    else:
                                        testo_messaggio = "Errore ❌\nL'<b>ID</b> deve essere numerico."
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()
                                else:
                                    testo_messaggio = "Non sono presenti ordini all'interno del database."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()

                                
                            ### BOTTONE CREA CSV
                            elif(scelta_GESTIONE == "crea_csv"):
                                try:
                                    crea_csv("cartella2")
                                    testo_messaggio = "<b>File csv creato correttamente ✔️</b>\nLo troverai nella stessa cartella di questo codice."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()
                                except:
                                    testo_messaggio = "Errore ❌\nRiprova più tardi, attualmente non posso creare il file csv."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()



                            ### BOTTONE ELIMINA ORDINE
                            elif(scelta_GESTIONE == "elimina_ordine"):
                                # Select per mostrare tutti gli ordini fino ad ora inseriti
                                crsr.execute("SELECT * FROM ordini_cartella_2")
                                ans = crsr.fetchall() 
                                if(ans):
                                    testo_messaggio = gestione_for_compatto(ans) 
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()

                                    # Inizio dell'operazione di delete
                                    await conv.send_message("<b>Ricevuto ⌨️</b>\nInviami il numero dell'ordine che vuoi eliminare", parse_mode='html')
                                    resp = (await conv.get_response()).raw_text
                                    numero = resp
                                    if(numero.isnumeric()):
                                        ## SELECT PER DOPO
                                        sql_command = "SELECT * FROM ordini_cartella_2 WHERE Id = (?);"
                                        ans_SELECT = crsr.execute(sql_command, [numero])
                                        ans_SELECT = crsr.fetchall() 
                                        ## DELETE
                                        sql_command = "DELETE FROM ordini_cartella_2 WHERE Id = (?);"
                                        ans = crsr.execute(sql_command, (numero,))
                                        conn.commit()
                                        # Se l'ordine selezionato non è presente allora restituisco un errore
                                        if ans.rowcount < 1:
                                            testo_messaggio = "Errore ❌\nL'ordine con ID {} non è presente.".format(numero)
                                            await conv.send_message(testo_messaggio, parse_mode='html')
                                            await gestione_ordini_keyboard.delete()

                                        # Altrimenti restituisco il messaggio che la righe è stata effettivamente eliminata, inoltre aggiorno il file CSV
                                        else: 
                                            testo_messaggio = ""
                                            for i in ans_SELECT:
                                                numero_id = i[0]
                                                testo_messaggio = "<b>Ricevuto 🗑️</b>\n\nHo eliminato l'ordine con ID <b>{}</b>.".format(numero_id)
                                                await conv.send_message(testo_messaggio, parse_mode='html')
                                                await gestione_ordini_keyboard.delete()
                                            try:
                                                crea_csv("cartella2")
                                                testo_messaggio = "<b>File csv aggiornato correttamente ✔️</b>\nLo troverai nella stessa cartella di questo codice."
                                                await conv.send_message(testo_messaggio, parse_mode='html')
                                                await gestione_ordini_keyboard.delete()
                                            except:
                                                testo_messaggio = "<b>Errore ❌</b>\nAttualmente non posso aggiornare il file csv, riprova più tardi."
                                                await conv.send_message(testo_messaggio, parse_mode='html')
                                                await gestione_ordini_keyboard.delete()

                                    else:
                                        testo_messaggio = "<b>Errore ❌</b>\nL'<b>ID</b> dell'ordine deve essere numerico."
                                        await conv.send_message(testo_messaggio, parse_mode='html')
                                        await gestione_ordini_keyboard.delete()

                                else:
                                    testo_messaggio = "<b>Errore ❌</b>\nNon sono presenti ordini all'interno del database, non è possibile svolgere l'operazione di cancellazione."
                                    await conv.send_message(testo_messaggio, parse_mode='html')
                                    await gestione_ordini_keyboard.delete()

                            ### BOTTONE TERMINA CONVERSAZIONE
                            elif(scelta_GESTIONE == "termina_conversazione"):
                                await gestione_ordini_keyboard.delete()
                                await conv.send_message("<b>Conversazione terminata ✔️</b>\n", parse_mode='html')
                                return


        except Exception as e:
            print(e)
            await client.send_message(SENDER, "<b>Conversazione Terminata ✔️</b>\nÈ trascorso troppo tempo dall'ultima tua risposta. Scrivi /gestisciOrdini per riniziare.", parse_mode='html')

    else:
        await client.send_message(SENDER, "<b>Errore ❌</b>\nNon hai il permesso di utilizzare questo comando", parse_mode='html')

        

##### MAIN
if __name__ == '__main__':
    try:

        ### DATABASE ORDINI COMPLETO
        conn = sqlite3.connect('Databases/Database_ordini_completo.db', check_same_thread=False)
        crsr = conn.cursor()
        print("Connected to the database")
        sql_command = """CREATE TABLE IF NOT EXISTS ordini ( 
            Id INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_utente VARCHAR(50),
            username VARCHAR(100), 
            nome VARCHAR(100), 
            cognome VARCHAR(100), 
            Risposta_1 VARCHAR(30), 
            Risposta_2 VARCHAR(30), 
            Risposta_3 VARCHAR(30),
            Risposta_4 VARCHAR(30),
            Risposta_5 VARCHAR(30),
            DATA_ORDINE VARCHAR(30),
            Cartella_utente INT(3));"""
        crsr.execute(sql_command)
        print("Tabella ordini completo presente")


        ### DATABASE UTENTI CARTELLA 1
        sql_command = """CREATE TABLE IF NOT EXISTS ordini_cartella_1 ( 
            Id INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_utente VARCHAR(50),
            username VARCHAR(100), 
            nome VARCHAR(100), 
            cognome VARCHAR(100), 
            Risposta_1 VARCHAR(30), 
            Risposta_2 VARCHAR(30), 
            Risposta_3 VARCHAR(30),
            Risposta_4 VARCHAR(30),
            Risposta_5 VARCHAR(30),
            DATA_ORDINE VARCHAR(30),
            Cartella_utente INT(3));"""
        crsr.execute(sql_command)
        print("Tabella ordini cartella 1 presente")


        ### DATABASE UTENTI CARTELLA 2
        sql_command = """CREATE TABLE IF NOT EXISTS ordini_cartella_2 ( 
            Id INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_utente VARCHAR(50),
            username VARCHAR(100), 
            nome VARCHAR(100), 
            cognome VARCHAR(100), 
            Risposta_1 VARCHAR(30), 
            Risposta_2 VARCHAR(30), 
            Risposta_3 VARCHAR(30),
            Risposta_4 VARCHAR(30),
            Risposta_5 VARCHAR(30),
            DATA_ORDINE VARCHAR(30),
            Cartella_utente INT(3));"""
        crsr.execute(sql_command)
        print("Tabella ordini cartella 2 presente")



        ### DATABASE ABILITAZIONE SITI AMAZON | ZALANDO
        sql_command = """CREATE TABLE IF NOT EXISTS abilitazione_siti ( 
            Id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome_sito VARCHAR(50),
            disponibilita VARCHAR(50));"""
        crsr.execute(sql_command)
        print("Tabella abilitazione_siti presente")
        try:
            # Inserisco l'id dell'utente dentro alla tabella utenti_abilitati
            sql_command = """INSERT INTO abilitazione_siti VALUES (1, "Amazon", "Disponibile");"""
            crsr.execute(sql_command)
            conn.commit()

            sql_command = """INSERT INTO abilitazione_siti VALUES (2, "Zalando", "Disponibile");"""
            crsr.execute(sql_command)
            conn.commit()

        except:
            print("Valori già presenti")



        ### DATABASE UTENTI ABILITATI
        conn_utenti_abilitati = sqlite3.connect('Databases/Database_utenti_abilitati.db', check_same_thread=False)
        crsr_utenti_abilitati = conn_utenti_abilitati.cursor()
        sql_command = """CREATE TABLE IF NOT EXISTS utenti_abilitati (id_utente VARCHAR(50) PRIMARY KEY, numero_cartella INT(3));"""
        crsr_utenti_abilitati.execute(sql_command)
        print("Tabella utenti_abilitati presente")
        

        print("Bot Started")
        client.run_until_disconnected()
    except Exception as error:
        print('Cause: {}'.format(error))
