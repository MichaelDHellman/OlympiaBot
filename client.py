from discord.ext import tasks
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText

import asyncio
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
        await self.updateRoles()
        await self.messagePresents()
        
    def mailAllParticipants(self):
        self.mailParticipants()

    def mailMissingParticipants(self):
        present = [m.name for m in self.server.members]
        missing = []
        for p in self.sheetData:
            if p[2].lower() not in present:
                missing.append(p)
        print(missing)

        self.mailParticipants(missing)
        
                
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
                self.sheetData = sheetDataTemp[1:]
            
        except HttpError as err:
            print("HTTP ERROR")
    
    async def updateRoles(self):
        sheetNames = []
        for p in self.sheetData:
            sheetNames.append(p[2])
        
        mailedTo = {}
        present = [m for m in self.server.members if m.name in sheetNames]
        print(present)

        with open("sentto.json", 'r') as sent:
            mailedTo = json.load(sent)
            for i, m in enumerate(present):
                if m.name in mailedTo["discord"]:
                    continue
                print("adding roles to " + m.name)
                if self.sheetData[i][3] == "Red":
                    print("adding red")
                    await m.add_roles(self.server.get_role(1024692661917065256))
                    await m.remove_roles(self.server.get_role(1024693348730155070), self.server.get_role(1024692666832781322), self.server.get_role(1024693270175039539))
                if self.sheetData[i][3] == "Blue":
                    print("adding Blue")
                    await m.add_roles(self.server.get_role(1024693348730155070))
                    await m.remove_roles(self.server.get_role(1024692661917065256), self.server.get_role(1024692666832781322), self.server.get_role(1024693270175039539))
                if self.sheetData[i][3] == "Yellow":
                    print("adding yellow")
                    await m.add_roles(self.server.get_role(1024692666832781322))
                    await m.remove_roles(self.server.get_role(1024692661917065256), self.server.get_role(1024693348730155070), self.server.get_role(1024693270175039539))
                if self.sheetData[i][3] == "Green":
                    print("adding green")
                    await m.add_roles(self.server.get_role(1024693270175039539))
                    await m.remove_roles(self.server.get_role(1024692661917065256), self.server.get_role(1024693348730155070), self.server.get_role(1024692666832781322))
                await m.add_roles(self.server.get_role(1088654298012987422))
                await asyncio.sleep(2)
                print("added roles")

    def mailParticipants(self):
        service = build('gmail', 'v1', credentials=self.gCreds)
        sent = open("sentto.json", 'r')
        mailedTo = json.load(sent)
        sent.close()
        for p in self.sheetData:
            if p[1] in mailedTo["email"]:
                continue
            mailedTo["email"].append(p[1])
            tmpMessage = "Hi, " + p[0] + ", we're so glad you are planning to attend ACM Olympics. Before the events begin, make sure to join the ACM official Discord server. To partcipate we need you to join using this link " + self.tokens["INVITE"] +". Please do so now, if you haven't already. \nAll information about ACM Olympics will be posted to the \"Olympics\" channel in that Discord. \n\n You have been placed on the {} Team! Introduce yourself in the channel for your team color when you get the chance \n For your reference, here's a list of all of the events you signed up for! \n\n".format(p[3])
            if p[3] != "No Preference":
                events = p[4].split(", ")
                eventsString = ""
                for e in events:
                    if ("Opening" in e):
                        eventsString = eventsString + "Opening Ceremony | 4:00 PM to 5:00 PM | Friday | TI Auditorium\n\n"
                        continue
                    if ("Typing" in e):
                        eventsString = eventsString + "Typing | 5:30 PM to 6:30 PM | Friday | TI Auditorium\n\n"
                        continue
                    if ("Trivia" in e):
                        eventsString = eventsString + "Trivia | 7:00 PM to 8:00 PM | Friday | TI Auditorium\n\n"
                        continue
                    if ("Soccer" in e):
                        eventsString = eventsString + "Soccer | 8:15 PM to 10:15 PM | Friday | Soccer Field 9\n\n"
                        continue
                    if ("Programming" in e):
                        eventsString = eventsString + "Partner Programming | 1:00 PM to 2:00 PM | Saturday | TI Auditorium\n\n"
                        continue
                    if ("Event Rush" in e):
                        eventsString = eventsString + "Event Rush | 3:00 PM to 5:00 PM | Saturday | SCI Courtyard\n\n"
                        continue
                    if ("Mystery" in e):
                        eventsString = eventsString + "Mystery Event | 5:30 PM to 6:30 PM | Saturday | TI Auditorium\n\n"
                        continue
                    if ("Table" in e):
                        eventsString = eventsString + "Table Tennis | 6:30 PM to 7:30 PM | Saturday | SU 1st Floor\n\n"
                        continue
                    if ("Smash" in e):
                        eventsString = eventsString + "Smash Bros | 7:45 PM to 9:45 PM | Saturday | TI Auditorium\n\n"
                        continue
                    if ("Chess" in e):
                        eventsString = eventsString + "Chess | 10:30 AM to 12:00 PM | Sunday | TI Auditorium\n\n"
                        continue
                    if ("Basketball" in e):
                        eventsString = eventsString + "Basketball | 1:00 PM to 3:00 PM | Sunday | Courts South of UREC\n\n"
                        continue
                    if ("Water" in e):
                        eventsString = eventsString + "WATER BALLOON FIGHT | 4:00 PM to 5:00 PM | Sunday | SCI Courtyard\n\n"
                        continue
                    if ("Closing" in e):
                        eventsString = eventsString + "Closing Ceremony | 6:00 PM to 7:00 PM | Sunday | TI Auditorium\n\n"
                        continue
                    
            tmpMessage = tmpMessage + eventsString
            tmpmessage = tmpMessage + "\n We can't wait to see you at Olympics! \n\n Sincerely, \n  The ACM Events Team"
            message = MIMEText(tmpMessage)
            message['Subject'] = "Welcome to ACM Olympics! <PLEASE READ>"
            print(p[1])
            message['To'] = p[1]
            created_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
            try:
                message = (service.users().messages().send(userId="me", body=created_message).execute())
            except HttpError as error:
                print(error)
        with open("sentto.json", 'w') as f:
            json.dump(mailedTo, f) 
    
    async def messagePresents(self):
        sheetNames = [] #MESSAGING BLOCKED
        for p in self.sheetData:
            sheetNames.append(p[2].lower())

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
                    await m.send("Hello, and welcome to ACM Olympics! You have been placed on the " + self.sheetData[i][3] + ":" + self.sheetData[i][3].lower() + "_square: team! If this is your first Olympics, thanks for joining us this year, we're going to have a great time!")
                    events = self.sheetData[i][4].split(", ")
                    eventsString = ""
                    for e in events:
                        if ("Opening" in e):
                            eventsString = eventsString + "Opening Ceremony :balloon: | 4:00 PM to 5:00 PM | Friday | ECSS 2.201\n\n"
                            continue
                        if ("Typing" in e):
                            eventsString = eventsString + "Typing :keyboard: | 5:15 PM to 6:15 PM | Friday | ECSS 2.201\n\n"
                            continue
                        if ("Soccer" in e):
                            eventsString = eventsString + "Soccer :soccer: | 6:30 PM to 8:30 PM | Friday | Soccer Field 8\n\n"
                            continue
                        if ("Push" in e):
                            eventsString = eventsString + "Push Ups :muscle: | 11:00 PM to 11:30 AM | Saturday | Multipurpose Field\n\n"
                            continue
                        if ("One Mile" in e):
                            eventsString = eventsString + "One Mile Run :athletic_shoe: | 11:30 AM to 12:00 PM | Saturday | Multipurpose Field\n\n"
                            continue
                        if ("Table" in e):
                            eventsString = eventsString + "Table Tennis :Ping_Pong: | 12:15 PM to 1:45 PM | Saturday | SU 1st Floor\n\n"
                            continue
                        if ("Mystery" in e):
                            eventsString = eventsString + "Mystery Event :question: | 2:00 PM to 3:00 PM | Saturday | ECSS 2.201\n\n"
                            continue
                        if ("Programming" in e):
                            eventsString = eventsString + "Partner Programming :computer: | 3:15 PM to 4:15 PM | Saturday | ECSS 2.201\n\n"
                            continue
                        if ("Basketball" in e):
                            eventsString = eventsString + "Basketball :basketball: | 4:30 PM to 6:30 PM | Saturday | Main Gym North Court\n\n"
                            continue
                        if ("Smash" in e):
                            eventsString = eventsString + "Smash Bros :boxing_glove: | 6:45 PM to 8:45 PM | Saturday | ECSS 2.201\n\n"
                            continue
                        if ("Volleyball" in e):
                            eventsString = eventsString + "Volleyball :volleyball: | 1:30 PM to 3:30 PM | Sunday | UTD Volleyball Courts\n\n"
                            continue
                        if ("Trivia" in e):
                            eventsString = eventsString + "Trivia :brain: | 3:45 PM to 4:45 PM | Sunday | ECSS 2.201\n\n"
                            continue
                        if ("Closing" in e):
                            eventsString = eventsString + "Closing Ceremony :pizza: | 5:30 PM to 6:30 PM | Sunday | ECSS 2.201\n\n"
                            continue
                    await m.send("As a quick reminder for your own reference, you signed up for the following events: \n\n" + eventsString)
                    await m.send("We're sure you can't wait for the games to begin, so to tide yourself over, go and visit the #Olympics channel in the Discord, as well as your team channel, and get to know your fellow competitors! If you have any questions, message @Glassshatter on Discord. See you soon!")
                    await asyncio.sleep(2)
        with open("sentto.json", 'w') as f:
            json.dump(mailedTo, f)
            f.close()

    """
    def mailAbsentees(self, absenteeList):
        service = build('gmail', 'v1', credentials=self.gCreds)
        sent = open("sentto.json", 'r')
        mailedTo = json.load(sent)
        sent.close()
        for a in absenteeList:
            if a[1] in mailedTo["email"]:
                continue
            mailedTo["email"].append(a[1])
            message = MIMEText("Hi, " + a[0] + ", we're so glad you are planning to attend ACM Olympics. Before the events begin, make sure to join the ACM official Discord server. To partcipate we need you to join using this link " + self.tokens["INVITE"] +". Please do so now, if you haven't already. \nAll information about ACM Olympics will be posted to the \"Olympics\" channel in that Discord. \n\n You have been placed on the {} Team! Introduce yourself in the channel for your team color when you get the chance \n We can't wait to see you at Olympics! \n\n Sincerely, \n  The ACM Events Team")
            message['Subject'] = "Welcome to ACM Olympics! <PLEASE READ>"
            print(a[1])
            message['To'] = a[1]
            created_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
            try:
                message = (service.users().messages().send(userId="me", body=created_message).execute())
            except HttpError as error:
                print(error)
        with open("sentto.json", 'w') as f:
            json.dump(mailedTo, f)"""