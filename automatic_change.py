import conf, json, time, requests, os, ctypes, math, statistics, subprocess
from boltiot import Email, Bolt


mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
mailer = Email(conf.MAILGUN_API_KEY, conf.SANDBOX_URL, conf.SENDER_EMAIL, conf.RECIPIENT_EMAIL)
history_data = []
INTEGROMAT_WEBHOOK_URL = "https://hook.eu2.make.com/51gjlum1vs7gbub69kjnx1ygxwxb7jw5"
start_time = time.time()

def read_lm35():
  mybolt.digitalWrite('4', 'LOW')
  time.sleep(5)
  mybolt.digitalWrite('1', 'HIGH') 
  time.sleep(5)  
  response = mybolt.analogRead('A0')  # Read LM35 value
  value = json.loads(response)
  if value['success'] != 1 or not value['value'].isdigit():
    print("There was an error while retrieving the data.")
    print("Error retrieving LM35 data:", value.get('value', 'Unknown Error'))
    time.sleep(5)
    return None
  Temparature = int(value['value'])
  Temparature = (100*Temparature)/1024  
  mybolt.digitalWrite('1', 'LOW')  
  time.sleep(5) 
  mybolt.digitalWrite('4', 'HIGH')
  return Temparature

def read_ldr():
  response = mybolt.analogRead('A0')  # Read LDR directly
  value = json.loads(response)
  if value['success'] != 1 or not value['value'].isdigit():
    print("There was an error while retrieving the data.")
    print("Error retrieving LDR data:", value.get('value', 'Unknown Error'))
    time.sleep(5)
    return None
  Light = int(value['value'])
  return Light


def weather_determine(temp, light):
    if temp > 45 and light > 950:
        return "Extreme Heatwave with Blazing Sun"
    elif temp > 40 and light > 900:
        return "Scorching Hot and Intensely Sunny"
    elif temp > 35 and light > 800:
        return "Hot and Radiant Sunshine"
    elif temp > 30 and light > 700:
        return "Warm and Clear Skies"
    elif temp > 25 and light > 600:
        return "Mild and Pleasant with a Gentle Breeze"
    elif temp > 20 and light > 500:
        return "Cool and Comfortably Bright"
    
    # Cloudy and Overcast Conditions
    elif temp > 15 and light > 300:
        return "Partly Cloudy with Sunlight Peeking Through"
    elif temp > 10 and light > 200:
        return "Crisp and Cloudy with a Hint of Sunshine"
    elif temp > 5 and light > 150:
        return "Cold and Overcast, Feels Like Rain"
    elif light < 300:
        return "Cloudy Skies – Sunlight Blocked"

    # Rainy or Stormy Weather
    elif temp > 30 and light < 200:
        return "Warm but Cloudy – Expect Humidity"
    elif temp > 25 and light < 150:
        return "Muggy and Overcast, Thunderstorms Possible"
    elif temp > 20 and light < 100:
        return "Cool and Misty with Drizzle in the Air"
    elif temp > 15 and light < 80:
        return "Rainy and Overcast – Light Showers Possible"
    elif temp > 10 and light < 50:
        return "Dark and Rainy – Heavy Downpour Expected"
    elif temp > 5 and light < 30:
        return "Very Cold and Dark – Looks Like Midnight"

    # Foggy and Misty Weather
    elif temp > 10 and 50 < light < 200:
        return "Hazy Morning with Low Visibility"
    elif temp > 5 and light < 100:
        return "Foggy Twilight with Thick Mist"

    # Freezing and Snow Conditions
    elif temp > 0 and light < 100:
        return "Freezing and Dark with a Winter Chill"
    elif temp < 0 and light < 50:
        return "Icy Cold and Pitch Black – Possible Snowfall"
    elif temp < -5 and light < 30:
        return "Arctic Frost with a Silent Night"

    # Default case for anything else
    else:
        return "Unique Weather Pattern – A Mystical Atmosphere!"



def trigger_integromat_webhook(webhook_url, weather):
  url = f"{webhook_url}?query={weather}"
  response = requests.get(url)
  return response.text


def set_wallpaper(image_url):
    try:
        response = requests.get(image_url)
        print("Image Download Status:", response.status_code)
        
        if response.status_code == 200:
            save_directory = "D:\\Wallpapers"
            os.makedirs(save_directory, exist_ok=True)  # Ensure directory exists
            wallpaper_path = os.path.join(save_directory, "wallpaper.jpg")

            with open(wallpaper_path, "wb") as file:
                file.write(response.content)

            print(f"Wallpaper saved at: {wallpaper_path}")

            # Use ctypes to update wallpaper
            SPI_SETDESKWALLPAPER = 20
            if ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, wallpaper_path, 3):
                print("Wallpaper set successfully!")
                return True
            else:
                print("Failed to set wallpaper via ctypes.")
                return False

        else:
            print("Failed to download image")
            return False

    except Exception as e:
        print("Error setting wallpaper:", e)
        return False




def compute_bounds(history_data, frame_size, mul_factor):
  if len(history_data) < frame_size :
    return None

  if(len(history_data) > frame_size):
    del history_data[0:len(history_data)-frame_size]
  temp_t = []
  light_l = []

  for item in history_data:
    temp_t.append(item['temp'])
    light_l.append(item['light'])  

  Mean_t = statistics.mean(temp_t)
  variance_t = 0
  for data in temp_t:
    variance_t += math.pow((data-Mean_t), 2)
  Zn_t = mul_factor * math.sqrt(variance_t/frame_size)
  High_bound_t = temp_t[frame_size-1]+Zn_t 
  Low_bound_t =  temp_t[frame_size-1]-Zn_t 

  Mean_l = statistics.mean(light_l)
  variance_l = 0
  for data in light_l:
    variance_l += math.pow((data-Mean_l), 2)
  Zn_l = mul_factor * math.sqrt(variance_l/frame_size)
  High_bound_l = light_l[frame_size-1]+Zn_l 
  Low_bound_l =  light_l[frame_size-1]-Zn_l 

  return [{'temp': Low_bound_t, 'light': Low_bound_l}, {'temp': High_bound_t, 'light': High_bound_l}]



while True:
  temp = read_lm35()
  time.sleep(10)
  light = read_ldr()
  if temp is not None and light is not None:
    bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR)
    if not bound:
      required_data_count=conf.FRAME_SIZE-len(history_data)
      print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
      history_data.append({'temp': temp, 'light': light})
      time.sleep(10)
      continue

    try:
      if temp < bound[0]['temp'] or temp > bound[1]['temp'] or light < bound[0]['light'] or light > bound[1]['light'] or time.time() - start_time >= 3600:
        if time.time() - start_time >= 3600:
          start_time = time.time()
        print("Weather changed...")
        time.sleep(2)
        print("Determining Weather...")
        weather = weather_determine(temp, light)
        print("Fetching Wallpaper...")
        image = trigger_integromat_webhook(INTEGROMAT_WEBHOOK_URL, weather)
        print("Setting Wallpaper...")
        result = set_wallpaper(image)
        if result:
          print("Sending Email...")
          response_1 = mailer.send_email(" Wallpaper changed ", " The Current temperature is " + str(temp) + " The Light Intensity is " + str(light) + " Weather Status: " + str(weather)+ " Link for the Image: " + str(image)) 
          response_text = json.loads(response_1.text)
          print("Response received from Mailgun is: " + str(response_text['message'])) 
      history_data.append({'temp': temp, 'light': light})
    except Exception as e:
      print ("Error",e)
    print(f"Temperature: {temp:.2f}°C, Light Level: {light}")
  else:
    print("Error reading sensor values.")
  time.sleep(10)  # Adjust delay as needed