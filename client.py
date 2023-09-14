from discord.ext import tasks
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText

import base64
import discord
import os
import logging
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly',"https://www.googleapis.com/auth/gmail.send"]
SHEET_RANGE = "Master!B:F"

class olympiaClient(discord.Client):
    tokens = {}
    sheetData = []
    server = None
    gCreds = None

    def __init__(self, fpath):
        with open(fpath, 'r') as file:
            self.tokens = json.load(file)
            oIntents = discord.Intents.default()
            oIntents.members = True
            super().__init__(intents=oIntents)
    
    async def on_ready(self):
        print(f"Logged in as {self.user}")
        logging.debug(f"Logged in as {self.user}")
        self.server = self.get_guild(int(self.tokens["SERVER_ID"]))
        self.gCreds = self.googleAuth()
        if not (os.path.exists("sentto.json")):
            test = {"email":[], "discord":[]}
            f = open("sentto.json", 'w')
            json.dump(test, f)
            f.close()
        self.roleUpdateLoop.start()

    
    @tasks.loop(seconds=300)
    async def roleUpdateLoop(self):
        await self.server.chunk()
        self.fetchSheetData()
        self.mailMissingParticipants()
        await self.messagePresents()
        

    def mailMissingParticipants(self):
        present = [m.name for m in self.server.members]
        missing = []
        for p in self.sheetData:
            if p[2].lower() not in present:
                missing.append(p)
        self.mailAbsentees([["Michael Hellman", "michaelhellmaniii@gmail.com", "glassshatter", "Blue"]])
        
                
    def googleAuth(self):
        credentials = None
        #if os.path.exists('gToken.json'):
        #    credentials = Credentials.from_authorized_user_file('gToken.json', SCOPES)
        #if not credentials or not credentials.valid:
            #if credentials and credentials.expired and credentials.refresh_token:
            #    credentials.refresh(Request())
            
            #else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials\credentials.json', SCOPES)
        credentials = flow.run_local_server(port=0)
            
            #with open('gToken.json', 'w') as token:
            #    token.write(credentials.to_json())    

        return credentials        

    def fetchSheetData(self):
        try:
            sheetServe = build('sheets', 'v4', credentials=self.gCreds)

            #Pull our user data from the Sheets API
            sheet = sheetServe.spreadsheets()
            result = sheet.values().get(spreadsheetId=self.tokens["SS_ID"],
                                        range=SHEET_RANGE).execute()
            
            sheetDataTemp = result.get('values', [])

            #Don't replace our good info with None if it fails
            if not sheetDataTemp:
                print("Failed to retrieve values from spreadsheet")
                return
            else:
                self.sheetData = sheetDataTemp[2:]
            
        except HttpError as err:
            print("HTTP ERROR")
    
    def mailAbsentees(self, absenteeList):
        service = build('gmail', 'v1', credentials=self.gCreds)
        sent = open("sentto.json", 'r')
        mailedTo = json.load(sent)
        sent.close()
        for a in absenteeList:
            if a[1] in mailedTo["email"]:
                continue
            mailedTo["email"].append(a[1])
            message = MIMEText("Hi, " + a[0] + ", we're so glad you are planning to attend ACM Olympics. Before the events begin, we noticed you hadn't joined the ACM Discord server. To partcipate we need you to join using this link " + self.tokens["INVITE"] +". Please do so now. We can't wait to see you at Olympics! \n\n Sincerely, \n  The ACM Events Team")
            message['Subject'] = "Welcome to ACM Olympics! <ACTION REQUIRED>"
            print(a[1])
            message['To'] = a[1]
            created_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
            try:
                message = (service.users().messages().send(userId="me", body=created_message).execute())
            except HttpError as error:
                print(error)
        with open("sentto.json", 'w') as f:
            json.dump(mailedTo, f)

    
    async def messagePresents(self):
        sheetNames = ["glassshatter"]
        #for p in self.sheetData:
        #    sheetNames.append(p[2])

        print(self.sheetData)

        mailedTo = {}
        present = [m for m in self.server.members if m.name in sheetNames]
        print(present)
        with open("sentto.json", 'r') as sent:
            mailedTo = json.load(sent)
            for i, m in enumerate(present):
                if m.name in mailedTo["discord"]:
                    continue
                mailedTo["discord"].append(m.name)
                if self.sheetData[i][3] != "No Preference":
                    await m.send("Hello, and welcome to ACM Olympics! You have been placed on the " + self.sheetData[i][3] + " team! If this is your first Olympics, thanks for joining us this year, we're going to have a great time!")
                    events = self.sheetData[i][4]
                    await m.send("As a quick reminder for your own reference, you signed up for the following events: ")
        with open("sentto.json", 'w') as f:
            json.dump(mailedTo, f)
            f.close()


            
