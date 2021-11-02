import time
import string
import pynmea2
import paho.mqtt.client as mqtt
import sys
import RPi.GPIO as GPIO
import serial

#DEFINICOES MQTT
keepalivebroker=60
topico="gps"
portabroker=1883
broker="test.mosquitto.org"

#PINO DIGITAL DE LEITURA
Pin_In=23
#PINO DIGITAL DE SAIDA
Pin_Out=24
#UTILIZANDO PINOS COMO GPIO
GPIO.setmode(GPIO.BCM)
#CONFIGURANDO PINO COMO ENTRADA PARA SELECINAR GPS
GPIO.setup(Pin_In,GPIO.IN)
#CONFIGURANDO PINO DE SAIDA COMO SINALIZADOR DE DADO ENVIADO
GPIO.setup(Pin_Out,GPIO.OUT)

#FLAG DE LATIDUDE E LONGITUDE
COORD_FLAG=False
#FLAG DE DOP (DILUTION OF POLUTION)
DOP_FLAG=False

#CALLBACK DE CONEXAO REALIZADA
def on_connect(client,userdata,flags,rc):
        print("CONECTADO AO BROKER:"+str(rc))
	pass

try:
       print("INICIALIZANDO MQTT")
       client=mqtt.Client()
       client.on_connect=on_connect
       client.connect(broker,portabroker,keepalivebroker)
except:
       print(" Programa interrompido")
       sys.exit(0)     

port="/dev/ttyAMA0"
ser=serial.Serial(port,baudrate=9600,timeout=1)
#SE PINO ESTIVER EM NIVEL ALTO, LER FIRMWARE DO SIM_808
GPIO.output(Pin_Out,False)
if GPIO.input(Pin_In): #CASO O FIRMWARE DO SIM808 SEJA ESCOLHIDO
	print("FIRMWARE DO SIM808 INICIALIZANDO")
	time.sleep(1)
	ser.write("AT")
	time.sleep(1)
	ser.write("AT+CGNSPWR=1") #LIGA O MOODULO GPS DO SIM808
	time.sleep(1)
	while True:
		if GPIO.input(Pin_In)!=1:
			print("Firmware do SIM808 interrompido")
  			time.sleep(1)
 			break
		ser.write("AT+CGNSINF") #ESCREVE PARA LER DADOS DE LATITUDE E LONGITUDE DO SIM808 EM SEGUIDA
		time.sleep(0.6)
		newdata=ser.readline() #LER DADOS DE LATITUDE E LONGITUDE
		print("Dado:"+newdata) #LOG DE DADOS RETORNADOS PELO SIM808

		if "+CGNSINF:" in newdata: #ORGANIZA DADOS DO SIM808
			geo_localizacao="Latitude:"+str(newdata[33:43])+" Longitude:"+str(newdata[44:54])+" HDoP:"+str(newdata[76:80])+" VDoP:"+str(newdata[84:88])+" PDoP:"+str(newdata[80:84])
			print(geo_localizacao) #PRINTA DADOS ORGANIZADOS DO SIM808
			geo_localizacao_mqtt=str(newdata[33:43])+" "+str(newdata[44:54])+" "+str(newdata[76:80])+" "+str(newdata[84:88])+" "+str(newdata[80:84])+"2"

			if float(newdata[33:43])<0:  #ACENDE LED CASO A GEOLOCALIZACAO SEJA CALCULADA E ENVIADA VIA MQTT
                                GPIO.output(Pin_Out,True)
				client.publish(topico,geo_localizacao_mqtt+"2") #INSERE INDICE 2 PARA DADOS DO SIM808 NO BROKER MQTT 
                        else:
                                GPIO.output(Pin_Out,False) #APAGA LED QUANDO NÃO RECEBE O DADO DE GPS SIM808

else:
	print("Firmware NEO6MV2") #FIRMWARE DE COMUNICACAO CO O NEO6MV2 SEJA ESCOLHIDO
	while True:
		if GPIO.input(Pin_In):
			print("Firmware do NEO6MV2 interrompido")
			time.sleep(1)
			break
		newdata=ser.readline()
		if newdata[0:6]=="$GPRMC":
			newmsg=pynmea2.parse(newdata)
			lat=newmsg.latitude
                        lng=newmsg.longitude
			COORD_FLAG=True    #FLAG ATIVO PORQUE RECEBEU COORDENADAS
			gps="Latitude:"+str(lat)+" Longitude:"+str(lng)
			gps_mqtt=str(lat)+" "+str(lng)
		if newdata[0:6]=="$GPGSA":
			newmsg=pynmea2.parse(newdata)

			hdop=newmsg.hdop
			vdop=newmsg.vdop
			pdop=newmsg.pdop
			DOP_FLAG=True #FLAG ATIVO PORQUE RECEBEU DILUICAO DE PRECISAO
			dop="HDoP:"+str(hdop)+" VDoP:"+str(vdop)+" PDoP:"+str(pdop)
			dop_mqtt=str(hdop)+" "+str(vdop)+" "+str(pdop)
			
			#CASO A LEITURA DE DOIS PARAMETROS SEJA FEITA
			if COORD_FLAG==True and DOP_FLAG==True:
				print(gps+" "+dop)
				#ZERA FLAGS PARA PROXIMA LEITURA DE DADOS
                                COORD_FLAG=False
                                DOP_FLAG=False 

				if float(lat)<0: #ACENDE LED CASO A GEOLOCALIZACAO SEJA CALCULADA E ENVIADA VIA MQTT

					GPIO.output(Pin_Out,True)
					payload_mqtt=gps_mqtt+" "+dop_mqtt+"1"

					client.publish(topico,gps_mqtt+" "+dop_mqtt+"1") #INSERE INDICE 1 PARA DADOS DO NEO6MV2 NO BROKER MQTT
				else:
					GPIO.output(Pin_Out,False) #APAGA LED QUANDO NÃO RECEBE O DADO DE GPS NEO6MV2




