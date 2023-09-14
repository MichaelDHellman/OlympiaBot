This is a simple bot designed for the administration of ACM Olympics, an on-campus activity at the University of Texas at Dallas put on by our student ACM Chapter. 

To setup the bot for your own use, first create a credentials folder. In this folder you will place a google oauth 2.0 api key from a Google Cloud App with both Gmail and Sheets APIs enabled, a simple explanation as to how can be found on the Google Sheets API quickstart page. Download the credentials token from the app and place it here. Then, create a tokens.json file and load it with:

"TOKEN": Your Discord bot token

"SS_ID": Your Google spreadsheet ID

"APP_ID": Your Discord app ID

"SERVER_ID": The ID for the server you wish to operate on

"INVITE": An invite link to the server

"SEND_ADDRESS": The email address you wish to automail from

"SEND_PASS": The password for that email account
