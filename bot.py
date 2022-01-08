from flask import Flask, request
import os
import telebot
import fire

server = Flask(__name__)

API_KEY = os.environ('API_KEY')
bot = telebot.TeleBot(API_KEY)

NO_USER_TIMESLOT_MESSAGE = "Sorry, but you have not added any swap requests yet; try adding one first!"

########################
### FILTER FUNCTIONS ###
########################

def change_timeslot_request(message):
    request = message.text.split()
    if len(request) != 2 or request[0].lower() not in "change":
        return False
    else:
        return True

def select_timeslot_request(message):
    request = message.text.split()
    if len(request) != 3 or request[0].lower() not in "select":
        return False
    else:
        return True

def resolve_timeslot_request(message):
    request = message.text.split()
    if len(request) != 2 or request[0].lower() not in "resolve":
        return False
    if request[1][0] not in "@":
        return False
    return True

def resolve_timeslot_response(message):
    request = message.text.split()
    if len(request) != 2 or request[0].lower() not in "accept":
        return False
    if request[1][0] not in "@":
        return False
    return True

#####################
### BOT FUNCTIONS ###
#####################

@bot.message_handler(commands=['start'])
def greet(message):
    bot.send_message(message.chat.id, "Greetings!")


@bot.message_handler(commands=['list'])
def list(message):
    bot.send_message(message.chat.id, "Fetching data...")
    list_string = fire.list_timeslots_all()
    bot.send_message(message.chat.id, list_string)


@bot.message_handler(commands=['listcurrent'])
def list(message):
    bot.send_message(message.chat.id, "Fetching data...")
    tele_handle = message.chat.username
    timeslot_current = fire.get_slot_from_tele_handle(tele_handle, "current")
    if not timeslot_current:
        bot.send_message(message.chat.id, NO_USER_TIMESLOT_MESSAGE)
    else:
        list_string = fire.list_timeslots_filtered_only_current(timeslot_current)
        if not list_string:
            list_string = "Oops! There are no users that require your current timeslot. Please try again later!"
        else:
            bot.send_message(message.chat.id,"Here is a list of all users that want your current timeslot:")
        bot.send_message(message.chat.id, list_string)


@bot.message_handler(commands=['listmutual'])
def list(message):
    bot.send_message(message.chat.id, "Fetching data...")
    tele_handle = message.chat.username
    timeslot_current = fire.get_slot_from_tele_handle(tele_handle, "current")
    if not timeslot_current:
        bot.send_message(message.chat.id, NO_USER_TIMESLOT_MESSAGE)
    else:
        timeslot_desired = fire.get_slot_from_tele_handle(tele_handle, "desired")
        list_string = fire.list_timeslots_filtered_mutual(timeslot_current, timeslot_desired)
        if not list_string:
            list_string = "Oops! There are no mutual swaps available currently. Please try again later!"
        else:
            bot.send_message(message.chat.id,"Here is a list of all users that are eligible for a mutual swap with you:")
        bot.send_message(message.chat.id, list_string)


@bot.message_handler(commands=["delete"])
def delete(message):
    tele_handle = message.chat.username
    user_does_exist = fire.delete_user_data(tele_handle)
    if (user_does_exist):
        bot.send_message(message.chat.id, "Your swap request has been deleted.")
    else:
        bot.send_message(message.chat.id, NO_USER_TIMESLOT_MESSAGE)


@bot.message_handler(commands=['get'])
def get(message):
    tele_handle = message.chat.username
    list_string = fire.get_user_data(tele_handle)
    if (list_string):
        bot.send_message(message.chat.id, list_string)
    else:
        bot.send_message(message.chat.id, "You have not added any swap requests yet; add one using the select command.")

#Change Timeslot
@bot.message_handler(func=change_timeslot_request)
def change(message):
    tele_handle = message.chat.username
    new_desired_slot = message.text.split()[1]
    fire.update_user_data(tele_handle, new_desired_slot)
    bot.send_message(message.chat.id, "Your swap request has been updated to request for slot " + new_desired_slot + ".")
        

#Select/Add Timeslot
@bot.message_handler(func=select_timeslot_request)
def select_timeslot(message):
    timeslot_current = message.text.split()[1]
    timeslot_desired = message.text.split()[2]
    tele_handle = message.chat.username
    confirmation_message = "Nice! So these are your chosen timeslots:\n" + "Currently has: " + timeslot_current + "\n" + "Requesting for: " + timeslot_desired + "\n" 
    bot.send_message(message.chat.id, confirmation_message)
    fire.push_user_data(tele_handle, timeslot_current, timeslot_desired, message.chat.id)

#Request to resolve a mutual swap with another user
@bot.message_handler(func=resolve_timeslot_request)
def resolve_timeslot_request(message):
    user1 = message.chat.username
    user2 = message.text.split()[1][1:]
    print(user1, user2)
    mutual_user_id = fire.get_user_id(user2)
    if not mutual_user_id:
        bot.send_message(message.chat.id, "Sorry, but the telegram handle you keyed in does not exist. Please try again.")
    else:
        timeslot_string = fire.get_user_data(user2)
        message_string = "@" + user1 + " has requested a mutual swap with you for the following timeslot:\n\n" + timeslot_string + "\n\nDo you accept?"
        bot.send_message(mutual_user_id, message_string)

#Respond to resolve a mutual swap with another user
@bot.message_handler(func=resolve_timeslot_response)
def resolve_timeslot_response(message):
    user1 = message.chat.username
    user2 = message.text.split()[1][1:]
    mutual_user_id = fire.get_user_id(user2)
    fire.delete_user_data(user1)
    fire.delete_user_data(user2)
    message_string_1 = "Your timeslot swap has been successfully resolved with @" + user1 + ". Congratulations!"
    message_string_2 = "Your timeslot swap has been successfully resolved with @" + user2 + ". Congratulations!"
    bot.send_message(message.chat.id, message_string_1)
    bot.send_message(mutual_user_id, message_string_2)

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))