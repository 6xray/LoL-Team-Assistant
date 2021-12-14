# The MIT License (MIT)

# Copyright (c) 2021 Quentin Mouillade

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import json
import discord
import traceback
import configparser
import logging.config

from os.path                        import abspath
from discord.ext                    import commands
from googleapiclient.discovery      import build
from google.oauth2.credentials      import Credentials
from google_auth_oauthlib.flow      import InstalledAppFlow
from google.auth.transport.requests import Request

class Bot(commands.Bot):

    def __init__(self):
        """"Bot initialization and startup"""

        self.settings_file = abspath('./settings.ini')

        # Setting pu logging
        logging.config.fileConfig(self.settings_file)
        self.logger = logging.getLogger('lol_team_assistant')

        # Parsing settings
        self.logger.info(f'Loading settings located at {self.settings_file}')
        self.settings = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
        self.settings.read(self.settings_file, encoding='utf-8')

        super().__init__(command_prefix = self.settings.get('common', 'prefix'), intents = discord.Intents.all())

        self._creds = self.load_credentials()

        self.sheet_service = build('sheets', 'v4', credentials=self._creds)

        self.loop.create_task(self.load_extensions())

        token = configparser.ConfigParser()
        token.read(abspath('./token.ini'), encoding='utf-8')
        self.run(token.get('DEFAULT', 'token'))

    async def load_extensions(self):
        """"Load all existing cogs"""

        try:
            await self.wait_for('ready', timeout=30)
            self.logger.info('Loading cogs...')
        except Exception as e:
            self.logger.error("Couldn't wait for on_ready event, cogs might not work as intended")

        for filename in os.listdir('./lol_team_assistant/cogs'):
            if (filename.endswith('.py') and filename.find('__init__') == -1):
                formated_filename = filename[:-3]
                
                try:
                    self.load_extension(f'lol_team_assistant.cogs.{formated_filename}')
                    self.logger.info(f'Loaded cog lol_team_assistant.cogs.{formated_filename}')
                except Exception as e:
                    self.logger.error(f"Failed to load cog named lol_team_assistant.cogs.{formated_filename}")
                    await self.on_error()

    def load_credentials(self):
        """" Loads Google credentials and writes them in a file for future loadings """

        creds = None
        google_token_file_name = self.settings.get('google_api', 'token')

        if os.path.exists(google_token_file_name):
            creds = Credentials.from_authorized_user_file(google_token_file_name)

        if (not creds or not creds.valid):
            if (creds and creds.expired and creds.refresh_token):
                creds.refresh(Request())
            else:
                scopes = json.loads(self.settings.get('google_api', 'scopes'))
                google_credentials_file_name = self.settings.get('google_api', 'credentials')

                flow = InstalledAppFlow.from_client_secrets_file(google_credentials_file_name, scopes)

                creds = flow.run_local_server(port=0)
            with open(google_token_file_name, 'w') as token:
                token.write(creds.to_json())

        return creds

    async def on_ready(self):
        """Called when the bot is connected to discord and ready to operate"""

        self.logger.info(f"Logged in as {self.user.name}#{self.user.discriminator} (ID: {self.user.id})")

        return

    async def on_connect(self):
        """Called when the bot is connected to discord"""

        self.logger.info("Connected to Discord")

        return

    async def on_disconnect(self):
        """Called when the bot is disconnected from discord"""

        self.logger.info("Disconnected from discord")

        return

    async def on_error(self):
        """Report errors with the associated stacktrace"""

        self.logger.critical('An internal error occured:')

        for err in traceback.format_exc().split('\n'):
            self.logger.critical(err)

        return