import time
import smtplib
from bs4 import BeautifulSoup
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, render_template
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=2)

master_data_store = {
    "users": [
        {"id": 1, "name": "Arpit", "email": "arpitagarwal.09@gmail.com", "server_status": False},
        {"id": 2, "name": "Aneet", "email": "ameet.srivastava@hotmail.com", "server_status": False},
        {"id": 3, "name": "Shivansh", "email": "shivanshk1197@gmail.com", "server_status": False},
        {"id": 35, "name": "Uttu", "email": "ua20500@gmail.com", "server_status": False},

    ]
}

maryBriaURL = "https://charge.pod-point.com/address/sainsburys-redhill-j9pm/mary-bria"
philAlanURL = "https://charge.pod-point.com/address/sainsburys-redhill-j9pm/phil-alan"

pod_data_source = {}

def get_user_data(user_id):
    return next((u for u in master_data_store['users'] if u['id'] == int(user_id)), None)

def display_pod_status():
    maryBria = check_status(maryBriaURL, "maryBria")
    philAlan = check_status(philAlanURL, "philAlan")
    pod_data_source.update(maryBria)
    pod_data_source.update(philAlan)
    return pod_data_source

# Function to scrape the webpage and get status
def check_status(pod_url, pod_name):
    url = pod_url
    available = False
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    # Send HTTP request to the page
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find the 'ul' element with the class 'pod-status'
    # status_list = soup.find('ul', class_='fa-ul pod-status')
    connector_a_dt = soup.find('dt', text='Connector A Status')
    connector_b_dt = soup.find('dt', text='Connector B Status')
    print(connector_a_dt)
    print(connector_b_dt)
    podA_status = pod_status(connector_a_dt)
    podB_status = pod_status(connector_b_dt)

    if podA_status == "Available" or podB_status == "Available":
        available = True
    print("Pod status A", podA_status)
    print("Pod status B", podB_status)

    final_status = {
        pod_name: {
            "PodA": podA_status,
            "PodB": podB_status
        },
        "available": available
    }
    print("final_status ----->", pod_name, final_status)
    return final_status

def pod_status(connector_b_dt):
    if connector_b_dt:
        # Find the next sibling <dd> element, which contains the <ul> with status info
        connector_b_dd = connector_b_dt.find_next_sibling('dd')
        
        if connector_b_dd:
            # Find the <ul> inside the <dd> element with the class 'fa-ul pod-status'
            status_list = connector_b_dd.find('ul', class_='fa-ul pod-status')
            
            if status_list:
                # Find the first <li> element, which contains the availability status
                status_item = status_list.find('li')
                
                if status_item:
                    status = status_item.text.strip()  # Extract the text (e.g., "Available")
                    # print("status for pod B ", status)
                    return status

# Function to send email notification
def send_email(status, receiver_email, receiver_name):
    sender = "pointpod4@gmail.com"
    receiver = receiver_email
    name = receiver_name
    # receiver = "anshul.sharma11@gmail.com"
    password = "ntxe cnnl zahm gnwq"
    
    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = "Charging Station Status Update"
    status_line = ""

    if 'maryBria' in status:
        if status['maryBria']['PodA'] == 'Available':
            status_line = "Mary Bria - Pod A is Available. "
        if status['maryBria']['PodB'] == 'Available':
            status_line = status_line + "Mary Bria - Pod B is Available. "
            
    if 'philAlan'in status:
        if status['philAlan']['PodA'] == 'Available':
            status_line = "Phil Alan, Pod A is Available. "
        if status['philAlan']['PodB'] == 'Available':
            status_line = status_line + "Phil Alan, Pod B is Available. "

    print("email mesasage    ", status_line)

    body = f"Hi {name}, The available charging pod details - {status_line}"

    msg.attach(MIMEText(body, 'plain'))
    
    # Create SMTP session for sending email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Gmail SMTP server
        print("1")
        server.starttls()  # Enable security
        print("2")
        server.login(sender, password)
        print("2")
        text = msg.as_string()
        server.sendmail(sender, receiver, text)
        server.quit()
        print(f"Email sent successfully to {receiver} with status {status}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

def monitor(user_id):
    user_data = next((u for u in master_data_store['users'] if u['id'] == int(user_id)), None)
    receiver_email =  user_data['email']
    receiver_name = user_data['name']
    pod_result = []
    while user_data["server_status"]:
        a = check_status(maryBriaURL, "maryBria")
        b = check_status(philAlanURL, "philAlan")
        if a['available'] and b['available'] :
            pod_result = a
            pod_result.update(b)
        elif a['available'] == True :
            pod_result = a
        elif b['available'] == True :
            pod_result = b
        print("pd result --->", pod_result)
        if a['available'] or b['available'] :
            send_email(pod_result, receiver_email, receiver_name)
        time.sleep(300)  # Sleep for 5 minutes

def check_server_status(user_id):
    return next((u['server_status'] for u in master_data_store['users'] if u['id'] == int(user_id)), None)

def update_server_status(user_id, server_status):
    for u in master_data_store['users']:
        if u['id'] == int(user_id):
            print("")
            u["server_status"] = server_status

# GET API
@app.route('/get-user', methods=['GET'])
def get_user():
    user_id = request.args.get('id')  # Retrieve query parameter 'id'
    if user_id:
        user = get_user_data(user_id)
        if user:
            status = check_server_status(user_id)
            pod_status_data = display_pod_status()
            status_label = 'off'
            if status:
                status_label = 'on'
            return render_template('index.html', user_name=user['name'], pod_status_data=pod_status_data, status=status_label)
            # return jsonify({"message": "User found", "user": user, "server_status": check_server_status(user_id)}), 200
        else:
            return jsonify({"message": "User not found"}), 404
    else:
        return jsonify({"message": "No user ID provided"}), 400

@app.route('/toggle', methods=['POST'])
def toggle():
    data = request.json
    status = data.get('status')
    user_id = data.get('user_id')
    user = get_user_data(user_id)
    boolStatus = False
    if status == 'on':
        boolStatus = True
    elif status == 'off':
        boolStatus = False
    update_server_status(user_id, boolStatus)
    pod_status_data = display_pod_status()
    executor.submit(monitor, user_id)
    return render_template('index.html',user_name=user['name'], pod_status_data=pod_status_data, status=status)

@app.route('/get-data', methods=['GET'])
def get_data():
    user_id = request.args.get('id')  # Retrieve query parameter 'id'
    if user_id:
        user = next((u for u in master_data_store['users'] if u['id'] == int(user_id)), None)
        if user:
            check_server_status(user_id)
            return jsonify({"message": "User found", "user": user, "server_status": check_server_status(user_id)}), 200
            # return render_template('index.html')
        else:
            return jsonify({"message": "User not found"}), 404
    else:
        return jsonify({"message": "No user ID provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)
