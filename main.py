# -*- coding: utf-8 -*-
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from sheldueVkBot import VkBot
import  time



def write_msg(user_id, answer):
    message = answer[0]
    keyboardType = answer[1]
    vk.method('messages.send', {
                                'user_id': user_id,
                                'message': message,
                                'random_id' : time.time(),
                                'keyboard' : open("keyboards/" + str(keyboardType) + ".json", "r", encoding="UTF-8").read()
                               }
             )

# API-токен
file = open("tokenVk.txt", "r")
token = file.read()
file.close()
# Авторизуемся как сообщество
vk = vk_api.VkApi(token=token)

# Работа с сообщениями
longpoll = VkLongPoll(vk)

# Основной цикл
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            print('\n\nNew message:')
            print('For me by: {}'.format(event.user_id))

            bot = VkBot(event.user_id)
            write_msg(event.user_id, bot.new_message(event.text))
            print("Text: " + event.text)