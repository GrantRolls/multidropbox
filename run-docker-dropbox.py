#!/usr/bin/env python3

import signal
import sys
import os
import subprocess
import gi
import threading
import argparse

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk as gtk
#Deps gir1.2-appindicator3-0.1
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify

APPINDICATOR_ID = ''
indicator = None

instance_name = ''
image_tag = 'dropbox'

file_path = os.path.dirname(os.path.abspath(__file__))
unknown_emblem = file_path + '/images/emblems/emblem-dropbox-selsync.png'
idle_emblem = file_path + '/images/emblems/dropbox-icon.png'  
syncing_emblem = file_path + '/images/emblems/emblem-dropbox-syncing.png'

thread_handle = None

def setup_arg_parser():
    parser = argparse.ArgumentParser(description='Run dropbox in a docker container. \
        Interrogates container and displays status as app indicator')
    parser.add_argument('instance-name',
                        help='an integer for the accumulator')

    group = parser.add_argument_group('Create a new instance')                    
    group.add_argument('--create-instance', 
                        action='store_true',
                        help='Create the docker instance (if not created)')
    group.add_argument('--mount-path',
                        default='~/dropbox',
                        help='Path of the folder to use for this dropbox instance')

    parser.add_argument('--image-tag', 
                        default='dropbox',
                        help='Tag of the docker image to run')

    return parser

def build_menu(title):
    menu = gtk.Menu()

    item_title = gtk.MenuItem(title)
    menu.append(item_title)

    item_quit = gtk.MenuItem('Quit')
    item_quit.connect('activate', quit)
    menu.append(item_quit)
    
    item_status = gtk.MenuItem('Status')
    item_status.connect('activate', status)
    menu.append(item_status)

    menu.show_all()
    return menu

def status(_):
    global instance_name
    global image_tag
    notify.Notification.new('Dropbox sync status', \
            get_dropbox_status(instance_name, image_tag), None).show()

def quit(source):
    stop_dropbox_docker(instance_name)
    notify.uninit()
    gtk.main_quit()


def create_dropbox_instance(instance_name, mount_path, image_tag):
    ret = 0

    try:
        ret = subprocess.check_call( \
                ['docker', \
                'run', \
                '-d', \
                '--name={0}'.format(instance_name), \
                '-v {0}:/dbox/Dropbox'.format(mount_path), \
                '{0}'.format(image_tag)])
    except subprocess.CalledProcessError as e:
        print(e.output)
    except FileNotFoundError:
        exit('Docker may not be installed')
    return ret


def start_dropbox_docker(instance_name):
    ret = 0
    try:
        ret = subprocess.check_call( \
                ['docker', 'start', '{0}'.format(instance_name)])
    except subprocess.CalledProcessError as e:
        print(e.output)
    except FileNotFoundError:
        exit('Docker may not be installed')
    return ret


def stop_dropbox_docker(instance_name):
    try:
        subprocess.check_call( \
                ['docker', 'stop', '{0}'.format(instance_name)])
    except subprocess.CalledProcessError as e:
        print(e.output)
    except FileNotFoundError:
        exit('Docker may not be installed')

            
def get_dropbox_status(instance_name, image_tag):
    ret = ""
    try:
        ret = subprocess.check_output( \
                ['docker', \
                'exec', \
                '-ti', \
                '{0}'.format(instance_name), \
                '{0}'.format(image_tag), \
                'status']) \
                .decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(e.output)
    except FileNotFoundError:
        exit('Docker may not be installed')
    return ret

def timed_status_check(instance_name, image_tag):
    global indicator
    global thread_handle
    
    status_string = get_dropbox_status(instance_name, image_tag)
    print(status_string)

    next_check = 5.0
    if('Up to date' in status_string):
        set_icon(indicator, idle_emblem)
        next_check = 30
    elif('Syncing' in status_string):
        set_icon(indicator, syncing_emblem)
    else:
        set_icon(indicator, unknown_emblem)
    
    thread_handle = threading.Timer(next_check, timed_status_check, [instance_name, image_tag])
    thread_handle.daemon = True
    thread_handle.start()

def set_icon(indicator, iconPath=idle_emblem):
    indicator.set_icon(os.path.abspath(iconPath))

def main():
    global instance_name
    global APPINDICATOR_ID
    global indicator
    global thread_handle

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = setup_arg_parser()
    args = vars(parser.parse_args())

    instance_name = args['instance-name']
    APPINDICATOR_ID = instance_name + '-appind'
    print('Dropbox instance {0}'.format(instance_name))

    create_instance = args['create_instance']
    mount_path = args['mount_path']

    image_tag = args['image_tag']

    indicator = appindicator.Indicator.new( \
            APPINDICATOR_ID, \
            os.path.abspath(syncing_emblem), \
            appindicator.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_title('Dropbox in docker container {0}'.format(instance_name))
    indicator.set_menu(build_menu(instance_name))

    notify.init(APPINDICATOR_ID)

    if create_instance:
        create_dropbox_instance(instance_name, mount_path, image_tag)
    else:
        start_dropbox_docker(instance_name)

    timed_status_check(instance_name, image_tag)
 
    gtk.main()
    thread_handle.cancel()
    print('Dropbox instance {0} closed'.format(instance_name))

if __name__ == "__main__":
    main()
