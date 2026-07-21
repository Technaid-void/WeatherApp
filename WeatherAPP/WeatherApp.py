#This software was made for the sake of learning, and is not meant to be used in actual application 

#Credits:

#Software icon made by  Dewi Sari from www.flaticon.com

#Emotes from https://emojidb.org/

#Api's used:
#https://open-meteo.com/
#https://openweathermap.org/

#Tutorial by Bro code:
#https://youtu.be/ix9cRaBkVe0?si=ync9Fa18Ega38ryj&t=39965
#Channel: https://www.youtube.com/@BroCodez



import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry



class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 400)
        self.city_label = QLabel("Enter city name: ", self)
        self.city_input = QLineEdit(self)
        self.get_weather_button = QPushButton("Get Weather", self)
        self.temperature_label = QLabel(self)
        self.emoji_label = QLabel(self)
        self.description_label = QLabel(self)
        self.humidity_label = QLabel(self)


        self.initUI()


    def initUI(self):
        self.setWindowTitle("Weather App")
        vbox = QVBoxLayout()
        
        vbox.addWidget(self.city_label)
        vbox.addWidget(self.city_input)
        vbox.addWidget(self.get_weather_button)
        vbox.addWidget(self.temperature_label)
        vbox.addWidget(self.emoji_label)
        vbox.addWidget(self.description_label)
        vbox.addWidget(self.humidity_label)

        self.setLayout(vbox)
        self.city_label.setAlignment(Qt.AlignCenter) #type: ignore
        self.city_input.setAlignment(Qt.AlignCenter) #type: ignore
        self.temperature_label.setAlignment(Qt.AlignCenter) #type: ignore
        self.emoji_label.setAlignment(Qt.AlignCenter) #type: ignore
        self.description_label.setAlignment(Qt.AlignCenter) #type: ignore
        self.humidity_label.setAlignment(Qt.AlignCenter) #type: ignore

        self.city_label.setObjectName("city_label")
        self.city_input.setObjectName("city_input")
        self.get_weather_button.setObjectName("get_weather_button")
        self.temperature_label.setObjectName("temperature_label")
        self.emoji_label.setObjectName("emoji_label")
        self.description_label.setObjectName("description_label")
        self.humidity_label.setObjectName("humidity_label")

        self.setStyleSheet("""
                        QLabel, QPushButton{
                           font-family: calibri;
                           }
                        QLabel#city_label{
                           font-size: 40px;
                           font-style: italic;
                           }
                        QLineEdit#city_input{
                            font-size: 40px;
                           }
                        QPushButton#get_weather_button{
                            font-size: 30px;
                            font-weight: bold;
                           }
                        QLabel#temperature_label{
                            font-size: 30px;
                           }
                        QLabel#emoji_label{
                            font-size: 100px;
                            font-family: Segoe UI emoji;
                           }
                        QLabel#description_label{
                            font-size: 50px
                           }
                        QLabel#humidity_label{
                            font-size: 30px
                           }""")

        self.get_weather_button.clicked.connect(self.get_weather)



    def get_weather(self):
        api_key = "295be62b2bba086bcf3b59ea898f0fff"
        city = self.city_input.text()
        #get the lat and long
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={api_key}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            lat = 0
            lon = 0

            if response.status_code and data and isinstance(data[0], dict) and 'lat' in data[0] and 'lon' in data[0] :
                lat = int(data[0]['lat'])
                lon = int(data[0]['lon'])
            else:
                self.display_error("Coudln't find city")
                raise ValueError("City name doesn't exist")

            # Setup the Open-Meteo API client with cache and retry on error
            cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
            retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
            openmeteo = openmeteo_requests.Client(session = retry_session) #type: ignore
            #get the weather
            url = f"https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": ["temperature_2m", "weather_code", "rain", "relative_humidity_2m"],
                "timezone": "auto",
                "forecast_days": 1,
                "forecast_hours": 1,
                
            }
            responses = openmeteo.weather_api(url, params = params)
            data_response = responses[0]

            hourly = data_response.Hourly()
            hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy() # type: ignore
            hourly_weather_code = hourly.Variables(1).ValuesAsNumpy() # type: ignore
            hourly_rain = hourly.Variables(2).ValuesAsNumpy() # type: ignore
            hourly_relative_humidity_2m = hourly.Variables(3).ValuesAsNumpy() # type: ignore

            hourly_data = {
                "date": pd.date_range(
                    start = pd.to_datetime(hourly.Time(), unit = "s", utc = True), # type: ignore
                    end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True), # type: ignore
                    freq = pd.Timedelta(seconds = hourly.Interval()), # type: ignore
                    inclusive = "left"
                ).tz_convert(data_response.Timezone().decode()) # type: ignore
            }


            hourly_data["temperature_2m"] = hourly_temperature_2m # type: ignore
            hourly_data["weather_code"] = hourly_weather_code # type: ignore
            hourly_data["rain"] = hourly_rain # type: ignore
            hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m # type: ignore

            hourly_dataframe = pd.DataFrame(data = hourly_data)
            self.display_weather(hourly_dataframe)



        except requests.exceptions.HTTPError as http_error:
            match response.status_code: #type: ignore
                case 400:
                    self.display_error("Bad request:\nPlease check your input")
                case 401:
                    self.display_error("Unauthroized:\nInvalid API key")
                case 403:
                    self.display_error("Forbidden:\nAccess denied")
                case 404:
                    self.display_error("Not found:\nCity not found")
                case 500:
                    self.display_error("Internal Server error:\nPlease try again later")
                case 502:
                    self.display_error("Bad Gateway:\nInvalid response from the server")
                case 503:
                    self.display_error("Service Unavailable:\nServer is down")
                case 504:
                    self.display_error("Gateway Timeout:\nNo response from the server")
                case _:
                    self.display_error(f"HTTP error occured:\n{http_error}")
        except requests.exceptions.ConnectionError:
            self.display_error("Connection Error:\nCheck your internet connection")
        except requests.exceptions.Timeout:
            self.display_error("Timeout Error:\nThe request timed out")
        except requests.exceptions.TooManyRedirects:
            self.display_error("Too many Redirects:\nCheck the URL")
        except ValueError as e:
            self.display_error(f'{e}')
        except requests.exceptions.RequestException as req_error:
            self.display_error(f"Request Error:\n{req_error}")




    def display_error(self, message):
        self.temperature_label.setText(message)
        self.description_label.setText('')
        self.emoji_label.setText('')
        self.humidity_label.setText('')
    
    def display_weather(self, data):

        time = data['date'][0]
        temp = data['temperature_2m'][0]
        weather = data['weather_code'][0]
        rain = data['rain'][0]
        humidity = data['relative_humidity_2m'][0]

        self.temperature_label.setText(f'Temperature: {temp:.2f}℃')
        self.get_cloudiness(weather)


        self.description_label.setText(f'{self.cloudiness}')
        self.emoji_label.setText(f'{self.cloudiness_emote}')

        self.humidity_label.setText(f'Humidity:{humidity:.2f}%')
        print(humidity)


    def get_cloudiness(self, code):
        self.cloudiness = ''
        self.cloudiness_emote = ''
        match code:
            case 0:
                self.cloudiness = 'Clear sky'
                self.cloudiness_emote = '☀️'
            case 1:
                self.cloudiness = 'Mainly clear'
                self.cloudiness_emote = '⛅'
            case 2:
                self.cloudiness = 'Partly cloudy'
                self.cloudiness_emote = '⛅'
            case 3:
                self.cloudiness = 'Overcast'
                self.cloudiness_emote = '☁️'
            case 45:
                self.cloudiness = 'Fog'
                self.cloudiness_emote = '☁️'
            case 48:
                self.cloudiness = 'Depositing rime fog'
                self.cloudiness_emote = '☁️'
            case 51:
                self.cloudiness = 'Light drizzle'
                self.cloudiness_emote = '🌧️'
            case 53:
                self.cloudiness = 'Moderate drizzle'
                self.cloudiness_emote = '🌧️'
            case 55:
                self.cloudiness = 'Dense drizzle'
                self.cloudiness_emote = '🌧️'
            case 56:
                self.cloudiness = 'Light freezing drizzle'
                self.cloudiness_emote = '🌨️'
            case 57:
                self.cloudiness = 'Dense freezing drizzle'
                self.cloudiness_emote = '🌨️'
            case 61:
                self.cloudiness = 'Slight rain'
                self.cloudiness_emote = '🌧️'
            case 63:
                self.cloudiness = 'Moderate rain'
                self.cloudiness_emote = '🌧️'
            case 65:
                self.cloudiness = 'Heavy rain'
                self.cloudiness_emote = '🌧️'
            case 66:
                self.cloudiness = 'Light freezing rain'
                self.cloudiness_emote = '🌨️'
            case 67:
                self.cloudiness = 'Heavy freezing rain'
                self.cloudiness_emote = '🌨️'
            case 71:
                self.cloudiness = 'Slight snow fall'
                self.cloudiness_emote = '🌨️'
            case 73:
                self.cloudiness = 'Moderate snow fall'
                self.cloudiness_emote = '🌨️'
            case 75:
                self.cloudiness = 'Heavy snow fall'
                self.cloudiness_emote = '🌨️'
            case 77:
                self.cloudiness = 'Snow grains'
                self.cloudiness_emote = '🌨️'
            case 80:
                self.cloudiness = 'Slight rain showers'
                self.cloudiness_emote = '🌧️'
            case 81:    
                self.cloudiness = 'Moderate rain showers'
                self.cloudiness_emote = '🌧️'
            case 82:
                self.cloudiness = 'Heavy rain shower'
                self.cloudiness_emote = '🌧️'
            case 85:
                self.cloudiness = 'Slight snow shower'
                self.cloudiness_emote = '🌨️'
            case 86:
                self.cloudiness = 'Heavy snow shower'
                self.cloudiness_emote = '🌨️'


if __name__ == "__main__":
    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    weather_app.setWindowIcon(QIcon('icons_atmospheric-conditions.ico'))
    weather_app.show()
    sys.exit(app.exec_())
