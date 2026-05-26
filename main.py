import json
import os
import time

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

API_KEY = os.getenv("ASTROMETRY_API_KEY")
if not API_KEY:
    raise ValueError("Error: No Astrometry API key found in environment variables.")

session_id = None

try:
    LOGIN_URL = "http://nova.astrometry.net/api/login"
    payload = {"request-json": json.dumps({"apikey": API_KEY})}
    response = requests.post(url=LOGIN_URL, data=payload, timeout=15)
    response.raise_for_status()

    data = response.json()
    if data.get("status") == "success":
        session_id = data.get("session")
        print(f"Authenticated successfully! SessionID: {session_id}")
    else:
        print(f"Authentication failed: {data}")
except requests.exceptions.RequestException as e:
    print(f"An error occured during the initial API request: {e}")

if session_id is not None:
    UPLOAD_URL = "http://nova.astrometry.net/api/upload"
    upload_params = {
        "session": session_id,
        "allow_commercial_use": "d",
        "allow_modifications": "d",
        "publicly_visible": "y",
    }

    payload = {"request-json": json.dumps(upload_params)}

    try:
        with open("north america.png", "rb") as image_file:
            files = {"file": ("north america.png", image_file)}
            print("Submitting to Astrometry.net...")

            response = requests.post(UPLOAD_URL, data=payload, files=files, timeout=180)
            response.raise_for_status()

            upload_data = response.json()
            if upload_data.get("status") == "success":
                sub_id = upload_data.get("subid")
                print(f"Upload success! Sub ID: {sub_id}")

                STATUS_URL = f"http://nova.astrometry.net/api/submissions/{sub_id}"
                job_id = None

                print("Waiting for server response...")
                while True:
                    try:
                        job_status = requests.get(STATUS_URL).json()
                        jobs = job_status.get("jobs")
                        if jobs and jobs[0] is not None:
                            job_id = jobs[0]

                        if job_status.get("job_calibrations"):
                            print("\nImage successfully plate solved!")
                            break

                        print(".", end="", flush=True)
                        time.sleep(10)
                    except requests.exceptions.RequestException:
                        print("X", end="", flush=True)
                        time.sleep(10)

                INFO_URL = f"http://nova.astrometry.net/api/jobs/{job_id}/info/"
                info_request = requests.get(INFO_URL)
                info_data = info_request.json()

                calibration = info_data.get("calibration")

                print(f"Right Ascension: {calibration.get('ra')}")
                print(f"Declination: {calibration.get('dec')}")
                print(f"Radius: {calibration.get('radius')}")

                objects_found = info_data.get("objects", [])
                print(f"\nIdentified objects: {objects_found}")

                tags = info_data.get("machine_tags", [])
                print(f"Machine tags: {tags}")
            else:
                print(f"Upload failed: {upload_data}")
    except FileNotFoundError:
        print("Error: could not find file in the directory.")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
