from tkinter.filedialog import askopenfilenames
from tkinter.filedialog import askdirectory
import configparser
from tkinter import *
import asyncio
from discord.ext.commands import Bot
import requests
import os

# FIX DOWNLOAD
class Discord:
    def __init__(self):
        """Discord bot class
        Setup discord bot, connect to discord, get information from discord, upload and download pictures/attachments
        """
        # Bot setup
        self.client = Bot(command_prefix=",", description="Self bot", pm_help=None, self_bot=True)

        # Server variables
        self.servers = []
        self.server_selected = None

        # Channel variables
        self.channels = []
        self.channels_selected = []
        self.channel_selected = None

    async def connect_to_server(self, token):
        @self.client.event
        async def on_ready():  # Event for when the bot connects to server
            print('Logged in as')
            print(self.client.user.name)
        # WILL THROW AN EXCEPT. WILL CONNECT CORRECTLY. REASON IS EVENT LOOP IS ALREADY RUNNING
        try:
            await self.client.run(token, bot=False)
        except:
            pass

    async def update_servers(self):
        self.servers.clear()
        for server in self.client.servers:
            self.servers.append(server)

    async def get_servers(self):
        return self.servers

    async def set_server(self, selected):
        self.server_selected = self.servers[selected]

    async def update_channels(self, sort=True):
        self.channels.clear()
        for channel in self.server_selected.channels:
            try:
                if channel.type.name == "text":
                    self.channels.append(channel)
            except:
                pass
        if sort:
            self.channels.sort(key=lambda x: x.name)

    async def get_channels(self):
        return self.channels

    async def set_channels(self, selected):
        self.channels_selected.clear()
        for item in selected:
            self.channels_selected.append(self.channels[item])

    async def set_channel(self, selected):
        self.channel_selected = self.channels[selected]

    async def upload_files(self, files):
        for file in files:
            await self.client.send_file(self.channel_selected, file)

    # NEED TO CHANGE THIS. DOWNLOADS IS SLOW, DISCONNECTS ETC. ADD THREADING, SEPERATE MESSAGE AND DONWLOAD
    async def download_files(self, folder):
        try:
            os.mkdir(self.server_selected.name)
        except:
            print("Folder for server <{}> already exists".format(self.server_selected.name))
        count = 0
        for channel in self.channels_selected:
            os.chdir(folder+"/"+self.server_selected.name)
            try:
                os.mkdir(channel.name)
            except:
                print("Folder for channel <{}> already exists".format(channel.name))
            os.chdir(folder+"/"+self.server_selected.name+"/"+channel.name)
            async for message in self.client.logs_from(channel, limit=10000):
                try:
                    if message.embeds:
                        content_type = message.embeds[0]['type']
                        content_url = message.embeds[0]['url']
                        if content_type == 'image':
                            r = requests.get(content_url, allow_redirects=True)
                            filename = 'test' + str(count) + '.jpg'
                            open(filename, 'wb').write(r.content)
                    elif message.attachments:
                        content_filename = message.attachments[0]['filename']
                        content_url = message.attachments[0]['url']
                        r = requests.get(content_url, allow_redirects=True)
                        #filename = 'test' + str(count) + '.jpg'
                        open(content_filename, 'wb').write(r.content)
                except:
                    print("Failed to get attachment or embed")
                count += 1


class App:
    def __init__(self):
        """Tkinter app class.
        Setup of labels, buttons, entry fields, etc."""
        # App setup
        self.master = Tk()
        self.master.title("Discord uploader")
        self.master.geometry("{}x{}".format(640, 480))
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.master.bind("<Delete>", self.remove_downloads)

        # Run variables
        self.run = True
        self.interval = 0.05

        # Token variables
        config = configparser.ConfigParser()
        try:
            config.read("config.ini")
            self.token = config.get("Token", "Key")
        except:
            error_message = """
            Could not read config.ini file. Check if the file exist, and the token key is there.
            config.ini file should look like this:
            [Token]
            Key: 156841844.48sda334sd3ad
            """
            print(error_message)
            self.token = ""

        # Setup discord from discord class. Used to get all information and control bot
        self.discord = Discord()

        # Setup GUI, labels, entry, listbox, buttons, etc.
        self.entry_token = None
        self.listbox_servers = None
        self.listbox_channels = None
        self.listbox_downloads = None
        self.label_number_of_files = StringVar()
        self.setup_gui()

        # Other variables
        self.folder = ""
        self.files = []

    def setup_gui(self):
        frame = Frame(self.master)
        frame.grid(row=0, column=0, sticky=N + S + E + W)
        rows = 14
        cols = 3
        for row_index in range(rows):
            frame.rowconfigure(row_index, weight=1)
            for col_index in range(cols):
                frame.columnconfigure(col_index, weight=1)

        # TOKEN
        Label(frame, text="Token key", borderwidth=2, relief="groove").grid(row=0, columnspan=2, sticky="NWSE")
        self.entry_token = Entry(frame, borderwidth=2, relief="groove")
        self.entry_token.grid(row=1, columnspan=2, sticky="NWSE")
        self.entry_token.insert(0, self.token)
        Button(frame, text='Connect', command=self.connect, borderwidth=2, relief="groove").grid(row=0, column=2, rowspan=2, sticky="NWSE")

        # SERVER LIST
        Button(frame, text='Get servers', command=self.btn_get_servers, borderwidth=2, relief="groove").grid(row=2, sticky="NWSE")
        self.listbox_servers = Listbox(frame, selectmode=SINGLE, borderwidth=2, relief="groove")  # SINGLE, BROWSE, MULTIPLE, EXTENDED
        self.listbox_servers.grid(row=3, rowspan=4, sticky="NWSE")

        # CHANNEL LIST
        Button(frame, text='Get channels', command=self.btn_get_channels, borderwidth=2, relief="groove").grid(row=2, column=1, sticky="NWSE")
        self.listbox_channels = Listbox(frame, selectmode=EXTENDED, borderwidth=2, relief="groove")  # SINGLE, BROWSE, MULTIPLE, EXTENDED
        self.listbox_channels.grid(row=3, column=1, rowspan=4, sticky="NWSE")

        # OTHER
        Label(frame, textvariable=self.label_number_of_files, borderwidth=2, relief="groove").grid(row=2, column=2, sticky="NWSE")
        Button(frame, text='Browse files', command=self.browse_files, borderwidth=2, relief="groove").grid(row=3, column=2, sticky="NWSE")
        Button(frame, text='Upload files', command=self.upload_files, borderwidth=2, relief="groove").grid(row=4, column=2, sticky="NWSE")
        Button(frame, text='Browse folder', command=self.browse_folder, borderwidth=2, relief="groove").grid(row=5, column=2, sticky="NWSE")
        Button(frame, text='Download files', command=self.download_files, borderwidth=2, relief="groove").grid(row=6, column=2, sticky="NWSE")

        # DOWNLOAD LIST
        self.listbox_downloads = Listbox(frame, selectmode=EXTENDED, borderwidth=2, relief="groove")  # SINGLE, BROWSE, MULTIPLE, EXTENDED
        self.listbox_downloads.grid(row=7, rowspan=rows-7, columnspan=3, sticky="NWSE")

    async def run_tk(self):
        """Run a tkinter app in an asyncio event loop."""
        try:
            while self.run:
                self.master.update_idletasks()
                self.master.update()

                await asyncio.sleep(self.interval)
        except TclError as e:
            if "application has been destroyed" not in e.args[0]:
                raise

    def remove_downloads(self, event):
        """Remove downloads selected when "delete-key" is pressed"""
        selected = self.listbox_downloads.curselection()  # Get the downloads that are selected (int value list)
        for index in selected[::-1]:
            self.listbox_downloads.delete(index)

    def connect(self):
        self.token = self.entry_token.get()
        asyncio.ensure_future(self.discord.connect_to_server(self.token))  # async function instead of brackets

    def btn_get_servers(self):
        asyncio.ensure_future(self.get_servers())

    async def get_servers(self):
        self.listbox_servers.delete(0, END)
        await self.discord.update_servers()
        servers = await self.discord.get_servers()
        for server in servers:
            self.listbox_servers.insert(END, server.name)

    def btn_get_channels(self):
        asyncio.ensure_future(self.get_channels())

    async def get_channels(self):
        selected = self.listbox_servers.curselection()[0]  # Get the server that is selected (int value list)
        await self.discord.set_server(selected)

        self.listbox_channels.delete(0, END)
        await self.discord.update_channels()
        channels = await self.discord.get_channels()
        for channel in channels:
            self.listbox_channels.insert(END, channel.name)

    def browse_files(self):
        self.files = askopenfilenames()
        self.label_number_of_files.set("Files selected: " + str(len(self.files)))

    def upload_files(self):
        selected = self.listbox_channels.curselection()[0]  # Get the channel that is selected (int value list)
        asyncio.ensure_future(self.discord.set_channel(selected))
        asyncio.ensure_future(self.discord.upload_files(self.files))

    def browse_folder(self):
        self.folder = askdirectory()
        os.chdir(self.folder)

    def download_files(self):
        selected = self.listbox_channels.curselection()  # Get the channels that are selected (int value list)
        asyncio.ensure_future(self.discord.set_channels(selected))
        asyncio.ensure_future(self.discord.download_files(self.folder))

    def quit(self):
        self.run = False
        self.discord.client.close()
        self.master.quit()


async def main():
    app = App()
    app.master.protocol("WM_DELETE_WINDOW", app.quit)
    await app.run_tk()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
