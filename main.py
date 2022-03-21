from auth            import login
from datetime        import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
import os.path, json, traceback, vk_api, random, http.client, requests

#=================================

BUFFSIZE = 3

#=================================

def continue_text (text: str) -> str:
    print (f"TEST: {text}")

    tries = 0
    while tries < 3:
        try:
            request_data = {
                'prompt': text,
                'length': 50
            }

            response = requests.post ("https://pelevin.gpt.dobro.ai/generate/", timeout = 10, json = request_data)
            if response.status_code != requests.codes.ok:
                raise RuntimeError (f"Request failed: {http.client.responses [response.status_code]} ({response.status_code})")

            response_data = json.loads (response.text)
            return response_data['replies'][0]

        except Exception as exc:
            traceback.print_exc ()
            
        tries += 1

    return "Пошёл нахуй"

#=================================

class Bot ():
    cache_filename = 'cache.json'
    ids_filename   = 'ids.json'
    log_filename   = 'log.txt'

#=================================

    def __init__ (self):
        self.buffer   = {}
        self.cache    = {}
        self.longpoll = None
        self.session  = None

        if not os.path.exists (self.ids_filename):
            with open (self.ids_filename, 'w') as file:
                json.dump ([], file, indent = 4)
                file.close ()

                self.log (f"File '{self.ids_filename}' looks to be empty. Add ids you wish the bot to reply to into this file.")            

        if os.path.exists (self.log_filename):
            os.remove (self.log_filename)

        try: 
            if os.path.exists (self.cache_filename):
                with open (self.cache_filename, 'r') as file:
                    self.cache = json.load (file)
                    file.close ()

        except Exception: pass

        if not 'token' in self.cache:
            try:
                token = login () 
                if not token:
                    return

                self.cache['token'] = token

            except Exception as exc:
                self.log (f"Authorization failed: {exc}\n\n{traceback.format_exc ()}")
                return

            while True:
                print ("Do you want to save the token in cache? [y/n]: ", end = '')
                
                ans = input ()
                if not len (ans): continue

                if ans.startswith ('y'):
                    try:
                        self.log ("Saving the cache")

                        with open (self.cache_filename, 'w') as file:
                            json.dump (self.cache, file, indent = 4)
                            file.close ()

                    except Exception as exc:
                        self.log (f"Failed: {exc}")

                    break

                elif ans.startswith ('n'):
                    break

        self.log ("Logging in...")
        self.session = vk_api.VkApi (token = self.cache['token'])

#=================================

    def start (self):
        self.log ("Starting the bot...")
        
        if not self.session:
            self.log ("Failed")
            return

        self.vk       = self.session.get_api ()
        self.longpoll = VkLongPoll (self.session)

        self.log ("Waiting for events")
        while True:
            try:
                for event in self.longpoll.listen ():
                    try: self.handle_event (event)
                    except Exception as exc:
                        self.log (f"Event handler error: {exc}\n\n{traceback.format_exc ()}")

            except KeyboardInterrupt:
                self.log ("Interrupted")
                return

            except Exception as exc:
                self.log (f"Unexpected exception: {exc}\n\n{traceback.format_exc ()}")

#=================================

    def get_spam_ids (self) -> list:
        with open (self.ids_filename, 'r') as file:
            ids = json.load (file)
            file.close ()

            return ids

#=================================

    def handle_event (self, event):
        if event.type != VkEventType.MESSAGE_NEW:
            return

        if not event.from_user:
            return

        if not event.to_me or not event.text:
            return

        if not event.user_id in self.get_spam_ids ():
            return

        self.log (f"Received message from id{event.user_id}: {event.text}")

        text_begin = ""

        key = str (event.user_id)
        if key in self.buffer:
            text_begin += ' '.join (self.buffer[str (event.user_id)])

        else: self.buffer[key] = []

        text_begin += event.text
        message = continue_text (text_begin)

        self.send_message (event.user_id, message)

        self.buffer[key].append (event.text + message)
        if len (self.buffer[key]) > BUFFSIZE:
            self.buffer[key] = self.buffer[key][1:]

#=================================

    def send_message (self, user_id: int, text: str):
        self.log (f"Sending message to id{user_id}: {text}")
        self.vk.messages.send (user_id = user_id, message = text, random_id = self.get_random_id ())

#=================================

    def get_random_id (self):
        return random.getrandbits (31) * random.choice ([-1, 1])

#=================================

    def log (self, message):
        text = datetime.strftime (datetime.now (), "[%H:%M:%S]: ") + message
        print (text)

        with open (self.log_filename, 'a') as file:
            file.write (text + '\n')
            file.close ()

#=================================

bot = Bot ()
try: bot.start ()
except Exception as exc:
    bot.log (f"Uhandled exception: {exc}\n\n{traceback.format_exc ()}")

#=================================
