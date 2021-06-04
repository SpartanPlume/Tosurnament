# Tosurnament
Discord bot to help in Discord/spreadsheet relationships

## How to use Tosurnament in your tournament ?

You can check out [the tutorial](https://github.com/SpartanPlume/Tosurnament/wiki/Tutorial) to know how to setup the Tosurnament Bot in your Discord server.

You can also check [the commands](https://github.com/SpartanPlume/Tosurnament/wiki/Tosurnament-commands) directly if you are an experienced user.

## How to add a new language / more traductions to Tosurnament ?

First, you need to clone the repository. Then, in the folder `backend/bot/replies`, you will see multiple subfolders with `en.json` file in them. You need to copy this file in the same folder, rename it to the language code in the language you want to translate (`fr.json` for French for example). Now you only need to translate every entries, **but beware** of:
- entries containing `$`, you must not modify the path name to another language (example: `$./no_staff_notification Some other text`, `$./no_staff_notification` must not be changed, but what is after should be changed)
- entries containing `%`, you must not modify the number following them
After you're done translating, just open a Pull Request in this repo and I will check it.

## How to host your own Tosurnament bot ?

Prerequisite:

- Linux on where you want to host the bot (server or on your personal computer)
- mysql/mariadb installed
- python3.8 or later installed
- Clone the repo =)

### Creating the bot (if not already done)

1. Go to the [discord developer portal](https://discord.com/developers/applications)
2. Click the `New Application` button and fill the form

### Get the bot token

1. After selecting the newly created application, click the `Bot` tab in the left
2. Click the `Copy` button below `TOKEN`
3. Paste the copied token in the `BOT_TOKEN` field of the `constants.json` file present in the repository

### Get your osu api

1. This can be a little annoying to get, but you need to go to https://osu.ppy.sh/p/api/, login, then close the tab, copy paste the url in the adress bar, and do Shift+ENTER, it should lead you to the correct page and here you can generate/get your osu api key.
2. Paste the copied api key in the `OSU_API_KEY` field of the `constants.json` file present in the repository

### Get your discord ID

1. Activate developer mode in discord if not already done: `Settings -> Appearance -> Advanced -> Developer Mode`
2. Right-click on your name in any channel and click `Copy ID`
3. Paste the copied id in the `BOT_OWNER_ID` field of the `constants.json` file present in the repository

### Set the bot prefix

You can set the bot prefix to anything you want by changing the `COMMAND_PREFIX` field in `constants.json`.

### Set the database username and password

Change the `DB_USERNAME` and `DB_PASSWORD` to anything you want in `constants.json`. You don't need to create the user, it will be created automatically by the `setup.sh` script.

### Set the challonge username and api key

1. Go to https://challonge.com/settings/developer and copy your API key.
2. Paste the copied id in the `CHALLONGE_API_KEY` field in `constants.json`.
3. Put your challonge username in the `CHALLONGE_USERNAME` field in `constants.json`.

### Use the setup.sh script

Go to the root of the repository and do `./setup.sh`. It will install all the required python dependencies and setup the database.

### Get an encryption key

To get an encryption key you need to:
1. Open a python shell (`python3`)
2. `from cryptography.fernet import Fernet`
3. `Fernet.generate_key()`
4. Copy the generated key and paste it in the `ENCRYPTION_KEY` field in `constants.json`.

## Start the bot

You have 2 options to start the bot: create a service or use the script.  
Still, the better option is the service, as it will restart even if the script gets killed.

### Option 1: Script

Just use the `tosurnament.sh` script at the root of the repository.

### Option 2: Service

1. Create a new service file. For example: `/etc/systemd/system/tosurnament.service`.
2. Fill the file with:
```
[Unit]
Description=Tosurnament bot service
After=mysqld.service
StartLimitIntervalSec=0

[Service]
Restart=always
RestartSec=1
ExecStart=/path/to/tosurnament.sh

[Install]
WantedBy=multi-user.target
```
3. Modify `ExecStart` with the path to the `tosurnament.sh` script.
4. Start the service with `sudo systemctl start tosurnament`, where `tosurnament` is the name of your service file (without the `.service` extension).