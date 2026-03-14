from flask import Flask, render_template, request, redirect, session, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from flask import send_file
import io
import requests
import ssl
import certifi
import os
import json
import smtplib
from email.mime.text import MIMEText
ssl._create_default_https_context = ssl._create_unverified_context




app = Flask(__name__)
app.secret_key = "SECRET_KEY_123"

# ================= FIREBASE INIT =================
firebase_key = json.loads(os.environ["FIREBASE_KEY"])
cred = credentials.Certificate(firebase_key)
firebase_admin.initialize_app(cred)
db = firestore.client()
FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# ================= SYMPTOM → DEPARTMENT MAP =================
SYMPTOM_MAP = {

    # 🟢 GENERAL MEDICINE
    "fever": "General",
    "cold": "General",
    "cough": "General",
    "headache": "General",
    "body pain": "General",
    "weakness": "General",
    "vomiting": "General",
    "nausea": "General",

    "காய்ச்சல்": "General",
    "சளி": "General",
    "இருமல்": "General",
    "தலைவலி": "General",
    "உடல் வலி": "General",
    "சோர்வு": "General",
    "வாந்தி": "General",

    # ❤️ CARDIOLOGY
    "chest pain": "Cardiology",
    "heart pain": "Cardiology",
    "palpitation": "Cardiology",
    "bp": "Cardiology",
    "blood pressure": "Cardiology",

    "மார்பு வலி": "Cardiology",
    "இதயம் வலி": "Cardiology",
    "இதய துடிப்பு": "Cardiology",
    "ரத்த அழுத்தம்": "Cardiology",

    # 🧠 NEUROLOGY
    "migraine": "Neurology",
    "seizure": "Neurology",
    "fits": "Neurology",
    "paralysis": "Neurology",
    "memory loss": "Neurology",
    "dizziness": "Neurology",

    "மைக்ரேன்": "Neurology",
    "வலிப்பு": "Neurology",
    "மயக்கம்": "Neurology",
    "நினைவிழப்பு": "Neurology",
    "தலைசுற்றல்": "Neurology",

    # 👁️ OPHTHALMOLOGY
    "eye pain": "Ophthalmology",
    "eye irritation": "Ophthalmology",
    "blurred vision": "Ophthalmology",
    "red eye": "Ophthalmology",

    "கண் வலி": "Ophthalmology",
    "கண் எரிச்சல்": "Ophthalmology",
    "பார்வை மங்கல்": "Ophthalmology",
    "கண் சிவப்பு": "Ophthalmology",

    # 🦷 DENTAL
    "tooth pain": "Dentist",
    "gum pain": "Dentist",
    "mouth ulcer": "Dentist",

    "பல் வலி": "Dentist",
    "பல் ஈறு வலி": "Dentist",
    "வாய் புண்": "Dentist",

    # 🍽️ GASTROENTEROLOGY
    "stomach pain": "Gastroenterology",
    "gas": "Gastroenterology",
    "acidity": "Gastroenterology",
    "diarrhea": "Gastroenterology",
    "constipation": "Gastroenterology",

    "வயிறு வலி": "Gastroenterology",
    "வாயு": "Gastroenterology",
    "அஜீரணம்": "Gastroenterology",
    "வயிற்றுப்போக்கு": "Gastroenterology",

    # 🧴 DERMATOLOGY
    "skin allergy": "Dermatology",
    "itching": "Dermatology",
    "rash": "Dermatology",
    "pimples": "Dermatology",

    "தோல் அரிப்பு": "Dermatology",
    "அலர்ஜி": "Dermatology",
    "தோல் புண்": "Dermatology",
    "முகப்பரு": "Dermatology",

    # 👂 ENT
    "ear pain": "ENT",
    "throat pain": "ENT",
    "voice problem": "ENT",
    "sinus": "ENT",

    "காது வலி": "ENT",
    "தொண்டை வலி": "ENT",
    "குரல் பிரச்சனை": "ENT",
    "மூக்கு அடைப்பு": "ENT",

    # 🧘 ORTHOPEDICS
    "joint pain": "Orthopedics",
    "knee pain": "Orthopedics",
    "back pain": "Orthopedics",
    "neck pain": "Orthopedics",

    "மூட்டு வலி": "Orthopedics",
    "முதுகு வலி": "Orthopedics",
    "கழுத்து வலி": "Orthopedics",

    # 👶 PEDIATRICS
    "child fever": "Pediatrics",
    "child cough": "Pediatrics",

    "குழந்தை காய்ச்சல்": "Pediatrics",
    "குழந்தை இருமல்": "Pediatrics",

    # 👩 WOMEN / GYNECOLOGY
    "period pain": "Gynecology",
    "irregular periods": "Gynecology",
    "pregnancy": "Gynecology",

    "மாதவிடாய் வலி": "Gynecology",
    "மாதவிடாய் கோளாறு": "Gynecology",
    "கர்ப்பம்": "Gynecology",
}



def detect_departments(symptoms):
    symptoms = symptoms.lower()
    departments = set()
    for key, dept in SYMPTOM_MAP.items():
        if key in symptoms:
            departments.add(dept)
    return list(departments) if departments else ["General"]

# ================= HOME =================
@app.route("/")
def home():
    if "user" in session:
        if session.get("role") == "patient":
            return redirect("/patient_dashboard")
        elif session.get("role") == "doctor":
            return redirect("/doctor_dashboard")

    return render_template("login.html")


# ================= PATIENT LOGIN =================
@app.route("/login_patient", methods=["GET", "POST"])
def login_patient():
    if request.method == "POST":
        email = request.form.get("email")
        name = request.form.get("name")

        session["role"] = "patient"
        session["user"] = email
        session["name"] = name

        db.collection("patients").document(email).set({
            "name": name,
            "email": email
        }, merge=True)

        return redirect("/patient_dashboard")

    return render_template("login_patient.html")

# ================= DOCTOR LOGIN =================
@app.route("/login_doctor", methods=["GET", "POST"])
def login_doctor():
    if request.method == "POST":
        session["role"] = "doctor"
        session["user"] = request.form.get("email")
        return redirect("/doctor_dashboard")
    return render_template("login_doctor.html")

# ================= DASHBOARDS =================
@app.route("/patient_dashboard")
def patient_dashboard():
    # ✅ SESSION CHECK (VERY IMPORTANT)
    if session.get("role") != "patient":
        return redirect("/login_patient")

    email = session.get("user")

    appointments = db.collection("appointments") \
        .where("patient_id", "==", email) \
        .stream()

    result = []
    for a in appointments:
        d = a.to_dict()
        d["id"] = a.id
        result.append(d)

    return render_template("patient.html", appointments=result)



@app.route("/doctor_dashboard")
def doctor_dashboard():
    if session.get("role") != "doctor":
        return redirect("/login_doctor")

    appointments = db.collection("appointments") \
        .where("status", "==", "Confirmed") \
        .order_by("time") \
        .stream()

    appointment_list = []
    for a in appointments:
        data = a.to_dict()
        data["id"] = a.id
        appointment_list.append(data)

    return render_template("doctor.html", appointments=appointment_list)
# ================= TIME SLOT CHECK =================
def slot_available(department, time):
    query = db.collection("appointments") \
        .where("department", "==", department) \
        .where("time", "==", time) \
        .where("status", "==", "Confirmed") \
        .stream()
    return not any(query)

# ================= BOOK APPOINTMENT =================

@app.route("/book_appointments_multi", methods=["POST"])
def book_appointments_multi():
    if session.get("role") != "patient":
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.json
    name = data.get("name")
    symptoms = data.get("symptoms")
    time = data.get("time")      # e.g. "11:00"
    phone = data.get("phone")

    if not phone:
        return jsonify({"status": "error", "message": "Phone required"}), 400

    patient_id = session["user"]
    departments = detect_departments(symptoms)

    # ✅ PLACE IT HERE (IMPORTANT)
    appointment_datetime = datetime.combine(
        datetime.today(),
        datetime.strptime(time, "%H:%M").time()
    )

    booked = []
    rejected = []

    for dept in departments:
        if slot_available(dept, time):
            db.collection("appointments").add({
                "patient_id": patient_id,
                "patient_name": name if name else session.get("name", "Unknown"),
                "department": dept,
                "symptoms": symptoms,
                "time": time,
                "appointment_datetime": appointment_datetime,
                "appointment_date": appointment_datetime.strftime("%d-%m-%Y"),
                "status": "Confirmed",
                "phone": phone,
                "reminder_sent": False,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            booked.append(dept)
        else:
            rejected.append(dept)

    return jsonify({
        "status": "success",
        "booked": booked,
        "rejected": rejected
    })


# ================= CANCEL APPOINTMENT =================
@app.route("/cancel_appointment", methods=["POST"])
def cancel_appointment():
    data = request.json
    appointment_id = data.get("appointment_id")

    db.collection("appointments").document(appointment_id).update({
        "status": "Cancelled"
    })

    return jsonify({"status": "success"})

# ================= GET APPOINTMENTS =================
@app.route("/get_appointments")
def get_appointments():
    docs = db.collection("appointments").order_by("created_at").stream()
    appointments = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        appointments.append(data)
    return jsonify({"appointments": appointments})
@app.route("/complete_appointment", methods=["POST"])
def complete_appointment():
    if session.get("role") != "doctor":
        return jsonify({"status": "unauthorized"}), 401

    data = request.json
    appointment_id = data.get("appointment_id")

    db.collection("appointments").document(appointment_id).update({
        "status": "Completed"
    })

    return jsonify({"status": "success"})
@app.route("/add_prescription", methods=["POST"])
def add_prescription():
    try:
        data = request.json
        appointment_id = data["appointment_id"]
        prescription = data["prescription"]

        appointment_ref = db.collection("appointments").document(appointment_id)
        appointment = appointment_ref.get().to_dict()

        # Save prescription
        appointment_ref.update({
            "prescription": prescription,
            "status": "Completed"
        })

        # EMAIL
        try:
            email_message = f"""
Appointment Completed

Patient: {appointment['patient_name']}
Department: {appointment['department']}
Time: {appointment['time']}

Prescription:
{prescription}
"""
            email_status, email_error = send_email_notification(
                appointment["patient_id"],
                "Your Prescription",
                email_message
            )

            appointment_ref.update({
                "email_status": email_status,
                "email_error": str(email_error) if email_error else None
            })

        except Exception as e:
            appointment_ref.update({
                "email_status": "failed",
                "email_error": str(e)
            })

        # SMS
        try:
            sms_text = f"""
AI Health Assistant
Department: {appointment['department']}
Time: {appointment['time']}

Prescription:
{prescription}
"""

            sms_status, sms_error = send_sms_fast2sms(
                appointment["phone"],
                sms_text
            )

            appointment_ref.update({
                "sms_status": sms_status,
                "sms_error": str(sms_error) if sms_error else None
            })

        except Exception as e:
            appointment_ref.update({
                "sms_status": "failed",
                "sms_error": str(e)
            })

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/my_prescriptions")
def my_prescriptions():
    if session.get("role") != "patient":
        return jsonify([])

    email = session["user"]
    docs = db.collection("appointments") \
        .where("patient_id", "==", email) \
        .where("status", "==", "Completed") \
        .stream()

    data = []
    for d in docs:
        item = d.to_dict()
        item["id"] = d.id
        data.append(item)

    return jsonify(data)

@app.route("/download_prescription/<appointment_id>")
def download_prescription(appointment_id):
    doc = db.collection("appointments").document(appointment_id).get()

    if not doc.exists:
        return "Prescription not found", 404

    data = doc.to_dict()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 800, "AI Health Assistant - Prescription")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Patient: {data['patient_name']}")
    pdf.drawString(50, 740, f"Department: {data['department']}")
    pdf.drawString(50, 720, f"Time: {data['time']}")

    pdf.drawString(50, 680, "Prescription:")
    text = pdf.beginText(50, 660)
    for line in data.get("prescription", "").split("\n"):
        text.textLine(line)

    pdf.drawText(text)
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name="prescription.pdf",
                     mimetype="application/pdf")
def send_sms_fast2sms(phone, message):
    try:
        # Fast2SMS accepts only 10-digit Indian numbers
        phone = phone.replace("+91", "").strip()

        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "route": "q",
            "message": message,
            "language": "english",
            "numbers": phone
        }
        headers = {
            "authorization": FAST2SMS_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        result = response.json()

        if result.get("return") is True:
            return "sent", None
        else:
            return "failed", result

    except Exception as e:
        return "failed", str(e)
@app.route("/send_reminders")
def send_reminders():
    now = datetime.now()
    one_hour_later = now + timedelta(hours=1)

    appointments = db.collection("appointments") \
        .where("status", "==", "Confirmed") \
        .where("reminder_sent", "==", False) \
        .stream()

    for a in appointments:
        data = a.to_dict()
        appt_time = data.get("appointment_datetime")

        if appt_time and now <= appt_time <= one_hour_later:
            tamil_msg = f"""
AI மருத்துவ உதவியாளர் 🏥
உங்கள் டாக்டர் சந்திப்பு இன்று {data['time']} மணிக்கு உள்ளது.
துறை: {data['department']}
நன்றி.
"""

            status, error = send_sms_fast2sms(data["phone"], tamil_msg)

            db.collection("appointments").document(a.id).update({
                "reminder_sent": True,
                "reminder_status": status,
                "reminder_error": str(error) if error else None
            })

    return "Reminders checked"

def send_email_notification(to_email, subject, message):
    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        # Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)

        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()

        return "sent", None

    except Exception as e:
        print("EMAIL ERROR:", e)
        return "failed", str(e)
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
