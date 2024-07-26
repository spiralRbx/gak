import discord
import subprocess
import os

# Use os.getenv para obter as variáveis de ambiente
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID_OGG'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID_OGG'))

intents = discord.Intents.default()
intents.message_content = True

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_channel = None

    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        guild = discord.utils.get(self.guilds, id=GUILD_ID)
        if guild:
            self.target_channel = discord.utils.get(guild.text_channels, id=CHANNEL_ID)
            print(f'Target channel set to {self.target_channel.name}')
        else:
            print(f'Guild with ID {GUILD_ID} not found')

    async def on_message(self, message):
        print(f'Received a message: {message.content} from {message.author}')

        if message.content.startswith('!ogg'):
            if message.attachments:
                attachment = message.attachments[0]
                print(f'Attachment found: {attachment.filename}')

                if attachment.filename.lower().endswith(('ogg', 'mp3')):
                    await attachment.save(attachment.filename)

                    # Determina o formato de bit depth com base no comando
                    if message.content.startswith('!ogg 16bits'):
                        sample_fmt = 'pcm_s16le'
                        bit_depth = '16 bits'
                        temp_filename = f'{os.path.splitext(attachment.filename)[0]}_temp.wav'
                        output_filename = f'{os.path.splitext(attachment.filename)[0]}_16bits.ogg'
                    elif message.content.startswith('!ogg 24bits'):
                        sample_fmt = 'pcm_s24le'
                        bit_depth = '24 bits'
                        temp_filename = f'{os.path.splitext(attachment.filename)[0]}_temp.wav'
                        output_filename = f'{os.path.splitext(attachment.filename)[0]}_24bits.ogg'
                    elif message.content.startswith('!ogg 32float'):
                        sample_fmt = 'pcm_f32le'
                        bit_depth = '32 bits float'
                        temp_filename = f'{os.path.splitext(attachment.filename)[0]}_temp.wav'
                        output_filename = f'{os.path.splitext(attachment.filename)[0]}_32float.ogg'
                    else:
                        await message.channel.send('Profundidade de bits não suportada. Use `!ogg 16bits`, `!ogg 24bits` ou `!ogg 32float`.')
                        return

                    try:
                        # Primeiro, converta para WAV com o bit depth especificado usando ffmpeg
                        subprocess.run(
                            ['ffmpeg', '-i', attachment.filename, '-acodec', sample_fmt, temp_filename],
                            check=True
                        )

                        # Em seguida, converta de WAV para OGG usando ffmpeg
                        subprocess.run(
                            ['ffmpeg', '-i', temp_filename, '-acodec', 'libvorbis', output_filename],
                            check=True
                        )

                        if self.target_channel:
                            await self.target_channel.send(
                                content=f'Convertendo {attachment.filename} to {bit_depth}...',
                                file=discord.File(output_filename)
                            )
                            print(f'Sent converted file: {output_filename}')

                        # Remover arquivos temporários
                        os.remove(attachment.filename)
                        os.remove(temp_filename)
                        os.remove(output_filename)
                    except subprocess.CalledProcessError as e:
                        print(f'Error during conversion: {e}')
                        await message.channel.send('There was an error converting the file.')
                else:
                    print(f'Unsupported file type: {attachment.filename}')
                    await message.channel.send('Tipo de arquivo não suportado. Por favor carregue um arquivo ogg ou mp3.')
            else:
                print('No attachments found')
                await message.channel.send('Please attach a file to convert.')
        else:
            print('No command detected')

client = MyClient(intents=intents)
client.run(TOKEN)
