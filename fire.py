import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime
import os

#fetch service account key JSON file contents
cred = credentials.Certificate('serviceAccountKey.json')

#initialize app with a service account to grant admin privileges
app = firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ['FIREBASE']
})

#save data
ref = db.reference("/")

def push_user_data(tele_handle, current, desired, chat_id):
    date_time_obj = datetime.now()
    date_time_value = int(round(date_time_obj.timestamp()))
    ref.push({
        tele_handle:
        {
            "id": date_time_value,
            "current": current,
            "desired": desired,
            "chatId": chat_id
        }
    })

def get_user_data(tele_handle):
    list = ref.get()
    for key in list:
        for user in list[key]:
            if user == tele_handle:
                user_properties = list[key][user]
                list_string = ""
                list_string += "@" + tele_handle + ":\n"
                list_string += "Currently has: " + user_properties["current"] + "\n"
                list_string += "Requesting for: " + user_properties["desired"]
                return list_string
    return ""

def get_user_id(tele_handle):
    list = ref.get()
    for key in list:
        for user in list[key]:
            if user == tele_handle:
                return list[key][user]["chatId"]
    return 0

def delete_user_data(tele_handle):
    list = ref.get()
    for key in list:
        for user in list[key]:
            if user == tele_handle:
                ref.child(key).set({})
                return True
    return False

def update_user_data(tele_handle, slot):
    list = ref.get()
    for key in list:
        for user in list[key]:
            if user == tele_handle:
                user_ref = ref.child(key).child(user)
                user_ref.update({
                    "desired": slot
                })
                return

def get_slot_from_tele_handle(tele_handle, slot_type):
    list = ref.get()
    for key in list:
        for user in list[key]:
            if user == tele_handle:
                return list[key][user]["current"] if (slot_type == "current") else list[key][user]["desired"]

#Shouldn't be exposed for the actual bot but leaving it here for testing purposes
def list_timeslots_all():
    list = ref.get()
    return formatted_list_output(list, "verbose")

#Produces a list of users that can swap to requester's timeslot, but not necessarily requester's desired timeslot  
def list_timeslots_filtered_only_current(user_current_timeslot):
    list = ref.get()
    filtered_list = {}
    for key in list:
        for user in list[key]:
            if list[key][user]["desired"] == user_current_timeslot:
                filtered_list[key] = list[key]

    return formatted_list_output(filtered_list, "verbose")

#Produces a list of users that are eligible for a mutual swap
def list_timeslots_filtered_mutual(user_current_timeslot, user_desired_timeslot):
    list = ref.get()
    filtered_list = {}
    for key in list:
        for user in list[key]:
            if list[key][user]["desired"] == user_current_timeslot and list[key][user]["current"] == user_desired_timeslot:
                filtered_list[key] = list[key]

    return formatted_list_output(filtered_list, "name")

def formatted_list_output(list, type):
    liststring = ""
    format_string = ":\n" if (type == "verbose") else "\n"
    for key in list:
        for user in list[key]:
            liststring += "@" + user + format_string
            if (type == "verbose"):
                liststring += "Currently has: " + list[key][user]["current"] + "\n\n"
    return liststring