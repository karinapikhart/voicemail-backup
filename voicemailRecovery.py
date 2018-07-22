# @karinapikhart

# version history
# 2018-07-21 V0.1

# Background:
# I was inspired to make this script when I was cleaning up my voicemails
# and came across one from my godfather, who had recently passed away.
# Hearing his voice was so precious, especially knowing I would never hear it in real
# life again, so I decided to try to figure out how to scrape voice mails from iPhone backups.

# Credits/Sources:
# http://www.instructables.com/id/How-to-Download-Voicemail-from-an-iPhone/

# Compatible with:
# iPhone, Mac (versions??)

# Instructions:
# 1. Plug your phone into your computer, and back up to your computer (not to iCloud) using iTunes.
# 2.

# Lessons learned:
# 1. Make the tracer bullet first! One pass all the way through, as fast as possible. Super helpful to validate the overall plan
# 2. Mentioned this little project to my aunt, and she said "you can already do that!".
#    Oh shoot, it's true... you can save voicemails to Dropbox in the iPhone UI. Was that always there?
#    Was this project a waste? Maybe I need to modify the project to just add helpful metadata to saved m4a voicemail files!!


# NOTES AND TODOS:
# how to remove dup voicemails found in two different backups
# any metadata to make more sense of the voicemail? - eg phone number, date received etc
# can we convert to better file type?

##########
# IMPORT #
##########

import os
import sys
import time
import subprocess
import pprint
import shutil

###########
# GLOBALS #
###########

DEFAULT_IPHONE_MAC_BACKUP_DIR = '~/Library/Application Support/MobileSync/Backup'
DEFAULT_IPHONE_MAC_BACKUP_DIR = os.path.expanduser(DEFAULT_IPHONE_MAC_BACKUP_DIR)

SCRIPT_START_TIME = time.time()
RECOMMENDED_MAX_BACKUP_AGE_DAYS = 2

VOICEMAIL_FILE_TYPE_SUBSTRING = 'GSM telephony'
VOICEMAIL_FILE_EXTENSION = '.amr'

DEFAULT_VOICEMAIL_DESTINATION_DIRECTORY = '/tmp'

# ALLOWED_INPUT_CHARS = 'abc123' # just letters and numbers... avoid evil string injection

#############
# FUNCTIONS #
#############

# returns the correct location for iPhone backups
# does X if no location found
# also, need to give the user an opportunity to provide a directory
def validate_backups_directory():

    # check if the default backup location exists
    # if not, give the user a choice to provide the correct directory, or coach them to perform a backup
    # (which may create the dir)
    if os.path.exists(DEFAULT_IPHONE_MAC_BACKUP_DIR):
        print 'confirmed that default directory for iTunes backup exists: ' + DEFAULT_IPHONE_MAC_BACKUP_DIR
        backup_dir = DEFAULT_IPHONE_MAC_BACKUP_DIR
    else:
        # TBD
        backup_dir = None # ??? should i do this?
        sys.exit()

    return backup_dir

# allows the user to select the backup to scrape voicemails from,
# suggesting the most recent backup by default
def select_backup(backup_dir):
    backup_folders = os.listdir(backup_dir)
    backup_folders_by_time_modified = {}

    print 'found ' + str(len(backup_folders)) + ' backups'

    # create a dictionary of backups, stored by time modified
    for folder in backup_folders:
        last_modified_time = os.path.getmtime(backup_dir + '/' + folder)

        # add folder to dictionary
        if last_modified_time in backup_folders_by_time_modified.keys():
            backup_folders_by_time_modified[last_modified_time].append(folder)
        else:
            backup_folders_by_time_modified[last_modified_time] = [folder]

        print folder, last_modified_time, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified_time))

    print backup_folders_by_time_modified

    # give the user some information about the backups that were found
    print 'the following iPhone backups were found:'
    for last_modified_time in sorted(backup_folders_by_time_modified.keys()):
        print '  backup date:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified_time))
        print '    ', backup_folders_by_time_modified[last_modified_time]

    # recommend a backup to use for voicemail scraping
    most_recent_backup_time = max(backup_folders_by_time_modified.keys())
    num_recent_backups = len(backup_folders_by_time_modified[most_recent_backup_time])
    most_recent_backup_age_days = (SCRIPT_START_TIME - most_recent_backup_time)/3600.0/24.0

    print 'the most recent backup was', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(most_recent_backup_time))
    print num_recent_backups, 'backups were found on this day'
    if most_recent_backup_age_days <= RECOMMENDED_MAX_BACKUP_AGE_DAYS:
        if num_recent_backups == 1:
            print 'we recommend doing voicemail scraping on folder:', backup_folders_by_time_modified[most_recent_backup_time]
        else:
            print 'we recommend doing voicemail scraping on one of these folders:', backup_folders_by_time_modified[most_recent_backup_time]
    else:
        print 'no backup has been done in the last', RECOMMENDED_MAX_BACKUP_AGE_DAYS, 'days. we recommend you do a fresh backup and then come back to scrape voicemails'

    selected_backup_folder = raw_input('which backup folder would you like to scrape for voicemails? enter the folder name to continue, or press enter to exit')
    if selected_backup_folder not in backup_folders:
        if selected_backup_folder != '':
            print 'folder not found:', selected_backup_folder
        sys.exit()

    return selected_backup_folder

def select_voicemail_destination():
    valid_destination = False
    while not valid_destination:
        voicemail_destination_directory = raw_input('Provide full path to the folder where you would like the voicemails to be saved. '
                                                    + 'Or press enter to use ' + DEFAULT_VOICEMAIL_DESTINATION_DIRECTORY
                                                    + '. However, note that this directory\'s contents are erased'
                                                    + ' whenever the computer is shut down')

        if voicemail_destination_directory == '':
            voicemail_destination_directory = DEFAULT_VOICEMAIL_DESTINATION_DIRECTORY

        valid_destination = os.path.exists(voicemail_destination_directory)

    return voicemail_destination_directory

def exit_script_with_message(message):
    print message
    sys.exit(0)

# loop through everything in source_directory
# if it matches some criteria, cp it to destination_directory
# DO NOT MODIFY ANYTHING IN SOURCE DIRECTORY EVER!!!
def fetch_voicemails_from_backup(source_directory, destination_directory):
    # os.walk loops through ALL layers of directories, no matter how many layers nested
    # at each layer, it returns a list of the directories and files found there
    # we just care about the files
    i = 0
    file_types_full = {}
    file_types_abridged = {}
    for dirpath, dirnames, filenames in os.walk(source_directory): # returns 1 tuple for each directory (down all layers)
        # look at the files found in that directory
        for filename in filenames:
            i += 1

            # efficiency timer
            if i % 100 == 0: # seems to do appx 100 files / second. 50k files = 500 seconds = 10 minutes.
                print i

            # for testing
            if i > 100000:
                break

            # this is the slow line of code. so the above 'break' avoids this for fast running
            file_type = subprocess.check_output('file -b "' + dirpath + '/' + filename + '"', shell=True)

            if VOICEMAIL_FILE_TYPE_SUBSTRING in file_type:
                shutil.copy(dirpath + '/' + filename, destination_directory)

            # count how many of each file type there are
            # notice that we have 66 GSM, CoreAudio, and GIF -- wonder if they are related to each other?? to investigate later
            if file_type in file_types_full.keys():
                file_types_full[file_type] += 1
            else:
                file_types_full[file_type] = 1

            if file_type.split(',')[0] in file_types_abridged.keys():
                file_types_abridged[file_type.split(',')[0]] += 1
            else:
                file_types_abridged[file_type.split(',')[0]] = 1

    print i
    #print pprint.pprint(file_types_full)
    print pprint.pprint(file_types_abridged)

    return

def change_voicemail_file_extension(voicemail_directory):
    file_names = os.listdir(voicemail_directory)
    for file_name in file_names:
        os.rename(voicemail_directory + '/' + file_name, voicemail_directory + '/' + file_name + VOICEMAIL_FILE_EXTENSION)

    return

########
# MAIN #
########

if __name__ == "__main__":

    ##############################
    # 0. Get up and running
    ##############################

    print 'hello world!'

    ##############################
    # 1. Look for recent iPhone backups (confirm)
    ##############################

    backup_directory = validate_backups_directory()
    backup_folder = select_backup(backup_directory)
    #print backup_directory, backup_folder

    ##############################
    # 2. Figure out voicemail backup destination.
    ##############################

    voicemail_directory = select_voicemail_destination()
    new_folder_name = 'iPhoneBackupFolder-' + backup_folder \
                      + '-ScriptRunTime-' + time.strftime('%Y-%m-%d-%H%M%S', time.localtime(SCRIPT_START_TIME))
    voicemail_destination = voicemail_directory + '/' + new_folder_name
    if not os.path.exists(voicemail_destination):
        print 'making new directory', voicemail_destination
        os.mkdir(voicemail_destination)
    else:
        exit_script_with_message('exiting script. unable to make new directory ' + voicemail_destination)

    ##############################
    # 3. Extract/Backup voicemails
    ##############################

    # make sure you have enough space on the computer to do this!
    # BE CAREFUL TO NOT INJUR THE BACKUP!!!!
    fetch_voicemails_from_backup(backup_directory + '/' + backup_folder, voicemail_destination)

    ##############################
    # 4. Tidy up voicemails (make them somehow user-friendly!)
    ##############################

    change_voicemail_file_extension(voicemail_destination)

    ##############################
    # 5. Prove you made it to the end!
    ##############################

    print 'goodbye world!'