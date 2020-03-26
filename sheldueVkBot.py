# -*- coding: utf-8 -*-
import bs4
import requests
import random
import pymysql

pymysql.install_as_MySQLdb()


class VkBot:
    db = None
    debugMode = True
    _COMMANDS: list = ["ПРИВЕТ", 'ПОГОДА', "ВРЕМЯ", "ПОКА", "ПОМОЩЬ", "РАСПИСАНИЕ", "СЕГОДНЯ", "ЗАВТРА", "1 НЕДЕЛЯ",
                       "2 НЕДЕЛЯ"]
    _ANSWER_VARIANTS: dict = {'DoesntUnderstand': ["Хмм... Не понимаю тебя, повтори снова",
                                                   "Я тебя не понимаю",
                                                   "Не понимаю"],
                              'Hello': ['Да привет-привет :)',
                                        'Здоровались уже :)'],
                              'Bye': ['Пока :)',
                                      'Еще увидимся!']
                              }

    def __init__(self, user_id):
        self.userData = {}
        self._USER_ID = user_id
        self._USERNAME = self._get_user_name_from_vk_id(user_id)
        VkBot.debug_print('#DEBUG: Constructor <BEGIN>')
        VkBot._try_connect_to_db()
        self._add_user_ifno_exists()
        self.userData = self._get_data_from_db_by_id()
        VkBot._try_disconnect_db()
        VkBot.debug_print('#DEBUG: Constructor <END>')

    @staticmethod
    def debug_print(msg: str):
        if VkBot.debugMode:
            print(msg)

    # БД_BEGIN-------------------------------------------------------------------------------------
    @staticmethod
    def _if_connected():
        VkBot.debug_print('#DEBUG: _if_connected() <BEGIN>')
        return not (VkBot.db is None)
        VkBot.debug_print('#DEBUG: _if_connected() <END>')

    @staticmethod
    def _try_connect_to_db():
        VkBot.debug_print('#DEBUG: _try_connect_to_db() <BEGIN>')
        if VkBot.db is not None:
            VkBot.debug_print('#DEBUG: _try_connect_to_db(): Already connected')
            VkBot.ac = True
        try:
            data = []
            file = open("dbData.txt", "r")
            for row in file:
                data.append(str(row))
            file.close()
            VkBot.db = pymysql.connect(host=data[0][0:-1],
                                       user=data[1][0:-1],
                                       passwd=data[2][0:-1],
                                       db=data[3])
            VkBot.debug_print('#DEBUG: _try_connect_to_db(): VkBot.db after connection:' + str(VkBot.db))
        except Exception:
            VkBot.debug_print('#DEBUG: _try_connect_to_db(): Connection failed' + str(Exception))
            VkBot.db = None
            VkBot.ac = False
        finally:
            VkBot.debug_print('#DEBUG: _try_connect_to_db() <END>')

    @staticmethod
    def _try_disconnect_db():
        VkBot.debug_print('#DEBUG: _try_disconnect_db() <BEGIN>')
        try:
            VkBot.db.close()
            VkBot.db = None
            VkBot.debug_print('#DEBUG: _try_disconnect_db(): Disconnected')
        except:
            VkBot.debug_print('#DEBUG: _try_disconnect_db(): Disconnection failed')
        finally:
            VkBot.debug_print('#DEBUG: _try_disconnect_db() <END>')

    def _get_data_from_db_by_id(self):
        VkBot.debug_print('#DEBUG: _get_data_from_db_by_id() <BEGIN>')
        num_fields = 0
        fieldsNames = None
        fieldsData = None
        resultDict: dict = {}
        wasConnected = VkBot._if_connected()
        if not wasConnected:
            VkBot._try_connect_to_db()
        VkBot.debug_print('#DEBUG: _get_data_from_db_by_id(): vkbot.db = ' + str(VkBot.db))
        if VkBot.db is None:
            VkBot.debug_print('#DEBUG: _get_data_from_db_by_id(): There is no connection')
            raise Exception('no connetion')
        if self._is_user_in_base():
            VkBot.debug_print('#DEBUG: _get_data_from_db_by_id(): User in base')
            VkBot.debug_print('#DEBUG: _get_data_from_db_by_id(): vkbot.db = ' + str(VkBot.db))
            cursor = VkBot.db.cursor()
            cursor.execute("select * from usersTable where userId=" + str(self._USER_ID))
            fieldsData = cursor.fetchone()
            num_fields = len(cursor.description)
            fieldsNames = [i[0] for i in cursor.description]
            cursor.close()
        for i in range(num_fields):
            resultDict[fieldsNames[i]] = fieldsData[i]
        if not wasConnected:
            VkBot._try_disconnect_db()
        VkBot.debug_print('#DEBUG: _get_data_from_db_by_id() <END>')
        return resultDict

    def _commit_data(self):
        VkBot.debug_print('#DEBUG: _commit_data() <BEGIN>')
        wasConnected = VkBot._if_connected()
        if not wasConnected:
            VkBot._try_connect_to_db()
        cursor = VkBot.db.cursor()
        cursor.execute(
            'update usersTable set state=\'' + self.userData['state'] + '\' where userId=' + str(self._USER_ID))
        VkBot.db.commit()
        cursor.close()
        if not wasConnected:
            VkBot._try_disconnect_db()
        VkBot.debug_print('#DEBUG: _commit_data() <END>')

    def _is_user_in_base(self):  # false-doesn't exist in db; true - exists in db
        VkBot.debug_print('#DEBUG:_is_user_in_base(self): ' + str(self._USER_ID) + ' <BEGIN>')
        wasConnected = VkBot._if_connected()
        if not wasConnected:
            VkBot._try_connect_to_db()
        cursor = VkBot.db.cursor()
        cursor.execute("select * from usersTable where userId=" + str(self._USER_ID))
        row = cursor.fetchone()
        if not wasConnected:
            VkBot._try_disconnect_db()
        VkBot.debug_print('#DEBUG:_is_user_in_base(self): ' + str(self._USER_ID) + ' <END>')
        if row is None:
            return False
        else:
            return True

    def _add_user_into_base(self):
        VkBot.debug_print('#DEBUG:add_user_into_base(self):' + str(self._USER_ID) + ' <BEGIN>')
        wasConnected = VkBot._if_connected()
        if not wasConnected:
            VkBot._try_connect_to_db()
        cursor = VkBot.db.cursor()
        cursor.execute("insert into usersTable (userId, state) values(" +
                       str(self._USER_ID) +
                       ", " +
                       "\'None\'" +
                       ")")
        VkBot.db.commit()
        cursor.close()
        if not wasConnected:
            VkBot._try_disconnect_db()
        VkBot.debug_print('#DEBUG:add_user_into_base(self):' + str(self._USER_ID) + ' <END>')

    def _add_user_ifno_exists(self):
        VkBot.debug_print('#DEBUG:_add_user_ifno_exists(self):' + str(self._USER_ID) + ' <BEGIN>')
        wasConnected = VkBot._if_connected()
        if not wasConnected:
            VkBot._try_connect_to_db()
        if not self._is_user_in_base():
            self._add_user_into_base()
        if not wasConnected:
            VkBot._try_disconnect_db()
        VkBot.debug_print('#DEBUG:_add_user_ifno_exists(self):' + str(self._USER_ID) + '<END>')

    # БД_END---------------------------------------------------------------------------------------

    # АЛГОРИТМЫ_BEGIN--------------------------------------------------------------------------------
    @staticmethod
    def _lewenstein(a, b):
        "Calculates the Levenshtein distance between a and b."
        n, m = len(a), len(b)
        if n > m:
            # Make sure n <= m, to use O(min(n, m)) space
            a, b = b, a
            n, m = m, n

        current_row = range(n + 1)  # Keep current and previous row, not entire matrix
        for i in range(1, m + 1):
            previous_row, current_row = current_row, [i] + [0] * n
            for j in range(1, n + 1):
                add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
                if a[j - 1] != b[i - 1]:
                    change += 1
                current_row[j] = min(add, delete, change)

        return current_row[n]

    # АЛГОРИТМЫ_END--------------------------------------------------------------------------------

    # ОТВЕТЫ_BEGIN---------------------------------------------------------------------------------
    def _doesnt_understand(self):
        resultStr = random.choice(self._ANSWER_VARIANTS["DoesntUnderstand"]) + '\n\n'
        resultStr += self._get_help()
        return resultStr

    def _get_help(self):
        resultStr = ''
        resultStr += 'Список доступных команд:\n'
        resultStr += '\n'.join(self._COMMANDS)
        return resultStr

    # Получение времени:
    def _get_time(self):
        request = requests.get("https://my-calend.ru/date-and-time-today")
        b = bs4.BeautifulSoup(request.text, "html.parser")
        return VkBot._clean_all_tag_from_str(str(b.select(".page")[0].findAll("h2")[1])).split()[1]

    # Получение погоды
    def _get_weather(self, city: str = "Volgograd,RU"):
        s_city = city
        resultStr = ''
        resultDict: dict = {}
        appid = "eabbdc3d4153fe5bbf267a916b05447b"
        try:
            res = requests.get("http://api.openweathermap.org/data/2.5/weather?",
                               'q=' + s_city +
                               '&' + 'appid=' + appid +
                               '&units=metric&lang=ru')
            data = res.json()
            resultDict['Город'] = data['name']
            resultDict['Небо'] = data['weather'][0]['description']
            resultDict['Температура'] = str(data['main']['temp']) + ' °C'
            resultDict['Ощущается как'] = str(data['main']['feels_like']) + ' °C'
            resultDict['Минимальная температура за день'] = str(data['main']['temp_min']) + ' °C'
            resultDict['Максимальная температура за день'] = str(data['main']['temp_max']) + ' °C'
            resultDict['Давление'] = str(data['main']['pressure']) + ' мм.рт.ст.'
            resultDict['Влажность'] = str(data['main']['humidity']) + ' %'
            resultDict['Скорость ветра'] = str(data['wind']['speed']) + 'м/c'
            resultDict['Направление ветра'] = str(data['wind']['deg']) + ' °'
            for (key, value) in resultDict.items():
                resultStr += str(key) + ':  ' + str(value) + '\n'
            return resultStr
        except Exception as e:
            print("Exception (find):", e)
            pass

        return {'Ошибка': 'Ошибка'}

    # ОТВЕТЫ_END-----------------------------------------------------------------------------------

    def _get_guess_list(self, word):
        resultList = []
        for command in VkBot._COMMANDS:
            dist = VkBot._lewenstein(word, command)
            if (dist < 2):
                resultList.append(command)
        return resultList

    def _get_user_name_from_vk_id(self, user_id):
        request = requests.get("https://vk.com/id" + str(user_id))
        bs = bs4.BeautifulSoup(request.text, "html.parser")
        user_name = self._clean_all_tag_from_str(bs.findAll("title")[0])
        return user_name.split()[0]

    # Метод для очистки от ненужных тэгов
    @staticmethod
    def _clean_all_tag_from_str(string_line):
        """
        Очистка строки stringLine от тэгов и их содержимых
        :param string_line: Очищаемая строка
        :return: очищенная строка
        """
        result = ""
        not_skip = True
        for i in list(string_line):
            if not_skip:
                if i == "<":
                    not_skip = False
                else:
                    result += i
            else:
                if i == ">":
                    not_skip = True

        return result

    def new_message(self, message):

        # Привет
        if message.upper() == self._COMMANDS[0]:
            ansMsg = ''
            if self.userData['state'] == 'hello':
                ansMsg = random.choice(self._ANSWER_VARIANTS["Hello"])
            else:
                ansMsg = "Привет-привет, {}!".format(self._USERNAME)
            self.userData['state'] = 'hello'
            self._commit_data()
            return [ansMsg, "helpKeyboard"]

        # Погода
        elif message.upper() == self._COMMANDS[1]:
            return [self._get_weather(), "helpKeyboard"]

        # Время
        elif message.upper() == self._COMMANDS[2]:
            return ['Временно недоступно', "helpKeyboard"]  # В Москве сейчас ' + self._get_time()

        # Пока
        elif message.upper() == self._COMMANDS[3]:
            ansMsg = ''
            if self.userData['state'] == 'bye':
                ansMsg = random.choice(self._ANSWER_VARIANTS["Bye"])
            else:
                ansMsg = "Пока-пока, {}!".format(self._USERNAME)
            self.userData['state'] = 'bye'
            self._commit_data()
            return [ansMsg, "helpKeyboard"]

        # Помощь
        elif message.upper() == self._COMMANDS[4]:
            return [self._get_help(), "helpKeyboard"]

        # Расписание
        elif message.upper() == self._COMMANDS[5]:
            return ['Выберите вариант расписания из меню ниже', "sheldueKeyboard"]

        # Расписание.Сегодня
        elif message.upper() == self._COMMANDS[6]:
            return ['В разработке', "sheldueKeyboard"]

        # Расписание.Завтра
        elif message.upper() == self._COMMANDS[7]:
            return ['В разработке', "sheldueKeyboard"]

        # Расписание.1 неделя
        elif message.upper() == self._COMMANDS[8]:
            return ['В разработке', "sheldueKeyboard"]

        # Расписание.2 неделя
        elif message.upper() == self._COMMANDS[9]:
            return ['В разработке', "sheldueKeyboard"]

        else:
            guessList = self._get_guess_list(message.upper())
            if len(guessList) > 0:
                resultStr = ''
                resultStr += 'Хмм...Возможно вы имели в виду:\n'
                for el in guessList:
                    resultStr += str(el) + '\n'
            return [self._doesnt_understand(), "helpKeyboard"]
