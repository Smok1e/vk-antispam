import requests, json
from getpass import getpass

#=================================

APP_SECRET_KEY  = "hHbZxrka2uZ6jB1inYsH"
APP_ID          = "2274003"

#=================================

class NeedValidationCode (RuntimeError):
    pass

class InvalidClient (RuntimeError):
    description: str

    def __init__ (self, message: str, description: str):
        super ().__init__ (message)
        self.description = description

    def __str__ (self):
        return f"{super ().__str__ ()}: {self.description}"

#=========================================

def authorize (login: str, password: str, code = None) -> str:
    scope = 'notify,friends,photos,audio,video,stories,pages,status,notes,messages,wall,ads,offline,docs,groups,notifications,stats,email,market'

    params = {
        'grant_type':    'password',
        'client_id':     APP_ID,
        'client_secret': APP_SECRET_KEY,
        'username':      login,
        'password':      password,
        '2fa_supported': 1,
        'v':             5.131,
        'scope':         scope
    }

    if code: params['code'] = code
    
    response = requests.post ("https://oauth.vk.com/token", timeout = 5, params = params)
    if response.status_code != requests.codes.ok:
        error = json.loads (response.text)
        if error['error'] == 'need_validation':
            raise NeedValidationCode ("Need validation code")

        elif error['error'] == 'invalid_client':
            raise InvalidClient ("Invalid client", error['error_description'])

        return None

    data = json.loads (response.text)
    return data['access_token']

#=========================================

def login ():
    print ("Login: ", end = '')
    login = input ()

    password = getpass ()

    try:
        try: access_token = authorize (login, password)
        except NeedValidationCode:
            print ("Validation code: ", end = '')
            code = input ()

            access_token = authorize (login, password, code)

        return access_token

    except InvalidClient as exc:
        print (f"Invalid client: {exc.description}")
        return None

#=========================================
