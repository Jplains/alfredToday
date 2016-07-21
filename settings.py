import sys
import argparse
from workflow import Workflow, ICON_WEB, ICON_WARNING, ICON_NOTE, web, PasswordNotFound, Workflow3

DEFAULT_SERVER = 'https://outlook.office365.com/EWS/Exchange.asmx'
CREDENTIAL_ENTRY = 'outlook.office365.com'


def guess_domain():

    from subprocess import Popen, PIPE
    p = Popen(['grep', '^search', '/private/etc/resolv.conf'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    raw_result, err = p.communicate(b"input data that is passed to subprocess' stdin")
    domain = raw_result.strip('\n').split(' ')[1]
    return domain

def guess_username():
    import os
    import pwd
    return pwd.getpwuid(os.getuid()).pw_name

def get_server(wf):
    server = get_value_from_settings(wf, 'exchange_server')
    if server is None:
        return DEFAULT_SERVER, True
    else:
        return server, False

def get_timezone(wf):
    """Returns the timezone as stored on disk - defaults to US/Eastern """
    stored_timezone = get_value_from_settings(wf, 'timezone')
    if stored_timezone is None:
        return "US/Eastern", True
    else:
        return stored_timezone, False


def get_regex(wf):
    return get_value_from_settings(wf, 'regex')

def get_stored_login(wf):
    return get_value_from_settings(wf, 'exchange_login')

def get_stored_password(wf):
    try:
        password = wf.get_password('today.workflow.password')
        return password
    except:
        return None


def get_value_from_settings(wf, value):
    try:
        ret = wf.settings[value]['value']
        return ret
    except KeyError:
       return None

def get_value_from_settings_with_default_int(wf, value, default_value):
    """Returns either a value as set in the settings file or a default as specified by caller"""
    try:
        ret = wf.settings[value]['value']
        return int(ret)
    except KeyError:
        return default_value


def get_value_from_settings_with_default_boolean(wf, value, default_value):
    """Returns either a value as set in the settings file or a default as specified by caller"""
    try:
        ret = wf.settings[value]['value']
        if ret == u'0':
            return False
        return True
    except KeyError:
        return default_value

def autodetect_password(wf):
    from subprocess import Popen, PIPE
    import re
    # Fire off security to open up the site credentials

    p = Popen(['security', 'find-internet-password', '-w', '-g', '-s', CREDENTIAL_ENTRY], stdin=PIPE, stdout=PIPE,stderr=PIPE)
    raw_password, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode
    password = raw_password.strip('\n')
    if password == "":
        return None
    return password


def autodetect_login(wf):
    from subprocess import Popen, PIPE
    import re

    p = Popen(['security', 'find-internet-password', '-s', CREDENTIAL_ENTRY], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    keychain_result, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode

    # Run REGEX Match
    p = re.compile('acct\"<blob>="([^"]*)')
    m = re.search(p, keychain_result)
    if m:
        return m.group(1)
    return None



def get_login(wf, show_alfred_items=True):
    stored_login = get_stored_login(wf)
    auto_login= autodetect_login(wf)
    if stored_login is None:

        if auto_login is None:
            if show_alfred_items:
                login_item = wf.add_item('Please set Login', 'Could not auto detect a login from keychain for ' + CREDENTIAL_ENTRY,
                        valid=True, icon=ICON_WARNING)
            ret = None
        else:
            if show_alfred_items:
                login_item = wf.add_item('Exchange Login', "(autodetcted) " + auto_login, arg=auto_login, valid=True, icon='ok.png')
            ret = auto_login

    else:
        if show_alfred_items:
            login_item = wf.add_item('Exchange Login', stored_login, arg=stored_login, valid=True, icon='ok.png')
        ret = stored_login

    if show_alfred_items:
        login_item.setvar('text_to_display', 'Exchange Login:')
        login_item.setvar('settings_value' , 'exchange_login')

    return


def get_password(wf, show_alfred_items=True):
    stored_password = get_stored_password(wf)
    auto_password   = autodetect_password(wf)

    if stored_password is None:

        if auto_password is None:
            if show_alfred_items:
                password_item = wf.add_item('Please set Exchange Password', 'Could not auto detect password from keychain for ' + CREDENTIAL_ENTRY, valid=True, icon=ICON_WARNING)
            ret = None
        else:
            if show_alfred_items:
                password_item = wf.add_item('Exchange Password stored in keychain', '(auto detected from keychain)', valid=True, icon='ok.png')
            ret = auto_password

    else:
        if show_alfred_items:
            password_item = wf.add_item('Exchange Password stored in keychain', 'xxxxxxxxxx', valid=True, icon='ok.png')
        ret = stored_password

    if show_alfred_items:
        password_item.setvar('text_to_display','Exchange Password')
        password_item.setvar('settings_value' ,'password')
    return ret



def main(wf):

    from workflow import Workflow3
    wf = Workflow3()

    #######################
    ## Load Credentials  ##
    #######################
    from subprocess import Popen, PIPE
    import re

    # Default items for workflow

    wf.add_item('Today workflow configuration Menu', icon='gear.png')
    use_google   = get_value_from_settings_with_default_boolean(wf, 'use_google', True)
    if not use_google:
        google_toggle = wf.add_item('Google calendar disabled', 'Toggle this to enable support', valid=True, arg="refresh", icon="googleNo.png")
        google_toggle.setvar('value_to_store', True)
    else:
        google_toggle = wf.add_item('Google calendar disabled', 'Toggle this to enable support', valid=True, arg="refresh", icon="googleYes.png")
        google_toggle.setvar('value_to_store', False)

    google_toggle.setvar('settings_value', 'use_google')
    google_toggle.setvar('text_to_display', 'Google Calendar')

    use_exchange = get_value_from_settings_with_default_boolean(wf, 'use_exchange', True)
    if not use_exchange:
        exchange_toggle = wf.add_item('Exchange support disabled', 'Toggle this to enable exchange support', valid=True, arg="refresh", icon='outlookNo.png')
        exchange_toggle.setvar('settings_value', 'use_exchange')
        exchange_toggle.setvar('value_to_store', True)
        exchange_toggle.setvar('text_to_display', 'Use Exchange Server')
    else:

        exchange_toggle = wf.add_item('Exchange support enabled', 'Toggle this to disable exchange support', valid=True, arg="refresh", icon="outlookYes.png")

        exchange_toggle.setvar('settings_value', 'use_exchange')
        exchange_toggle.setvar('value_to_store', False)
        exchange_toggle.setvar('text_to_display', 'Use Exchange Server')

        get_login(wf)
        get_password(wf)
        tz = get_timezone(wf)

        #################
        ## Load Server ##
        #################

        server, using_default = get_server(wf)
        if not using_default:
            server_item = wf.add_item('Exchange Server URL', server, arg=server, copytext=server, valid=True, icon='ok.png')
            server_item.setvar('text_to_display', 'Exchange Server:')
            server_item.setvar('settings_value', 'exchange_server')
        else:
            server_item = wf.add_item('Exchange Server URL (Using Default)', DEFAULT_SERVER, copytext=server, arg=DEFAULT_SERVER, valid=True, icon=ICON_NOTE)
            server_item.setvar('text_to_display', 'Exchange Server:')
            server_item.setvar('settings_value', 'exchange_server')

        ########################
        ## Load Regex Settings #
        ########################
        regex = get_regex(wf)

        if regex is not None:
            regex = get_regex(wf)
            it = wf.add_item('Exchange Detection Regex', regex, arg=regex, copytext=regex, valid=True, icon='ok.png')
            it.setvar('text_to_display', 'Regex:')
        else:
            it = wf.add_item('Meeting Detection Regex Not Set', 'Select this item to set', valid=True,
                        icon=ICON_WARNING)
            it.setvar('text_to_display','Regex:')
            it.setvar('settings_value', 'regex')


    cache_time = get_value_from_settings_with_default_int(wf, 'cache_time', 30)

    cache_item = wf.add_item('Cache Time: ' + str(cache_time) + " seconds",'This is the time between refreshing the calendar data cache',arg=cache_time, icon='hourglass.png', valid=True)
    cache_item.setvar('text_to_display', 'Cache time in seconds')
    cache_item.setvar('settings_value', 'cache_time')

    # Timezone supressed for now - may not be required
    # timezone_string, using_default_timezone = get_timezone(wf)
    # timezone_subtitle = timezone_string
    # if using_default_timezone:
    #     timezone_subtitle += " [DEFAULT]"
    #
    # tz_item = wf.add_item("Using Timezone", timezone_subtitle, valid=True, arg=timezone_string, icon="timezone.png")
    # tz_item.setvar('text_to_display', 'Time Zone:')
    # tz_item.setvar('settings_value', 'timezone')

    wf.send_feedback()


if __name__ == u"__main__":
    wf = Workflow3(libraries=['./lib'])
    sys.exit(wf.run(main))
