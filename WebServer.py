from flask import Flask, render_template, request,make_response
import flask
import paho.mqtt.client as mqtt
import sqlite3 as lite
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import io
import os
import sys
import subprocess
app = Flask(__name__)

#subprocess.check_call([sys.executable, '-m','pip','install', 'matplotlib'])
#subprocess.check_call([sys.executable, '-m','pip','install', 'paho-mqtt'])
#subprocess.check_call([sys.executable, '-m','pip','install', 'pandas'])
#subprocess.check_call([sys.executable, '-m','pip','install', 'numpy = 1.19.3'])
#subprocess.check_call([sys.executable, '-m','pip','install', 'pyodbc'])

server = 'solognier.database.windows.net'
database = 'Database1'
username = 'michsol'
password = '0000_HANZE'
driver = 'FreeTDS'
databaseId = []
dates =      []
food =       []
ambhum =     []
ambtemp =    []
soilMoist =  []
plthum =     []
plttemp =    []

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = '192.168.178.199'
app.config['MQTT_BROKER_PORT'] = 9001
#app.config['MQTT_USERNAME'] = 'user'
#app.config['MQTT_PASSWORD'] = 'secret'
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds

#global
#mqtt = Mqtt(app)
#socketio = SocketIO(app)
global MSG_on
MSG_on="state"





def getlastData():
    conn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password + ';TDS_Version=8.0')
    cursor=conn.cursor()
    for row in cursor.execute("SELECT * FROM [dbo].[IOHPPtable] WHERE Measurement=(SELECT max(Measurement) FROM [dbo].[IOHPPtable]);"):
        databaseId= row[0]
        dates    = row[1]
        food      = row[2]
        ambhum    = row[3]
        ambtemp   = row[4]
        soilMoist = row[5]
        plthum    = row[6]
        plttemp   = row[7]
    
    return dates,food, ambhum, ambtemp,soilMoist,plthum,plttemp



def dfamountplantdata(numsamples):
    conn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password + ';TDS_Version=8.0')
    sql='''SELECT * FROM IOHPPtable WHERE Measurement > (SELECT MAX(Measurement) - %s FROM IOHPPtable)'''%numsamples
    #SQL_Query = pd.read_sql_query('''SELECT * FROM IOHPPtable WHERE Measurement > (SELECT MAX(Measurement) - 10 FROM IOHPPtable)''',conn)
    SQL_Query = pd.read_sql_query(sql,conn)
    df = pd.DataFrame(SQL_Query,columns =['dttime','food','ambhum','ambtemp','soilMoist','plthum','plttemp'])
    df['dttime'] = pd.to_datetime(df['dttime'], format="%d/%m/%Y %H:%M:%S")
    df.sort_values('dttime',ascending = True)
    df['food'] = pd.to_numeric(df['food'])
    df['ambhum'] = pd.to_numeric(df['ambhum'])
    df['ambtemp'] = pd.to_numeric(df['ambtemp'])
    df['soilMoist'] = pd.to_numeric(df['soilMoist'])
    df['plthum'] = pd.to_numeric(df['plthum'])
    df['plttemp'] = pd.to_numeric(df['plttemp'])
    return(df)


# define and initialize global variables

def dfAllData():
    conn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password + ';TDS_Version=8.0')
    sql='''SELECT * FROM IOHPPtable '''
    #SQL_Query = pd.read_sql_query('''SELECT * FROM IOHPPtable WHERE Measurement > (SELECT MAX(Measurement) - 10 FROM IOHPPtable)''',conn)
    SQL_Query = pd.read_sql_query(sql,conn)
    df = pd.DataFrame(SQL_Query,columns =['dttime','food','ambhum','ambtemp','soilMoist','plthum','plttemp'])
    #df['dttime'] = pd.to_datetime(df['dttime'], format="%d/%m/%Y %H:%M:%S")
    #df.sort_values('dttime',ascending = True)
    df['food'] = pd.to_numeric(df['food'])
    df['ambhum'] = pd.to_numeric(df['ambhum'])
    df['ambtemp'] = pd.to_numeric(df['ambtemp'])
    df['soilMoist'] = pd.to_numeric(df['soilMoist'])
    df['plthum'] = pd.to_numeric(df['plthum'])
    df['plttemp'] = pd.to_numeric(df['plttemp'])
    
    
    return(df)

def getlocalHistData ():
    conn = lite.connect('sensorAR.db')
    curs = conn.cursor()
    curs.execute("SELECT * FROM ALL_data ORDER BY dttime DESC LIMIT 5")
    data = curs.fetchall()
    dates = []
    food = []
    ambhum = []
    ambtemp = []
    soilMoist = []
    plthum = []
    plttemp = []
    for row in reversed(data):
        dates.append     (row[0])
        food.append      (row[1])
        ambhum.append    (row[2])
        ambtemp.append   (row[3])
        soilMoist.append (row[4])
        plthum.append    (row[5])
        plttemp.append   (row[6])
        return dates, food, ambhum, ambtemp , soilMoist , plthum , plttemp

def on_log(client, userdata, level, buf):
    print("log : "+buf)
    



def on_message2(client,userdata,msg):
    topic = msg.topic
    print(topic)
    m_decode = str(msg.payload.decode("utf-8","ignore"))
    print("Message Receieved", m_decode)
    msg_arr = msg.payload
    client.publish("esp32/output","on")


def on_connect2(client, userdata, flags, rc):
    client2.subscribe("esp32/Window")
    client2.subscribe("esp32/Ambient")
    client2.subscribe("esp32/Plant")
    client2.subscribe("esp32/complete")
    if rc==0:
        print("Connected ok")
    else:
        print("Ba connection return code", rc)

# main route 

@app.route("/")
def index():
    data = dfAllData()
    input_data = dfamountplantdata(10)
    #time,food, ambhum, ambtemp,soilMoist,plthum,plttemp = getlastData()
    time = input_data['dttime']
    food = input_data['food']
    ambhum = input_data['ambhum']
    ambtemp = input_data['ambtemp']
    soilMoist = input_data['soilMoist']
    plthum = input_data['plthum']
    plttemp = input_data['plttemp']
    templateData = {
	  	'time'	: time[9],
		'food'	: food[9],
      	'ambhum': ambhum[9],
        'ambtemp'	: ambtemp[9],
        'soilMoist'	: soilMoist[9],
        'plthum'	: plthum[9],
        'plttemp'	: plttemp[9],
        'lightstate': MSG_on
        
	}
    return data.to_html(),render_template('index.html', **templateData)

	
	
@app.route('/plot/ambient')
def plot_ambient():
    
    topa = dfamountplantdata(10)
    #time,ambhum, ambtemp= ASDB.getlastAmountAmbientdata(5)
    ys = topa['ambtemp']
    ys2 =topa['ambhum'] 
    fig = Figure()
    axis = fig.add_subplot(2, 1, 2)
    axis2 = fig.add_subplot(2,1,1 )
    axis2.set_ylabel("Humidty [%]")
    
    axis2.set_title("Ambient Temperature & Humidity ")
    axis.set_ylabel("Temperature [°C]")
    axis.set_xlabel("samples")
    axis2.grid(True)
    axis.grid(True)
    xs = range(10)
    xs2 = range(10)
    axis.plot(xs, ys)
    axis2.plot(xs2,ys2)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route('/plot/plant')
def plot_plant():
    topa = dfamountplantdata(10)
    #time,ambhum, ambtemp= ASDB.getlastAmountAmbientdata(numbSamples)
    
    ys = topa['plttemp']
    ys2 =topa['soilMoist']
    fig = Figure()
    axis = fig.add_subplot(2, 1, 2)
    axis2 = fig.add_subplot(2,1,1 )
    axis2.set_ylabel("Humidty [%]")
    
    axis2.set_title("Plant Temperature & Humidity ")
    axis.set_ylabel("Temperature [°C]")
    axis.set_xlabel("samples")

    axis2.grid(True)
    axis.grid(True)
    xs = range(10)
    xs2 = range(10)

    axis.plot(xs, ys)
    axis2.plot(xs2,ys2)

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response


@app.route('/turn_on_lights',methods =['post'])
def my_form_post1():
    global MSG_on
    client2.publish('esp32/output','ON')
    MSG_on = "ON"
    input_data = dfamountplantdata(10)
    time = input_data['dttime']
    food = input_data['food']
    ambhum = input_data['ambhum']
    ambtemp = input_data['ambtemp']
    soilMoist = input_data['soilMoist']
    plthum = input_data['plthum']
    plttemp = input_data['plttemp']
    templateData = {
	  	'time'	: time[0],
		'food'	: food[0],
      	'ambhum': ambhum[0],
        'ambtemp'	: ambtemp[0],
        'soilMoist'	: soilMoist[0],
        'plthum'	: plthum[0],
        'plttemp'	: plttemp[0],
        'lightstate': MSG_on
        
	}
    
    return render_template('index.html', **templateData)

@app.route('/turn_off_lights',methods =['post'])
def my_form_post2():
    global MSG_on
    client2.publish('esp32/output','OFF')
    MSG_on = "OFF"
    input_data = dfamountplantdata(10)
    time = input_data['dttime']
    food = input_data['food']
    ambhum = input_data['ambhum']
    ambtemp = input_data['ambtemp']
    soilMoist = input_data['soilMoist']
    plthum = input_data['plthum']
    plttemp = input_data['plttemp']
    templateData = {
	  	'time'	: time[0],
		'food'	: food[0],
      	'ambhum': ambhum[0],
        'ambtemp'	: ambtemp[0],
        'soilMoist'	: soilMoist[0],
        'plthum'	: plthum[0],
        'plttemp'	: plttemp[0],
        'lightstate': MSG_on
        
	}
    
    return render_template('index.html', **templateData)



@app.route('/tables')
def showTables():
    data = dfAlldata()
    return data.to_html()

if __name__ == "__main__":
    
    
    client2 = mqtt.Client("Website",transport = 'websockets')
    client2.on_connect = on_connect2
    client2.connect("192.168.178.199",9001,60)
    
     
    app.run(host='192.168.178.199', port=5000, debug=False, threaded=False )
